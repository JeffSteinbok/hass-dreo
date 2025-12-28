"""Dreo API for controlling Dehumidifiers."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    MODE_KEY,
    MUTEON_KEY,
    POWERON_KEY,
    HUMIDITY_KEY,
    WINDLEVEL_KEY,
    CHILDLOCKON_KEY,
    LIGHTON_KEY,
    SPEED_RANGE,
    TEMPERATURE_KEY
)

from .pydreobasedevice import PyDreoBaseDevice
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo

# Dehumidifier-specific constants
RHAUTOLEVEL_KEY = "rhautolevel"
AUTOON_KEY = "autoon"

class PyDreoDehumidifier(PyDreoBaseDevice):
    """Base class for Dreo Dehumidifiers"""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize dehumidifier devices."""
        super().__init__(device_definition, details, dreo)

        self._modes = [("Auto", 1), ("Continuous", 2)]
        
        self._mode = None
        self._mute_on = None
        self._humidity = None
        self._target_humidity = None
        self._wind_level = None
        self._child_lock_on = None
        self._light_on = None
        self._auto_on = None
        self._temperature = None
        
        self._speed_range = device_definition.device_ranges.get(SPEED_RANGE, (1, 3)) if device_definition.device_ranges else (1, 3)
        
    @property
    def is_on(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._is_on

    @is_on.setter
    def is_on(self, value: bool):
        """Set if the dehumidifier is on or off"""
        _LOGGER.debug("PyDreoDehumidifier:is_on.setter - %s", value)
        if self._is_on == value:
            _LOGGER.debug("PyDreoDehumidifier:is_on - value already %s, skipping command", value)
            return
        self._send_command(POWERON_KEY, value)

    @property
    def modes(self) -> list[str]:
        """Get the list of operating modes"""
        return [mode[0] for mode in self._modes]

    @property
    def humidity(self):
        """Get the current humidity"""
        return self._humidity

    @property
    def target_humidity(self):
        """Get the target humidity"""
        return self._target_humidity

    @target_humidity.setter
    def target_humidity(self, value: int) -> None:
        """Set the target humidity"""
        _LOGGER.debug("PyDreoDehumidifier:target_humidity.setter(%s) %s --> %s", self, self._target_humidity, value)
        if value < 30 or value > 85:
            raise ValueError(f"Target humidity {value} is out of range (30-85)")
        if self._target_humidity == value:
            _LOGGER.debug("PyDreoDehumidifier:target_humidity - value already %s, skipping command", value)
            return
        self._target_humidity = value
        self._send_command(RHAUTOLEVEL_KEY, value)

    @property
    def wind_level(self):
        """Get the fan speed level"""
        return self._wind_level

    @wind_level.setter 
    def wind_level(self, value: int) -> None:
        """Set the fan speed level (1-3)"""
        _LOGGER.debug("PyDreoDehumidifier:wind_level.setter(%s) %s --> %s", self, self._wind_level, value)
        if value < 1 or value > 3:
            raise ValueError(f"Wind level {value} is out of range (1-3)")
        if self._wind_level == value:
            _LOGGER.debug("PyDreoDehumidifier:wind_level - value already %s, skipping command", value)
            return
        self._wind_level = value
        self._send_command(WINDLEVEL_KEY, value)

    @property
    def panel_sound(self) -> bool:
        """Is the panel sound on"""
        if self._mute_on is not None:
            return not self._mute_on
        return None

    @panel_sound.setter
    def panel_sound(self, value: bool) -> None:
        """Set if the panel sound is on"""
        _LOGGER.debug("PyDreoDehumidifier:panel_sound.setter(%s) --> %s", self.name, value)
        if self._mute_on == (not value):
            _LOGGER.debug("PyDreoDehumidifier:panel_sound - value already %s, skipping command", value)
            return
        self._send_command(MUTEON_KEY, not value)

    @property
    def display_light(self) -> bool:
        """Is the display light on"""
        return self._light_on

    @display_light.setter
    def display_light(self, value: bool) -> None:
        """Set if the display light is on"""
        _LOGGER.debug("PyDreoDehumidifier:display_light.setter(%s) --> %s", self.name, value)
        if self._light_on == value:
            _LOGGER.debug("PyDreoDehumidifier:display_light - value already %s, skipping command", value)
            return
        self._send_command(LIGHTON_KEY, value)

    @property
    def childlockon(self) -> bool:
        """Is the child lock on"""
        return self._child_lock_on

    @childlockon.setter
    def childlockon(self, value: bool) -> None:
        """Set if the child lock is on"""
        _LOGGER.debug("PyDreoDehumidifier:childlockon.setter(%s) --> %s", self.name, value)
        if self._child_lock_on == value:
            _LOGGER.debug("PyDreoDehumidifier:childlockon - value already %s, skipping command", value)
            return
        self._send_command(CHILDLOCKON_KEY, value)

    @property
    def auto_mode(self) -> bool:
        """Is auto mode on"""
        return self._auto_on

    @auto_mode.setter
    def auto_mode(self, value: bool) -> None:
        """Set if auto mode is on"""
        _LOGGER.debug("PyDreoDehumidifier:auto_mode.setter(%s) --> %s", self.name, value)
        if self._auto_on == value:
            _LOGGER.debug("PyDreoDehumidifier:auto_mode - value already %s, skipping command", value)
            return
        self._send_command(AUTOON_KEY, value)

    @property
    def speed_range(self):
        """Get the fan speed range"""
        return self._speed_range

    @property
    def fan_speed(self):
        """Get the current fan speed (alias for wind_level)"""
        return self._wind_level

    @fan_speed.setter
    def fan_speed(self, value: int) -> None:
        """Set the fan speed (alias for wind_level)"""
        self.wind_level = value

    @property
    def preset_modes(self):
        """Get the list of fan speed preset modes"""
        return ["Low", "Medium", "High"]

    @property
    def preset_mode(self):
        """Get the current fan speed preset mode"""
        if self._wind_level == 1:
            return "Low"
        elif self._wind_level == 2:
            return "Medium"
        elif self._wind_level == 3:
            return "High"
        return None

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the fan speed preset mode"""
        _LOGGER.debug("PyDreoDehumidifier:set_preset_mode(%s) --> %s", self.name, preset_mode)
        if preset_mode == "Low":
            self.wind_level = 1
        elif preset_mode == "Medium":
            self.wind_level = 2
        elif preset_mode == "High":
            self.wind_level = 3
        else:
            raise ValueError(f"Invalid fan preset mode: {preset_mode}")

    @property
    def oscillating(self):
        """Get oscillating state (dehumidifier doesn't oscillate)"""
        return False

    @property 
    def temperature(self):
        """Get the current temperature"""
        return self._temperature
        
    @property
    def mode(self):
        """Return the current operating mode."""
        for mode_name, mode_value in self._modes:
            if self._mode == mode_value:
                return mode_name
        return None

    @mode.setter
    def mode(self, value: str) -> None:
        """Set the operating mode"""
        mode_value = None
        for mode_name, mode_val in self._modes:
            if mode_name == value:
                mode_value = mode_val
                break
                
        if mode_value is not None:
            _LOGGER.debug("PyDreoDehumidifier:mode.setter(%s) %s --> %s", self, self._mode, mode_value)
            if self._mode == mode_value:
                _LOGGER.debug("PyDreoDehumidifier:mode - value already %s, skipping command", value)
                return
            self._send_command(MODE_KEY, mode_value)
        else:
            raise ValueError(f"Operating mode {value} is not in the acceptable list: {self.modes}")

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        super().update_state(state)

        _LOGGER.debug("PyDreoDehumidifier(%s):update_state: %s", self.name, state)
        self._mode = self.get_state_update_value(state, MODE_KEY)
        self._mute_on = self.get_state_update_value(state, MUTEON_KEY)
        self._humidity = self.get_state_update_value(state, HUMIDITY_KEY)
        self._target_humidity = self.get_state_update_value(state, RHAUTOLEVEL_KEY)
        self._wind_level = self.get_state_update_value(state, WINDLEVEL_KEY)
        self._child_lock_on = self.get_state_update_value(state, CHILDLOCKON_KEY)
        self._light_on = self.get_state_update_value(state, LIGHTON_KEY)
        self._auto_on = self.get_state_update_value(state, AUTOON_KEY)
        self._temperature = self.get_state_update_value(state, TEMPERATURE_KEY)
        
    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("PyDreoDehumidifier:handle_server_update(%s): %s", self.name, message)

        val_poweron = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_poweron, bool):
            self._is_on = val_poweron
            _LOGGER.debug("PyDreoDehumidifier:handle_server_update - poweron is %s", self._is_on)

        val_mode = self.get_server_update_key_value(message, MODE_KEY)
        if isinstance(val_mode, int):
            self._mode = val_mode

        val_humidity = self.get_server_update_key_value(message, HUMIDITY_KEY)
        if isinstance(val_humidity, int):
            self._humidity = val_humidity

        val_target_humidity = self.get_server_update_key_value(message, RHAUTOLEVEL_KEY)
        if isinstance(val_target_humidity, int):
            self._target_humidity = val_target_humidity

        val_wind_level = self.get_server_update_key_value(message, WINDLEVEL_KEY)
        if isinstance(val_wind_level, int):
            self._wind_level = val_wind_level

        val_mute = self.get_server_update_key_value(message, MUTEON_KEY)
        if isinstance(val_mute, bool):
            self._mute_on = val_mute

        val_light = self.get_server_update_key_value(message, LIGHTON_KEY)
        if isinstance(val_light, bool):
            self._light_on = val_light

        val_child_lock = self.get_server_update_key_value(message, CHILDLOCKON_KEY)
        if isinstance(val_child_lock, bool):
            self._child_lock_on = val_child_lock

        val_auto = self.get_server_update_key_value(message, AUTOON_KEY)
        if isinstance(val_auto, bool):
            self._auto_on = val_auto

        val_temperature = self.get_server_update_key_value(message, TEMPERATURE_KEY)
        if isinstance(val_temperature, (int, float)):
            self._temperature = val_temperature