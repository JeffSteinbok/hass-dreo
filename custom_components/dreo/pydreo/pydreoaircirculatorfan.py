"""Dreo API for controling air circulator fans."""
import logging
from typing import Dict
from typing import TYPE_CHECKING

from .pydreofan import PyDreoFan
from .fandefinition import PyDreoFanDefinition

from .constant import (
    LOGGER_NAME,
    AIR_CIRCULATOR_WIND_MODE_KEY,
    HORIZONTAL_OSCILLATION_KEY,
    HORIZONTAL_OSCILLATION_ANGLE_KEY,
    VERTICAL_OSCILLATION_KEY,
    VERTICAL_OSCILLATION_ANGLE_KEY
)

if TYPE_CHECKING:
    from pydreo import PyDreo

_LOGGER = logging.getLogger(LOGGER_NAME)

class PyDreoAirCirculatorFan(PyDreoFan):
    """
    Class representing a Dreo Air Circulator Fan
    """

    def __init__(self, 
                 fan_definition: PyDreoFanDefinition, 
                 details: Dict[str, list], 
                 dreoManager: "PyDreo") -> None:
        """Initialize air devices."""
        super().__init__(fan_definition, details, dreoManager)
        self._fan_definition = fan_definition
        self._wind_mode = None
        self._horizontally_oscillating = None
        self._vertically_oscillating = None

    def handle_server_update(self, message: dict):
        """Handle an incoming WebSocket message."""
        super().handle_server_update(message)

        val_wind_mode = self.get_server_update_key_value(
            message, AIR_CIRCULATOR_WIND_MODE_KEY
        )
        if isinstance(val_wind_mode, int):
            self._wind_mode = val_wind_mode

        val_horiz_oscillaation = self.get_server_update_key_value(message, HORIZONTAL_OSCILLATION_KEY)
        if isinstance(val_horiz_oscillaation, bool):
            self._horizontally_oscillating = val_horiz_oscillaation

        val_vert_oscillaation = self.get_server_update_key_value(message, VERTICAL_OSCILLATION_KEY)
        if isinstance(val_vert_oscillaation, bool):
            self._vertically_oscillating = val_vert_oscillaation
    
    @property
    def preset_mode(self):
        """Get the current preset mode"""
        if (self._wind_mode is None):
            return None
        
        return self._fan_definition.preset_modes[self._wind_mode - 1]

    @preset_mode.setter
    def preset_mode(self, preset_mode: str):
        """Set the preset mode."""
        if self._wind_mode is None:
            _LOGGER.error("Attempting to set preset_mode on a device that doesn't support.")
            return
    
        _LOGGER.debug("PyDreoAirCirculatorFan:set_preset_mode")        
        if (preset_mode in self.preset_modes):
            self._send_command(AIR_CIRCULATOR_WIND_MODE_KEY, 
                               self._fan_definition.preset_modes.index(preset_mode) + 1)
        else:
            _LOGGER.error("Preset mode %s is not in the acceptable list: %s",
                          preset_mode, 
                          self._fan_definition.preset_modes)

    @property
    def oscillating(self):
        """Returns `True` if either horizontal or vertical oscillation is on."""
        return self._horizontally_oscillating or self._vertically_oscillating

    @oscillating.setter
    def oscillating(self, oscillating: bool) -> None:
        """Enable oscillation.  Perfer horizontal if supported."""
        _LOGGER.debug("PyDreoAirCirculatorFan:oscillating.setter")
        if self._horizontally_oscillating is not None:
            self.horizontally_oscillating = oscillating
        elif self._vertically_oscillating is not None:
            self.vertically_oscillating = oscillating
        else:
            _LOGGER.error("This device does not support oscillation")

    @property
    def horizontally_oscillating(self):
        return self._horizontally_oscillating
    
    @horizontally_oscillating.setter
    def horizontally_oscillating(self, oscillating: bool) -> None:
        """Enable or disable vertical oscillation"""
        _LOGGER.debug("PyDreoAirCirculatorFan:horizontally_oscillating.setter")
        if (self._horizontally_oscillating is None):
            _LOGGER.error("Horizontal oscillation is not supported.")
            return
        self._send_command(HORIZONTAL_OSCILLATION_KEY, oscillating)

    @property
    def vertically_oscillating(self):
        return self._vertically_oscillating

    @vertically_oscillating.setter
    def vertically_oscillating(self, oscillating: bool) -> None:
        """Enable or disable vertical oscillation"""
        _LOGGER.debug("PyDreoAirCirculatorFan:vertically_oscillating.setter")

        if (self._vertically_oscillating is None):
            _LOGGER.error("Vertical oscillation is not supported.")
            return
        self._send_command(VERTICAL_OSCILLATION_KEY, oscillating)

    def set_horizontal_oscillation_angle(self, angle: int) -> None:
        """Set the horizontal oscillation angle."""
        _LOGGER.debug("PyDreoAirCirculatorFan:set_horizontal_oscillation_angle")
        if not self._horizontally_oscillating is None:
            _LOGGER.error("This device does not support horizontal oscillation")
            return
        self._send_command(HORIZONTAL_OSCILLATION_ANGLE_KEY, angle)

    def set_vertical_oscillation_angle(self, angle: int) -> None:
        """Set the vertical oscillation angle."""
        _LOGGER.debug("PyDreoAirCirculatorFan:set_vertical_oscillation_angle")
        if not self._vertically_oscillating is None:
            _LOGGER.error("This device does not support vertical oscillation")
            return

        self._send_command(VERTICAL_OSCILLATION_ANGLE_KEY, angle)

    def update_state(self, state: dict):
        _LOGGER.debug("PyDreoAirCirculatorFan:update_state")
        super().update_state(state)

        self._wind_mode = self.get_state_update_value(state, AIR_CIRCULATOR_WIND_MODE_KEY)
        self._horizontally_oscillating = self.get_state_update_value(state, HORIZONTAL_OSCILLATION_KEY)
        self._vertically_oscillating = self.get_state_update_value(state, VERTICAL_OSCILLATION_KEY)
