"""Dreo API for controlling Humidifiers."""

# Trigger CI checks
import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    MODE_KEY,
    MUTEON_KEY,
    POWERON_KEY,
    HUMIDITY_KEY,
    TARGET_AUTO_HUMIDITY_KEY,
    TARGET_SLEEP_HUMIDITY_KEY,
    FOGLEVEL_KEY,
    FOG_LEVEL_KEY,
    LEDKEPTON_KEY,
    LEDLEVEL_KEY,
    LED_LEVEL_KEY,
    RGB_LEVEL,
    RGB_TH,
    SCHEDULE_ENABLE,
)

from .helpers import Helpers


from .pydreobasedevice import PyDreoBaseDevice
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(__name__)

WATER_LEVEL_STATUS_KEY = "wrong"
WORKTIME_KEY = "worktime"
FOGLEVEL_INTERNAL_KEY = "foglevel"

# Status for water level indicator
WATER_LEVEL_OK = "Ok"
WATER_LEVEL_EMPTY = "Empty"

LIGHT_ON = "Enable"
LIGHT_OFF = "Disabled"

WATER_LEVEL_STATUS_MAP = {0: WATER_LEVEL_OK, 1: WATER_LEVEL_EMPTY, WATER_LEVEL_OK: 0, WATER_LEVEL_EMPTY: 1}

RGB_LEVEL_PRESETS = (0, 1, 31, 61)

RGB_MAP = {}

LEDLEVEL_MAP = {0: LIGHT_OFF, 2: LIGHT_ON, LIGHT_OFF: 0, LIGHT_ON: 2}

# Status for mode indicator
MODE_NORMAL = "normal"
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
        if self._modes is None:
            self._modes = self.parse_modes(details)

        self._target_humidity_min = 30
        self._target_humidity_max = 90
        controls_conf = details.get("controlsConf", None)
        if controls_conf:
            hum_range = controls_conf.get("humRange", None)
            if hum_range:
                self._target_humidity_min = hum_range.get("controlMin", 30)
                self._target_humidity_max = hum_range.get("controlMax", 90)

        self._mode = None
        self._mute_on = None
        self._humidity = None
        self._target_humidity = None
        self._sleep_target_humidity = None
        self._ledkepton = None
        self._wrong = None
        self._worktime = None
        self._foglevel = None
        self._rgblevel = None
        self._last_rgblevel = 1
        self._rgbth = None
        self._scheon = None
        self._fog_level = None
        self._ledlevel = None

    def parse_modes(self, details: Dict[str, list]) -> tuple[str, int]:
        """Parse the preset modes from the details."""
        modes = []
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            schedule = controls_conf.get("schedule", None)
            if schedule is not None:
                modes_node = schedule.get("modes", None)
                if modes_node is not None:
                    for mode_item in modes_node:
                        text = self.get_mode_string(mode_item.get("title", None))
                        value = mode_item.get("value", None)
                        modes.append((text, value))

        modes.sort(key=lambda tup: tup[1])  # sorts in place
        if len(modes) == 0:
            _LOGGER.debug("parse_modes: No preset modes detected")
            modes = None
        _LOGGER.debug("parse_modes: Detected preset modes - %s", modes)
        return modes

    @property
    def is_on(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._is_on

    @is_on.setter
    def is_on(self, value: bool):
        """Set if the fan is on or off"""
        _LOGGER.debug("is_on: is_on.setter - %s", value)
        self._send_command(POWERON_KEY, value)

    @property
    def modes(self) -> list[str]:
        """Get the list of modes"""
        if self._modes is None:
            return None
        return Helpers.get_name_list(self._modes)

    @property
    def target_humidity_range(self) -> tuple[int, int]:
        """Return the (min, max) settable humidity range for this device."""
        return (self._target_humidity_min, self._target_humidity_max)

    @property
    def humidity(self):
        """Get the humidity"""
        return self._humidity

    @property
    def target_humidity(self):
        """Get the target_humidity. In sleep mode returns sleep target if available."""
        if self._mode == 2 and self._sleep_target_humidity is not None:
            return self._sleep_target_humidity
        return self._target_humidity

    @target_humidity.setter
    def target_humidity(self, value: int) -> None:
        """Set the target humidity. Routes to sleep key when in sleep mode."""
        _LOGGER.debug("target_humidity: target_humidity.setter(%s) %s --> %s", self, self._target_humidity, value)
        if value < 30 or value > 90:
            raise ValueError(f"Target humidity {value} is out of range (30-90)")
        if self._mode == 2:
            if self._sleep_target_humidity == value:
                _LOGGER.debug("target_humidity: sleep target already %s, skipping command", value)
                return
            self._sleep_target_humidity = value
            self._send_command(TARGET_SLEEP_HUMIDITY_KEY, value)
            return
        if self._target_humidity == value:
            _LOGGER.debug("target_humidity: target_humidity - value already %s, skipping command", value)
            return
        self._target_humidity = value
        self._send_command(TARGET_AUTO_HUMIDITY_KEY, value)

    @property
    def sleep_target_humidity(self):
        """Get the sleep target humidity."""
        return self._sleep_target_humidity

    @sleep_target_humidity.setter
    def sleep_target_humidity(self, value: int) -> None:
        """Set the sleep target humidity."""
        _LOGGER.debug(
            "sleep_target_humidity: sleep_target_humidity.setter(%s) %s --> %s",
            self,
            self._sleep_target_humidity,
            value,
        )
        if value < 30 or value > 90:
            raise ValueError(f"Sleep target humidity {value} is out of range (30-90)")
        if self._sleep_target_humidity == value:
            _LOGGER.debug(
                "sleep_target_humidity: sleep_target_humidity - value already %s, skipping command",
                value,
            )
            return
        self._sleep_target_humidity = value
        self._send_command(TARGET_SLEEP_HUMIDITY_KEY, value)

    @property
    def fog_level(self):
        """Get the manual fog level (mist intensity)."""
        return self._fog_level

    @fog_level.setter
    def fog_level(self, value: int) -> None:
        """Set the manual fog level (mist intensity)."""
        _LOGGER.debug(
            "fog_level: fog_level.setter(%s) %s --> %s",
            self,
            self._fog_level,
            value,
        )
        if value < 0 or value > 6:
            raise ValueError(f"Fog level {value} is out of range (0-6)")
        if self._fog_level == value:
            _LOGGER.debug(
                "fog_level: fog_level - value already %s, skipping command",
                value,
            )
            return
        self._fog_level = value
        self._send_command(FOG_LEVEL_KEY, value)

    @property
    def panel_sound(self) -> bool:
        """Is the panel sound on"""
        if self._mute_on is not None:
            return not self._mute_on
        return None

    @panel_sound.setter
    def panel_sound(self, value: bool) -> None:
        """Set if the panel sound"""
        _LOGGER.debug("panel_sound: panel_sound.setter(%s) --> %s", self.name, value)
        if self._mute_on == (not value):
            _LOGGER.debug("panel_sound: panel_sound - value already %s, skipping command", value)
            return
        self._send_command(MUTEON_KEY, not value)

    @property
    def mode(self):
        """Return the current mode."""
        # Handle case where modes haven't been initialized
        if self._modes is None:
            _LOGGER.debug("mode: _modes is None, returning None")
            return None

        str_value: str = Helpers.name_from_value(self._modes, self._mode)
        if str_value is None:
            return None
        return str_value

    @property
    def wrong(self):
        """Return the water level status"""
        return self._wrong

    @property
    def water_level(self):
        """Return the water level status"""
        return self._wrong

    @property
    def worktime(self):
        """Return the working time (used since cleaning)"""
        return self._worktime

    @property
    def display_light(self) -> bool | None:
        """Return display (LED) on/off state via ledlevel."""
        if self._ledlevel is None:
            return None
        return self._ledlevel == LIGHT_ON

    @display_light.setter
    def display_light(self, value: bool) -> None:
        """Set display (LED) on/off via ledlevel (0=off, 2=on)."""
        _LOGGER.debug("display_light: display_light.setter(%s) --> %s", self.name, value)
        desired = LIGHT_ON if value else LIGHT_OFF
        if self._ledlevel == desired:
            _LOGGER.debug("display_light: value already %s, skipping command", value)
            return
        self._ledlevel = desired  # optimistic update so HA reflects state immediately
        self._send_command(LEDLEVEL_KEY, LEDLEVEL_MAP[desired])

    @property
    def foglevel(self) -> int | None:
        """Raw fog level reported by the API (typically 0-6)."""
        return self._foglevel

    @property
    def mist_level(self) -> int | None:
        """Mist speed level (1-3).

        Many Dreo humidifiers report `foglevel` as a 0-6 scale where
        2,4,6 correspond to Low/Med/High. We expose a clean 1-3 level.
        """
        if self._foglevel is None:
            return None
        try:
            lvl = int(self._foglevel)
        except (TypeError, ValueError):
            return None
        if lvl <= 0:
            return None
        return max(1, min(3, (lvl + 1) // 2))

    @mist_level.setter
    def mist_level(self, value: int) -> None:
        """Set mist speed level (1-3)."""
        try:
            level = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"mist_level must be an integer 1-3, got {value!r}")
        if level < 1 or level > 3:
            raise ValueError(f"mist_level must be between 1 and 3, got {level}")
        raw = level * 2  # 2,4,6
        if self._foglevel == raw:
            _LOGGER.debug("mist_level: value already %s, skipping command", level)
            return
        self._foglevel = raw  # optimistic update
        self._send_command(FOGLEVEL_KEY, raw)

    @property
    def rgblevel(self) -> int | None:
        """Return raw ambient light level reported by the API."""
        return self._rgblevel

    @property
    def ambient_light(self) -> bool | None:
        """Return ambient light on/off state based on raw rgblevel."""
        if self._rgblevel is None:
            return None
        return int(self._rgblevel) > 0

    @ambient_light.setter
    def ambient_light(self, value: bool) -> None:
        """Set ambient light on/off using the raw rgblevel values."""
        _LOGGER.debug("ambient_light: ambient_light.setter(%s) --> %s", self.name, value)
        desired = self._last_rgblevel if value else 0
        if self._rgblevel == desired:
            _LOGGER.debug("ambient_light: value already %s, skipping command", value)
            return
        self._rgblevel = desired  # optimistic update so HA reflects state immediately
        self._send_command(RGB_LEVEL, desired)

    @property
    def ambient_light_level(self) -> int | None:
        """Return the raw ambient light slider value."""
        return self._rgblevel

    @ambient_light_level.setter
    def ambient_light_level(self, value: int) -> None:
        """Set the ambient light slider value."""
        try:
            requested = int(value)
        except (TypeError, ValueError) as ex:
            raise ValueError(f"ambient_light_level must be an integer, got {value!r}") from ex

        desired = min(RGB_LEVEL_PRESETS, key=lambda preset: abs(preset - requested))
        if self._rgblevel == desired:
            _LOGGER.debug("ambient_light_level: value already %s, skipping command", desired)
            return
        if desired > 0:
            self._last_rgblevel = desired
        self._rgblevel = desired
        self._send_command(RGB_LEVEL, desired)

    @property
    def rgbth(self):
        """Return raw rgbth string (e.g. '30,65') for ambient light thresholds."""
        return self._rgbth

    @property
    def rgbth_low(self) -> int | None:
        """Return low humidity threshold for ambient light."""
        if not self._rgbth or not isinstance(self._rgbth, str) or "," not in self._rgbth:
            return None
        try:
            low_str, _ = self._rgbth.split(",", 1)
            return int(low_str.strip())
        except (ValueError, AttributeError):
            return None

    @rgbth_low.setter
    def rgbth_low(self, value: int) -> None:
        """Set low humidity threshold for ambient light."""
        high = self.rgbth_high if self.rgbth_high is not None else 0
        payload = f"{int(value)},{high}"
        if self._rgbth == payload:
            return
        self._rgbth = payload  # optimistic update
        self._send_command(RGB_TH, payload)

    @property
    def rgbth_high(self) -> int | None:
        """Return high humidity threshold for ambient light."""
        if not self._rgbth or not isinstance(self._rgbth, str) or "," not in self._rgbth:
            return None
        try:
            _, high_str = self._rgbth.split(",", 1)
            return int(high_str.strip())
        except (ValueError, AttributeError):
            return None

    @rgbth_high.setter
    def rgbth_high(self, value: int) -> None:
        """Set high humidity threshold for ambient light."""
        low = self.rgbth_low if self.rgbth_low is not None else 0
        payload = f"{low},{int(value)}"
        if self._rgbth == payload:
            return
        self._rgbth = payload  # optimistic update
        self._send_command(RGB_TH, payload)

    @property
    def rgb_indicator(self) -> bool | None:
        """Return True if the water level RGB indicator is enabled."""
        if self._rgblevel is None:
            return None
        return self._rgblevel == LIGHT_ON

    @rgb_indicator.setter
    def rgb_indicator(self, value: bool) -> None:
        """Set the water level RGB indicator on/off."""
        _LOGGER.debug("rgb_indicator: rgb_indicator.setter(%s) --> %s", self.name, value)
        new_level = LIGHT_ON if value else LIGHT_OFF
        if self._rgblevel == new_level:
            _LOGGER.debug("rgb_indicator: rgb_indicator - value already %s, skipping command", value)
            return
        self._rgblevel = new_level
        self._send_command(RGB_LEVEL, RGB_MAP[new_level])

    @property
    def scheon(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._scheon

    @scheon.setter
    def scheon(self, value: bool):
        """Set if the fan is on or off"""
        _LOGGER.debug("scheon: scheon.setter - %s", value)
        if self._scheon == value:
            _LOGGER.debug("scheon: scheon - value already %s, skipping command", value)
            return
        self._send_command(SCHEDULE_ENABLE, value)

    @mode.setter
    def mode(self, value: str) -> None:
        if self._modes is None:
            raise NotImplementedError("Attempting to set mode on a device that doesn't support modes.")
        numeric_value = Helpers.value_from_name(self._modes, value)
        if numeric_value is not None:
            if self._mode == numeric_value:
                _LOGGER.debug("mode: mode - value already %s, skipping command", value)
                return
            self._send_command(MODE_KEY, numeric_value)
        else:
            raise ValueError(f"Preset mode {value} is not in the acceptable list: {self._modes}")

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        super().update_state(state)  # handles _is_on

        _LOGGER.debug("update_state: %s - %s", self.name, state)
        self._mode = self.get_state_update_value(state, MODE_KEY)
        self._mute_on = self.get_state_update_value(state, MUTEON_KEY)
        self._humidity = self.get_state_update_value(state, HUMIDITY_KEY)
        self._target_humidity = self.get_state_update_value(state, TARGET_AUTO_HUMIDITY_KEY)
        self._sleep_target_humidity = self.get_state_update_value(state, TARGET_SLEEP_HUMIDITY_KEY)
        self._ledkepton = self.get_state_update_value(state, LEDKEPTON_KEY)
        self._ledlevel = self.get_state_update_value_mapped(state, LEDLEVEL_KEY, LEDLEVEL_MAP)
        self._wrong = self.get_state_update_value_mapped(state, WATER_LEVEL_STATUS_KEY, WATER_LEVEL_STATUS_MAP)
        self._worktime = self.get_state_update_value(state, WORKTIME_KEY)
        self._foglevel = self.get_state_update_value(state, FOGLEVEL_INTERNAL_KEY)
        self._rgblevel = self.get_state_update_value(state, RGB_LEVEL)
        self._rgbth = self.get_state_update_value(state, RGB_TH)
        self._scheon = self.get_state_update_value(state, SCHEDULE_ENABLE)
        self._fog_level = self.get_state_update_value(state, FOG_LEVEL_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("handle_server_update: handle_server_update(%s): %s", self.name, message)

        val_poweron = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_poweron, bool):
            self._is_on = val_poweron
            _LOGGER.debug("handle_server_update: handle_server_update - poweron is %s", self._is_on)

        val_mode = self.get_server_update_key_value(message, MODE_KEY)
        if isinstance(val_mode, int):
            self._mode = val_mode

        val_worktime = self.get_server_update_key_value(message, WORKTIME_KEY)
        if isinstance(val_worktime, int):
            self._worktime = val_worktime

        val_water_level = self.get_server_update_key_value(message, WATER_LEVEL_STATUS_KEY)
        if isinstance(val_water_level, int):
            val_water_level = WATER_LEVEL_STATUS_MAP.get(val_water_level, val_water_level)
            self._wrong = val_water_level

        val_foglevel = self.get_server_update_key_value(message, FOGLEVEL_INTERNAL_KEY)
        if isinstance(val_foglevel, int):
            self._foglevel = val_foglevel

        val_rgblevel = self.get_server_update_key_value(message, RGB_LEVEL)
        if isinstance(val_rgblevel, int):
            if val_rgblevel > 0:
                self._last_rgblevel = val_rgblevel
            val_rgblevel = RGB_MAP.get(val_rgblevel, val_rgblevel)
            self._rgblevel = val_rgblevel

        val_rgbth = self.get_server_update_key_value(message, RGB_TH)
        if isinstance(val_rgbth, str):
            self._rgbth = val_rgbth

        val_ledlevel = self.get_server_update_key_value(message, LED_LEVEL_KEY)
        if isinstance(val_ledlevel, int):
            self._ledlevel = val_ledlevel

        val_ledlevel = self.get_server_update_key_value(message, LED_LEVEL_KEY)
        if isinstance(val_ledlevel, int):
            self._ledlevel = val_ledlevel

        val_scheon = self.get_server_update_key_value(message, SCHEDULE_ENABLE)
        if isinstance(val_scheon, bool):
            self._scheon = val_scheon

        val_mute_on = self.get_server_update_key_value(message, MUTEON_KEY)
        if isinstance(val_mute_on, bool):
            self._mute_on = val_mute_on

        val_humidity = self.get_server_update_key_value(message, HUMIDITY_KEY)
        if isinstance(val_humidity, int):
            self._humidity = val_humidity
            _LOGGER.debug("handle_server_update: handle_server_update - humidity is %s", self._humidity)

        val_target_humidity = self.get_server_update_key_value(message, TARGET_AUTO_HUMIDITY_KEY)
        if isinstance(val_target_humidity, int):
            self._target_humidity = val_target_humidity
            _LOGGER.debug("handle_server_update: handle_server_update - target_humidity is %s", self._target_humidity)

        val_sleep_target_humidity = self.get_server_update_key_value(message, TARGET_SLEEP_HUMIDITY_KEY)
        if isinstance(val_sleep_target_humidity, int):
            self._sleep_target_humidity = val_sleep_target_humidity
            _LOGGER.debug("handle_server_update: handle_server_update - sleep_target_humidity is %s", self._sleep_target_humidity)

        val_ledkepton = self.get_server_update_key_value(message, LEDKEPTON_KEY)
        if isinstance(val_ledkepton, bool):
            self._ledkepton = val_ledkepton

        val_ledlevel = self.get_server_update_key_value(message, LEDLEVEL_KEY)
        if isinstance(val_ledlevel, int):
            self._ledlevel = LEDLEVEL_MAP.get(val_ledlevel, LIGHT_OFF)

        val_fog_level = self.get_server_update_key_value(message, FOG_LEVEL_KEY)
        if isinstance(val_fog_level, int):
            self._fog_level = val_fog_level
            _LOGGER.debug("handle_server_update: handle_server_update - fog_level is %s", self._fog_level)
