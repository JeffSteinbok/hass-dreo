"""Dreo API for controling fans."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    HORIZONTAL_OSCILLATION_KEY,
    HORIZONTAL_OSCILLATION_ANGLE_KEY,
    VERTICAL_OSCILLATION_KEY,
    VERTICAL_OSCILLATION_ANGLE_KEY,
    CRUISECONF_KEY,
    MIN_OSC_ANGLE_DIFFERENCE,
    OSCMODE_KEY,
    FIXEDCONF_KEY,
    OscillationMode,
    HORIZONTAL_ANGLE_RANGE,
    VERTICAL_ANGLE_RANGE,
    SPEED_RANGE
)

from .pydreofanbase import PyDreoFanBase
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoAirCirculator(PyDreoFanBase):
    """Base class for Dreo Fan API Calls."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        super().__init__(device_definition, details, dreo)

        self._horizontal_angle_range = None
        # Check if the device has a horizontal angle range defined in the device definition
        # If not, parse the horizontal angle range from the details
        if device_definition.device_ranges is not None and HORIZONTAL_ANGLE_RANGE in device_definition.device_ranges:
            self._horizontal_angle_range = device_definition.device_ranges[HORIZONTAL_ANGLE_RANGE]
        if self._horizontal_angle_range is None:
            self._horizontal_angle_range = self.parse_swing_angle_range(details, "hor")

        self._vertical_angle_range = None
        # Check if the device has a vertical angle range defined in the device definition
        # If not, parse the vertical angle range from the details
        if device_definition.device_ranges is not None and VERTICAL_ANGLE_RANGE in device_definition.device_ranges:
            self._vertical_angle_range = device_definition.device_ranges[VERTICAL_ANGLE_RANGE]
        if self._vertical_angle_range is None:
            self._vertical_angle_range = self.parse_swing_angle_range(details, "ver")

        self._osc_mode = None
        self._cruise_conf = None
        self._fixed_conf = None

        self._horizontally_oscillating = None
        self._vertically_oscillating = None

    @staticmethod
    def parse_swing_angle_range(details: Dict[str, list], direction: str) -> tuple[int, int] | None:
        """Parse the swing angle range from the details."""
        controls_conf = details.get("controlsConf", None)
        if controls_conf is None:
            return None

        swing_angle = controls_conf.get("swingAngle", None)
        if swing_angle is None:
            _LOGGER.debug("PyDreoAirCirculator:no swing angle detected")
            return None

        fixed_angle = swing_angle.get("fixedAngle", None)
        if fixed_angle is None:
            _LOGGER.debug("PyDreoAirCirculator:no fixed angle detected")
            return None

        angle = fixed_angle.get(direction + "Angle", None)
        zero_angle = fixed_angle.get(direction + "ZeroAngle", None)
        if angle is None or zero_angle is None:
            return None

        return -zero_angle, angle - zero_angle

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
            _LOGGER.debug("PyDreoAirCirculator:No preset modes detected")
            preset_modes = None
        _LOGGER.debug("PyDreoAirCirculator:Detected preset modes - %s", preset_modes)
        return preset_modes

    @property
    def horizontal_angle_range(self):
        """Get the horizontal swing angle range"""
        return self._horizontal_angle_range

    @property
    def vertical_angle_range(self):
        """Get the vertical swing angle range"""
        return self._vertical_angle_range

    @property
    def oscillating(self) -> bool:
        """Returns `True` if either horizontal or vertical oscillation is on."""
        if self._horizontally_oscillating is not None:
            if self._vertically_oscillating is not None:
                return self._horizontally_oscillating or self._vertically_oscillating
            return self._horizontally_oscillating
        if self._osc_mode is not None:
            return self._osc_mode != OscillationMode.OFF
        return None

    @oscillating.setter
    def oscillating(self, value: bool) -> None:

        """Enable or disable oscillation"""
        _LOGGER.debug("PyDreoAirCirculator:oscillating.setter")

        if self._horizontally_oscillating is not None:
            self.horizontally_oscillating = value
            self.vertically_oscillating = False
        elif self._osc_mode is not None:
            self._osc_mode = OscillationMode.HORIZONTAL if value else OscillationMode.OFF
        else:
            raise NotImplementedError("Attempting to set oscillating on a device that doesn't support.")

    @property
    def horizontally_oscillating(self) -> bool:
        """Returns `True` if horizontal oscillation is on."""
        if self._horizontally_oscillating is not None:
            return self._horizontally_oscillating
        if self._osc_mode is not None:
            return (self._osc_mode & OscillationMode.HORIZONTAL) != OscillationMode.OFF

        # Note we do not consider a fan with JUST horizontal oscillation to have a seperate
        # horizontal oscillation switch.
        return None

    @horizontally_oscillating.setter
    def horizontally_oscillating(self, value: bool) -> None:
        """Enable or disable vertical oscillation"""
        _LOGGER.debug("PyDreoAirCirculator:horizontally_oscillating.setter")
        if self._horizontally_oscillating is not None:
            self._send_command(HORIZONTAL_OSCILLATION_KEY, value)
        elif self._osc_mode is not None:
            osc_computed = None
            if value:
                osc_computed = self._osc_mode | OscillationMode.HORIZONTAL
            else:
                osc_computed = self._osc_mode & ~OscillationMode.HORIZONTAL
            self._send_command(OSCMODE_KEY, osc_computed)
        else:
            raise NotImplementedError("Horizontal oscillation is not supported.")

    @property
    def horizontal_osc_angle_left_range(self):
        """Get the left horizontal oscillation angle range."""
        return self.horizontal_angle_range

    @property
    def horizontal_osc_angle_right_range(self):
        """Get the right horizontal oscillation angle range."""
        return self.horizontal_angle_range

    @property
    def vertically_oscillating(self):
        """Returns `True` if vertical oscillation is on."""
        if self._vertically_oscillating is not None:
            return self._vertically_oscillating
        if self._osc_mode is not None:
            return self._osc_mode & OscillationMode.VERTICAL != OscillationMode.OFF

        return None

    @vertically_oscillating.setter
    def vertically_oscillating(self, value: bool) -> None:
        """Enable or disable vertical oscillation"""
        if self._horizontally_oscillating is not None:
            self._send_command(VERTICAL_OSCILLATION_KEY, value)
        elif self._osc_mode is not None:
            osc_computed = None
            if value:
                osc_computed = self._osc_mode | OscillationMode.VERTICAL
            else:
                osc_computed = self._osc_mode & ~OscillationMode.VERTICAL
            self._send_command(OSCMODE_KEY, osc_computed)
        else:
            raise NotImplementedError("Vertical oscillation is not supported.")

    @property
    def vertical_osc_angle_top_range(self):
        """Get the top vertical oscillation angle range."""
        return self.vertical_angle_range

    @property
    def vertical_osc_angle_bottom_range(self):
        """Get the bottom vertical oscillation angle range."""
        return self.vertical_angle_range

    def set_horizontal_oscillation_angle(self, angle: int) -> None:
        """Set the horizontal oscillation angle."""
        _LOGGER.debug("PyDreoAirCirculatorFan:set_horizontal_oscillation_angle")
        if not self._horizontally_oscillating is None:
            raise NotImplementedError("This device does not support horizontal oscillation")
            
        self._send_command(HORIZONTAL_OSCILLATION_ANGLE_KEY, angle)

    def set_vertical_oscillation_angle(self, angle: int) -> None:
        """Set the vertical oscillation angle."""
        _LOGGER.debug("PyDreoAirCirculatorFan:set_vertical_oscillation_angle")
        if not self._vertically_oscillating is None:
            raise NotImplementedError("This device does not support vertical oscillation")
            

        self._send_command(VERTICAL_OSCILLATION_ANGLE_KEY, angle)

    @property
    def vertical_osc_angle_top(self) -> int:
        """Get the current top vertical oscillation angle."""
        if self._cruise_conf is not None:
            return self._cruise_conf.split(",")[0]

    @vertical_osc_angle_top.setter
    def vertical_osc_angle_top(self, value: int) -> None:
        """Set the top vertical oscillation angle."""
        _LOGGER.debug("PyDreoAirCirculator:vertical_osc_angle_top.setter")
        if self._cruise_conf is not None:
            bottom_angle = int(self._cruise_conf.split(",")[2])
            # 30 deg is the minimum top-bottom and left-right difference for the tested fan (DR-HAF003S)
            if value - bottom_angle < MIN_OSC_ANGLE_DIFFERENCE:
                raise ValueError(f"Top angle must be at least {MIN_OSC_ANGLE_DIFFERENCE} greater than bottom angle")
            cruise_conf_values = self._cruise_conf.split(',')
            # Note that HA seems to send this in as a float, so we need to convert to int just in case
            cruise_conf_values[0] = int(value)
            self._send_command(CRUISECONF_KEY, ','.join(map(str, cruise_conf_values)))

    @property
    def vertical_osc_angle_bottom(self) -> int:
        """Get the current bottom vertical oscillation angle."""
        if self._cruise_conf is not None:
            return self._cruise_conf.split(",")[2]

    @vertical_osc_angle_bottom.setter
    def vertical_osc_angle_bottom(self, value: int) -> None:
        """Set the bottom vertical oscillation angle."""
        _LOGGER.debug("PyDreoAirCirculator:vertical_osc_angle_bottom.setter")
        if self._cruise_conf is not None:
            top_angle = int(self._cruise_conf.split(",")[0])
            # 30 deg is the minimum top-bottom and left-right difference for the tested fan (DR-HAF003S)
            if top_angle - value < MIN_OSC_ANGLE_DIFFERENCE:
                raise ValueError(f"Bottom angle must be at least {MIN_OSC_ANGLE_DIFFERENCE} less than top angle")
            cruise_conf_values = self._cruise_conf.split(',')
            # Note that HA seems to send this in as a float, so we need to convert to int just in case
            cruise_conf_values[2] = int(value)
            self._send_command(CRUISECONF_KEY, ','.join(map(str, cruise_conf_values)))

    @property
    def horizontal_osc_angle_right(self) -> int:
        """Get the current right horizontal oscillation angle."""
        if self._cruise_conf is not None:
            return self._cruise_conf.split(",")[1]

    @horizontal_osc_angle_right.setter
    def horizontal_osc_angle_right(self, value: int) -> None:
        """Set the right horizontal oscillation angle."""
        _LOGGER.debug("PyDreoAirCirculator:horizontal_osc_angle_right.setter")
        if self._cruise_conf is not None:
            left_angle = int(self._cruise_conf.split(",")[3])
            # 30 deg is the minimum top-bottom and left-right difference for the tested fan (DR-HAF003S)
            if value - left_angle < MIN_OSC_ANGLE_DIFFERENCE:
                raise ValueError(f"Right angle must be at least {MIN_OSC_ANGLE_DIFFERENCE} greater than left angle")
            cruise_conf_values = self._cruise_conf.split(',')
            # Note that HA seems to send this in as a float, so we need to convert to int just in case
            cruise_conf_values[1] = int(value)
            self._send_command(CRUISECONF_KEY, ','.join(map(str, cruise_conf_values)))

    @property
    def horizontal_osc_angle_left(self) -> int:
        """Get the current left horizontal oscillation angle."""
        if self._cruise_conf is not None:
            return self._cruise_conf.split(",")[3]

    @horizontal_osc_angle_left.setter
    def horizontal_osc_angle_left(self, value: int) -> None:
        """Set the left horizontal oscillation angle."""
        _LOGGER.debug("PyDreoAirCirculator:horizontal_osc_angle_left.setter")
        if self._cruise_conf is not None:
            right_angle = int(self._cruise_conf.split(",")[1])
            # 30 deg is the minimum top-bottom and left-right difference for the tested fan (DR-HAF003S)
            if right_angle - value < MIN_OSC_ANGLE_DIFFERENCE:
                raise ValueError(f"Left angle must be at least {MIN_OSC_ANGLE_DIFFERENCE} less than right angle")
            cruise_conf_values = self._cruise_conf.split(',')
            # Note that HA seems to send this in as a float, so we need to convert to int just in case
            cruise_conf_values[3] = int(value)
            self._send_command(CRUISECONF_KEY, ','.join(map(str, cruise_conf_values)))

    @property
    def horizontal_angle(self) -> int:
        """Get the current fixed horizontal angle."""
        if (self._fixed_conf is not None):
            return self._fixed_conf.split(",")[1]

    @horizontal_angle.setter
    def horizontal_angle(self, value: int) -> None:
        """Set the horizontal angle."""
        _LOGGER.debug("PyDreoAirCirculator:horizontal_angle.setter")
        if (self._fixed_conf is not None):
            # Note that HA seems to send this in as a float, so we need to convert to int just in case
            self._send_command(FIXEDCONF_KEY, f"{self._fixed_conf.split(',')[0]},{int(value)}")

    @property
    def vertical_angle(self) -> int:
        """Get the current fixed vertical angle."""
        if self._fixed_conf is not None:
            return self._fixed_conf.split(",")[0]

    @vertical_angle.setter
    def vertical_angle(self, value: int) -> None:
        """Set the vertical angle."""
        _LOGGER.debug("PyDreoAirCirculator:vertical_angle.setter")
        if self._fixed_conf is not None:
            # Note that HA seems to send this in as a float, we need to convert to int just in case
            self._send_command(FIXEDCONF_KEY, f"{int(value)},{self._fixed_conf.split(',')[1]}")

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("PyDreoAirCirculator:update_state")
        super().update_state(state)

        self._horizontally_oscillating = self.get_state_update_value(state, HORIZONTAL_OSCILLATION_KEY)
        self._vertically_oscillating = self.get_state_update_value(state, VERTICAL_OSCILLATION_KEY)
        self._osc_mode = self.get_state_update_value(state, OSCMODE_KEY)
        self._cruise_conf = self.get_state_update_value(state, CRUISECONF_KEY)
        self._fixed_conf = self.get_state_update_value(state, FIXEDCONF_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("PyDreoAirCirculator:handle_server_update")
        super().handle_server_update(message)

        val_horiz_oscillation = self.get_server_update_key_value(message, HORIZONTAL_OSCILLATION_KEY)
        if isinstance(val_horiz_oscillation, bool):
            self._horizontally_oscillating = val_horiz_oscillation

        val_vert_oscillation = self.get_server_update_key_value(message, VERTICAL_OSCILLATION_KEY)
        if isinstance(val_vert_oscillation, bool):
            self._vertically_oscillating = val_vert_oscillation

        val_osc_mode = self.get_server_update_key_value(message, OSCMODE_KEY)
        if isinstance(val_osc_mode, int):
            self._osc_mode = val_osc_mode

        val_cruiseconf = self.get_server_update_key_value(message, CRUISECONF_KEY)
        if isinstance(val_cruiseconf, str):
            self._cruise_conf = val_cruiseconf

        val_fixed_conf = self.get_server_update_key_value(message, FIXEDCONF_KEY)
        if isinstance(val_fixed_conf, str):
            self._fixed_conf = val_fixed_conf
