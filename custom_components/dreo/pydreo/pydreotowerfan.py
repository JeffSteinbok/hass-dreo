"""Dreo API for controling tower fans."""

import logging
from typing import Dict
from typing import TYPE_CHECKING

from .pydreofan import PyDreoFan
from .models import SUPPORTED_TOWER_FANS
from .constant import *

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
        self._windType = None
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
            self._windType = valWindType

        valShakeHorizon = self.get_server_update_key_value(message, SHAKEHORIZON_KEY)
        if (isinstance(valShakeHorizon, bool)):
            self._oscillating = valShakeHorizon

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        return self.preset_modes[self._windType - 1]

    @property
    def supports_oscillation(self) -> bool:
        """Does the fan support oscillation?"""
        return self._oscillating is not None

    @property
    def oscillating(self) -> bool:
        """Is the fan currently oscillating?"""
        return self._oscillating
    
    def update_state(self, state: dict) -> None:
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("PyDreoTowerFan:update_state")
        super().update_state(state)
        self._windType = self.get_state_update_value(state, WINDTYPE_KEY)
        self._oscillating = self.get_state_update_value(state, SHAKEHORIZON_KEY)

    def set_preset_mode(self, preset_mode: str):
        _LOGGER.debug("PyDreoTowerFan:set_preset_mode")        
        if (preset_mode in self.preset_modes):
            self._send_command(WINDTYPE_KEY, self._fan_definition.preset_modes.index(preset_mode) + 1)
        else:
            _LOGGER.error("Preset mode %s is not in the acceptable list: %s", preset_mode, self._fan_definition.preset_modes)

    def oscillate(self, oscillating: bool) -> None:
        """Enable or disable oscillation"""
        _LOGGER.debug("PyDreoTowerFan:oscillate")
        self._send_command(SHAKEHORIZON_KEY, oscillating)
