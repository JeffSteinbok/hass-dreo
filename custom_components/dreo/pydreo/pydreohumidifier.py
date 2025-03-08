"""Dreo API for controlling Humidifiers."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    MODE_KEY,
    MUTEON_KEY,
    POWERON_KEY,
    HUMIDITY_KEY,
    TARGET_AUTO_HUMIDITY_KEY,
    TARGET_SLEEP_HUMIDITY_KEY,
    FILTERON_KEY,
    FILTER_TIME_KEY,
    FOG_LEVEL_KEY,
    WORK_TIME_KEY,
    RGBTH_KEY,
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
        self._min_humidity = 30  # Default value
        self._max_humidity = 60  # Default value
        self._modes = device_definition.preset_modes
        if (self._modes is None):
            self._modes = self.parse_modes(details)

        self._mode = None
        self._mute_on = None
        self._filter_on = None
        self._humidity = None
        self._target_humidity = None
        self._work_time = None
        self._filter_time = None
        self._target_humidity_sleep = None
        self._fog_level = None

        
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
    def fog_level(self):
        """Returns fog level for manual setting"""
        return self._fog_level

    @fog_level.setter
    def fog_level(self, value: int):
        """Sets fog level for manual setting"""
        _LOGGER.debug("PyDreoHumidifier:fog_level.setter - %s", value)
        self._fog_level = value
        self._send_command(FOG_LEVEL_KEY, value)

    @property
    def filter_on(self):
        """Is the filter on"""
        if self._filter_on is not None:
            return self._filter_on
        return None

    @filter_on.setter
    def filter_on(self, value: bool):
        """Set if the water filter is on or off"""
        _LOGGER.debug("PyDreoHumidifier:filter_on.setter - %s", value)
        self._filter_on = value
        self._send_command(FILTERON_KEY, value)

    @property
    def filter_time(self):
        if self._filter_time is not None:
            return self._filter_time
        return None
    
    @property
    def work_time(self):
        if self._work_time is not None:
            return self._work_time
        return None
    
    def reset_filter(self) -> None:
        """Reset the filter life counter to 0."""
        _LOGGER.debug("PyDreoHumidifier:reset_filter for %s", self.name)
        self._filter_time = 100  # Update local state
        self._send_command(FILTER_TIME_KEY, 0)

    def reset_work_time(self) -> None:
        """Reset the cleaning reminder counter to 0."""
        _LOGGER.debug("PyDreoHumidifier:reset_work_time for %s", self.name)
        self._work_time = 0  # Update local state
        self._send_command(WORK_TIME_KEY, 0)

    @property
    def min_humidity_target(self) -> int:
        """Get the minimum humidity target."""
        return self._min_humidity

    @min_humidity_target.setter
    def min_humidity_target(self, value: int) -> None:
        """Set the minimum humidity target."""
        value = int(value)  # Explicitly convert to integer
        _LOGGER.debug("PyDreoHumidifier:min_humidity_target.setter(%s) --> %s", self.name, value)
        if value > self._max_humidity:
            _LOGGER.warning("Min humidity cannot be greater than max humidity")
            raise ValueError(f"Min humidity {value} cannot be greater than max humidity {self._max_humidity}")
        self._min_humidity = value
        self._send_command(RGBTH_KEY, f"{value},{int(self._max_humidity)}")

    @property
    def max_humidity_target(self) -> int:
        """Get the maximum humidity target."""
        return self._max_humidity

    @max_humidity_target.setter
    def max_humidity_target(self, value: int) -> None:
        """Set the maximum humidity target."""
        value = int(value)  # Explicitly convert to integer
        _LOGGER.debug("PyDreoHumidifier:max_humidity_target.setter(%s) --> %s", self.name, value)
        if value < self._min_humidity:
            _LOGGER.warning("Max humidity cannot be less than min humidity")
            raise ValueError(f"Max humidity {value} cannot be less than min humidity {self._min_humidity}")
        self._max_humidity = value
        self._send_command(RGBTH_KEY, f"{int(self._min_humidity)},{value}")

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
    def target_humidity_sleep(self):
        """Get the target_humidity_sleep"""
        return self._target_humidity_sleep

    @target_humidity_sleep.setter
    def target_humidity_sleep(self, value: int) -> None:
        """Set the target humidity for sleep mode"""
        _LOGGER.debug("PyDreoHumidifier:target_humidity_sleep.setter(%s) %s --> %s", self, self._target_humidity_sleep, value)
        self._target_humidity_sleep = value
        self._send_command(TARGET_SLEEP_HUMIDITY_KEY, value)

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
        self._filter_on = self.get_state_update_value(state, FILTERON_KEY)
        self._work_time = self.get_state_update_value(state, WORK_TIME_KEY)
        self._filter_time = self.get_state_update_value(state, FILTER_TIME_KEY)
        self._target_humidity_sleep = self.get_state_update_value(state, TARGET_SLEEP_HUMIDITY_KEY)
        self._fog_level = self.get_state_update_value(state, FOG_LEVEL_KEY)
        # Handle humidity range from rgbth
        rgbth_state = self.get_state_update_value(state, RGBTH_KEY)
        if rgbth_state and isinstance(rgbth_state, str):
            try:
                min_h, max_h = map(int, rgbth_state.split(","))
                self._min_humidity = min_h
                self._max_humidity = max_h
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid humidity range format: %s", rgbth_state)

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

        val_filter_on = self.get_server_update_key_value(message, FILTERON_KEY)
        if isinstance(val_filter_on, bool):
            self._filter_on = val_filter_on

        val_work_time = self.get_server_update_key_value(message, WORK_TIME_KEY)
        if isinstance(val_work_time, int):
            self._work_time = val_work_time

        val_filter_time = self.get_server_update_key_value(message, FILTER_TIME_KEY)
        if isinstance(val_filter_time, int):
            self._filter_time = val_filter_time

        val_target_humidity = self.get_server_update_key_value(message, TARGET_AUTO_HUMIDITY_KEY)
        if isinstance(val_target_humidity, int):
            self._target_humidity = val_target_humidity

        val_target_humidity_sleep = self.get_server_update_key_value(message, TARGET_SLEEP_HUMIDITY_KEY)
        if isinstance(val_target_humidity_sleep, int):
            self._target_humidity_sleep = val_target_humidity_sleep

        val_fog_level = self.get_server_update_key_value(message, FOG_LEVEL_KEY)
        if isinstance(val_fog_level, int):
            self._fog_level = val_fog_level

        val_mute_on = self.get_server_update_key_value(message, MUTEON_KEY)
        if isinstance(val_mute_on, bool):
            self._mute_on = val_mute_on

        val_humidity = self.get_server_update_key_value(message, HUMIDITY_KEY)
        if isinstance(val_humidity, int):
            self._humidity = val_humidity

        # Handle rgbth updates
        rgbth_value = self.get_server_update_key_value(message, RGBTH_KEY)
        if rgbth_value and isinstance(rgbth_value, str):
            try:
                min_h, max_h = map(int, rgbth_value.split(","))
                self._min_humidity = min_h
                self._max_humidity = max_h
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid humidity range update: %s", rgbth_value)