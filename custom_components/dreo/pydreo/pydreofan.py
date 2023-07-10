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

    def __init__(self, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        super().__init__(details, dreo)

        if (self.model not in SUPPORTED_TOWER_FANS):
            raise UnknownModelError(self.model)

        fan_details = SUPPORTED_TOWER_FANS[self.model]

        self._speed_range= fan_details.speed_range
        self._preset_modes = fan_details.preset_modes

    def __repr__(self):
        # Representation string of object.
        return "<{0}:{1}:{2}>".format(
            self.__class__.__name__, self._device_id, self._name
        )

    def handle_server_update(self, message):
        _LOGGER.debug("{}: got {} message **".format(self.name, message))

        valPoweron = self.get_server_update_key_value(message, POWERON_KEY)
        if (isinstance(valPoweron, bool)):
            self._is_on = valPoweron

        valWindType = self.get_server_update_key_value(message, WINDTYPE_KEY)
        if (isinstance(valWindType, int)):
            self._windType = valWindType

        # HAVE TO FIGURE OUT HOW TO DO THE MAPPING EXACTLY
        valWindLevel = self.get_server_update_key_value(message, WINDLEVEL_KEY)
        if (isinstance(valWindLevel, int)):
            self._fan_speed = valWindLevel

        valShakeHorizon = self.get_server_update_key_value(message, SHAKEHORIZON_KEY)
        if (isinstance(valShakeHorizon, bool)):
            self._oscillating = valShakeHorizon

        valTemperature = self.get_server_update_key_value(message, TEMPERATURE_KEY)
        if (isinstance(valTemperature, int)):
            self._temperature = valTemperature

    @property
    def speed_range(self):
        return self._speed_range

    @property
    def preset_modes(self):
        return self._preset_modes

    @property
    def is_on(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._is_on

    @property
    def fan_speed(self):
        return self._fan_speed

    @property
    def preset_mode(self):
        return self.preset_modes[self._windType - 1]

    @property
    def temperature(self):
        return self._temperature

    @property
    def oscillating(self):
        return self._oscillating

    def update_state(self, state: dict):
        _LOGGER.debug("PyDreoFan:update_state")
        super().update_state(state)
        self._fan_speed = state[WINDLEVEL_KEY][STATE_KEY]
        self._windType = state[WINDTYPE_KEY][STATE_KEY]
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

    def change_fan_speed(self, fan_speed: int):
        _LOGGER.debug("PyDreoFan:change_fan_speed")
        if fan_speed >= self._speed_range[0] and fan_speed <= self._speed_range[1]:
            self._send_command(WINDLEVEL_KEY, fan_speed)
        else:
            _LOGGER.error("Fan speed %s is not in the acceptable range: %s", fan_speed, self._speed_range)

    def oscillate(self, oscillating: bool) -> None:
        _LOGGER.debug("PyDreoFan:oscillate")
        self._send_command(SHAKEHORIZON_KEY, oscillating)
