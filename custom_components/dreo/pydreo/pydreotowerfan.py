"""Dreo API for controling tower fans."""

import logging
from typing import Dict
from typing import TYPE_CHECKING

from .pydreofan import PyDreoFan, UnknownModelError
from .models import SUPPORTED_TOWER_FANS
from .constant import *

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoTowerFan(PyDreoFan):
    """Base class for Dreo Fan API Calls."""

    def __init__(self, fan_definition: PyDreoFanDefinition, details: Dict[str, list], dreoManager: "PyDreo"):
        """Initialize air devices."""
        super().__init__(fan_definition, details, dreoManager)
        self._fan_definition = fan_definition

    def __repr__(self):
        # Representation string of object.
        return "<{0}:{1}:{2}>".format(
            self.__class__.__name__, self._device_id, self._name
        )

    def handle_server_update(self, message):
        super().handle_server_update

        valWindType = self.get_server_update_key_value(message, WINDTYPE_KEY)
        if isinstance(valWindType, int):
            self._windType = valWindType

        valShakeHorizon = self.get_server_update_key_value(message, SHAKEHORIZON_KEY)
        if (isinstance(valShakeHorizon, bool)):
            self._oscillating = valShakeHorizon

    @property
    def preset_mode(self):
        return self.preset_modes[self._windType - 1]

    @property
    def supports_oscillation(self):
        return self._oscillating is not None

    @property
    def oscillating(self):
        return self._oscillating
    
    def update_state(self, state: dict) :
        _LOGGER.debug("PyDreoTowerFan:update_state")
        super().update_state(state)
        self._windType = state[WINDTYPE_KEY][STATE_KEY]
        self._oscillating = state[SHAKEHORIZON_KEY][STATE_KEY]

    def oscillate(self, oscillating: bool) -> None:
        _LOGGER.debug("PyDreoTowerFan:oscillate")
        self._send_command(SHAKEHORIZON_KEY, oscillating)
