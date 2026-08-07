"""Per-device outbox that coalesces command keys into single requests.

Near-simultaneous key changes (scenes, Adaptive Lighting, linked wall switches)
historically went out as separate single-key commands milliseconds apart, and
DR-HCF002S hardware silently drops a command arriving <~250 ms after the
previous one (probe-measured: 10/50/100 ms gaps dropped, 250/500 ms landed) -
while the same keys sent as ONE command always land, up to at least 10 keys.
Each device therefore collects outgoing keys in an outbox and flushes them as
one command.

The outbox never creates threads of its own: the delayed flush is handed to a
host scheduler injected at construction (``PyDreo.schedule_call_later``, which
under Home Assistant is ``async_call_later`` running the work in an executor
job, and a daemon ``threading.Timer`` when running standalone). That keeps
timer lifecycle with the host, so everything is cancelled on unload.
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import ClassVar

_LOGGER = logging.getLogger(__name__)

# Lands the timer callback just past its deadline instead of a float hair before it.
_TIMER_EPSILON = 0.005


@dataclass(frozen=True)
class OutboxTiming:
    """Timing profile for a CommandOutbox."""

    # Seconds of key-silence that ends a batch. Observed automation bursts have
    # up to ~83 ms between keys; anything shorter splits a burst.
    quiet_period: float
    # Hard cap on total collection time once a batch has started, so a steady
    # stream of changes cannot delay the first send indefinitely.
    max_wait: float
    # Minimum spacing between consecutive sends to one device (2x the measured
    # 250 ms hardware safe point).
    min_interval: float

    # Flush synchronously on the caller's thread with no pacing - the exact
    # historical one-call-one-command behaviour. For device classes that opt
    # out of batching, and for the test suites.
    IMMEDIATE: ClassVar["OutboxTiming"]

    @property
    def is_immediate(self) -> bool:
        """True if keys are sent synchronously instead of collected."""
        return self.quiet_period <= 0


OutboxTiming.IMMEDIATE = OutboxTiming(quiet_period=0.0, max_wait=0.0, min_interval=0.0)


class CommandOutbox:
    """Collects command keys and flushes them as single merged commands.

    ``submit`` merges keys into the pending batch (last value per key wins);
    the batch is sent once ``timing.quiet_period`` elapses with no new keys or
    ``timing.max_wait`` after its first key - whichever comes first - but never
    sooner than ``timing.min_interval`` after the previous send. Waits are
    implemented by re-scheduling, never by sleeping, so keys arriving during a
    wait join the batch. ``timing`` is read live on every decision and may be
    replaced at runtime.

    Callback contract:

    * ``schedule(delay, work) -> cancel`` - the host's delayed-call scheduler
      (``PyDreo.schedule_call_later``). The outbox owns no threads itself, so
      the host controls when ``work`` runs and can cancel everything on unload.
      ``work`` may land on any thread, and ``cancel`` must be safe to call from
      another one.

    * ``send(params)`` - the transport call. Invoked OUTSIDE the outbox lock:
      it may block for seconds (ack waits, transport retries), and holding the
      lock would stall every submitter behind it. A failed send is logged and
      the batch DROPPED, never re-queued - a zombie command firing long after
      the user's action is worse than a drop, and state verification heals
      divergence. In immediate mode the error is also re-raised, because the
      submitting caller is still on the stack and owns it (device classes
      unwind in-flight bookkeeping in an ``except`` around the setter); a
      deferred batch has no caller left to tell, so it is only logged.
    * ``on_submit(params)`` - under the lock, once per ``submit`` with that
      caller's keys, and again at flush time with any keys ``finalize`` added.
      Devices apply optimistic local state here.
    * ``finalize(params) -> dict`` - under the lock, on the merged batch just
      before sending. An exception drops the batch.
    * ``on_sent()`` - after every send attempt, success or failure, outside
      the lock.

    ``on_submit`` and ``finalize`` share the lock so that by the time
    ``finalize`` reads device state, every key in the claimed batch has already
    been folded into that state (device classes derive cross-key semantics,
    e.g. power-gate keys, on that assumption). Both must be fast and must never
    block. Callbacks run on the submitting thread (immediate mode and inline
    drains) or on whichever thread the host scheduler dispatches ``work`` to -
    under Home Assistant an executor thread, never the event loop.
    """

    def __init__(
        self,
        name: str,
        timing: OutboxTiming,
        send: Callable[[dict], None],
        schedule: Callable[[float, Callable[[], None]], Callable[[], None]],
        *,
        on_submit: Callable[[dict], None] | None = None,
        finalize: Callable[[dict], dict] | None = None,
        on_sent: Callable[[], None] | None = None,
    ) -> None:
        self._name = name
        self.timing = timing
        self._send = send
        self._schedule = schedule
        self._on_submit = on_submit
        self._finalize = finalize
        self._on_sent = on_sent

        self._lock = threading.Lock()
        self._pending: dict = {}
        self._cancel_scheduled: Callable[[], None] | None = None
        self._disposed = False
        self._in_flight = False
        self._batch_started = 0.0
        self._last_submit = 0.0
        self._last_send = float("-inf")

    def submit(self, params: dict) -> None:
        """Merge params into the pending batch and (re)schedule its flush."""
        if not params:
            return
        with self._lock:
            if self._disposed:
                _LOGGER.debug("outbox %s: disposed; dropping %s", self._name, params)
                return
            now = time.monotonic()
            if not self._pending:
                self._batch_started = now
            self._pending.update(params)
            self._last_submit = now
            if self._on_submit is not None:
                self._on_submit(params)
            flush_inline = self.timing.is_immediate
            if not flush_inline and not self._in_flight:
                # If a send is in flight, its drain step re-arms instead.
                self._arm(self._delay_until_ready(now))
        if flush_inline:
            self._flush()

    def cancel(self) -> None:
        """Drop unsent keys and cancel any pending flush.

        Called from the owning device's ``dispose()`` on unload, so it also
        latches the outbox closed: a later ``submit`` must not re-arm work
        against a torn-down transport. An already-running send is not aborted.
        """
        with self._lock:
            self._disposed = True
            self._cancel_scheduled_locked()
            if self._pending:
                _LOGGER.debug("outbox %s: dropping unsent %s", self._name, self._pending)
                self._pending = {}

    @property
    def busy(self) -> bool:
        """True while keys are pending or a send is in flight."""
        with self._lock:
            return bool(self._pending) or self._in_flight

    def _delay_until_ready(self, now: float) -> float:
        """Seconds until the pending batch may be sent; <= 0 means ready now.

        Caller must hold the lock.
        """
        timing = self.timing
        quiet_remaining = timing.quiet_period - (now - self._last_submit)
        max_wait_remaining = timing.max_wait - (now - self._batch_started)
        pace_remaining = timing.min_interval - (now - self._last_send)
        return max(min(quiet_remaining, max_wait_remaining), pace_remaining)

    def _cancel_scheduled_locked(self) -> None:
        """Cancel the pending flush, if any. Caller must hold the lock."""
        if self._cancel_scheduled is None:
            return
        try:
            self._cancel_scheduled()
        except Exception as ex:  # pylint: disable=broad-except
            # Teardown race: the handle may already be invalid.
            _LOGGER.debug("outbox %s: cancel handle failed: %s", self._name, ex)
        self._cancel_scheduled = None

    def _arm(self, delay: float) -> None:
        """(Re)arm the flush. Caller must hold the lock.

        Delegated to the host scheduler so Home Assistant owns the lifecycle
        (event-loop timers cancelled on unload); the epsilon lands the callback
        just past the deadline instead of a float hair before it.
        """
        self._cancel_scheduled_locked()
        self._cancel_scheduled = self._schedule(max(delay, 0.0) + _TIMER_EPSILON, self._on_timer)

    def _on_timer(self) -> None:
        """Scheduler entry point; an uncaught exception here dies silently.

        May run on any thread the host picks (under Home Assistant, an executor
        job), so it must not assume it is on the event loop.
        """
        with self._lock:
            # This scheduled work is now running; its handle is spent.
            self._cancel_scheduled = None
            if self._disposed:
                return
        try:
            self._flush()
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("outbox %s: error flushing command batch", self._name)

    def _claim_batch(self) -> dict | None:
        """Claim the pending batch if it is ready to send.

        Returns the finalized params, or None if there is nothing to do or a
        timer was (re)armed for later. Timing is validated here rather than
        trusted from the timer: ``Timer.cancel()`` cannot stop a callback that
        has already started, so a stale callback may fire moments after a
        fresh submit restarted the window.
        """
        with self._lock:
            if not self._pending or self._in_flight:
                return None
            if not self.timing.is_immediate:
                delay = self._delay_until_ready(time.monotonic())
                if delay > 0:
                    self._arm(delay)
                    return None
            snapshot = self._pending
            self._pending = {}
            try:
                params = dict(snapshot) if self._finalize is None else self._finalize(dict(snapshot))
                # Fold derived keys (e.g. gate keys) into local state too.
                derived = {key: value for key, value in params.items() if key not in snapshot}
                if derived and self._on_submit is not None:
                    self._on_submit(derived)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("outbox %s: finalize failed; dropping batch %s", self._name, snapshot)
                return None
            if not params:
                return None
            self._in_flight = True
            return params

    def _flush(self) -> None:
        """Send the ready batch; drain anything submitted during the send."""
        while True:
            params = self._claim_batch()
            if params is None:
                return
            send_error: Exception | None = None
            try:
                _LOGGER.debug("outbox %s: sending batch %s", self._name, params)
                self._send(params)
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.warning("outbox %s: send failed; dropping batch %s: %s", self._name, params, ex)
                send_error = ex
            drain_inline = False
            with self._lock:
                self._last_send = time.monotonic()
                self._in_flight = False
                if self._pending:
                    # Drain step: keys arrived during the send. Without this
                    # they would sit here until some future submit.
                    if self.timing.is_immediate:
                        drain_inline = True
                    else:
                        self._arm(self._delay_until_ready(time.monotonic()))
            if self._on_sent is not None:
                try:
                    self._on_sent()
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("outbox %s: post-send hook failed", self._name)
            if send_error is not None and self.timing.is_immediate:
                # Immediate mode still has the submitting caller on the stack, and
                # that caller owns the error - device classes unwind their own
                # in-flight bookkeeping in an `except` around the setter. Deferred
                # batches have no caller left to tell, so there the failure is only
                # logged and the batch dropped (never re-queued: a zombie command
                # firing after a reconnect outlives the user's action).
                raise send_error
            if not drain_inline:
                return
