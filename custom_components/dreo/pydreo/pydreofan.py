"""Dreo API for controling fans."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    POWERON_KEY,
    WINDLEVEL_KEY,
    TEMPERATURE_KEY,
    LEDALWAYSON_KEY,
    VOICEON_KEY,
    PyDreoFanDefinition,
    TemperatureUnit
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
        self._display_auto_off = None
        self._panel_sound = None

    def __repr__(self):
        # Representation string of object.
        return "<{0}:{1}:{2}>".format(
            self.__class__.__name__, self._device_id, self._name
        )

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
    def temperature_units(self) -> TemperatureUnit:
        """Get the temperature units."""
        # I'm not sure how the API returns in other regions, so I'm just auto-detecting
        # based on some reasonable range.
        
        # Going to return Celcius as the default.  None of this matters if there is no
        # temperature returned anyway
        if self._temperature is not None:
            if self._temperature > 50:
                return TemperatureUnit.FAHRENHEIT
            
        return TemperatureUnit.CELCIUS

    @property
    def oscillating(self) -> bool:
        """Get if the fan is oscillating"""

    @oscillating.setter
    def oscillating(self, value: bool) -> None:
        """Set if the fan is oscillating"""

    @property
    def display_auto_off(self) -> bool:
        """Is the display always on?"""
        return self._display_auto_off
    
    @display_auto_off.setter
    def display_auto_off(self, value: bool) -> None:
        """Set if the display is always on"""
        _LOGGER.debug("PyDreoFan:display_auto_off.setter")
        
        if (self.display_auto_off is None):
            _LOGGER.error("Attempting to set display always on on a device that doesn't support.")
            return
        
        self._send_command(LEDALWAYSON_KEY, not value)

    @property
    def panel_sound(self) -> bool:
        """Is the panel sound on"""
        return self._panel_sound
    
    @panel_sound.setter
    def panel_sound(self, value: bool) -> None:
        """Set if the panel sound"""
        _LOGGER.debug("PyDreoFan:panel_sound.setter")
        
        if (self.panel_sound is None):
            _LOGGER.error("Attempting to set panel_sound on a device that doesn't support.")
            return
        
        self._send_command(VOICEON_KEY, value)
        
        
    def update_state(self, state: dict) :
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("PyDreoFan:update_state")
        super().update_state(state)
        self._fan_speed = self.get_state_update_value(state, WINDLEVEL_KEY)
        self._temperature = self.get_state_update_value(state, TEMPERATURE_KEY)
        self._display_auto_off = not self.get_state_update_value(state, LEDALWAYSON_KEY)
        self._panel_sound = self.get_state_update_value(state, VOICEON_KEY)

        
    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("PyDreoFan:handle_server_update")

        val_power_on = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_power_on, bool):
            self._is_on = val_power_on

        val_wind_level = self.get_server_update_key_value(message, WINDLEVEL_KEY)
        if isinstance(val_wind_level, int):
            self._fan_speed = val_wind_level

        val_temperature = self.get_server_update_key_value(message, TEMPERATURE_KEY)
        if isinstance(val_temperature, int):
            self._temperature = val_temperature

        val_display_always_on = self.get_server_update_key_value(message, LEDALWAYSON_KEY)
        if isinstance(val_display_always_on, bool):
            self._display_auto_off = not val_display_always_on

        val_panel_sound = self.get_server_update_key_value(message, VOICEON_KEY)
        if isinstance(val_panel_sound, bool):
            self._panel_sound = val_panel_sound