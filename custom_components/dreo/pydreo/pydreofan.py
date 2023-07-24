"""Dreo API for controling fans."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    POWERON_KEY,
    WINDLEVEL_KEY,
    TEMPERATURE_KEY,
    PyDreoFanDefinition
)

from .pydreobasedevice import PyDreoBaseDevice

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo

class PyDreoFan(PyDreoBaseDevice):
    """Base class for Dreo Fan API Calls."""

    def __init__(self, fan_definition: PyDreoFanDefinition, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        super().__init__(details, dreo)

        self._fan_definition = fan_definition
        self._fan_speed = None
        self._temperature = None

    def __repr__(self):
        # Representation string of object.
        return "<{0}:{1}:{2}>".format(
            self.__class__.__name__, self._device_id, self._name
        )

    def handle_server_update(self, message):
        val_power_on = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_power_on, bool):
            self._is_on = val_power_on

        val_wind_level = self.get_server_update_key_value(message, WINDLEVEL_KEY)
        if isinstance(val_wind_level, int):
            self._fan_speed = val_wind_level

        val_temperature = self.get_server_update_key_value(message, TEMPERATURE_KEY)
        if isinstance(val_temperature, int):
            self._temperature = val_temperature

    @property
    def speed_range(self):
        """Get the speed range"""
        return self._fan_definition.speed_range

    @property
    def preset_modes(self):
        """Get the list of preset modes"""
        return self._fan_definition.preset_modes

    @property
    def is_on(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._is_on

    @is_on.setter
    def is_on(self, value: bool):
        """Set if the fan is on or off"""
        _LOGGER.debug("PyDreoFan:is_on.setter - %s", value)
        self._send_command(POWERON_KEY, value)

    @property
    def fan_speed(self):
        """Return the curretn fan speed"""
        return self._fan_speed

    @fan_speed.setter
    def fan_speed(self, fan_speed : int) :
        """Set the fan speed."""
        # TODO: Make sure fan speed in range
        self._send_command(WINDLEVEL_KEY, fan_speed)

    @property
    def preset_mode(self):
        """Get the preset mode"""

    @preset_mode.setter
    def preset_mode(self, value: str) -> None:
        """Set the preset mode"""

    @property
    def temperature(self):
        """Get the temperature"""
        return self._temperature

    @property
    def oscillating(self) -> bool:
        """Get if the fan is oscillating"""

    @oscillating.setter
    def oscillating(self, value: bool) -> None:
        """Set if the fan is oscillating"""

    def update_state(self, state: dict) :
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("PyDreoFan:update_state")
        super().update_state(state)
        self._fan_speed = self.get_state_update_value(state, WINDLEVEL_KEY)
        self._temperature = self.get_state_update_value(state, TEMPERATURE_KEY)