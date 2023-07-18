"""Dreo API for controling fans."""

import logging
from typing import Dict
from typing import TYPE_CHECKING

from .pydreobasedevice import PyDreoBaseDevice, UnknownModelError
from .helpers import Helpers

from .constant import *

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo

class PyDreoFan(PyDreoBaseDevice):
    """Base class for Dreo Fan API Calls."""

    def __init__(self, details: Dict[str, list], dreo : "PyDreo"):
        """Initialize air devices."""
        super().__init__(details, dreo)

        if (self.model not in SUPPORTED_FANS):
            raise UnknownModelError(self.model)
        
        self._fan_definition = SUPPORTED_FANS[self.model]
        
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

        valWindLevel = self.get_server_update_key_value(message, WINDLEVEL_KEY)
        if (isinstance(valWindLevel, int)):
            self._fan_speed = valWindLevel          

        valShakeHorizon = self.get_server_update_key_value(message, SHAKEHORIZON_KEY)
        if (isinstance(valShakeHorizon, bool)):
            self._oscillation_mode = OscillationMode.HORIZONTAL if valShakeHorizon else OscillationMode.OFF

        valOscMode = self.get_server_update_key_value(message, OSCMODE_KEY)
        if (isinstance(valOscMode, int)):
            self._oscillation_mode = valOscMode

        valTemperature = self.get_server_update_key_value(message, TEMPERATURE_KEY)
        if (isinstance(valTemperature, int)):
            self._temperature = valTemperature            

    @property
    def speed_range(self):
        return self._fan_definition.speed_range

    @property
    def preset_modes(self):
        return self._fan_definition.preset_modes
            
    @property
    def oscillation_support(self):
        return self._fan_definition.oscillation_support
    
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
    def oscillation_mode(self):
        return self._oscillation_mode
    
    def update_state(self, state: dict) :
        _LOGGER.debug("PyDreoFan:update_state")
        super().update_state(state)
        self._fan_speed = state[WINDLEVEL_KEY][STATE_KEY]
        self._windType = state[WINDTYPE_KEY][STATE_KEY]
        self._temperature = state[TEMPERATURE_KEY][STATE_KEY]

        if (self.oscillation_support == OscillationSupport.BOTH):
            self._oscillation_mode = state[OSCMODE_KEY][STATE_KEY]
        elif (self.oscillation_support == OscillationSupport.HORIZONTAL):
            self._oscillation_mode = OscillationMode.HORIZONTAL if (state[SHAKEHORIZON_KEY][STATE_KEY] == True) else OscillationMode.OFF

    def set_power(self, value: bool):
        _LOGGER.debug("PyDreoFan:set_power")
        self._send_command(POWERON_KEY, value)

    def set_preset_mode(self, preset_mode: str):
        _LOGGER.debug("PyDreoFan:set_preset_mode")        
        if (preset_mode in self.preset_modes):
            self._send_command(WINDTYPE_KEY, self._fan_definition.preset_modes.index(preset_mode) + 1)
        else:
            _LOGGER.error("Preset mode %s is not in the acceptable list: %s", preset_mode, self._fan_definition.preset_modes)
    
    def change_fan_speed(self, fan_speed : int) :
        # TODO: Make sure fan speed in range
        self._send_command(WINDLEVEL_KEY, fan_speed)

    def oscillate(self, oscillating: bool) -> None:
        self._send_command(SHAKEHORIZON_KEY, oscillating)

