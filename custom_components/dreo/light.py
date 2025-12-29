"""Support additionl Lights for some Dreo devices"""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613
from __future__ import annotations
from typing import Any
import logging
import math

from .haimports import * # pylint: disable=W0401,W0614
from .pydreo import PyDreo
from .pydreo.pydreobasedevice import PyDreoBaseDevice
from .pydreo.constant import DreoDeviceType # pylint: disable=C0415
from .dreobasedevice import DreoBaseDeviceHA

from .const import (
    DOMAIN,
    PYDREO_MANAGER
)

_LOGGER = logging.getLogger(__name__)

def get_entries(pydreo_devices : list[PyDreoBaseDevice]) -> list[DreoLightHA]:
    """Add Light entries for Dreo devices.
    
    Iterates through all Dreo devices and creates appropriate light entities based on
    device capabilities. A single device may have multiple lights (e.g., ceiling fans
    have both a main light and an RGB atmosphere light).
    
    Args:
        pydreo_devices: List of PyDreo device objects from the device manager
        
    Returns:
        List of DreoLightHA entities to be registered with Home Assistant
    """
    light_ha_collection : list[DreoLightHA] = []

    for pydreo_device in pydreo_devices:
        _LOGGER.debug("get_entries: Adding Lights for %s", pydreo_device.name)

        # Check if device has a main light (display, main light with brightness/color temp)
        if pydreo_device.is_feature_supported("light_on"):
            _LOGGER.debug("get_entries: Adding Light for %s", pydreo_device.name)
            light_ha_collection.append(DreoLightHA(pydreo_device))

        # Check if device has an RGB atmosphere light (ceiling fans)
        if pydreo_device.is_feature_supported("atm_light"):
            _LOGGER.debug("get_entries: Adding RGB Light for %s", pydreo_device.name)
            light_ha_collection.append(DreoRGBLightHA(pydreo_device))

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
    pydreo_manager : PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    # Discover and register all light entities
    async_add_entities(get_entries(pydreo_manager.devices))


class DreoLightHA(DreoBaseDeviceHA, LightEntity): # pylint: disable=abstract-method
    """Representation of a Dreo Light entity.
    
    This class wraps a PyDreo device to expose its lighting capabilities as a
    Home Assistant Light entity. Supports on/off, brightness, and color temperature
    depending on device capabilities. Can be subclassed for specialized light types.
    """
    def __init__(self,  pyDreoDevice: PyDreoBaseDevice,
                 light_on_attr: str = "light_on",
                 brightness_attr: str = "brightness",
                 brightness_scale: tuple[int, int] = (1, 100),
                 color_temp_attr: str = "color_temperature") -> None:
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
        self._color_mode : ColorMode = ColorMode.ONOFF  # Default: simple on/off
        if self.device.is_feature_supported("color_temperature"):
            self._color_mode = ColorMode.COLOR_TEMP  # Supports brightness + color temperature
        elif self.device.is_feature_supported("brightness"):
            self._color_mode = ColorMode.BRIGHTNESS  # Supports brightness only

        _LOGGER.info(
            "new DreoLightHA instance(%s), unique ID %s",
            self._attr_name,
            self._attr_unique_id)

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
        _LOGGER.debug(
            "is_on for %s is %s",
            self.pydreo_device.name,
            getattr(self.pydreo_device, self._light_on_attr)
        )
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
        if (ATTR_BRIGHTNESS in kwargs):
            brightness = kwargs[ATTR_BRIGHTNESS]
            _LOGGER.debug("turn_on: Setting brightness to %s", brightness)
            setattr(self.pydreo_device, self._brightness_attr, math.ceil(brightness_to_value(self._brightness_scale, brightness)))

        # Handle color temperature adjustment (part of turn_on action, not a separate method)
        if (ATTR_COLOR_TEMP_KELVIN in kwargs):
            color_temp = kwargs[ATTR_COLOR_TEMP_KELVIN]
            _LOGGER.debug("turn_on: Setting color temperature to %s", color_temp)
            setattr(self.pydreo_device, self._color_temp_attr, math.ceil(ranged_value_to_percentage((self.min_color_temp_kelvin,self.max_color_temp_kelvin), color_temp)))

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
        if not self.device.is_feature_supported("brightness"):
            return None

        # Convert device's brightness scale (e.g., 1-100) to HA's 0-255 scale
        return math.ceil(value_to_brightness(self._brightness_scale, getattr(self.pydreo_device, self._brightness_attr, 0)))

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the current color temperature in Kelvin.
        
        Converts from device's percentage-based color temperature to Kelvin (2700K-6500K).
        Returns None if device doesn't support color temperature control.
        """
        if not self.device.is_feature_supported("color_temperature"):
            return None

        # Convert device's percentage (0-100) to Kelvin range (2700K-6500K)
        return math.ceil(percentage_to_ranged_value((self.min_color_temp_kelvin,self.max_color_temp_kelvin), getattr(self.pydreo_device, self._color_temp_attr, 0)))


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
        super().__init__(pyDreoDevice,
                        light_on_attr="atm_light_on",
                        brightness_attr="atm_brightness",
                        brightness_scale=(1, 5))  # RGB lights have only 5 brightness levels

        # Override attributes for RGB light to distinguish from main light
        self.entity_description = EntityDescription("RGB Light")
        self._attr_name = self.pydreo_device.name + " RGB Light"
        self._attr_unique_id = f"{self.pydreo_device.serial_number}-rgb-light"
        self._attr_icon = "mdi:led-strip-variant"

        # RGB lights support RGB color mode (not brightness-only or color temp)
        self._color_mode = ColorMode.RGB

        _LOGGER.info(
            "new DreoRGBLightHA instance(%s), unique ID %s",
            self._attr_name,
            self._attr_unique_id)

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