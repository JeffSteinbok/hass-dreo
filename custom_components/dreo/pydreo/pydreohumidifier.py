"""Dreo API for controlling Humidifiers."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    MODE_KEY,
    MUTEON_KEY,
    POWERON_KEY,
    HUMIDITY_KEY,
    TARGET_AUTO_HUMIDITY_KEY
)

from .helpers import Helpers


from .pydreobasedevice import PyDreoBaseDevice
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo

class PyDreoHumidifier(PyDreoBaseDevice):
    """Base class for Dreo Humidifiers"""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air conditioner devices."""
        super().__init__(device_definition, details, dreo)

        self._modes = device_definition.preset_modes
        if (self._modes is None):
            self._modes = self.parse_modes(details)

        self._mode = None
        self._mute_on = None
        self._humidity = None
        self._target_humidity = None
        
    def parse_modes(self, details: Dict[str, list]) -> tuple[str, int]:
        """Parse the preset modes from the details."""
        modes = []
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            schedule = controls_conf.get("schedule", None)
            if (schedule is not None):
                modes_node = schedule.get("modes", None)
                if (modes_node is not None):
                    for mode_item in modes_node:
                        text = self.get_mode_string(mode_item.get("title", None))
                        value = mode_item.get("value", None)
                        modes.append((text, value))

        modes.sort(key=lambda tup: tup[1])  # sorts in place
        if (len(modes) == 0):
            _LOGGER.debug("PyDreoHumidifier:No preset modes detected")
            modes = None
        _LOGGER.debug("PyDreoHumidifier:Detected preset modes - %s", modes)
        return modes
        
    @property
    def is_on(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._is_on

    @is_on.setter
    def is_on(self, value: bool):
        """Set if the fan is on or off"""
        _LOGGER.debug("PyDreoHumidifier:is_on.setter - %s", value)
        self._send_command(POWERON_KEY, value)

    @property
    def modes(self) -> list[str]:
        """Get the list of modes"""
        return Helpers.get_name_list(self._modes)

    @property
    def humidity(self):
        """Get the humidity"""
        return self._humidity

    @property
    def target_humidity(self):
        """Get the target_humidity"""
        return self._target_humidity

    @target_humidity.setter
    def target_humidity(self, value: int) -> None:
        """Set the target humidity"""
        _LOGGER.debug("PyDreoHumidifier:target_humidity.setter(%s) %s --> %s", self, self._target_humidity, value)
        self._target_humidity = value
        self._send_command(TARGET_AUTO_HUMIDITY_KEY, value)

    @property
    def panel_sound(self) -> bool:
        """Is the panel sound on"""
        if self._mute_on is not None:
            return not self._mute_on
        return None

    @panel_sound.setter
    def panel_sound(self, value: bool) -> None:
        """Set if the panel sound"""
        _LOGGER.debug("PyDreoHumidifier:panel_sound.setter(%s) --> %s", self.name, value)
        self._send_command(MUTEON_KEY, not value)
        
    @property
    def mode(self):
        """Return the current mode."""
        
        str_value : str = Helpers.name_from_value(self._modes, self._mode)
        if (str_value is None):
            return None
        return str_value

    @mode.setter
    def mode(self, value: str) -> None:
        numeric_value = Helpers.value_from_name(self._modes, value)
        if numeric_value is not None:
            self._send_command(MODE_KEY, numeric_value)
        else:
            raise ValueError(f"Preset mode {value} is not in the acceptable list: {self._modes}")

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        super().update_state(state)  # handles _is_on

        _LOGGER.debug("PyDreoHumidifier(%s):update_state: %s", self.name, state)
        self._mode = self.get_state_update_value(state, MODE_KEY)
        self._mute_on = self.get_state_update_value(state, MUTEON_KEY)
        self._humidity = self.get_state_update_value(state, HUMIDITY_KEY)
        self._target_humidity = self.get_state_update_value(state, TARGET_AUTO_HUMIDITY_KEY)
        
    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("PyDreoHumidifier:handle_server_update(%s): %s", self.name, message)

        val_poweron = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_poweron, bool):
            self._is_on = val_poweron  # Ensure poweron state is updated
            _LOGGER.debug("PyDreoHumidifier:handle_server_update - poweron is %s", self._is_on)

        val_mode = self.get_server_update_key_value(message, MODE_KEY)
        if isinstance(val_mode, int):
            self._mode = val_mode
