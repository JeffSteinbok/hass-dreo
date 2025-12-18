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
    RGB_LEVEL,
    SCHEDULE_ENABLE,
    FOGLEVEL_KEY,
    WATERLEVEL_KEY,
    FILTERTIME_KEY,
    WORKTIME_KEY,
    LEDLEVEL_KEY,
    AUTODRYON_KEY,
    WRONG_KEY
)

from .helpers import Helpers


from .pydreobasedevice import PyDreoBaseDevice
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(LOGGER_NAME)

WATER_LEVEL_STATUS_KEY = "wrong"
WORKTIME_KEY = "worktime"

# Status for water level indicator
WATER_LEVEL_OK = "Ok"
WATER_LEVEL_EMPTY = "Empty"

LIGHT_ON = "Enable"
LIGHT_OFF = "Disabled"

WATER_LEVEL_STATUS_MAP = {
    0: WATER_LEVEL_OK,
    1: WATER_LEVEL_EMPTY,
    WATER_LEVEL_OK: 0,
    WATER_LEVEL_EMPTY: 1
}

RGB_MAP = {
    0: LIGHT_OFF,
    2: LIGHT_ON,
    LIGHT_OFF: 0,
    LIGHT_ON: 2
}

# Status for mode indicator
MODE_MANUAL = "manual"
MODE_AUTO = "auto" 
MODE_SLEEP = "sleep"

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
        if (self._modes is None):
            # Default modes for humidifiers (DR-HHM014S and similar)
            self._modes = [("Manual", 0), ("Auto", 1), ("Sleep", 2)]
            _LOGGER.debug("PyDreoHumidifier: Using default modes %s", self._modes)

        self._mode = None
        self._mute_on = None
        self._humidity = None
        self._target_humidity = None
        self._wrong = None
        self._worktime = None
        self._rgblevel = None
        self._scheon = None
        self._mist_level = None
        self._mist_level_range = (1, 6)  # DR-HHM014S has 6 mist levels (1-, 1, 2-, 2, 3-, 3)
        self._water_level = None
        self._filter_time = None
        self._work_time = None
        self._led_level = None
        self._auto_dry_on = None
        self._error_code = None
        
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
    def mist_level(self) -> int:
        """Get the mist level (1-3 for Manual mode)"""
        return self._mist_level

    @mist_level.setter
    def mist_level(self, value: int) -> None:
        """Set the mist level"""
        value = int(value)
        _LOGGER.debug("PyDreoHumidifier:mist_level.setter(%s) %s --> %s", self.name, self._mist_level, value)
        if value < self._mist_level_range[0] or value > self._mist_level_range[1]:
            raise ValueError(f"Mist level {value} is out of range {self._mist_level_range}")
        self._send_command(FOGLEVEL_KEY, value)

    @property
    def mist_level_range(self) -> tuple:
        """Get the mist level range"""
        return self._mist_level_range

    @property
    def water_level(self) -> int:
        """Get the water level percentage"""
        return self._water_level

    @property
    def filter_time(self) -> int:
        """Get the filter life remaining percentage"""
        return self._filter_time

    @property
    def work_time(self) -> int:
        """Get the work time in hours"""
        return self._work_time

    @property
    def led_level(self) -> int:
        """Get the LED brightness level"""
        return self._led_level

    @led_level.setter
    def led_level(self, value: int) -> None:
        """Set the LED brightness level"""
        value = int(value)
        _LOGGER.debug("PyDreoHumidifier:led_level.setter(%s) %s --> %s", self.name, self._led_level, value)
        self._send_command(LEDLEVEL_KEY, value)

    @property
    def auto_dry_on(self) -> bool:
        """Get the auto dry feature state"""
        return self._auto_dry_on

    @auto_dry_on.setter
    def auto_dry_on(self, value: bool) -> None:
        """Set the auto dry feature state"""
        _LOGGER.debug("PyDreoHumidifier:auto_dry_on.setter(%s) --> %s", self.name, value)
        self._send_command(AUTODRYON_KEY, value)

    @property
    def error_code(self) -> int:
        """Get the error code (0 = no error)"""
        return self._error_code

    @property
    def mode(self):
        """Return the current mode."""
        
        str_value : str = Helpers.name_from_value(self._modes, self._mode)
        if (str_value is None):
            return None
        return str_value
        
    @property
    def wrong(self):
        """Return the water level status"""
        return self._wrong

    @property
    def worktime(self):
        """Return the working time (used since cleaning)"""
        return self._worktime

    @property
    def rgblevel(self):
        """Return RGB Level to verify Light is ON/OFF """
        return self._rgblevel
    
    @property
    def scheon(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._scheon

    @scheon.setter
    def scheon(self, value: bool):
        """Set if the fan is on or off"""
        _LOGGER.debug("PyDreoHumidifier:scheon.setter - %s", value)
        self._send_command(SCHEDULE_ENABLE, value)        
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
        self._wrong = self.get_state_update_value_mapped(state, WATER_LEVEL_STATUS_KEY, WATER_LEVEL_STATUS_MAP)
        self._worktime = self.get_state_update_value(state, WORKTIME_KEY)
        self._rgblevel = self.get_state_update_value_mapped(state, RGB_LEVEL, RGB_MAP)
        self._scheon = self.get_state_update_value(state, SCHEDULE_ENABLE)
        
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

        val_mist_level = self.get_server_update_key_value(message, FOGLEVEL_KEY)
        if isinstance(val_mist_level, int):
            self._mist_level = val_mist_level

        val_humidity = self.get_server_update_key_value(message, HUMIDITY_KEY)
        if isinstance(val_humidity, int):
            self._humidity = val_humidity

        val_target_humidity = self.get_server_update_key_value(message, TARGET_AUTO_HUMIDITY_KEY)
        if isinstance(val_target_humidity, int):
            self._target_humidity = val_target_humidity

        val_water_level = self.get_server_update_key_value(message, WATERLEVEL_KEY)
        if isinstance(val_water_level, int):
            self._water_level = val_water_level

        val_mute = self.get_server_update_key_value(message, MUTEON_KEY)
        if isinstance(val_mute, bool):
            self._mute_on = val_mute

        val_led = self.get_server_update_key_value(message, LEDLEVEL_KEY)
        if isinstance(val_led, int):
            self._led_level = val_led

        val_auto_dry = self.get_server_update_key_value(message, AUTODRYON_KEY)
        if isinstance(val_auto_dry, bool):
            self._auto_dry_on = val_auto_dry

        val_error = self.get_server_update_key_value(message, WRONG_KEY)
        if isinstance(val_error, int):
            self._error_code = val_error

        val_worktime = self.get_server_update_key_value(message, WORKTIME_KEY)
        if isinstance(val_worktime, int):
            self._worktime = val_worktime

        val_water_level = self.get_server_update_key_value(message, WATER_LEVEL_STATUS_KEY)
        if isinstance(val_water_level, int):
            val_water_level = WATER_LEVEL_STATUS_MAP[val_water_level]
            self._wrong = val_water_level		

        val_rgblevel = self.get_server_update_key_value(message, RGB_LEVEL)
        if isinstance(val_rgblevel, int):
            val_rgblevel = RGB_MAP[val_rgblevel]
            self._rgblevel = val_rgblevel 

        val_scheon = self.get_server_update_key_value(message, SCHEDULE_ENABLE)
        if isinstance(val_scheon, bool):
            self._scheon = val_scheon  

        val_mute_on = self.get_server_update_key_value(message, MUTEON_KEY)
        if isinstance(val_mute_on, bool):
            self._mute_on = val_mute_on      
