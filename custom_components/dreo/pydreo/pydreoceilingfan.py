"""Dreo API for controling fans."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    FANON_KEY,
    LIGHTON_KEY,
    WINDLEVEL_KEY,
    SPEED_RANGE,
    BRIGHTNESS_KEY,
    COLORTEMP_KEY,
    POWERON_KEY,
    ATMON_KEY,
    ATMCOLOR_KEY,
    ATMBRI_KEY,
    ATMMODE_KEY
)

from .pydreofanbase import PyDreoFanBase
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoCeilingFan(PyDreoFanBase):
    """Base class for Dreo Fan API Calls."""

    @staticmethod
    def _clamp_rgb_tuple(rgb: tuple) -> tuple[int, int, int]:
        """Clamp RGB tuple values to 0-255 integers."""
        return tuple(max(0, min(255, int(round(c)))) for c in rgb)

    @staticmethod
    def _pack_rgb_to_int(rgb: tuple[int, int, int]) -> int:
        """Pack RGB tuple into 24-bit integer."""
        r, g, b = rgb
        return (r << 16) | (g << 8) | b

    @staticmethod
    def _unpack_int_to_rgb(color: int) -> tuple[int, int, int]:
        """Unpack 24-bit integer to RGB tuple."""
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        return (r, g, b)

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        super().__init__(device_definition, details, dreo)
        
        self._speed_range = None
        if (device_definition.device_ranges is not None and SPEED_RANGE in device_definition.device_ranges):
            self._speed_range = device_definition.device_ranges[SPEED_RANGE]
        if (self._speed_range is None):
            self._speed_range = self.parse_speed_range(details)
        self._preset_modes = device_definition.preset_modes
        if (self._preset_modes is None):
            self._preset_modes = self.parse_preset_modes(details)

        self._fan_speed = None
        self._light_on : bool = None
        self._brightness : int = None
        self._color_temp : int = None

        self._atm_light_on : bool = None
        self._atm_brightness : int = None
        self._atm_color : int = None
        self._atm_mode : int = None

        self._wind_type = None
        self._wind_mode = None

        self._device_definition = device_definition
    
    def parse_preset_modes(self, details: Dict[str, list]) -> tuple[str, int]:
        """Parse the preset modes from the details."""
        preset_modes = []
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            control = controls_conf.get("control", None)
            if (control is not None):
                for control_item in control:
                    if (control_item.get("type", None) == "CFFan"):
                        for mode_item in control_item.get("items", None):
                            text = self.get_mode_string(mode_item.get("text", None))
                            value = mode_item.get("value", None)
                            preset_modes.append((text, value))

        preset_modes.sort(key=lambda tup: tup[1])  # sorts in place
        if (len(preset_modes) == 0):
            _LOGGER.debug("PyDreoFan:No preset modes detected")
            preset_modes = None
        _LOGGER.debug("PyDreoFan:Detected preset modes - %s", preset_modes)
        return preset_modes

    @PyDreoFanBase.is_on.setter
    def is_on(self, value: bool):
        """Set if the fan is on or off"""
        _LOGGER.debug("PyDreoFan:is_on.setter - %s", value)
        if self._is_on == value:
            _LOGGER.debug("PyDreoCeilingFan:is_on - value already %s, skipping command", value)
            return
        self._send_command(FANON_KEY, value)

    @property
    def light_on(self) -> bool | None:
        """Returns `True` if the device light is on, `False` otherwise."""
        return self._light_on

    @light_on.setter
    def light_on(self, value: bool):
        """Set if the fan is on or off"""
        _LOGGER.debug("PyDreoCeilingFan:light_on.setter - %s", value)
        if (self._light_on is None):
            _LOGGER.error("Light control not supported by this fan model.")
            return
        if self._light_on == value:
            _LOGGER.debug("PyDreoCeilingFan:light_on - value already %s, skipping command", value)
            return
        self._send_command(LIGHTON_KEY, value)

    @property
    def oscillating(self) -> bool:
        return None
    
    @oscillating.setter
    def oscillating(self, value: bool) -> None:
        raise NotImplementedError(f"Attempting to set oscillating on a device that doesn't support ({value})")

    @property
    def brightness(self) -> int | None:
        """Returns the brightness of the light, or None if not supported."""
        return self._brightness

    @brightness.setter
    def brightness(self, value: int):
        """Set the brightness of the light on the fan."""
        _LOGGER.debug("PyDreoCeilingFan:brightness.setter - %s", value)
        if (self._brightness is None):
            _LOGGER.error("Brightness not supported by this fan model.")
            return
        if self._brightness == value:
            _LOGGER.debug("PyDreoCeilingFan:brightness - value already %s, skipping command", value)
            return
        self._send_command(BRIGHTNESS_KEY, value)

    @property
    def color_temperature(self) -> int | None:
        """Returns the color temperature of the light, or None if not supported."""
        return self._color_temp

    @color_temperature.setter
    def color_temperature(self, value: int):
        """Set the color temperature of the light on the fan."""
        _LOGGER.debug("PyDreoCeilingFan:color_temperature.setter - %s", value)
        if (self._color_temp is None):
            _LOGGER.error("Color temperature not supported by this fan model.")
            return
        if self._color_temp == value:
            _LOGGER.debug("PyDreoCeilingFan:color_temperature - value already %s, skipping command", value)
            return
        self._send_command(COLORTEMP_KEY, value)        

    @property
    def atm_light_on(self) -> bool | None:
        """Returns True if the atmosphere light is on, False otherwise."""
        return self._atm_light_on

    @atm_light_on.setter
    def atm_light_on(self, value: bool):
        """Set if the atmosphere light is on or off"""
        _LOGGER.debug("PyDreoCeilingFan:atm_light_on.setter - %s", value)
        if (self._atm_light_on is None):
            _LOGGER.error("Atmosphere light not supported by this fan model.")
            return
        if self._atm_light_on == value:
            _LOGGER.debug("PyDreoCeilingFan:atm_light_on - value already %s, skipping command", value)
            return
        self._send_command(ATMON_KEY, value)

    @property
    def atm_brightness(self) -> int | None:
        """Returns the brightness of the atmosphere light (1-5), or None if not supported."""
        return self._atm_brightness

    @atm_brightness.setter
    def atm_brightness(self, value: int):
        """Set the brightness of the atmosphere light (1-5 scale)."""
        _LOGGER.debug("PyDreoCeilingFan:atm_brightness.setter - %s", value)
        if (self._atm_brightness is None):
            _LOGGER.error("Atmosphere brightness not supported by this fan model.")
            return
        # Ensure value is in valid range
        brightness = max(1, min(5, value))
        if self._atm_brightness == brightness:
            _LOGGER.debug("PyDreoCeilingFan:atm_brightness - value already %s, skipping command", brightness)
            return
        self._send_command(ATMBRI_KEY, brightness)

    @property
    def atm_color_rgb(self) -> tuple[int, int, int] | None:
        """Returns the RGB color as a tuple (r, g, b), or None if not supported."""
        if self._atm_color is None:
            return None
        # Extract RGB from 24-bit integer
        return self._unpack_int_to_rgb(self._atm_color)

    @atm_color_rgb.setter
    def atm_color_rgb(self, rgb: tuple[int | float, int | float, int | float]):
        """Set the RGB color of the atmosphere light."""
        # Clamp RGB values and pack into 24-bit integer
        r_int, g_int, b_int = self._clamp_rgb_tuple(rgb)
        color_value = self._pack_rgb_to_int((r_int, g_int, b_int))
        _LOGGER.debug("PyDreoCeilingFan:atm_color_rgb.setter - RGB(%d,%d,%d) -> %d", r_int, g_int, b_int, color_value)
        if (self._atm_color is None):
            _LOGGER.error("Atmosphere color not supported by this fan model.")
            return
        if self._atm_color == color_value:
            _LOGGER.debug("PyDreoCeilingFan:atm_color_rgb - value already %s, skipping command", color_value)
            return
        self._send_command(ATMCOLOR_KEY, color_value)

    @property
    def atm_mode(self) -> int | None:
        """Returns the atmosphere mode (1=Constant, 2=Circle, 3=Breath), or None if not supported."""
        return self._atm_mode
    
    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("PyDreoFan:update_state")
        super().update_state(state)

        self._fan_speed = self.get_state_update_value(state, WINDLEVEL_KEY)
        if self._fan_speed is None:
            _LOGGER.error("Unable to get fan speed from state. Check debug logs for more information.")

        self._is_on = self.get_state_update_value(state, FANON_KEY)
        self._light_on = self.get_state_update_value(state, LIGHTON_KEY)
        self._brightness = self.get_state_update_value(state, BRIGHTNESS_KEY)
        self._color_temp = self.get_state_update_value(state, COLORTEMP_KEY)
        
        self._atm_light_on = self.get_state_update_value(state, ATMON_KEY)
        self._atm_brightness = self.get_state_update_value(state, ATMBRI_KEY)
        self._atm_color = self.get_state_update_value(state, ATMCOLOR_KEY)
        self._atm_mode = self.get_state_update_value(state, ATMMODE_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("PyDreoCeilingFan:handle_server_update")
        super().handle_server_update(message)

        val_power_on = self.get_server_update_key_value(message, FANON_KEY)
        if isinstance(val_power_on, bool):
            self._is_on = val_power_on

        val_light_on = self.get_server_update_key_value(message, LIGHTON_KEY)
        if isinstance(val_light_on, bool):
            self._light_on = val_light_on        

        val_brightness = self.get_server_update_key_value(message, BRIGHTNESS_KEY)
        if isinstance(val_brightness, int):
            self._brightness = val_brightness   

        val_color_temp = self.get_server_update_key_value(message, COLORTEMP_KEY)
        if isinstance(val_color_temp, int):
            self._color_temp = val_color_temp    

        val_atm_on = self.get_server_update_key_value(message, ATMON_KEY)
        if isinstance(val_atm_on, bool):
            self._atm_light_on = val_atm_on

        val_atm_brightness = self.get_server_update_key_value(message, ATMBRI_KEY)
        if isinstance(val_atm_brightness, int):
            self._atm_brightness = val_atm_brightness

        val_atm_color = self.get_server_update_key_value(message, ATMCOLOR_KEY)
        if isinstance(val_atm_color, int):
            self._atm_color = val_atm_color

        val_atm_mode = self.get_server_update_key_value(message, ATMMODE_KEY)
        if isinstance(val_atm_mode, int):
            self._atm_mode = val_atm_mode

    def _handle_power_state_update(self, message):
        """Override power state handling for ceiling fans"""
        # Handle poweron: False = turn off entire device (both fan and light)
        val_poweron = self.get_server_update_key_value(message, POWERON_KEY)
        if val_poweron is False:
            self._is_on = False
            self._light_on = False
            _LOGGER.debug("PyDreoCeilingFan: Device powered off - fan and light off")
            
        # Handle fanon: True/False = specific fan motor control
        val_fan_on = self.get_server_update_key_value(message, FANON_KEY)
        if isinstance(val_fan_on, bool):
            self._is_on = val_fan_on
            _LOGGER.debug("PyDreoCeilingFan: Fan state updated from fanon: %s", val_fan_on)

    def is_feature_supported(self, feature: str) -> bool:
        """Check if this ceiling fan supports a specific feature"""
        if feature == "atm_light":
            return self._atm_light_on is not None
        return super().is_feature_supported(feature)
