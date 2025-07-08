"""Dreo API extension for LED control on Air Circulator models."""

from enum import property
import logging
from typing import TYPE_CHECKING, Any

from custom_components.dreo.pydreo.pydreobasedevice import PyDreoBaseDevice

from ..constant import LIGHTBRIGHTNESS_KEY, LOGGER_NAME, LIGHTMODE_KEY, LIGHTCOLOUR_KEY

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo

class LedMixin(PyDreoBaseDevice):
    """Adds LED control on top of any PyDreoBaseDevice subclass."""

    def __init__(self, device_definition: Any, details: dict[str, Any], dreo: "PyDreo"):
        super().__init__(device_definition, details, dreo)

        self._is_led_on: bool | None = None
        self._rgb_color: int | None = None
        self._brightness: int | None = None

    @property
    def is_led_on(self) -> bool | None:
        return self._is_led_on

    @property
    def rgb_color(self) -> int | None:
        return self._rgb_color
    
    @property
    def brightness(self) -> int | None:
        return self._brightness

    @is_led_on.setter
    def is_led_on(self, on: bool) -> None:
        _LOGGER.debug("%s:set_led_on %s", self.__class__.__name__, on)
        self._send_command(LIGHTMODE_KEY, on)

    @rgb_color.setter
    def rgb_color(self, color: int) -> None:
        _LOGGER.debug("%s:set_led_color %s", self.__class__.__name__, color)
        self._send_command(LIGHTCOLOUR_KEY, color)

    @brightness.setter
    def brightness(self, brightness: int) -> int | None:
        _LOGGER.debug("%s:set_brightness %f", self.__class__.__name__, brightness)
        self._send_command(LIGHTBRIGHTNESS_KEY, brightness)

    def update_state(self, state: dict[str, Any]) -> None:
        _LOGGER.debug("%s:update_state", self.__class__.__name__)
        super().update_state(state)

        self._is_led_on = self.get_state_update_value(state, LIGHTMODE_KEY)
        self._rgb_color = self.get_state_update_value(state, LIGHTCOLOUR_KEY)
        self._brightness = self.get_state_update_value(state, LIGHTBRIGHTNESS_KEY)

    def handle_server_update(self, message: dict[str, Any]) -> None:
        _LOGGER.debug("%s:handle_server_update", self.__class__.__name__)
        super().handle_server_update(message)

        val_mode = self.get_server_update_key_value(message, LIGHTMODE_KEY)
        if isinstance(val_mode, bool):
            self._is_led_on = val_mode

        val_color = self.get_server_update_key_value(message, LIGHTCOLOUR_KEY)
        if isinstance(val_color, int):
            self._rgb_color = int(val_color)
        
        val_brightness = self.get_server_update_key_value(message, LIGHTBRIGHTNESS_KEY)
        if isinstance(val_brightness, int):
            self._brightness = int(val_brightness)
        
        