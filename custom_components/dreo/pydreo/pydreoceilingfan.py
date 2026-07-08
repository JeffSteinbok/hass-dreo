"""Dreo API for controling fans."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
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
    ATMMODE_KEY,
    RGBPRESETSEL_KEY,
    RGBPRESETNUM_KEY,
    RGBEFFECTID_KEY,
)

from .pydreofanbase import PyDreoFanBase
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoCeilingFan(PyDreoFanBase):
    """Base class for Dreo Fan API Calls."""

    @staticmethod
    def _clamp_rgb_tuple(rgb: tuple) -> tuple[int, int, int]:
        """Clamp RGB tuple values to 0-255 integers."""
        if len(rgb) != 3:
            raise ValueError(f"RGB tuple must have exactly 3 elements, got {len(rgb)}")
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
        if device_definition.device_ranges is not None and SPEED_RANGE in device_definition.device_ranges:
            self._speed_range = device_definition.device_ranges[SPEED_RANGE]
        if self._speed_range is None:
            self._speed_range = self.parse_speed_range(details)
        self._preset_modes = device_definition.preset_modes
        if self._preset_modes is None:
            self._preset_modes = self.parse_preset_modes(details)

        self._fan_speed = None
        self._light_on: bool = None
        self._brightness: int = None
        self._color_temp: int = None

        self._atm_light_on: bool = None
        self._atm_brightness: int = None
        self._atm_color: int = None
        self._atm_mode: int = None

        # Brightness range for the atmosphere light (device-specific; defaults to 1-5 for
        # older models, but HCF007S and similar use 1-100).
        self._atm_brightness_range: tuple[int, int] = (1, 5)
        if device_definition.device_ranges is not None and "atm_brightness_range" in device_definition.device_ranges:
            self._atm_brightness_range = device_definition.device_ranges["atm_brightness_range"]

        # RGBIC preset system (used by some ceiling fan variants)
        self._rgb_preset_sel: int = None
        self._rgb_preset_num: int = None

        # RGBIC effect ID system (used by HCF007S and similar) – the device
        # reports/accepts a string-based effect ID (e.g. "2070476690030592000")
        # where the last 3 digits are the effect index.
        self._rgb_effect_id: str = None
        self._rgb_effect_range: tuple[int, int] = None
        if device_definition.device_ranges is not None and "rgb_effect_range" in device_definition.device_ranges:
            self._rgb_effect_range = device_definition.device_ranges["rgb_effect_range"]

        self._wind_type = None
        self._wind_mode = None

        self._device_definition = device_definition

    def parse_preset_modes(self, details: Dict[str, list]) -> tuple[str, int]:
        """Parse the preset modes from the details."""
        preset_modes = []
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            control = controls_conf.get("control", None)
            if control is not None:
                for control_item in control:
                    if control_item.get("type", None) == "CFFan":
                        for mode_item in control_item.get("items", None):
                            text = self.get_mode_string(mode_item.get("text", None))
                            value = mode_item.get("value", None)
                            preset_modes.append((text, value))

        preset_modes.sort(key=lambda tup: tup[1])  # sorts in place
        if len(preset_modes) == 0:
            _LOGGER.debug("parse_preset_modes: No preset modes detected")
            preset_modes = None
        _LOGGER.debug("parse_preset_modes: Detected preset modes - %s", preset_modes)
        return preset_modes

    @PyDreoFanBase.is_on.setter
    def is_on(self, value: bool):
        """Set if the fan is on or off"""
        _LOGGER.debug("is_on: is_on.setter - %s", value)
        if self._is_on == value:
            _LOGGER.debug("is_on: is_on - value already %s, skipping command", value)
            return
        self._send_command(FANON_KEY, value)

    @property
    def light_on(self) -> bool | None:
        """Returns `True` if the device light is on, `False` otherwise."""
        return self._light_on

    @light_on.setter
    def light_on(self, value: bool):
        """Set if the fan is on or off"""
        _LOGGER.debug("light_on: light_on.setter - %s", value)
        if self._light_on is None:
            _LOGGER.error("light_on: Light control not supported by this fan model.")
            return
        if self._light_on == value:
            _LOGGER.debug("light_on: light_on - value already %s, skipping command", value)
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
        _LOGGER.debug("brightness: brightness.setter - %s", value)
        if self._brightness is None:
            _LOGGER.error("brightness: Brightness not supported by this fan model.")
            return
        if self._brightness == value:
            _LOGGER.debug("brightness: brightness - value already %s, skipping command", value)
            return
        self._send_command(BRIGHTNESS_KEY, value)

    @property
    def color_temperature(self) -> int | None:
        """Returns the color temperature of the light, or None if not supported."""
        return self._color_temp

    @color_temperature.setter
    def color_temperature(self, value: int):
        """Set the color temperature of the light on the fan."""
        _LOGGER.debug("color_temperature: color_temperature.setter - %s", value)
        if self._color_temp is None:
            _LOGGER.error("color_temperature: Color temperature not supported by this fan model.")
            return
        if self._color_temp == value:
            _LOGGER.debug("color_temperature: color_temperature - value already %s, skipping command", value)
            return
        self._send_command(COLORTEMP_KEY, value)

    @property
    def atm_light_on(self) -> bool | None:
        """Returns True if the atmosphere light is on, False otherwise."""
        return self._atm_light_on

    @atm_light_on.setter
    def atm_light_on(self, value: bool):
        """Set if the atmosphere light is on or off"""
        _LOGGER.debug("atm_light_on: atm_light_on.setter - %s", value)
        if self._atm_light_on is None:
            _LOGGER.error("atm_light_on: Atmosphere light not supported by this fan model.")
            return
        if self._atm_light_on == value:
            _LOGGER.debug("atm_light_on: atm_light_on - value already %s, skipping command", value)
            return
        self._send_command(ATMON_KEY, value)

    @property
    def atm_brightness(self) -> int | None:
        """Returns the brightness of the atmosphere light, or None if not supported."""
        return self._atm_brightness

    @property
    def atm_brightness_range(self) -> tuple[int, int]:
        """Returns the valid brightness range (min, max) for the atmosphere light."""
        return self._atm_brightness_range

    @atm_brightness.setter
    def atm_brightness(self, value: int):
        """Set the brightness of the atmosphere light."""
        _LOGGER.debug("atm_brightness: atm_brightness.setter - %s", value)
        if self._atm_brightness is None:
            _LOGGER.error("atm_brightness: Atmosphere brightness not supported by this fan model.")
            return
        # Clamp to the device-specific valid range
        low, high = self._atm_brightness_range
        brightness = max(low, min(high, value))
        if self._atm_brightness == brightness:
            _LOGGER.debug("atm_brightness: atm_brightness - value already %s, skipping command", brightness)
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
        _LOGGER.debug("atm_color_rgb: atm_color_rgb.setter - RGB(%d,%d,%d) -> %d", r_int, g_int, b_int, color_value)
        # Guard on atm_light_on (not _atm_color): some device variants track the atmosphere
        # light via atmon/atmbri but do not echo atmcolor in their state heartbeat.
        # We still allow sending the atmcolor command as long as the atmosphere light
        # feature itself is present on the device.
        if self._atm_light_on is None:
            _LOGGER.error("atm_color_rgb: Atmosphere light not supported by this fan model.")
            return
        if self._atm_color is not None and self._atm_color == color_value:
            _LOGGER.debug("atm_color_rgb: atm_color_rgb - value already %s, skipping command", color_value)
            return
        self._send_command(ATMCOLOR_KEY, color_value)

    @property
    def atm_mode(self) -> int | None:
        """Returns the atmosphere mode (1=Constant, 2=Circle, 3=Breath), or None if not supported."""
        return self._atm_mode

    @property
    def rgb_preset_sel(self) -> int | None:
        """Returns the currently selected RGBIC preset (0-based index), or None if not supported."""
        return self._rgb_preset_sel

    @rgb_preset_sel.setter
    def rgb_preset_sel(self, value: int):
        """Set the RGBIC preset selection (0-based index)."""
        _LOGGER.debug("rgb_preset_sel: rgb_preset_sel.setter - %s", value)
        if self._rgb_preset_sel is None:
            _LOGGER.error("rgb_preset_sel: RGBIC presets not supported by this fan model.")
            return
        if self._rgb_preset_sel == value:
            _LOGGER.debug("rgb_preset_sel: rgb_preset_sel - value already %s, skipping command", value)
            return
        self._send_command(RGBPRESETSEL_KEY, value)

    @property
    def rgb_preset_num(self) -> int | None:
        """Returns the number of available RGBIC presets, or None if not supported."""
        return self._rgb_preset_num

    @property
    def rgb_effect_id(self) -> str | None:
        """Returns the current RGBIC effect ID string, or None if not supported."""
        return self._rgb_effect_id

    @rgb_effect_id.setter
    def rgb_effect_id(self, value: str):
        """Set the RGBIC effect by full effect ID string."""
        _LOGGER.debug("rgb_effect_id: rgb_effect_id.setter - %s", value)
        if self._rgb_effect_id is None:
            _LOGGER.error("rgb_effect_id: RGBIC effect ID not supported by this fan model.")
            return
        if self._rgb_effect_id == value:
            _LOGGER.debug("rgb_effect_id: rgb_effect_id - value already %s, skipping command", value)
            return
        self._send_command(RGBEFFECTID_KEY, value)

    @property
    def rgb_effect_range(self) -> tuple[int, int] | None:
        """Returns the valid range (min, max) of RGBIC effect indices, or None."""
        return self._rgb_effect_range

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("update_state: Processing state")
        super().update_state(state)

        self._fan_speed = self.get_state_update_value(state, WINDLEVEL_KEY)
        if self._fan_speed is None:
            _LOGGER.error("update_state: Unable to get fan speed from state. Check debug logs for more information.")

        # Ceiling fans report both poweron (whole-device power) and fanon (fan motor).
        # poweron=False means the device is entirely off and takes priority over fanon.
        # When poweron is True (or absent), fanon reflects the actual fan motor state.
        poweron_val = self.get_state_update_value(state, POWERON_KEY)
        fanon_val = self.get_state_update_value(state, FANON_KEY)
        if poweron_val is not None:
            if not poweron_val:
                self._is_on = False
            elif fanon_val is not None:
                self._is_on = fanon_val
        elif fanon_val is not None:
            self._is_on = fanon_val

        self._light_on = self.get_state_update_value(state, LIGHTON_KEY)
        self._brightness = self.get_state_update_value(state, BRIGHTNESS_KEY)
        self._color_temp = self.get_state_update_value(state, COLORTEMP_KEY)

        self._atm_light_on = self.get_state_update_value(state, ATMON_KEY)
        self._atm_brightness = self.get_state_update_value(state, ATMBRI_KEY)
        self._atm_color = self.get_state_update_value(state, ATMCOLOR_KEY)
        self._atm_mode = self.get_state_update_value(state, ATMMODE_KEY)

        # RGBIC preset system
        self._rgb_preset_sel = self.get_state_update_value(state, RGBPRESETSEL_KEY)
        self._rgb_preset_num = self.get_state_update_value(state, RGBPRESETNUM_KEY)
        self._rgb_effect_id = self.get_state_update_value(state, RGBEFFECTID_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("handle_server_update: handle_server_update")
        super().handle_server_update(message)

        # Power state (fanon/poweron) is handled by _handle_power_state_update.

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

        # RGBIC preset system
        val_rgb_preset_sel = self.get_server_update_key_value(message, RGBPRESETSEL_KEY)
        if isinstance(val_rgb_preset_sel, int):
            self._rgb_preset_sel = val_rgb_preset_sel

        val_rgb_preset_num = self.get_server_update_key_value(message, RGBPRESETNUM_KEY)
        if isinstance(val_rgb_preset_num, int):
            self._rgb_preset_num = val_rgb_preset_num

        val_rgb_effect_id = self.get_server_update_key_value(message, RGBEFFECTID_KEY)
        if isinstance(val_rgb_effect_id, str):
            self._rgb_effect_id = val_rgb_effect_id

    def _handle_power_state_update(self, message):
        """Override power state handling for ceiling fans"""
        val_poweron = self.get_server_update_key_value(message, POWERON_KEY)
        val_fan_on = self.get_server_update_key_value(message, FANON_KEY)

        # Handle fanon first (fan motor state)
        if isinstance(val_fan_on, bool):
            self._is_on = val_fan_on
            _LOGGER.debug("_handle_power_state_update: Fan state updated from fanon: %s", val_fan_on)

        # poweron=False always takes priority: entire device off means fan is off too
        if val_poweron is False:
            self._is_on = False
            self._light_on = False
            _LOGGER.debug("_handle_power_state_update: Device powered off - fan and light off")

    def is_feature_supported(self, feature: str) -> bool:
        """Check if this ceiling fan supports a specific feature"""
        if feature == "atm_light":
            return self._atm_light_on is not None
        # atm_color_rgb is only supported if the device has atmcolor (not RGBIC preset system)
        if feature == "atm_color_rgb":
            # Device must have atmosphere light AND direct atmcolor support (not RGBIC presets)
            return self._atm_light_on is not None and self._atm_color is not None
        # Some RGBIC models (e.g. HCF007S) accept atmcolor commands but don't report atmcolor state.
        # This capability is model-defined so HA can expose direct RGB control where supported.
        if feature == "atm_color_rgb_write":
            direct_rgb = (
                self._device_definition is not None
                and self._device_definition.device_ranges is not None
                and self._device_definition.device_ranges.get("supports_direct_rgb_color", False)
            )
            return self._atm_light_on is not None and (self._atm_color is not None or direct_rgb)
        # RGBIC preset system - device has atmon + rgbpresetsel but not atmcolor
        if feature == "rgb_preset":
            return self._atm_light_on is not None and self._rgb_preset_sel is not None
        # RGBIC effect ID system - device uses string-based effect IDs (e.g. HCF007S)
        # Only enabled when the device also has a defined rgb_effect_range in its model
        if feature == "rgb_effect_id":
            return self._rgb_effect_id is not None and self._rgb_effect_range is not None
        return super().is_feature_supported(feature)
