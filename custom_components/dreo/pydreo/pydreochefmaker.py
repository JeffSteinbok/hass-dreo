"""Support for Dreo ChefMaker devices."""

import logging
from datetime import datetime, timezone
from typing import Dict, TYPE_CHECKING

from .constant import (
    POWERON_KEY,
)
from .models import DreoDeviceDetails

from .pydreobasedevice import PyDreoBaseDevice

if TYPE_CHECKING:
    from pydreo import PyDreo

LIGHT_KEY = "ledpotkepton"
MODE_KEY = "mode"
# The device does not report a live "remaining" value, and on the DR-KCM001S it never pushes an
# elapsed-duration field ("wkpdu" stays 0 for the whole cook - see #863).  "wkcountdown" is a
# static configured value (typically 300) that never changes either.  Instead the device reports
# the estimated total duration ("wkestdu") and the epoch timestamp at which the cook began
# ("wkbegin"), from which the absolute cook end time is derived (see cook_end_time).
COOK_TIME_ESTIMATED_KEY = "wkestdu"  # Estimated total cook duration in seconds.
COOK_TIME_BEGIN_KEY = "wkbegin"  # Epoch (seconds) at which the current cook began.
MODE_STANDBY = "standby"
MODE_CONFIGURING = "ckcfm"  # Transient "configuring" mode reported before a cook starts (see #868).
MODE_COOKING = "cooking"
MODE_PAUSED = "ckpause"
MODE_COMPLETE = "ckcomplete"
MODE_OFF = "off"

_LOGGER = logging.getLogger(__name__)


class PyDreoChefMaker(PyDreoBaseDevice):
    """Representation of a Dreo ChefMaker device."""

    def __init__(
        self,
        device_definition: DreoDeviceDetails,
        details: Dict[str, list],
        dreo: "PyDreo",
    ):
        """Initialize the ChefMaker device."""
        super().__init__(device_definition, details, dreo)
        self._is_on = False
        self._ledpotkepton = 0
        self.mode = None
        # Cook end time is derived from these two fields (see cook_end_time property).
        self._cook_time_estimated = None  # wkestdu: estimated total cook duration in seconds.
        self._cook_time_begin = None  # wkbegin: epoch (seconds) at which the current cook began.

    @property
    def cook_end_time(self) -> "datetime | None":
        """Return the absolute time at which the current cook is expected to finish.

        The device does not expose a live "remaining" field, and on the DR-KCM001S it never pushes
        an elapsed-duration field during a cook ("wkpdu" stays 0 the whole time - see #863), nor
        does it push anything at all between the "cooking" and "ckcomplete" reports (see #868).  A
        ticking duration sensor would therefore freeze between pushes.  Instead we expose the cook
        end time as a timezone-aware timestamp derived from the estimated total duration
        ("wkestdu") and the epoch at which the cook began ("wkbegin"): wkbegin + wkestdu.  This is
        written once per cook, so it never clutters history with synthetic state changes, and the
        Home Assistant frontend renders it as a live relative countdown on its own.

        Returns None unless a cook is actively in progress (mode cooking or paused) with valid
        duration/begin fields.  Gating on the active modes avoids surfacing a stale "wkbegin" left
        over from a previous cook while the next cook is still configuring (mode "ckcfm"), the
        stale-timestamp scenario guarded against in #864.
        """
        if self._mode not in (MODE_COOKING, MODE_PAUSED):
            return None
        if not isinstance(self._cook_time_estimated, int) or not isinstance(self._cook_time_begin, int):
            return None
        if self._cook_time_estimated <= 0:
            return None
        return datetime.fromtimestamp(self._cook_time_begin + self._cook_time_estimated, tz=timezone.utc)

    @property
    def is_on(self) -> bool:
        """Return True if device is on."""
        return self._is_on

    @is_on.setter
    def is_on(self, value: bool) -> None:
        """Set the power state of the device."""
        self._is_on = value
        self.set_mode_from_is_on()
        self._send_command(POWERON_KEY, value)

    @property
    def ledpotkepton(self) -> bool:
        """Return True if device is on."""
        return self._ledpotkepton > 0

    @ledpotkepton.setter
    def ledpotkepton(self, value: bool) -> None:
        """Set the power state of the device."""
        new_value = 1 if value else 0
        if self._ledpotkepton == new_value:
            _LOGGER.debug("ledpotkepton: ledpotkepton - value already %s, skipping command", value)
            return
        self._ledpotkepton = new_value
        self._send_command(LIGHT_KEY, self._ledpotkepton)

    @property
    def mode(self) -> str:
        """Return the current mode."""
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        """Set the mode of the device."""
        self._mode = value

    def set_mode_from_is_on(self) -> None:
        """Set the mode based on the power state."""
        val = MODE_STANDBY if self._is_on else MODE_OFF
        _LOGGER.debug("set_mode_from_is_on: %s --> %s", self.mode, val)
        self.mode = val

    def update_state(self, state: dict) -> None:
        """Process the state dictionary from the REST API."""
        super().update_state(state)  # handles _is_on

        _LOGGER.debug("update_state: %s", state)

        self._is_on = self.get_state_update_value(state, POWERON_KEY)
        self.set_mode_from_is_on()
        self._ledpotkepton = self.get_state_update_value(state, LIGHT_KEY)
        self._cook_time_estimated = self.get_state_update_value(state, COOK_TIME_ESTIMATED_KEY)
        self._cook_time_begin = self.get_state_update_value(state, COOK_TIME_BEGIN_KEY)

        if self.is_on:
            self.mode = self.get_state_update_value(state, MODE_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("handle_server_update: %s", message)

        val_poweron = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_poweron, bool):
            _LOGGER.debug(
                "handle_server_update: poweron: %s --> %s",
                self._is_on,
                val_poweron,
            )
            self._is_on = val_poweron  # Ensure poweron state is updated
            self.set_mode_from_is_on()

        val_ledpotkepton = self.get_server_update_key_value(message, LIGHT_KEY)
        if isinstance(val_ledpotkepton, int):
            _LOGGER.debug(
                "handle_server_update: ledpotkepton: %s --> %s",
                self._ledpotkepton,
                val_ledpotkepton,
            )
            self._ledpotkepton = val_ledpotkepton

        val_mode = self.get_server_update_key_value(message, MODE_KEY)
        if isinstance(val_mode, str):
            _LOGGER.debug(
                "handle_server_update: mode: %s --> %s",
                self.mode,
                val_mode,
            )
            self.mode = val_mode

        val_cook_time_estimated = self.get_server_update_key_value(message, COOK_TIME_ESTIMATED_KEY)
        if isinstance(val_cook_time_estimated, int):
            self._cook_time_estimated = val_cook_time_estimated

        val_cook_time_begin = self.get_server_update_key_value(message, COOK_TIME_BEGIN_KEY)
        if isinstance(val_cook_time_begin, int):
            self._cook_time_begin = val_cook_time_begin

        if isinstance(val_cook_time_estimated, int) or isinstance(val_cook_time_begin, int):
            _LOGGER.debug(
                "handle_server_update: cook_end_time: estimated=%s begin=%s --> %s",
                self._cook_time_estimated,
                self._cook_time_begin,
                self.cook_end_time,
            )
