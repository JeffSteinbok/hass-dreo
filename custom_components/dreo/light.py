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
    def __init__(self,  pyDreoDevice: PyDreoBaseDevice) -> None:
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice

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
            getattr(self.pydreo_device, "light_on")
        )
        return getattr(self.pydreo_device, "light_on")

    def turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn the device on."""
        _LOGGER.debug("Turning on %s", self.pydreo_device.name)
        setattr(self.pydreo_device, "light_on", True)
        
        if (ATTR_BRIGHTNESS in kwargs):
            brightness = kwargs[ATTR_BRIGHTNESS]
            _LOGGER.debug("Setting brightness to %s", brightness)
            setattr(self.pydreo_device, "brightness", math.ceil(brightness_to_value((1,100), brightness)))

        if (ATTR_COLOR_TEMP_KELVIN in kwargs):
            color_temp = kwargs[ATTR_COLOR_TEMP_KELVIN]
            _LOGGER.debug("Setting color temperature to %s", color_temp)
            setattr(self.pydreo_device, "color_temperature", math.ceil(ranged_value_to_percentage((self.min_color_temp_kelvin,self.max_color_temp_kelvin), color_temp)))


    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        _LOGGER.debug("Turning off %s", self.pydreo_device.name)
        setattr(self.pydreo_device, "light_on", False)

    @property
    def brightness(self) -> int | None:
        """Return the current brightness."""
        if not self.device.is_feature_supported("brightness"):
            return None
            
        return math.ceil(value_to_brightness((1,100), getattr(self.pydreo_device, "brightness", 0)))

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the current color temperature."""
        if not self.device.is_feature_supported("color_temperature"):
            return None
            
        return math.ceil(percentage_to_ranged_value((self.min_color_temp_kelvin,self.max_color_temp_kelvin), getattr(self.pydreo_device, "color_temperature", 0)))