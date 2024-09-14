"""Dreo API for controling air purifiers."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME
)

from .pydreofanbase import PyDreoFanBase
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoAirPurifier(PyDreoFanBase):
    """Class for Dreo Air Purifier API Calls."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        _LOGGER.debug("PyDreoAirPurifier:__init__")
        super().__init__(device_definition, details, dreo)

    def parse_speed_range_from_control_node(self, control_node) -> tuple[int, int]:
        """Parse the speed range from a control node"""
        # This is done differently for air purifiers than for other fan types
        for control_item in control_node:
            if control_item.get("value", None) == "manual":
                speed_low = control_item.get("items", None)[0].get("value", None)
                speed_high = control_item.get("items", None)[1].get("value", None)
                speed_range = (speed_low, speed_high)
                return speed_range
        return None

    def parse_preset_modes(self, details: Dict[str, list]) -> tuple[str, str]:
        """Parse the preset modes from the details."""
        preset_modes = []
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            control = controls_conf.get("control", None)
            if (control is not None):
                for control_item in control:
                    if (control_item.get("type", None) == "Mode"):
                        for mode_item in control_item.get("items", None):
                            value = mode_item.get("value", None)
                            preset_modes.append((value, value))
                    elif (control_item.get("type", None) == "Manual"):
                        value = control_item.get("value", None)
                        preset_modes.append((value, value))

        preset_modes.sort(key=lambda tup: tup[1])  # sorts in place
        if (len(preset_modes) == 0):
            _LOGGER.debug("PyDreoAirPurifier:No preset modes detected")
            preset_modes = None
        _LOGGER.debug("PyDreoAirPurifier:Detected preset modes - %s", preset_modes)
        return preset_modes

    @property
    def oscillating(self) -> bool:
        return None
    
    @oscillating.setter
    def oscillating(self, value: bool) -> None:
        raise NotImplementedError(f"Attempting to set oscillating on a device that doesn't support ({value})")
    
    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("PyDreoAirPurifier:update_state")
        super().update_state(state)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("PyDreoAirPurifier:handle_server_update")
        super().handle_server_update(message)
