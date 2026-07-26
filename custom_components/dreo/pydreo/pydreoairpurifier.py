"""Dreo API for controling air purifiers."""

import logging
from typing import TYPE_CHECKING, Dict

from .pydreofanbase import PyDreoFanBase
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoAirPurifier(PyDreoFanBase):
    """Class for Dreo Air Purifier API Calls."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        _LOGGER.debug("__init__: __init__")
        super().__init__(device_definition, details, dreo)
        # Set by _hap003s_mcu_override after device state is loaded when the "midea" or "001" MCU is
        # detected.  When True, _send_command remaps the "auto" mode value to "auto-silent"
        # before transmission because that hardware revision rejects the plain "auto" string.
        self._auto_mode_uses_auto_silent: bool = False
        # Alternate command string to send in place of the plain "auto" mode value for models that
        # reject "auto" (e.g. DR-HAP009S requires "auto-regular").  None means send "auto" unchanged.
        # Takes effect only when _auto_mode_uses_auto_silent is not set.
        self._auto_mode_command_value: str | None = None

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
            if control is not None:
                for control_item in control:
                    if control_item.get("type", None) == "Mode":
                        for mode_item in control_item.get("items", None):
                            value = mode_item.get("value", None)
                            preset_modes.append((value, value))
                    elif control_item.get("type", None) == "Manual":
                        value = control_item.get("value", None)
                        preset_modes.append((value, value))

        preset_modes.sort(key=lambda tup: tup[1])  # sorts in place
        if len(preset_modes) == 0:
            _LOGGER.debug("parse_preset_modes: No preset modes detected")
            preset_modes = None
        _LOGGER.debug("parse_preset_modes: Detected preset modes - %s", preset_modes)
        return preset_modes

    @property
    def oscillating(self) -> bool:
        return None

    @oscillating.setter
    def oscillating(self, value: bool) -> None:
        raise NotImplementedError(f"Attempting to set oscillating on a device that doesn't support ({value})")

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("update_state: update_state")
        super().update_state(state)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("handle_server_update: handle_server_update")
        super().handle_server_update(message)

    def _send_command(self, command_key: str, value) -> None:
        """Override to remap the 'auto' mode command for models that reject the plain "auto" string.

        Some hardware/firmware revisions reject the plain "auto" mode command and require a
        variant instead.  Newer DR-HAP003S units ("midea"/"001" MCU) require "auto-silent"
        (_auto_mode_uses_auto_silent); DR-HAP009S requires "auto-regular"
        (_auto_mode_command_value).  The device reports the variant back as its state;
        PyDreoFanBase.preset_mode normalizes mode variants by stripping any "-<suffix>" (so
        "auto-silent"/"auto-regular" resolve to "auto").  This keeps the Home Assistant-facing
        preset name stable across hardware/firmware variants.
        """
        if command_key == "mode" and value == "auto":
            if self._auto_mode_uses_auto_silent:
                value = "auto-silent"
            elif self._auto_mode_command_value is not None:
                value = self._auto_mode_command_value
            if value != "auto":
                _LOGGER.debug("PyDreoAirPurifier._send_command: remapping 'auto' to '%s' for %s", value, self.model)
        super()._send_command(command_key, value)
