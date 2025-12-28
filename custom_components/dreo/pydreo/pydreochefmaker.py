"""Support for Dreo ChefMaker devices."""
import logging
from typing import Dict, TYPE_CHECKING

from .constant import (
    LOGGER_NAME,
    POWERON_KEY,
)
from .models import DreoDeviceDetails

from .pydreobasedevice import PyDreoBaseDevice

if TYPE_CHECKING:
    from pydreo import PyDreo

LIGHT_KEY = "ledpotkepton"
MODE_KEY = "mode"
MODE_STANDBY = "standby"
MODE_COOKING = "cooking"
MODE_PAUSED = "ckpause"
MODE_OFF = "off"

_LOGGER = logging.getLogger(LOGGER_NAME)


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

    @property
    def is_on(self) -> bool:
        """Return True if device is on."""
        return self._is_on

    @is_on.setter
    def is_on(self, value: bool) -> None:
        """Set the power state of the device."""
        if self._is_on == value:
            _LOGGER.debug("PyDreoChefMaker:is_on - value already %s, skipping command", value)
            return
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
            _LOGGER.debug("PyDreoChefMaker:ledpotkepton - value already %s, skipping command", value)
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
        _LOGGER.debug(
            "PyDreoChefMaker(%s):set_mode_from_is_on: %s --> %s", self, self.mode, val
        )
        self.mode = val

    def update_state(self, state: dict) -> None:
        """Process the state dictionary from the REST API."""
        super().update_state(state)  # handles _is_on

        _LOGGER.debug("PyDreoChefMaker(%s):update_state: %s", self, state)

        self._is_on = self.get_state_update_value(state, POWERON_KEY)
        self.set_mode_from_is_on()
        self._ledpotkepton = self.get_state_update_value(state, LIGHT_KEY)

        if self.is_on:
            self.mode = self.get_state_update_value(state, MODE_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug(
            "PyDreoChefMaker:handle_server_update(%s): %s", self.name, message
        )

        val_poweron = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_poweron, bool):
            _LOGGER.debug(
                "PyDreoChefMaker:handle_server_update - poweron: %s --> %s",
                self._is_on,
                val_poweron,
            )
            self._is_on = val_poweron  # Ensure poweron state is updated
            self.set_mode_from_is_on()

        val_ledpotkepton = self.get_server_update_key_value(message, LIGHT_KEY)
        if isinstance(val_ledpotkepton, int):
            _LOGGER.debug(
                "PyDreoChefMaker:handle_server_update - ledpotkepton: %s --> %s",
                self._ledpotkepton,
                val_ledpotkepton,
            )
            self._ledpotkepton = val_ledpotkepton

        val_mode = self.get_server_update_key_value(message, MODE_KEY)
        if isinstance(val_mode, str):
            _LOGGER.debug(
                "PyDreoChefMaker:handle_server_update - mode: %s --> %s",
                self.mode,
                val_mode,
            )
            self.mode = val_mode
