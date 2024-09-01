"""Dreo API for controling air purifiers."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    POWERON_KEY,
    WINDLEVEL_KEY,
    LEDALWAYSON_KEY,
    WIND_MODE_KEY,
    LIGHTSENSORON_KEY,
    MUTEON_KEY,
    SPEED_RANGE
)

from .pydreobasedevice import PyDreoBaseDevice
from .models import DreoDeviceDetails
from .helpers import Helpers

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoAirPurifier(PyDreoBaseDevice):
    """Base class for Dreo Fan API Calls."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        super().__init__(device_definition, details, dreo)
        
        self._speed_range = None
        if (device_definition.range is not None):
            self._speed_range = device_definition.range[SPEED_RANGE]
        if (self._speed_range is None):
            self._speed_range = self.parse_speed_range(details)

        self._preset_modes = device_definition.preset_modes
        if (self._preset_modes is None):
            self._preset_modes = self.parse_preset_modes(details)

        self._fan_speed = None

        self._wind_mode = None

        self._led_always_on = None
        self._device_definition = device_definition
        self._light_sensor_on = None
        self._mute_on = None

        self._fixed_conf = None

    def __repr__(self):
        # Representation string of object.
        return f"<{self.__class__.__name__}:{self._device_id}:{self._name}>"

    def parse_speed_range(self, details: Dict[str, list]) -> tuple[int, int]:
        """Parse the speed range from the details."""
        # There are a bunch of different places this could be, so we're going to look in
        # multiple places.
        speed_range : tuple[int, int] = None
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            control_node = controls_conf.get("control", None)
            if (control_node is not None):
                speed_range = self.parse_speed_range_from_control_node(control_node)
                _LOGGER.debug("PyDreoAirPurifier:Detected speed range from controlsConf - %s", speed_range)
                return speed_range
        return None

    def parse_speed_range_from_control_node(self, control_node) -> tuple[int, int]:
        """Parse the speed range from a control node"""
        for control_item in control_node:
            if control_item.get("value", None) == "manual":
                speed_low = control_item.get("items", None)[0].get("value", None)
                speed_high = control_item.get("items", None)[1].get("value", None)
                speed_range = (speed_low, speed_high)
                return speed_range
        return None
    
    def parse_preset_modes(self, details: Dict[str, list]) -> tuple[str, str]:
        """Parse the preset modes from the details."""
        preset_modes = []
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            control = controls_conf.get("control", None)
            if (control is not None):
                for control_item in control:
                    if (control_item.get("type", None) == "Mode"):
                        for mode_item in control_item.get("items", None):
                            value = mode_item.get("value", None)
                            preset_modes.append((value, value))
                    elif (control_item.get("type", None) == "Manual"):
                        value = control_item.get("value", None)
                        preset_modes.append((value, value))

        preset_modes.sort(key=lambda tup: tup[1])  # sorts in place
        if (preset_modes.count is 0):
            _LOGGER.debug("PyDreoAirPurifier:No preset modes detected")
            preset_modes = None
        _LOGGER.debug("PyDreoAirPurifier:Detected preset modes - %s", preset_modes)
        return preset_modes
                        
    @property
    def speed_range(self):
        """Get the speed range"""
        return self._speed_range

    @property
    def preset_modes(self) -> list[str]:
        """Get the list of preset modes"""
        return Helpers.get_name_list(self._preset_modes)
    
    @property
    def is_on(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._is_on

    @is_on.setter
    def is_on(self, value: bool):
        """Set if the fan is on or off"""
        _LOGGER.debug("PyDreoAirPurifier:is_on.setter - %s", value)
        self._send_command(POWERON_KEY, value)

    @property
    def fan_speed(self):
        """Return the current fan speed"""
        return self._fan_speed

    @fan_speed.setter
    def fan_speed(self, fan_speed: int):
        """Set the fan speed."""
        if fan_speed < 1 or fan_speed > self._speed_range[1]:
            _LOGGER.error("Fan speed %s is not in the acceptable range: %s",
                          fan_speed,
                          self._speed_range)
            raise ValueError(f"fan_speed must be between {self._speed_range[0]} and {self._speed_range[1]}")
        self._send_command(WINDLEVEL_KEY, fan_speed)

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        mode = self._wind_mode
        if mode is None:
            mode = self._wind_mode

        if mode is None:
            return None

        # If we can't match the preset mode, just return the first one.
        if mode > len(self.preset_modes):
            return self.preset_modes[0]

        return self.preset_modes[mode - 1]

    @preset_mode.setter
    def preset_mode(self, value: str) -> None:
        key: str = None

        if self._wind_mode is not None:
            key = WIND_MODE_KEY
        else:
            raise NotImplementedError("Attempting to set preset_mode on a device that doesn't support.")

        if value in self.preset_modes:
            self._send_command(key, self.preset_modes.index(value) + 1)
        else:
            raise ValueError(f"Preset mode {value} is not in the acceptable list: {self.preset_modes}")


    @property
    def display_auto_off(self) -> bool:
        """Is the display always on?"""
        if self._led_always_on is not None:
            return not self._led_always_on

        return None

    @display_auto_off.setter
    def display_auto_off(self, value: bool) -> None:
        """Set if the display is always on"""
        _LOGGER.debug("PyDreoAirPurifier:display_auto_off.setter")

        if self._led_always_on is not None:
            self._send_command(LEDALWAYSON_KEY, not value)
        else:
            raise NotImplementedError("Attempting to set display always on on a device that doesn't support.")

    @property
    def adaptive_brightness(self) -> bool:
        """Is the display always on?"""
        if (self._light_sensor_on is not None):
            return self._light_sensor_on
        else:
            return None

    @adaptive_brightness.setter
    def adaptive_brightness(self, value: bool) -> None:
        """Set if the display is always on"""
        _LOGGER.debug("PyDreoAirPurifier:adaptive_brightness.setter")

        if self._light_sensor_on is not None:
            self._send_command(LIGHTSENSORON_KEY, value)
        else:
            raise NotImplementedError("Attempting to set adaptive brightness on on a device that doesn't support.")

    @property
    def panel_sound(self) -> bool:
        """Is the panel sound on"""
        if self._mute_on is not None:
            return not self._mute_on
        return None

    @panel_sound.setter
    def panel_sound(self, value: bool) -> None:
        """Set if the panel sound"""
        _LOGGER.debug("PyDreoAirPurifier:panel_sound.setter")

        if self._mute_on is not None:
            self._send_command(MUTEON_KEY, not value)
        else:
            raise NotImplementedError("Attempting to set panel_sound on a device that doesn't support.")

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("PyDreoAirPurifier:update_state")
        super().update_state(state)

        self._fan_speed = self.get_state_update_value(state, WINDLEVEL_KEY)
        if self._fan_speed is None:
            _LOGGER.error("Unable to get fan speed from state. Check debug logs for more information.")

        self._led_always_on = self.get_state_update_value(state, LEDALWAYSON_KEY)
        self._wind_mode = self.get_state_update_value(state, WIND_MODE_KEY)
        self._light_sensor_on = self.get_state_update_value(state, LIGHTSENSORON_KEY)
        self._mute_on = self.get_state_update_value(state, MUTEON_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("PyDreoAirPurifier:handle_server_update")

        val_power_on = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_power_on, bool):
            self._is_on = val_power_on

        val_wind_level = self.get_server_update_key_value(message, WINDLEVEL_KEY)
        if isinstance(val_wind_level, int):
            self._fan_speed = val_wind_level

        val_display_always_on = self.get_server_update_key_value(message, LEDALWAYSON_KEY)
        if isinstance(val_display_always_on, bool):
            self._led_always_on = val_display_always_on

        val_wind_mode = self.get_server_update_key_value(message, WIND_MODE_KEY)
        if isinstance(val_wind_mode, int):
            self._wind_mode = val_wind_mode

        val_light_sensor = self.get_server_update_key_value(message, LIGHTSENSORON_KEY)
        if isinstance(val_light_sensor, bool):
            self._light_sensor_on = val_light_sensor

        val_mute = self.get_server_update_key_value(message, MUTEON_KEY)
        if isinstance(val_mute, bool):
            self._mute_on = val_mute
