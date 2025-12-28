"""Dreo API for controling fans."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    SHAKEHORIZON_KEY,
    SHAKEHORIZONANGLE_KEY,
    OSCILLATION_KEY,
    SPEED_RANGE
)

from .pydreofanbase import PyDreoFanBase
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoTowerFan(PyDreoFanBase):
    """Base class for Dreo Fan API Calls."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        super().__init__(device_definition, details, dreo)
        
        self._speed_range = None
        if (device_definition.device_ranges is not None and SPEED_RANGE in device_definition.device_ranges):
            self._speed_range = device_definition.device_ranges[SPEED_RANGE]
        if (self._speed_range is None):
            self._speed_range = self.parse_speed_range(details)
        self._preset_modes = device_definition.preset_modes
        if (self._preset_modes is None):
            self._preset_modes = self.parse_preset_modes(details)

        self._shakehorizon = None
        self._oscillating = None
        self._shakehorizonangle = None

    def parse_speed_range_from_control_node(self, control_node) -> tuple[int, int]:
        """Parse the speed range from a control node"""
        for control_item in control_node:
            if control_item.get("type", None) == "Speed":
                speed_low = control_item.get("items", None)[0].get("value", None)
                speed_high = control_item.get("items", None)[1].get("value", None)
                speed_range = (speed_low, speed_high)
                return speed_range
        return None
    
    def parse_preset_modes(self, details: Dict[str, list]) -> tuple[str, int]:
        """Parse the preset modes from the details."""
        preset_modes = []
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            control = controls_conf.get("control", None)
            if (control is not None):
                for control_item in control:
                    if (control_item.get("type", None) == "Mode"):
                        for mode_item in control_item.get("items", None):
                            text = self.get_mode_string(mode_item.get("text", None))
                            value = mode_item.get("value", None)
                            preset_modes.append((text, value))
            schedule = controls_conf.get("schedule", None)
            if (schedule is not None):
                modes = schedule.get("modes", None)
                if (modes is not None):
                    for mode_item in modes:
                        text = self.get_mode_string(mode_item.get("title", None))
                        value = mode_item.get("value", None)
                        if (text, value) not in preset_modes:
                            preset_modes.append((text, value))

        preset_modes.sort(key=lambda tup: tup[1])  # sorts in place
        if (len(preset_modes) == 0):
            _LOGGER.debug("PyDreoFan:No preset modes detected")
            preset_modes = None
        _LOGGER.debug("PyDreoFan:Detected preset modes - %s", preset_modes)
        return preset_modes

    @property
    def oscillating(self) -> bool:
        """Returns `True` if either horizontal or vertical oscillation is on."""
        if self._shakehorizon is not None:
            return self._shakehorizon
        elif self._oscillating is not None:
            return self._oscillating
        return None

    @oscillating.setter
    def oscillating(self, value: bool) -> None:

        """Enable or disable oscillation"""
        _LOGGER.debug("PyDreoFan:oscillating.setter")

        if self._shakehorizon is not None:
            if self._shakehorizon == value:
                _LOGGER.debug("PyDreoTowerFan:oscillating - value already %s, skipping command", value)
                return
            self._send_command(SHAKEHORIZON_KEY, value)
        elif self._oscillating is not None:
            if self._oscillating == value:
                _LOGGER.debug("PyDreoTowerFan:oscillating - value already %s, skipping command", value)
                return
            self._send_command(OSCILLATION_KEY, value)
        else:
            raise NotImplementedError("Attempting to set oscillating on a device that doesn't support.")

    @property
    def shakehorizonangle(self) -> int:
        """Get the current oscillation angle"""
        if self._shakehorizonangle is not None:
            return self._shakehorizonangle

    @shakehorizonangle.setter
    def shakehorizonangle(self, value: int) -> None:
        """Set the oscillation angle."""
        _LOGGER.debug("PyDreoFan:shakehorizonangle.setter")
        if self._shakehorizonangle is not None:
            new_value = int(value)
            if self._shakehorizonangle == new_value:
                _LOGGER.debug("PyDreoTowerFan:shakehorizonangle - value already %s, skipping command", new_value)
                return
            self._send_command(SHAKEHORIZONANGLE_KEY, new_value)           

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("PyDreoFan:update_state")
        super().update_state(state)

        self._shakehorizon = self.get_state_update_value(state, SHAKEHORIZON_KEY)
        self._shakehorizonangle = self.get_state_update_value(state, SHAKEHORIZONANGLE_KEY)
        self._oscillating = self.get_state_update_value(state, OSCILLATION_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("PyDreoFan:handle_server_update")
        super().handle_server_update(message)

        # Some tower fans use SHAKEHORIZON and some seem to use OSCON
        val_shakehorizon = self.get_server_update_key_value(message, SHAKEHORIZON_KEY)
        if isinstance(val_shakehorizon, bool):
            self._shakehorizon = val_shakehorizon

        val_shakehorizonangle = self.get_server_update_key_value(message, SHAKEHORIZONANGLE_KEY)
        if isinstance(val_shakehorizonangle, int):
            self._shakehorizonangle = val_shakehorizonangle

        val_horiz_oscillation = self.get_server_update_key_value(message, OSCILLATION_KEY)
        if isinstance(val_horiz_oscillation, bool):
            self._horizontally_oscillating = val_horiz_oscillation
