"""Dreo API for controling fans."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    FANON_KEY,
    LIGHTON_KEY,
    WINDLEVEL_KEY,
    SPEED_RANGE,
)

from .pydreofanbase import PyDreoFanBase
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoCeilingFan(PyDreoFanBase):
    """Base class for Dreo Fan API Calls."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        super().__init__(device_definition, details, dreo)
        
        self._speed_range = None
        if (device_definition.device_ranges is not None):
            self._speed_range = device_definition.device_ranges[SPEED_RANGE]
        if (self._speed_range is None):
            self._speed_range = self.parse_speed_range(details)
        self._preset_modes = device_definition.preset_modes
        if (self._preset_modes is None):
            self._preset_modes = self.parse_preset_modes(details)

        self._fan_speed = None
        self._light_on = None

        self._wind_type = None
        self._wind_mode = None

        self._device_definition = device_definition
    
    def parse_preset_modes(self, details: Dict[str, list]) -> tuple[str, int]:
        """Parse the preset modes from the details."""
        preset_modes = []
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            control = controls_conf.get("control", None)
            if (control is not None):
                for control_item in control:
                    if (control_item.get("type", None) == "CFFan"):
                        for mode_item in control_item.get("items", None):
                            text = self.get_mode_string(mode_item.get("text", None))
                            value = mode_item.get("value", None)
                            preset_modes.append((text, value))

        preset_modes.sort(key=lambda tup: tup[1])  # sorts in place
        if (len(preset_modes) == 0):
            _LOGGER.debug("PyDreoFan:No preset modes detected")
            preset_modes = None
        _LOGGER.debug("PyDreoFan:Detected preset modes - %s", preset_modes)
        return preset_modes

    @PyDreoFanBase.is_on.setter
    def is_on(self, value: bool):
        """Set if the fan is on or off"""
        _LOGGER.debug("PyDreoFan:is_on.setter - %s", value)
        self._send_command(FANON_KEY, value)

    @property
    def light_on(self):
        """Returns `True` if the device light is on, `False` otherwise."""
        return self._light_on

    @light_on.setter
    def light_on(self, value: bool):
        """Set if the fan is on or off"""
        _LOGGER.debug("PyDreoCeilingFan:light_on.setter - %s", value)
        self._send_command(LIGHTON_KEY, value)

    @property
    def oscillating(self) -> bool:
        return None
    
    @oscillating.setter
    def oscillating(self, value: bool) -> None:
        raise NotImplementedError(f"Attempting to set oscillating on a device that doesn't support ({value})")
    
    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("PyDreoFan:update_state")
        super().update_state(state)

        self._fan_speed = self.get_state_update_value(state, WINDLEVEL_KEY)
        if self._fan_speed is None:
            _LOGGER.error("Unable to get fan speed from state. Check debug logs for more information.")

        self._is_on = self.get_state_update_value(state, FANON_KEY)
        self._light_on = self.get_state_update_value(state, LIGHTON_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("PyDreoCeilingFan:handle_server_update")
        super().handle_server_update(message)

        val_power_on = self.get_server_update_key_value(message, FANON_KEY)
        if isinstance(val_power_on, bool):
            self._is_on = val_power_on

        val_light_on = self.get_server_update_key_value(message, LIGHTON_KEY)
        if isinstance(val_light_on, bool):
            self._light_on = val_light_on            
