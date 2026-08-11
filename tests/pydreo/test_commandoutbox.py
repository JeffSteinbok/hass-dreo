"""Tests for the CommandOutbox component in isolation.

The outbox is pure scheduling machinery - these tests construct it directly
with a recording ``send`` callable and small timing constants. Device-level
behaviour (gate keys, optimistic state) is covered in the device test files;
the wider suite runs every device outbox in IMMEDIATE mode and so pins the
synchronous one-call-one-command behaviour throughout.
"""

import threading
import time

import pytest

from custom_components.dreo.pydreo.commandoutbox import CommandOutbox, OutboxTiming

from .testbase import wait_for

TIMING = OutboxTiming(quiet_period=0.03, max_wait=0.12, min_interval=0.0)


def timer_scheduler(delay: float, work) -> callable:
    """Stand-in for PyDreo.schedule_call_later's standalone Timer fallback.

    The outbox owns no threads of its own, so these tests supply the same kind
    of scheduler the library falls back to outside Home Assistant. That keeps
    them exercising real elapsed-time behaviour, which is the point for a
    concurrency component; tests that only care *when* a flush was requested
    use record_scheduler instead.
    """
    timer = threading.Timer(delay, work)
    timer.daemon = True
    timer.start()
    return timer.cancel


def record_scheduler() -> tuple[callable, list]:
    """A scheduler that records requested work instead of running it.

    Returns (schedule, entries) where each entry is
    {"delay", "work", "cancelled"} - the same shape TestBase installs on the
    manager, so assertions read the same way in both places.
    """
    entries: list[dict] = []

    def schedule(delay: float, work) -> callable:
        entry = {"delay": delay, "work": work, "cancelled": False}
        entries.append(entry)

        def cancel() -> None:
            entry["cancelled"] = True

        return cancel

    return schedule, entries


def make_outbox(timing: OutboxTiming = TIMING, schedule=timer_scheduler, **callbacks) -> tuple[CommandOutbox, list]:
    """Build an outbox whose sends append to the returned list."""
    sends: list = []
    outbox = CommandOutbox("test-device", timing, sends.append, schedule, **callbacks)
    return outbox, sends


class TestCollecting:
    """Merging behaviour of the collect window."""

    def test_burst_merges_into_one_send(self):
        """Keys submitted inside the quiet period ship as ONE merged batch."""
        outbox, sends = make_outbox()
        outbox.submit({"lighton": True})
        outbox.submit({"atmon": True})
        assert wait_for(lambda: len(sends) >= 1), "batch never flushed"
        time.sleep(0.1)  # several quiet periods: a second send would have fired by now
        assert sends == [{"lighton": True, "atmon": True}]

    def test_last_write_wins_within_window(self):
        """The same key submitted twice in one window sends once, last value."""
        outbox, sends = make_outbox()
        outbox.submit({"brightness": 30})
        outbox.submit({"brightness": 60})
        assert wait_for(lambda: len(sends) >= 1), "batch never flushed"
        time.sleep(0.1)
        assert sends == [{"brightness": 60}]

    def test_empty_submit_is_ignored(self):
        """An empty dict must not start a batch window or arm a timer."""
        outbox, sends = make_outbox()
        outbox.submit({})
        assert outbox.busy is False
        time.sleep(0.06)
        assert sends == []

    def test_max_wait_caps_a_continuous_stream(self):
        """A steady stream of keys must not postpone the first send past
        max_wait: the quiet-period timer alone would keep restarting."""
        send_times = []
        timing = OutboxTiming(quiet_period=0.06, max_wait=0.15, min_interval=0.0)
        outbox = CommandOutbox("test-device", timing, lambda params: send_times.append(time.monotonic()), timer_scheduler)

        start = time.monotonic()
        last_submit = start
        for value in range(10):
            outbox.submit({"brightness": value})
            last_submit = time.monotonic()
            time.sleep(0.03)
        assert wait_for(lambda: len(send_times) >= 1), "stream never flushed"

        assert send_times[0] - start < 0.30, f"first send took {send_times[0] - start:.3f}s (cap is 0.15s)"
        assert send_times[0] < last_submit, "cap should have fired while the stream was still running"

    def test_min_interval_paces_consecutive_sends(self):
        """Two batches too far apart to merge must still be spaced by
        min_interval (the hardware drops a command arriving <~250 ms after
        the previous one). The wait re-arms the timer; it never sleeps."""
        send_times = []
        sends = []

        def record(params):
            send_times.append(time.monotonic())
            sends.append(params)

        outbox = CommandOutbox("test-device", OutboxTiming(quiet_period=0.02, max_wait=0.05, min_interval=0.2), record, timer_scheduler)
        outbox.submit({"lighton": True})
        assert wait_for(lambda: len(send_times) == 1), "first batch never flushed"
        outbox.submit({"atmon": True})
        assert wait_for(lambda: len(send_times) == 2), "second batch never flushed"

        assert sends == [{"lighton": True}, {"atmon": True}]
        gap = send_times[1] - send_times[0]
        assert gap >= 0.18, f"sends not paced: gap={gap:.3f}s"

    def test_burst_requests_one_quiet_period_flush(self):
        """The scheduling decision itself: a burst asks the host for a flush
        ~quiet_period out, and each new key REPLACES that request rather than
        stacking another one."""
        schedule, entries = record_scheduler()
        outbox, sends = make_outbox(schedule=schedule)

        outbox.submit({"lighton": True})
        outbox.submit({"atmon": True})

        assert len(entries) == 2, "second key should re-arm"
        assert entries[0]["cancelled"] is True, "first request must be superseded, not left pending"
        pending = [e for e in entries if not e["cancelled"]]
        assert len(pending) == 1
        assert pending[0]["delay"] == pytest.approx(TIMING.quiet_period, abs=0.01)

        # The outbox re-validates timing when woken rather than trusting the
        # scheduler, so let the window actually pass before the host fires.
        time.sleep(TIMING.quiet_period + 0.01)
        pending[0]["work"]()
        assert sends == [{"lighton": True, "atmon": True}]

    def test_pacing_floor_is_requested_after_a_send(self):
        """Immediately after a send, the next flush must be requested no sooner
        than min_interval - the hardware drops anything closer."""
        schedule, entries = record_scheduler()
        timing = OutboxTiming(quiet_period=0.02, max_wait=0.05, min_interval=0.2)
        outbox, sends = make_outbox(timing=timing, schedule=schedule)

        outbox.submit({"lighton": True})
        time.sleep(timing.quiet_period + 0.01)
        [e for e in entries if not e["cancelled"]][0]["work"]()
        assert sends == [{"lighton": True}]

        # The fired request is spent, not cancelled (you do not cancel work that
        # already ran), so assert on the newest request rather than the count.
        outbox.submit({"atmon": True})
        newest = entries[-1]
        assert newest["cancelled"] is False
        assert newest["delay"] >= timing.min_interval, f"requested {newest['delay']}s, floor is {timing.min_interval}s"


class TestFlushing:
    """Send-side behaviour: draining, failure handling, cancellation."""

    def test_key_during_send_drains_in_next_batch(self):
        """A key submitted while a send is in flight is drained afterwards via
        a re-armed timer - not stranded, and not sent prematurely."""
        send_started = threading.Event()
        sends = []

        def slow_send(params):
            sends.append(params)
            send_started.set()
            time.sleep(0.12)

        outbox = CommandOutbox("test-device", OutboxTiming(0.02, 0.12, 0.0), slow_send, timer_scheduler)
        outbox.submit({"lighton": True})
        assert send_started.wait(timeout=2), "first batch never flushed"
        outbox.submit({"atmon": True})  # lands while the first send is sleeping
        assert wait_for(lambda: len(sends) == 2), "drained batch never flushed"
        assert sends == [{"lighton": True}, {"atmon": True}]

    def test_send_failure_drops_batch_and_recovers(self):
        """A failed send is dropped (never re-queued as a zombie) and must not
        wedge the outbox: the next submit flushes normally."""
        calls = []

        def failing_send(params):
            calls.append(params)
            if len(calls) == 1:
                raise RuntimeError("transport down")

        outbox = CommandOutbox("test-device", TIMING, failing_send, timer_scheduler)
        outbox.submit({"lighton": True})
        assert wait_for(lambda: len(calls) == 1), "first batch never attempted"
        assert wait_for(lambda: not outbox.busy), "outbox wedged after failure"

        outbox.submit({"lighton": False})
        assert wait_for(lambda: len(calls) == 2), "outbox did not recover"
        assert calls == [{"lighton": True}, {"lighton": False}]

    def test_cancel_drops_pending_and_stops_timer(self):
        """cancel() must silence a collecting batch entirely."""
        outbox, sends = make_outbox()
        outbox.submit({"lighton": True})
        outbox.cancel()
        assert outbox.busy is False
        time.sleep(0.1)  # far past quiet period + epsilon
        assert sends == []

    def test_busy_reflects_pending_and_in_flight(self):
        """busy covers both halves: keys collecting, and a send executing."""
        in_send = threading.Event()
        release = threading.Event()

        def blocking_send(_params):
            in_send.set()
            release.wait(timeout=2)

        outbox = CommandOutbox("test-device", TIMING, blocking_send, timer_scheduler)
        assert outbox.busy is False
        outbox.submit({"lighton": True})
        assert outbox.busy is True  # pending
        assert in_send.wait(timeout=2)
        assert outbox.busy is True  # in flight
        release.set()
        assert wait_for(lambda: not outbox.busy)


class TestCallbacks:
    """The callback contract."""

    def test_finalize_output_is_what_ships(self):
        """The wire batch is finalize's return value, not the raw merge."""
        outbox, sends = make_outbox(finalize=lambda params: {**params, "poweron": True})
        outbox.submit({"lighton": True})
        assert wait_for(lambda: len(sends) == 1)
        assert sends == [{"lighton": True, "poweron": True}]

    def test_finalize_added_keys_feed_back_through_on_submit(self):
        """Derived keys must reach on_submit so optimistic state includes them;
        the caller's own keys are not replayed a second time."""
        submitted = []
        outbox, sends = make_outbox(
            on_submit=submitted.append,
            finalize=lambda params: {**params, "poweron": True},
        )
        outbox.submit({"lighton": True})
        assert wait_for(lambda: len(sends) == 1)
        assert submitted == [{"lighton": True}, {"poweron": True}]

    def test_finalize_exception_drops_batch(self):
        """A finalize error must drop the batch, not wedge or send raw params."""
        calls = []

        def finalize_broken_once(params):
            calls.append(params)
            if len(calls) == 1:
                raise ValueError("bad params")
            return params

        outbox, sends = make_outbox(finalize=finalize_broken_once)
        outbox.submit({"lighton": True})
        assert wait_for(lambda: len(calls) == 1)
        assert wait_for(lambda: not outbox.busy)
        time.sleep(0.1)
        assert sends == []
        outbox.submit({"atmon": True})  # outbox still functional
        assert wait_for(lambda: sends == [{"atmon": True}])

    def test_finalize_returning_empty_sends_nothing(self):
        """finalize may veto a batch by returning an empty dict."""
        outbox, sends = make_outbox(finalize=lambda params: {})
        outbox.submit({"lighton": True})
        assert wait_for(lambda: not outbox.busy)
        time.sleep(0.1)
        assert sends == []

    def test_on_sent_fires_on_success_and_failure(self):
        """Post-send verification must run whether or not the transport threw -
        a failed send is precisely when state needs verifying."""
        sent_events = []

        def failing_send(params):
            if len(sent_events) == 0:
                raise RuntimeError("transport down")

        outbox = CommandOutbox("test-device", TIMING, failing_send, timer_scheduler, on_sent=lambda: sent_events.append(True))
        outbox.submit({"lighton": True})
        assert wait_for(lambda: len(sent_events) == 1), "on_sent skipped after failure"
        outbox.submit({"lighton": False})
        assert wait_for(lambda: len(sent_events) == 2), "on_sent skipped after success"

    def test_on_submit_sees_each_callers_keys(self):
        """on_submit runs per submit call with that caller's keys (optimistic
        state must reflect intent immediately, not at flush time)."""
        submitted = []
        outbox, _ = make_outbox(on_submit=submitted.append)
        outbox.submit({"lighton": True})
        outbox.submit({"atmon": True})
        assert submitted == [{"lighton": True}, {"atmon": True}]


class TestImmediateMode:
    """OutboxTiming.IMMEDIATE - the synchronous opt-out used by the suite."""

    def test_immediate_sends_synchronously_on_caller_thread(self):
        """No timers, no pacing: the send completes inside submit()."""
        sends = []
        thread_ids = []

        def record(params):
            sends.append(params)
            thread_ids.append(threading.get_ident())

        outbox = CommandOutbox("test-device", OutboxTiming.IMMEDIATE, record, timer_scheduler)
        outbox.submit({"lighton": True})
        outbox.submit({"atmon": True})
        assert sends == [{"lighton": True}, {"atmon": True}]
        assert thread_ids == [threading.get_ident()] * 2
        assert outbox.busy is False

    def test_immediate_send_exception_propagates_to_caller(self):
        """Synchronously, the submitting caller is still on the stack and owns the
        error - device classes clear in-flight bookkeeping in an `except` around
        the setter, so swallowing it would strand that state. The batch is still
        dropped and the outbox left usable."""

        def failing_send(_params):
            raise RuntimeError("transport down")

        outbox = CommandOutbox("test-device", OutboxTiming.IMMEDIATE, failing_send, timer_scheduler)
        with pytest.raises(RuntimeError, match="transport down"):
            outbox.submit({"lighton": True})
        assert outbox.busy is False

    def test_deferred_send_exception_is_contained(self):
        """Deferred batches have no caller left to raise to, so a failure is only
        logged and dropped - never re-queued as a zombie command."""
        calls = []

        def failing_send(params):
            calls.append(params)
            raise RuntimeError("transport down")

        outbox = CommandOutbox("test-device", TIMING, failing_send, timer_scheduler)
        outbox.submit({"lighton": True})  # must not raise out of submit
        assert wait_for(lambda: len(calls) == 1)
        assert wait_for(lambda: not outbox.busy)

    @pytest.mark.parametrize(
        ("timing", "expected"),
        [
            (OutboxTiming.IMMEDIATE, True),
            (OutboxTiming(quiet_period=0.0, max_wait=0.0, min_interval=0.5), True),
            (TIMING, False),
        ],
    )
    def test_is_immediate(self, timing, expected):
        """is_immediate keys off quiet_period alone."""
        assert timing.is_immediate is expected
