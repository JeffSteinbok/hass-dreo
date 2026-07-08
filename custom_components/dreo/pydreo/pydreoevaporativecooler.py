"""Dreo API for controling evaporative coolers."""

import logging
from typing import TYPE_CHECKING, Dict, Optional
from .pydreofanbase import PyDreoFanBase

from .constant import (
    CHILDLOCKON_KEY,
    FOG_LEVEL_KEY,
    HORIZONTAL_OSCILLATION_KEY,
    HORIZONTAL_OSCILLATION_ANGLE_KEY,
    HORIZONTAL_ANGLE_ADJ_KEY,
    HORIZONTAL_ANGLE_RANGE,
    HUMIDITY_KEY,
    LIGHTON_KEY,
    MODE_KEY,
    MUTEON_KEY,
    RGB_COLOR,
    RGB_MODE,
    TEMPOFFSET_KEY,
)
from .helpers import Helpers
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(__name__)

WIND_MODE_KEY = "windmode"
HUMIDIFY_MODE_KEY = "rhmode"
HUMIDIFY_SUSPEND_KEY = "rhsuspend"
HUMIDITY_TARGET_KEY = "rhtarget"
WORKTIME_KEY = "worktime"
WATER_LEVEL_STATUS_KEY = "wrong"
WATER_LEVEL_KEY = "water_level"
RGB_ON_KEY = "rgbon"

# Status for water level indicator
WATER_LEVEL_OK = "Ok"
WATER_LEVEL_EMPTY = "Empty"

# States (enabled, disabled) for humidifier
HUMIDIFY_MODE_MAP = {
    0: False,
    2: True,
    False: 0,  # noqa: F601
    True: 2,
}

WATER_LEVEL_STATUS_MAP = {0: WATER_LEVEL_OK, 1: WATER_LEVEL_EMPTY, WATER_LEVEL_OK: 0, WATER_LEVEL_EMPTY: 1}

WINDMODES = [
    "normal",
    "natural",
    "sleep",
    "auto",
]

# Windmodes for evaporative cooler (HEC002S legacy path, 0-indexed REST → 1-based internal)
WINDMODE_MAP = {"normal": 1, "auto": 2, "sleep": 3, "natural": 4, 1: "normal", 2: "auto", 3: "sleep", 4: "natural"}

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
        # Use model-defined preset_modes (set by super().__init__) when available;
        # fall back to the legacy WINDMODES list for devices without explicit configuration.
        # parse_preset_modes() returns False for this class, so guard with truthiness.
        if not self._preset_modes:
            self._preset_modes = WINDMODES
        self._work_time = None
        self._display_auto_off = None
        self._water_level = None
        self._fog_level = None
        self._rgb_light_on = None
        self._rgbmode = None
        self._rgbcolor = None
        self._light_on = None
        self._suspend = None
        self._horizontal_angle = None
        self._horizontal_angle_range = None

    def parse_preset_modes(self, details: Dict[str, list]) -> tuple[str, int]:
        # Not needed atm
        return False

    @property
    def temperature(self):
        """Get the temperature"""
        temp = self._temperature
        if temp is not None and self.temperature_offset is not None:
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
    def fog_level(self) -> int | None:
        """Return the misting level."""
        return self._fog_level

    @property
    def fog_level_range(self) -> tuple[int, int]:
        """Return the supported misting level range."""
        range_from_definition = self._device_definition.device_ranges.get("fog_level_range") if self._device_definition.device_ranges else None
        if range_from_definition is not None:
            return range_from_definition
        return (1, 3)

    @fog_level.setter
    def fog_level(self, value: int) -> None:
        """Set the misting level."""
        level = int(value)
        min_level, max_level = self.fog_level_range
        if level < min_level or level > max_level:
            raise ValueError(f"Fog level {level} is out of range ({min_level}-{max_level})")
        if self._fog_level == level:
            _LOGGER.debug("fog_level: fog_level - value already %s, skipping command", level)
            return
        self._fog_level = level
        self._send_command(FOG_LEVEL_KEY, level)

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
    def display_light(self) -> bool | None:
        """Return display light state."""
        return self._light_on

    @display_light.setter
    def display_light(self, value: bool) -> None:
        """Set display light state."""
        if self._light_on == value:
            _LOGGER.debug("display_light: display_light - value already %s, skipping command", value)
            return
        self._light_on = value
        self._send_command(LIGHTON_KEY, value)

    @property
    def preset_mode(self):
        """Return the current preset mode as a string."""
        if self._wind_mode is None:
            return None
        # Model-defined preset_modes are stored as (name, value) tuples.
        if self._preset_modes and isinstance(self._preset_modes[0], tuple):
            return Helpers.name_from_value(self._preset_modes, self._wind_mode)
        # Legacy WINDMODES path (e.g. HEC002S): use WINDMODE_MAP lookup.
        return WINDMODE_MAP.get(self._wind_mode, self._wind_mode)

    @preset_mode.setter
    def preset_mode(self, value: str) -> None:
        """Set preset mode"""
        if self._preset_modes and isinstance(self._preset_modes[0], tuple):
            # Model-defined path: send using global MODE_KEY ("mode").
            numeric_value = Helpers.value_from_name(self._preset_modes, value)
            if numeric_value is None:
                raise ValueError(f"Preset mode {value} is not in the acceptable list: {self.preset_modes}")
            if self._wind_mode == numeric_value:
                _LOGGER.debug("preset_mode: preset_mode - value already %s, skipping command", value)
                return
            self._send_command(MODE_KEY, numeric_value)
        else:
            # Legacy WINDMODES path (e.g. HEC002S): send using local WIND_MODE_KEY ("windmode").
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
        if not self._preset_modes:
            return None
        if isinstance(self._preset_modes[0], tuple):
            return Helpers.get_name_list(self._preset_modes)
        return self._preset_modes

    @property
    def rgblevel(self) -> int | None:
        """Return a compatibility RGB light level for the ambient light entity."""
        if self._rgb_light_on is None:
            return None
        return 1 if self._rgb_light_on else 0

    @rgblevel.setter
    def rgblevel(self, value: int) -> None:
        """Map ambient light on/off requests onto the device's rgbon field."""
        desired_on = int(value) > 0
        if self._rgb_light_on == desired_on:
            _LOGGER.debug("rgblevel: rgblevel - value already %s, skipping command", desired_on)
            return
        self._rgb_light_on = desired_on
        self._send_command(RGB_ON_KEY, desired_on)

    @property
    def rgbmode(self) -> int | None:
        """Return the ambient light mode."""
        return self._rgbmode

    @rgbmode.setter
    def rgbmode(self, value: int) -> None:
        """Set the ambient light mode."""
        if self._rgbmode == value:
            _LOGGER.debug("rgbmode: rgbmode - value already %s, skipping command", value)
            return
        self._rgbmode = value
        self._send_command(RGB_MODE, value)

    @property
    def rgbcolor(self) -> int | None:
        """Return the packed ambient light RGB color."""
        return self._rgbcolor

    @rgbcolor.setter
    def rgbcolor(self, value: int) -> None:
        """Set the packed ambient light RGB color."""
        if self._rgbcolor == value:
            _LOGGER.debug("rgbcolor: rgbcolor - value already %s, skipping command", value)
            return
        self._rgbcolor = value
        self._send_command(RGB_COLOR, value)

    @property
    def work_time(self) -> int:
        """Return the working time (used since cleaning)"""
        return self._work_time

    @property
    def water_level(self) -> int:
        """Return the water level status"""
        return self._water_level

    @property
    def suspend(self) -> bool | None:
        """Return True if humidifier is suspended (target humidity reached)."""
        return self._suspend

    @property
    def horizontal_angle(self) -> int | None:
        """Return the configured horizontal angle."""
        return self._horizontal_angle

    @horizontal_angle.setter
    def horizontal_angle(self, value: int) -> None:
        """Set the configured horizontal angle."""
        angle = int(value)
        if self._horizontal_angle == angle:
            _LOGGER.debug("horizontal_angle: horizontal_angle - value already %s, skipping command", angle)
            return
        self._horizontal_angle = angle
        self._send_command(HORIZONTAL_ANGLE_ADJ_KEY, angle)

    @property
    def horizontal_angle_range(self) -> tuple[int, int] | None:
        """Return the supported horizontal angle range."""
        range_from_definition = self._device_definition.device_ranges.get(HORIZONTAL_ANGLE_RANGE) if self._device_definition.device_ranges else None
        if range_from_definition is not None:
            return range_from_definition
        return self._horizontal_angle_range

    @property
    def horizontal_osc_angle_left(self) -> int | None:
        """Return the configured left horizontal oscillation angle (derived from horizontal_angle_range)."""
        if self._horizontal_angle_range is not None:
            return self._horizontal_angle_range[0]
        return None

    @horizontal_osc_angle_left.setter
    def horizontal_osc_angle_left(self, value: int) -> None:
        """Set the left horizontal oscillation angle."""
        _LOGGER.debug("horizontal_osc_angle_left: setting to %s", value)
        angle = int(value)
        current_left = self.horizontal_osc_angle_left
        current_right = self.horizontal_osc_angle_right
        if current_left == angle:
            _LOGGER.debug("horizontal_osc_angle_left: value already %s, skipping command", angle)
            return
        # Validate that left < right
        if current_right is not None and angle >= current_right:
            raise ValueError(f"Left angle {angle} must be less than right angle {current_right}")
        # Send as "left,right" via hoscangle key
        if current_right is not None:
            self._send_command(HORIZONTAL_OSCILLATION_ANGLE_KEY, f"{angle},{current_right}")

    @property
    def horizontal_osc_angle_left_range(self) -> tuple[int, int] | None:
        """Return the supported left horizontal oscillation angle range."""
        range_from_definition = self._device_definition.device_ranges.get("horizontal_osc_angle_left_range") if self._device_definition.device_ranges else None
        if range_from_definition is not None:
            return range_from_definition
        # Fall back to horizontal angle range if available
        if self._horizontal_angle_range is not None:
            return (self._horizontal_angle_range[0], self._horizontal_angle_range[1])
        return None

    @property
    def horizontal_osc_angle_right(self) -> int | None:
        """Return the configured right horizontal oscillation angle (derived from horizontal_angle_range)."""
        if self._horizontal_angle_range is not None:
            return self._horizontal_angle_range[1]
        return None

    @horizontal_osc_angle_right.setter
    def horizontal_osc_angle_right(self, value: int) -> None:
        """Set the right horizontal oscillation angle."""
        _LOGGER.debug("horizontal_osc_angle_right: setting to %s", value)
        angle = int(value)
        current_left = self.horizontal_osc_angle_left
        current_right = self.horizontal_osc_angle_right
        if current_right == angle:
            _LOGGER.debug("horizontal_osc_angle_right: value already %s, skipping command", angle)
            return
        # Validate that left < right
        if current_left is not None and angle <= current_left:
            raise ValueError(f"Right angle {angle} must be greater than left angle {current_left}")
        # Send as "left,right" via hoscangle key
        if current_left is not None:
            self._send_command(HORIZONTAL_OSCILLATION_ANGLE_KEY, f"{current_left},{angle}")

    @property
    def horizontal_osc_angle_right_range(self) -> tuple[int, int] | None:
        """Return the supported right horizontal oscillation angle range."""
        range_from_definition = self._device_definition.device_ranges.get("horizontal_osc_angle_right_range") if self._device_definition.device_ranges else None
        if range_from_definition is not None:
            return range_from_definition
        # Fall back to horizontal angle range if available
        if self._horizontal_angle_range is not None:
            return (self._horizontal_angle_range[0], self._horizontal_angle_range[1])
        return None

    @staticmethod
    def _parse_angle_range(value: str) -> tuple[int, int] | None:
        """Parse a Dreo angle range string like '-15,15'."""
        if not isinstance(value, str) or "," not in value:
            return None
        try:
            left, right = value.split(",", 1)
            return (int(left), int(right))
        except ValueError:
            _LOGGER.warning("_parse_angle_range: invalid angle range %s", value)
            return None

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
        self._mute_on = self.get_state_update_value(state, MUTEON_KEY)
        self._childlockon = self.get_state_update_value(state, CHILDLOCKON_KEY)
        # Only apply the legacy 0-indexed windmode mapping when the "windmode" key is
        # actually present.  Devices that use the global "mode" key (e.g. DR-HEC006S)
        # have _wind_mode already set correctly by super().update_state(), so we must
        # not overwrite it with the None that _map_wind_mode_from_rest() would return.
        wind_mode_raw = self.get_state_update_value(state, WIND_MODE_KEY)
        if wind_mode_raw is not None:
            self._wind_mode = self._map_wind_mode_from_rest(wind_mode_raw)
        self._work_time = self.get_state_update_value(state, WORKTIME_KEY)
        self._water_level = self.get_state_update_value_mapped(state, WATER_LEVEL_STATUS_KEY, WATER_LEVEL_STATUS_MAP)
        self._fog_level = self.get_state_update_value(state, FOG_LEVEL_KEY)
        self._rgb_light_on = self.get_state_update_value(state, RGB_ON_KEY)
        self._rgbmode = self.get_state_update_value(state, RGB_MODE)
        self._rgbcolor = self.get_state_update_value(state, RGB_COLOR)
        self._light_on = self.get_state_update_value(state, LIGHTON_KEY)
        self._suspend = self.get_state_update_value(state, HUMIDIFY_SUSPEND_KEY)
        self._horizontal_angle = self.get_state_update_value(state, HORIZONTAL_ANGLE_ADJ_KEY)
        self._horizontal_angle_range = self._parse_angle_range(self.get_state_update_value(state, HORIZONTAL_OSCILLATION_ANGLE_KEY))

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

        val_muteon = self.get_server_update_key_value(message, MUTEON_KEY)
        if isinstance(val_muteon, bool):
            self._mute_on = val_muteon

        val_humidify = self.get_server_update_key_value(message, HUMIDIFY_MODE_KEY)
        if isinstance(val_humidify, int):
            self._humidify = val_humidify == 2

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

        val_fog_level = self.get_server_update_key_value(message, FOG_LEVEL_KEY)
        if isinstance(val_fog_level, int):
            self._fog_level = val_fog_level

        val_rgb_light_on = self.get_server_update_key_value(message, RGB_ON_KEY)
        if isinstance(val_rgb_light_on, bool):
            self._rgb_light_on = val_rgb_light_on

        val_rgbmode = self.get_server_update_key_value(message, RGB_MODE)
        if isinstance(val_rgbmode, int):
            self._rgbmode = val_rgbmode

        val_rgbcolor = self.get_server_update_key_value(message, RGB_COLOR)
        if isinstance(val_rgbcolor, int):
            self._rgbcolor = val_rgbcolor

        val_light_on = self.get_server_update_key_value(message, LIGHTON_KEY)
        if isinstance(val_light_on, bool):
            self._light_on = val_light_on

        val_suspend = self.get_server_update_key_value(message, HUMIDIFY_SUSPEND_KEY)
        if isinstance(val_suspend, bool):
            self._suspend = val_suspend

        val_horizontal_angle = self.get_server_update_key_value(message, HORIZONTAL_ANGLE_ADJ_KEY)
        if isinstance(val_horizontal_angle, int):
            self._horizontal_angle = val_horizontal_angle

        val_horizontal_angle_range = self.get_server_update_key_value(message, HORIZONTAL_OSCILLATION_ANGLE_KEY)
        if isinstance(val_horizontal_angle_range, str):
            self._horizontal_angle_range = self._parse_angle_range(val_horizontal_angle_range)
