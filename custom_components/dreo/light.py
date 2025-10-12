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
    LOGGER,
    DOMAIN,
    PYDREO_MANAGER
)

_LOGGER = logging.getLogger(LOGGER)

def get_entries(pydreo_devices : list[PyDreoBaseDevice]) -> list[DreoLightHA]:
    """Add Light entries for Dreo devices."""
    light_ha_collection : list[DreoLightHA] = []

    for pydreo_device in pydreo_devices:
        _LOGGER.debug("Light:get_entries: Adding Lights for %s", pydreo_device.name)

        if pydreo_device.is_feature_supported("light_on"):
            _LOGGER.debug("Light:get_entries: Adding Light for %s", pydreo_device.name)
            light_ha_collection.append(DreoLightHA(pydreo_device))

        if pydreo_device.is_feature_supported("atm_light"):
            _LOGGER.debug("Light:get_entries: Adding RGB Light for %s", pydreo_device.name)
            light_ha_collection.append(DreoRGBLightHA(pydreo_device))

    return light_ha_collection

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Light platform."""
    _LOGGER.info("Starting Dreo Light Platform")

    pydreo_manager : PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    async_add_entities(get_entries(pydreo_manager.devices))


class DreoLightHA(DreoBaseDeviceHA, LightEntity): # pylint: disable=abstract-method
    """Representation of a Dreo Light entity."""
    def __init__(self,  pyDreoDevice: PyDreoBaseDevice,
                 light_on_attr: str = "light_on",
                 brightness_attr: str = "brightness",
                 brightness_scale: tuple[int, int] = (1, 100),
                 color_temp_attr: str = "color_temperature") -> None:
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice

        # Configure attribute names for this light type
        self._light_on_attr = light_on_attr
        self._brightness_attr = brightness_attr
        self._brightness_scale = brightness_scale
        self._color_temp_attr = color_temp_attr

        self.entity_description = EntityDescription("Light")

        self._attr_name = super().name + " Light"
        self._attr_unique_id = f"{super().unique_id}-light"

        self._attr_min_color_temp_kelvin = 2700  # Minimum color temperature in Kelvin (2700K)
        self._attr_max_color_temp_kelvin = 6500  # Maximum color temperature in Kelvin (6500K)

        if self.device.type is DreoDeviceType.CEILING_FAN:
            self._attr_icon = "mdi:ceiling-fan-light"

        self._color_mode : ColorMode = ColorMode.ONOFF
        if self.device.is_feature_supported("color_temperature"):
            self._color_mode = ColorMode.COLOR_TEMP
        elif self.device.is_feature_supported("brightness"):
            self._color_mode = ColorMode.BRIGHTNESS

        _LOGGER.info(
            "new DreoLightHA instance(%s), unique ID %s",
            self._attr_name,
            self._attr_unique_id)

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        return set([self._color_mode])

    @property
    def color_mode(self) -> ColorMode:
        return self._color_mode

    @property
    def is_on(self) -> bool:
        """Return True if device is on."""
        _LOGGER.debug(
            "DreoLightHA:is_on for %s is %s",
            self.pydreo_device.name,
            getattr(self.pydreo_device, self._light_on_attr)
        )
        return getattr(self.pydreo_device, self._light_on_attr, False)

    def turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn the device on."""
        _LOGGER.debug("Turning on %s", self.pydreo_device.name)
        setattr(self.pydreo_device, self._light_on_attr, True)

        if (ATTR_BRIGHTNESS in kwargs):
            brightness = kwargs[ATTR_BRIGHTNESS]
            _LOGGER.debug("Setting brightness to %s", brightness)
            setattr(self.pydreo_device, self._brightness_attr, math.ceil(brightness_to_value(self._brightness_scale, brightness)))

        if (ATTR_COLOR_TEMP_KELVIN in kwargs):
            color_temp = kwargs[ATTR_COLOR_TEMP_KELVIN]
            _LOGGER.debug("Setting color temperature to %s", color_temp)
            setattr(self.pydreo_device, self._color_temp_attr, math.ceil(ranged_value_to_percentage((self.min_color_temp_kelvin,self.max_color_temp_kelvin), color_temp)))


    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        _LOGGER.debug("Turning off %s", self.pydreo_device.name)
        setattr(self.pydreo_device, self._light_on_attr, False)

    @property
    def brightness(self) -> int | None:
        """Return the current brightness."""
        if not self.device.is_feature_supported("brightness"):
            return None

        return math.ceil(value_to_brightness(self._brightness_scale, getattr(self.pydreo_device, self._brightness_attr, 0)))

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the current color temperature."""
        if not self.device.is_feature_supported("color_temperature"):
            return None

        return math.ceil(percentage_to_ranged_value((self.min_color_temp_kelvin,self.max_color_temp_kelvin), getattr(self.pydreo_device, self._color_temp_attr, 0)))


class DreoRGBLightHA(DreoLightHA):
    """RGB atmosphere light for Dreo ceiling fans."""

    def __init__(self, pyDreoDevice: PyDreoBaseDevice) -> None:
        # Pass RGB-specific configuration to parent
        super().__init__(pyDreoDevice,
                        light_on_attr="atm_light_on",
                        brightness_attr="atm_brightness",
                        brightness_scale=(1, 5))

        # Override attributes for RGB light
        self.entity_description = EntityDescription("RGB Light")
        self._attr_name = self.pydreo_device.name + " RGB Light"
        self._attr_unique_id = f"{self.pydreo_device.serial_number}-rgb-light"
        self._attr_icon = "mdi:led-strip-variant"

        # RGB lights only support RGB color mode
        self._color_mode = ColorMode.RGB

        _LOGGER.info(
            "new DreoRGBLightHA instance(%s), unique ID %s",
            self._attr_name,
            self._attr_unique_id)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the current RGB color."""
        return getattr(self.pydreo_device, "atm_color_rgb", None)

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the RGB light on."""
        # Call parent to handle basic light on and brightness
        super().turn_on(**kwargs)

        # Handle RGB color
        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            _LOGGER.debug("Setting RGB color to %s", rgb)
            setattr(self.pydreo_device, "atm_color_rgb", rgb)