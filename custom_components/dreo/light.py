"""Support additional Lights for some Dreo devices"""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613
from __future__ import annotations
from typing import Any
import logging
import math

from .haimports import *  # pylint: disable=W0401,W0614
from .pydreo import PyDreo
from .pydreo.pydreobasedevice import PyDreoBaseDevice
from .pydreo.constant import DreoDeviceType  # pylint: disable=C0415
from .dreobasedevice import DreoBaseDeviceHA

from .const import DOMAIN, PYDREO_MANAGER

_LOGGER = logging.getLogger(__name__)


def get_entries(pydreo_devices: list[PyDreoBaseDevice]) -> list[DreoLightHA]:
    """Add Light entries for Dreo devices.

    Iterates through all Dreo devices and creates appropriate light entities based on
    device capabilities. A single device may have multiple lights (e.g., ceiling fans
    have both a main light and an RGB atmosphere light).

    Args:
        pydreo_devices: List of PyDreo device objects from the device manager

    Returns:
        List of DreoLightHA entities to be registered with Home Assistant
    """
    light_ha_collection: list[DreoLightHA] = []

    for pydreo_device in pydreo_devices:
        _LOGGER.debug("get_entries: Adding Lights for %s", pydreo_device.name)

        # Check if device has a main light (display, main light with brightness/color temp)
        if pydreo_device.is_feature_supported("light_on"):
            _LOGGER.debug("get_entries: Adding Light for %s", pydreo_device.name)
            light_ha_collection.append(DreoLightHA(pydreo_device))

        # Check if device has an RGBIC preset-based atmosphere light (e.g., HCF007S)
        if pydreo_device.is_feature_supported("rgb_preset"):
            _LOGGER.debug("get_entries: Adding RGBIC Preset Light for %s", pydreo_device.name)
            light_ha_collection.append(DreoRGBICLightHA(pydreo_device))
        # Check if device has an RGB atmosphere light with direct color control (ceiling fans)
        elif pydreo_device.is_feature_supported("atm_color_rgb"):
            _LOGGER.debug("get_entries: Adding RGB Light for %s", pydreo_device.name)
            light_ha_collection.append(DreoRGBLightHA(pydreo_device))

        # Check if device has an ambient light ring (humidifiers, evaporative coolers).
        # Older firmware exposes rgblevel; newer firmware exposes atm_on (ambient_switch key).
        if pydreo_device.is_feature_supported("rgblevel") or pydreo_device.is_feature_supported("atm_on"):
            _LOGGER.debug("get_entries: Adding Ambient Light for %s", pydreo_device.name)
            light_ha_collection.append(DreoHumidifierLightHA(pydreo_device))

    return light_ha_collection


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Light platform.

    Called by Home Assistant when the integration is loaded. Retrieves all devices
    from the PyDreo manager and creates appropriate light entities for each device
    that supports lighting features.
    """
    _LOGGER.info("get_entries: Starting Dreo Light Platform")

    # Get the PyDreo manager from Home Assistant's data storage
    pydreo_manager: PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    # Discover and register all light entities
    async_add_entities(get_entries(pydreo_manager.devices))


class DreoLightHA(DreoBaseDeviceHA, LightEntity):  # pylint: disable=abstract-method
    """Representation of a Dreo Light entity.

    This class wraps a PyDreo device to expose its lighting capabilities as a
    Home Assistant Light entity. Supports on/off, brightness, and color temperature
    depending on device capabilities. Can be subclassed for specialized light types.
    """

    def __init__(
        self,
        pyDreoDevice: PyDreoBaseDevice,
        light_on_attr: str = "light_on",
        brightness_attr: str = "brightness",
        brightness_scale: tuple[int, int] = (1, 100),
        color_temp_attr: str = "color_temperature",
    ) -> None:
        """Initialize the light entity.

        Args:
            pyDreoDevice: The underlying PyDreo device object
            light_on_attr: Name of the device attribute for on/off state
            brightness_attr: Name of the device attribute for brightness
            brightness_scale: Tuple of (min, max) brightness values the device uses
            color_temp_attr: Name of the device attribute for color temperature
        """
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice

        # Store configurable attribute names - allows subclasses to use different attributes
        self._light_on_attr = light_on_attr
        self._brightness_attr = brightness_attr
        self._brightness_scale = brightness_scale  # Device-specific range, converted to HA's 0-255 scale
        self._color_temp_attr = color_temp_attr

        self.entity_description = EntityDescription("Light")

        self._attr_name = super().name + " Light"
        self._attr_unique_id = f"{super().unique_id}-light"

        self._attr_min_color_temp_kelvin = 2700  # Minimum color temperature in Kelvin (2700K)
        self._attr_max_color_temp_kelvin = 6500  # Maximum color temperature in Kelvin (6500K)

        # Use special icon for ceiling fan lights
        if self.device.type is DreoDeviceType.CEILING_FAN:
            self._attr_icon = "mdi:ceiling-fan-light"

        # Determine color mode based on device capabilities
        # Color mode affects what controls are shown in the Home Assistant UI
        self._color_mode: ColorMode = ColorMode.ONOFF  # Default: simple on/off
        if self.device.is_feature_supported(color_temp_attr):
            self._color_mode = ColorMode.COLOR_TEMP  # Supports brightness + color temperature
        elif self.device.is_feature_supported(brightness_attr):
            self._color_mode = ColorMode.BRIGHTNESS  # Supports brightness only

        _LOGGER.info("new DreoLightHA instance(%s), unique ID %s", self._attr_name, self._attr_unique_id)

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        """Return the list of supported color modes.

        Tells Home Assistant what controls to show in the UI (on/off, brightness,
        color temperature, RGB, etc.).
        """
        return set([self._color_mode])

    @property
    def color_mode(self) -> ColorMode:
        """Return the active color mode.

        For Dreo devices, the color mode is fixed based on capabilities and doesn't
        change at runtime.
        """
        return self._color_mode

    @property
    def is_on(self) -> bool:
        """Return True if device is on."""
        _LOGGER.debug("is_on for %s is %s", self.pydreo_device.name, getattr(self.pydreo_device, self._light_on_attr))
        return getattr(self.pydreo_device, self._light_on_attr, False)

    def turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn the device on.

        Note: Home Assistant's Light entity does not have separate methods for adjusting
        brightness or color temperature. Instead, these adjustments are passed as kwargs
        to turn_on(). When the user adjusts brightness or color temperature in the UI,
        Home Assistant calls turn_on() with the new values in kwargs.
        """
        _LOGGER.debug("turn_on: Turning on light %s", self.pydreo_device.name)
        setattr(self.pydreo_device, self._light_on_attr, True)

        # Handle brightness adjustment (part of turn_on action, not a separate method)
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            _LOGGER.debug("turn_on: Setting brightness to %s", brightness)
            setattr(self.pydreo_device, self._brightness_attr, round(brightness_to_value(self._brightness_scale, brightness)))

        # Handle color temperature adjustment (part of turn_on action, not a separate method)
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            color_temp = kwargs[ATTR_COLOR_TEMP_KELVIN]
            _LOGGER.debug("turn_on: Setting color temperature to %s", color_temp)
            setattr(
                self.pydreo_device,
                self._color_temp_attr,
                math.ceil(ranged_value_to_percentage((self.min_color_temp_kelvin, self.max_color_temp_kelvin), color_temp)),
            )

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        _LOGGER.debug("turn_off: Turning off %s", self.pydreo_device.name)
        setattr(self.pydreo_device, self._light_on_attr, False)

    @property
    def brightness(self) -> int | None:
        """Return the current brightness.

        Converts from device-specific brightness scale to Home Assistant's 0-255 scale.
        Returns None if device doesn't support brightness control.
        """
        if not self.device.is_feature_supported(self._brightness_attr):
            return None

        # Convert device's brightness scale (e.g., 1-100) to HA's 0-255 scale
        return round(value_to_brightness(self._brightness_scale, getattr(self.pydreo_device, self._brightness_attr, 0)))

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the current color temperature in Kelvin.

        Converts from device's percentage-based color temperature to Kelvin (2700K-6500K).
        Returns None if device doesn't support color temperature control.
        """
        if not self.device.is_feature_supported(self._color_temp_attr):
            return None

        # Convert device's percentage (0-100) to Kelvin range (2700K-6500K)
        return math.ceil(
            percentage_to_ranged_value(
                (self.min_color_temp_kelvin, self.max_color_temp_kelvin), getattr(self.pydreo_device, self._color_temp_attr, 0)
            )
        )


class DreoRGBLightHA(DreoLightHA):
    """RGB atmosphere light for Dreo ceiling fans.

    Ceiling fans have two separate lights:
    1. Main light (DreoLightHA) - standard white light with brightness and color temp
    2. RGB light (DreoRGBLightHA) - colored atmosphere/ambient lighting

    This class extends DreoLightHA to add RGB color control while reusing the base
    on/off and brightness functionality.
    """

    def __init__(self, pyDreoDevice: PyDreoBaseDevice) -> None:
        """Initialize the RGB atmosphere light.

        RGB lights use different device attributes than main lights and have a smaller
        brightness scale (1-5 instead of 1-100).
        """
        # Pass RGB-specific configuration to parent - uses "atm_" prefixed attributes
        super().__init__(
            pyDreoDevice, light_on_attr="atm_light_on", brightness_attr="atm_brightness", brightness_scale=(1, 5)
        )  # RGB lights have only 5 brightness levels

        # Override attributes for RGB light to distinguish from main light
        self.entity_description = EntityDescription("RGB Light")
        self._attr_name = self.pydreo_device.name + " RGB Light"
        self._attr_unique_id = f"{self.pydreo_device.serial_number}-rgb-light"
        self._attr_icon = "mdi:led-strip-variant"

        # RGB lights support RGB color mode (not brightness-only or color temp)
        self._color_mode = ColorMode.RGB

        _LOGGER.info("new DreoRGBLightHA instance(%s), unique ID %s", self._attr_name, self._attr_unique_id)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the current RGB color as a tuple (red, green, blue).

        Each component is in the range 0-255. This property is required when
        color_mode is ColorMode.RGB.
        """
        return getattr(self.pydreo_device, "atm_color_rgb", None)

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the RGB light on.

        Note: RGB color adjustments are handled as part of turn_on() action.
        There is no separate method for changing colors - Home Assistant passes
        color changes as kwargs to this turn_on() method.
        """
        # Call parent to handle basic light on and brightness
        super().turn_on(**kwargs)

        # Handle RGB color adjustment (part of turn_on action, not a separate method)
        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            _LOGGER.debug("turn_on: Setting RGB color to %s", rgb)
            setattr(self.pydreo_device, "atm_color_rgb", rgb)


class DreoRGBICLightHA(DreoLightHA):
    """RGBIC preset-based atmosphere light for Dreo ceiling fans (e.g., HCF007S).

    Some ceiling fans use an RGBIC (addressable LED) ring that operates via preset
    effects rather than direct RGB color control. This class exposes preset selection
    through Home Assistant's light effect system.

    - On/off: atmon (atmosphere light power)
    - Brightness: atmbri (1-5 scale)
    - Effects: rgbpresetsel (0-based preset index)
    """

    # Effect names for RGBIC presets (generic names since API doesn't provide them)
    EFFECT_NAMES = ["Preset 1", "Preset 2", "Preset 3", "Preset 4"]

    def __init__(self, pyDreoDevice: PyDreoBaseDevice) -> None:
        """Initialize the RGBIC preset-based atmosphere light."""
        # Pass RGBIC-specific configuration to parent
        super().__init__(
            pyDreoDevice, light_on_attr="atm_light_on", brightness_attr="atm_brightness", brightness_scale=(1, 5)
        )

        # Override attributes for RGBIC light
        self.entity_description = EntityDescription("RGBIC Light")
        self._attr_name = self.pydreo_device.name + " RGB Light"
        self._attr_unique_id = f"{self.pydreo_device.serial_number}-rgb-light"
        self._attr_icon = "mdi:led-strip-variant"

        # Use ONOFF mode with effects (not RGB color mode)
        self._color_mode = ColorMode.ONOFF

        _LOGGER.info("new DreoRGBICLightHA instance(%s), unique ID %s", self._attr_name, self._attr_unique_id)

    @property
    def supported_features(self) -> LightEntityFeature:
        """Return the supported features for this light."""
        return LightEntityFeature.EFFECT

    @property
    def effect_list(self) -> list[str]:
        """Return the list of available effects (presets)."""
        # Use number of presets from device state if available
        num_presets = getattr(self.pydreo_device, "rgb_preset_num", None)
        if num_presets is not None and num_presets > 0:
            return [f"Preset {i + 1}" for i in range(num_presets)]
        # Fallback to default 4 presets
        return self.EFFECT_NAMES

    @property
    def effect(self) -> str | None:
        """Return the current active effect (preset)."""
        preset_sel = getattr(self.pydreo_device, "rgb_preset_sel", None)
        if preset_sel is None:
            return None
        # Convert 0-based index to "Preset N" name
        return f"Preset {preset_sel + 1}"

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the RGBIC light on, optionally setting effect (preset)."""
        # Call parent to handle basic light on and brightness
        super().turn_on(**kwargs)

        # Handle effect/preset selection
        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            _LOGGER.debug("turn_on: Setting RGBIC effect to %s", effect)
            # Parse "Preset N" to get 0-based index
            if effect.startswith("Preset "):
                try:
                    preset_idx = int(effect.split(" ")[1]) - 1
                    self.pydreo_device.rgb_preset_sel = preset_idx
                except (ValueError, IndexError):
                    _LOGGER.warning("turn_on: Invalid effect name %s", effect)


class DreoHumidifierLightHA(DreoBaseDeviceHA, LightEntity):  # pylint: disable=abstract-method
    """Ambient light ring for Dreo humidifiers and evaporative coolers.

    Supports two firmware generations transparently:
    - **Older firmware** (rgb* keys): rgblevel (on/off/brightness), rgbcolor (color), rgbmode (mode 0/1)
    - **Newer firmware** (atm* keys): ambient_switch (on/off), atmcolor (color), atmbri (brightness)

    The entity detects which firmware path is active at runtime by checking whether
    ``atm_on`` (the newer ``ambient_switch`` key) is present on the device object.
    """

    def __init__(self, pyDreoDevice: PyDreoBaseDevice) -> None:
        """Initialize the ambient light entity."""
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice

        self.entity_description = EntityDescription("Ambient Light")
        self._attr_name = self.pydreo_device.name + " Ambient Light"
        self._attr_unique_id = f"{self.pydreo_device.serial_number}-ambient-light"
        self._attr_icon = "mdi:lightbulb"

        # Determine brightness levels from model details (old firmware path only).
        details = getattr(pyDreoDevice, "device_definition", None)
        self._levels = getattr(details, "ambient_light_levels", None) if details else None
        if self._levels is None:
            self._levels = (0, 2)  # default: off/full only

        # Detect which firmware path is active.
        # Newer firmware exposes atm_on (bool); older firmware exposes rgblevel (int).
        self._uses_atm = pyDreoDevice.is_feature_supported("atm_on")

        # Determine supported color modes.
        # Newer firmware uses atmcolor; older firmware uses rgbcolor.
        if self._uses_atm:
            self._has_rgb = pyDreoDevice.is_feature_supported("atm_color")
            self._has_brightness = pyDreoDevice.is_feature_supported("atm_brightness")
        else:
            self._has_rgb = pyDreoDevice.is_feature_supported("rgbcolor")
            self._has_brightness = len(self._levels) > 2  # more than just off/on

        modes: set[ColorMode] = set()
        if self._has_rgb:
            modes.add(ColorMode.RGB)
        if self._has_brightness:
            modes.add(ColorMode.BRIGHTNESS)
        if not modes:
            modes.add(ColorMode.ONOFF)
        self._supported_modes = modes

        _LOGGER.info(
            "new DreoHumidifierLightHA instance(%s), unique ID %s, levels=%s, rgb=%s, uses_atm=%s",
            self._attr_name,
            self._attr_unique_id,
            self._levels,
            self._has_rgb,
            self._uses_atm,
        )

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        """Return the set of supported color modes."""
        return self._supported_modes

    @property
    def color_mode(self) -> ColorMode:
        """Return the active color mode.

        Must always return a value in supported_color_modes, or HA will raise
        HomeAssistantError during state_attributes validation.
        """
        if self._has_rgb:
            return ColorMode.RGB
        if self._has_brightness:
            return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

    @property
    def is_on(self) -> bool:
        """Return True if the ambient light is on."""
        if self._uses_atm:
            return getattr(self.device, "atm_on", False) is True
        rgblevel = getattr(self.device, "rgblevel", None)
        return rgblevel is not None and int(rgblevel) > 0

    @property
    def brightness(self) -> int | None:
        """Return brightness on HA's 0-255 scale."""
        if self._uses_atm:
            if not self._has_brightness:
                return None
            atm_bri = getattr(self.device, "atm_brightness", None)
            if atm_bri is None:
                return None
            # Newer firmware reports brightness as a raw integer value from the device.
            return int(atm_bri)
        if not self._has_brightness:
            return None
        rgblevel = getattr(self.device, "rgblevel", None)
        if rgblevel is None or int(rgblevel) == 0:
            return 0
        # Map: 1 (low) -> 128, 2 (full) -> 255
        return 128 if int(rgblevel) == 1 else 255

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the current RGB color."""
        if not self._has_rgb:
            return None
        if self._uses_atm:
            color_int = getattr(self.device, "atm_color", None)
        else:
            color_int = getattr(self.device, "rgbcolor", None)
        if color_int is None:
            return None
        # Unpack 24-bit integer to (r, g, b)
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        return (r, g, b)

    def turn_on(self, **kwargs: Any) -> None:
        """Turn on the ambient light, optionally setting brightness or color."""
        _LOGGER.debug("turn_on: Turning on ambient light %s, kwargs=%s", self.pydreo_device.name, kwargs)

        if self._uses_atm:
            # Newer firmware path: use ambient_switch and atm* keys.
            self.device.atm_on = True
            if ATTR_RGB_COLOR in kwargs and self._has_rgb:
                r, g, b = kwargs[ATTR_RGB_COLOR]
                color_value = (r << 16) | (g << 8) | b
                _LOGGER.debug("turn_on: Setting ATM color to (%d,%d,%d) -> %d", r, g, b, color_value)
                self.device.atm_color = color_value
            if ATTR_BRIGHTNESS in kwargs and self._has_brightness:
                self.device.atm_brightness = kwargs[ATTR_BRIGHTNESS]
        else:
            # Older firmware path: use rgblevel and rgb* keys.
            if ATTR_BRIGHTNESS in kwargs and self._has_brightness:
                brightness = kwargs[ATTR_BRIGHTNESS]
                # Map HA brightness (1-255) to rgblevel: 1-127 -> 1 (low), 128-255 -> 2 (full)
                desired_level = 1 if brightness < 128 else 2
            else:
                # Default to full brightness
                desired_level = max(self._levels)
            self.device.rgblevel = desired_level
            if ATTR_RGB_COLOR in kwargs and self._has_rgb:
                r, g, b = kwargs[ATTR_RGB_COLOR]
                color_value = (r << 16) | (g << 8) | b
                _LOGGER.debug("turn_on: Setting RGB color to (%d,%d,%d) -> %d", r, g, b, color_value)
                # Auto-switch to color mode
                if getattr(self.device, "rgbmode", None) != 1:
                    self.device.rgbmode = 1
                self.device.rgbcolor = color_value

    def turn_off(self, **kwargs: Any) -> None:
        """Turn off the ambient light."""
        _LOGGER.debug("turn_off: Turning off ambient light %s", self.pydreo_device.name)
        if self._uses_atm:
            self.device.atm_on = False
        else:
            self.device.rgblevel = 0
