"""Dreo API for controling tower fans."""

import logging
from typing import Dict
from typing import TYPE_CHECKING

from .pydreofan import PyDreoFan
from .fandefinition import PyDreoFanDefinition
from .constant import (
    LOGGER_NAME,
    WINDTYPE_KEY,
    SHAKEHORIZON_KEY
)

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoTowerFan(PyDreoFan):
    """
    Class representing a Dreo Tower Fan. 
    Tower Fans have horizontal oscillation only and no specific angle settings.
    There are also differences between fan types and how the modes are set.
    """

    def __init__(self, fan_definition: PyDreoFanDefinition, details: Dict[str, list], dreoManager: "PyDreo"):
        """Initialize air devices."""
        super().__init__(fan_definition, details, dreoManager)
        self._fan_definition = fan_definition
        self._wind_type = None
        self._oscillating = None

    def __repr__(self):
        # Representation string of object.
        return "<{0}:{1}:{2}>".format(
            self.__class__.__name__, self._device_id, self._name
        )

    def handle_server_update(self, message: dict):
        """Handle messages from the WebSocket connection."""
        super().handle_server_update(message)

        valWindType = self.get_server_update_key_value(message, WINDTYPE_KEY)
        if isinstance(valWindType, int):
            self._wind_type = valWindType

        valShakeHorizon = self.get_server_update_key_value(message, SHAKEHORIZON_KEY)
        if (isinstance(valShakeHorizon, bool)):
            self._oscillating = valShakeHorizon

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        if (self._wind_type is None):
            return None
        return self.preset_modes[self._wind_type - 1]

    @preset_mode.setter
    def preset_mode(self, value: str) -> None:
        _LOGGER.debug("PyDreoTowerFan:set_preset_mode")  

        if self._wind_type is None:
            _LOGGER.error("Attempting to set preset_mode on a device that doesn't support.")
            return
        
        if value in self.preset_modes:
            self._send_command(WINDTYPE_KEY, self._fan_definition.preset_modes.index(value) + 1)
        else:
            _LOGGER.error("Preset mode %s is not in the acceptable list: %s", 
                          value, 
                          self._fan_definition.preset_modes)

    @property
    def oscillating(self) -> bool:
        """Is the fan currently oscillating?"""
        return self._oscillating
    
    @oscillating.setter
    def oscillating(self, value: bool) -> None:
        """Enable or disable oscillation"""
        _LOGGER.debug("PyDreoTowerFan:oscillating.setter")
        
        if (self._oscillating is None):
            _LOGGER.error("Attempting to set oscillating on a device that doesn't support.")
            return
        
        self._send_command(SHAKEHORIZON_KEY, value)

    def update_state(self, state: dict) -> None:
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("PyDreoTowerFan:update_state")
        super().update_state(state)
        self._wind_type = self.get_state_update_value(state, WINDTYPE_KEY)
        self._oscillating = self.get_state_update_value(state, SHAKEHORIZON_KEY)
