"""Dreo API for controling fans."""

import logging
from typing import Dict
from typing import TYPE_CHECKING

from .pydreobasedevice import PyDreoBaseDevice, UnknownModelError
from .models import SUPPORTED_TOWER_FANS
from .constant import *

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoFan(PyDreoBaseDevice):
    """Base class for Dreo Fan API Calls."""

    def __init__(self, fan_definition: PyDreoFanDefinition, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        super().__init__(details, dreo)

        self._fan_definition = fan_definition

    def __repr__(self):
        # Representation string of object.
        return "<{0}:{1}:{2}>".format(
            self.__class__.__name__, self._device_id, self._name
        )

    def handle_server_update(self, message):
        valPoweron = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(valPoweron, bool):
            self._is_on = valPoweron

        valWindLevel = self.get_server_update_key_value(message, WINDLEVEL_KEY)
        if isinstance(valWindLevel, int):
            self._fan_speed = valWindLevel

        valTemperature = self.get_server_update_key_value(message, TEMPERATURE_KEY)
        if isinstance(valTemperature, int):
            self._temperature = valTemperature

    @property
    def speed_range(self):
        return self._fan_definition.speed_range

    @property
    def preset_modes(self):
        return self._fan_definition.preset_modes
            
    @property
    def is_on(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._is_on

    @property
    def fan_speed(self):
        return self._fan_speed

    @property
    def preset_mode(self):
        pass

    @property
    def temperature(self):
        return self._temperature

    @property
    def supports_oscillation(self):
        pass

    @property
    def oscillating(self):
        pass
    
    def update_state(self, state: dict) :
        _LOGGER.debug("PyDreoFan:update_state")
        super().update_state(state)
        self._fan_speed = state[WINDLEVEL_KEY][STATE_KEY]
        self._temperature = state[TEMPERATURE_KEY][STATE_KEY]
        self._oscillating = state[SHAKEHORIZON_KEY][STATE_KEY]

    def set_power(self, value: bool):
        _LOGGER.debug("PyDreoFan:set_power")
        self._send_command(POWERON_KEY, value)

    def set_preset_mode(self, preset_mode: str):
        _LOGGER.debug("PyDreoFan:set_preset_mode")        
        if (preset_mode in self.preset_modes):
            self._send_command(WINDTYPE_KEY, self._preset_modes.index(preset_mode) + 1)
        else:
            _LOGGER.error("Preset mode %s is not in the acceptable list: %s", preset_mode, self._preset_modes)
    
    def change_fan_speed(self, fan_speed : int) :
        # TODO: Make sure fan speed in range
        self._send_command(WINDLEVEL_KEY, fan_speed)
