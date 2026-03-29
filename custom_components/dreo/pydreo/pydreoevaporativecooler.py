"""Dreo API for controling evaporative coolers."""

import logging
from typing import TYPE_CHECKING, Dict, Optional
from .pydreofanbase import PyDreoFanBase

from .constant import (
    CHILDLOCKON_KEY,
    HORIZONTAL_OSCILLATION_KEY,
    HUMIDITY_KEY,
    TEMPOFFSET_KEY,
)

from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(__name__)

WIND_MODE_KEY = "windmode"
HUMIDIFY_MODE_KEY = "rhmode"
HUMIDIFY_SUSPEND_KEY = "rhsuspend"
HUMIDITY_TARGET_KEY = "rhtarget"
WORKTIME_KEY = "worktime"
WATER_LEVEL_STATUS_KEY = "wrong"

# Status for water level indicator
WATER_LEVEL_OK = "Ok"
WATER_LEVEL_EMPTY = "Empty"

# States (enabled, disabled) for humidifier
HUMIDIFY_MODE_MAP = {
    0: False,
    2: True,
    False : 0,
    True: 2
}

WATER_LEVEL_STATUS_MAP = {
    0: WATER_LEVEL_OK,
    1: WATER_LEVEL_EMPTY,
    WATER_LEVEL_OK: 0,
    WATER_LEVEL_EMPTY: 1
}

WINDMODES = [
    "Normal",
    "Natural",
    "Sleep",
    "Auto",  
]

# Windmodes for evaporative cooler
WINDMODE_MAP = {
    "Normal": 1,
    "Auto": 2,
    "Sleep": 3,
    "Natural": 4,
    1: "Normal",
    2: "Auto",
    3: "Sleep",
    4: "Natural"
}

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoEvaporativeCooler(PyDreoFanBase):
    """Base class for Dreo evaporative cooler API Calls."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize evaporative cooler devices."""
        super().__init__(device_definition, details, dreo)

        self._temperature_offset = None
        
        self._wind_type = None
        self._wind_mode = None
        self._humidity = None
        self._target_humidity = None
        self._mute_on = None
        self._oscillating = None
        self._humidify = None
        self._childlockon = None
        self._preset_modes = WINDMODES
        self._work_time = None
        self._display_auto_off = None
        self._water_level = None
    
    
    def parse_preset_modes(self, details: Dict[str, list]) -> tuple[str, int]:
        # Not needed atm            
        return False
    
    
    @property
    def temperature(self):
        """Get the temperature"""
        temp = self._temperature
        if (temp is not None and self.temperature_offset is not None):
            temp += self.temperature_offset
        return temp
    
    
    @property
    def temperature_offset(self):
        """Get the offset of the temperature"""
        return self._temperature_offset
                 
    @property
    def humidity(self):
        """Get the humidity"""
        return self._humidity
    
    @property 
    def humidify(self) -> bool:
        """Returns `True` if humidifying is on"""
        return self._humidify
    
    @humidify.setter
    def humidify(self, mode: bool) -> None:
        """Enable or disable humidifying"""
        if self._humidify == mode:
            _LOGGER.debug("humidify: humidify - value already %s, skipping command", mode)
            return
        self._humidify = mode
        self._send_command(HUMIDIFY_MODE_KEY, HUMIDIFY_MODE_MAP[mode])

    @property
    def target_humidity(self):
        """Get the target_humidity"""
        return self._target_humidity

    @target_humidity.setter
    def target_humidity(self, value: int) -> None:
        """Set the target humidity"""
        _LOGGER.debug("target_humidity: target_humidity.setter(%s) %s --> %s", self, self._target_humidity, value)
        if self._target_humidity == value:
            _LOGGER.debug("target_humidity: target_humidity - value already %s, skipping command", value)
            return
        self._target_humidity = value
        self._send_command(HUMIDITY_TARGET_KEY, value)
    
    @property
    def oscillating(self) -> bool:
       """Returns `True` if oscillation is on"""
       return self._oscillating
    
    @oscillating.setter
    def oscillating(self, value: bool) -> None:
        """Enable or disable oscillation"""
        if self._oscillating == value:
            _LOGGER.debug("oscillating: oscillating - value already %s, skipping command", value)
            return
        self._oscillating = value
        self._send_command(HORIZONTAL_OSCILLATION_KEY, value)

    @property
    def childlockon(self) -> bool:
        """Returns `True` if child lock is on"""
        return self._childlockon
    
    @childlockon.setter
    def childlockon(self, value: bool) -> None:
        """Enable or disable child lock"""
        if self._childlockon == value:
            _LOGGER.debug("childlockon: childlockon - value already %s, skipping command", value)
            return
        self._childlockon = value
        self._send_command(CHILDLOCKON_KEY, value)
        
    @property
    def preset_mode(self):
        """Return the current preset mode as a string."""
        if self._wind_mode is None:
            return None
        return WINDMODE_MAP.get(self._wind_mode, self._wind_mode)

    @preset_mode.setter
    def preset_mode(self, value: str) -> None:
        """Set preset mode"""
        if value not in WINDMODES:
            raise ValueError(f"Preset mode {value} is not in the acceptable list: {WINDMODES}")
        new_value = WINDMODE_MAP[value]
        if self._wind_mode == new_value:
            _LOGGER.debug("preset_mode: preset_mode - value already %s, skipping command", value)
            return
        self._send_command(WIND_MODE_KEY, new_value)

    @property
    def preset_modes(self) -> list[str]:
        """Get the list of preset modes"""
        if WINDMODES is None:
            return None
        return self._preset_modes
    
    @property
    def work_time(self) -> int:
       """Return the working time (used since cleaning)"""
       return self._work_time 
   
    @property
    def water_level(self) -> int:
       """Return the water level status"""
       return self._water_level
   
    @staticmethod
    def _map_wind_mode_from_rest(index: int) -> Optional[int]:
        """Convert REST API windmode 0-based index to internal int (1-4).

        The REST API returns 0-based indices into the WINDMODES list, while
        the WebSocket and internal storage use the 1-4 int values defined in
        WINDMODE_MAP.  Extracting this conversion makes both paths consistent
        and individually testable.
        """
        if index is None or index < 0 or index >= len(WINDMODES):
            _LOGGER.error("_map_wind_mode_from_rest: invalid windmode index %s", index)
            return None
        return WINDMODE_MAP.get(WINDMODES[index])

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API"""
        _LOGGER.debug("update_state: update_state")
        super().update_state(state)
        
        self._temperature_offset = self.get_state_update_value(state, TEMPOFFSET_KEY)
        self._humidity = self.get_state_update_value(state, HUMIDITY_KEY)
        self._target_humidity = self.get_state_update_value(state, HUMIDITY_TARGET_KEY)
        raw_humidify = self.get_state_update_value(state, HUMIDIFY_MODE_KEY)
        self._humidify = (raw_humidify == 2) if raw_humidify is not None else None
        self._oscillating = self.get_state_update_value(state, HORIZONTAL_OSCILLATION_KEY)
        self._childlockon = self.get_state_update_value(state, CHILDLOCKON_KEY)
        self._wind_mode = self._map_wind_mode_from_rest(
            self.get_state_update_value(state, WIND_MODE_KEY)
        )
        self._work_time = self.get_state_update_value(state, WORKTIME_KEY)
        self._water_level = self.get_state_update_value_mapped(state, WATER_LEVEL_STATUS_KEY, WATER_LEVEL_STATUS_MAP)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("handle_server_update: handle_server_update")
        super().handle_server_update(message)
        
        val_temperature_offset = self.get_server_update_key_value(message, TEMPOFFSET_KEY)
        if isinstance(val_temperature_offset, int):
            self._temperature_offset = val_temperature_offset

        val_oscon = self.get_server_update_key_value(message, HORIZONTAL_OSCILLATION_KEY)
        if isinstance(val_oscon, bool):
            self._oscillating = val_oscon

        val_humidity = self.get_server_update_key_value(message, HUMIDITY_KEY)
        if isinstance(val_humidity, int):
            self._humidity = val_humidity

        val_humidify = self.get_server_update_key_value(message, HUMIDIFY_MODE_KEY)
        if isinstance(val_humidify, int):
            self._humidify = (val_humidify == 2)

        val_target_humidity = self.get_server_update_key_value(message, HUMIDITY_TARGET_KEY)
        if isinstance(val_target_humidity, int):
            self._target_humidity = val_target_humidity

        val_childlockon = self.get_server_update_key_value(message, CHILDLOCKON_KEY)
        if isinstance(val_childlockon, bool):
            self._childlockon = val_childlockon

        val_wind_mode = self.get_server_update_key_value(message, WIND_MODE_KEY)
        if isinstance(val_wind_mode, int):
            # WebSocket sends 1-4 directly — store as int to stay consistent with
            # the int stored by update_state via _map_wind_mode_from_rest().
            self._wind_mode = val_wind_mode

        val_work_time = self.get_server_update_key_value(message, WORKTIME_KEY)
        if isinstance(val_work_time, int):
            self._work_time = val_work_time
            
        val_water_level = self.get_server_update_key_value(message, WATER_LEVEL_STATUS_KEY)
        if isinstance(val_water_level, int):
            self._water_level = WATER_LEVEL_STATUS_MAP.get(val_water_level, val_water_level)

