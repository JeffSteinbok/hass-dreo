"""Support for Dreo LED lighting."""
from __future__ import annotations

from enum import property
from functools import cached_property
import logging
from typing import Any

from homeassistant.components.light.const import ColorMode
from homeassistant.util.color import brightness_to_value, value_to_brightness
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_RGB_COLOR, LightEntity

from .haimports import *  # pylint: disable=W0401,W0614
from .dreobasedevice import DreoBaseDeviceHA
from .const import LOGGER
from .pydreo.mixins.ledmixin import LedMixin


_LOGGER = logging.getLogger(LOGGER)

BRIGHTNESS_SCALE = (1, 3)

class DreoLightHA(DreoBaseDeviceHA, LightEntity):
    """Representation of a Dreo device's LED light."""

    def __init__(self, pyDreoDevice: LedMixin):
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice

    @property
    def color_mode(self) -> str:
        return ColorMode.RGB

    @property
    def supported_color_modes(self):
        return {ColorMode.RGB}

    @property
    def is_on(self) -> bool:
        return bool(self.device.is_led_on)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        color = self.device.rgb_color
        if color is None:
            return
            
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF

        return (r, g, b)

    @property
    def brightness(self) -> int | None:
        brightness = self.device.brightness
        if brightness is None:
            return

        return value_to_brightness(BRIGHTNESS_SCALE, float(brightness))
        

    def turn_on(self, **kwargs: dict[str, Any]) -> None:
        _LOGGER.debug("DreoLightHA:turn_on kwargs=%s", kwargs)
        self.device.is_led_on = True

        rgb_color = kwargs.get(ATTR_RGB_COLOR)
        if isinstance(rgb_color, tuple):
            r, g, b = rgb_color
            color = (r << 16) | (g << 8) | b
            self.device.rgb_color = color
            
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if isinstance(brightness, int):
            normalised = brightness_to_value(BRIGHTNESS_SCALE, brightness)
            self.device.brightness = int(normalised)

        self.schedule_update_ha_state()

    def turn_off(self, **kwargs: dict[str, Any]) -> None:
        _LOGGER.debug("DreoLightHA:turn_off")
        self.device.is_led_on = False
        self.schedule_update_ha_state()