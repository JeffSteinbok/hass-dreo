"""Dreo API for controling fans."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    POWERON_KEY,
    WINDLEVEL_KEY,
    TEMPERATURE_KEY,
    LEDALWAYSON_KEY,
    VOICEON_KEY,
    WINDTYPE_KEY,
    WIND_MODE_KEY,
    SHAKEHORIZON_KEY,
    SHAKEHORIZONANGLE_KEY,
    HORIZONTAL_OSCILLATION_KEY,
    HORIZONTAL_OSCILLATION_ANGLE_KEY,
    VERTICAL_OSCILLATION_KEY,
    VERTICAL_OSCILLATION_ANGLE_KEY,
    CRUISECONF_KEY,
    MIN_OSC_ANGLE_DIFFERENCE,
    OSCMODE_KEY,
    LIGHTSENSORON_KEY,
    MUTEON_KEY,
    FIXEDCONF_KEY,
    OscillationMode,
    TemperatureUnit
)

from .pydreobasedevice import PyDreoBaseDevice
from .models import DreoDeviceDetails, SPEED_RANGE
from .helpers import Helpers

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoFan(PyDreoBaseDevice):
    """Base class for Dreo Fan API Calls."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        super().__init__(device_definition, details, dreo)
        
        self._speed_range = None
        if (device_definition.range is not None):
            self._speed_range = device_definition.range[SPEED_RANGE]
        if (self._speed_range is None):
            self._speed_range = self.parse_speed_range(details)
        self._preset_modes = device_definition.preset_modes
        if (self._preset_modes is None):
            self._preset_modes = self.parse_preset_modes(details)

        self._fan_speed = None

        self._wind_type = None
        self._wind_mode = None
        self._shakehorizon = None
        self._shakehorizonangle = None
        self._osc_mode = None
        self._cruise_conf = None

        self._horizontally_oscillating = None
        self._vertically_oscillating = None

        self._temperature = None
        self._led_always_on = None
        self._voice_on = None
        self._device_definition = device_definition
        self._light_sensor_on = None
        self._mute_on = None

        self._fixed_conf = None

    def __repr__(self):
        # Representation string of object.
        return f"<{self.__class__.__name__}:{self._device_id}:{self._name}>"

    def parse_speed_range(self, details: Dict[str, list]) -> tuple[int, int]:
        """Parse the speed range from the details."""
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            control = controls_conf.get("control", None)
            if (control is not None):
                for control_item in control:
                    if (control_item is not None):
                        if control_item.get("type", None) == "Speed":
                            lowSpeed = control_item.get("items", None)[0].get("value", None)
                            highSpeed = control_item.get("items", None)[1].get("value", None)
                            speed_range = (lowSpeed, highSpeed)
                            _LOGGER.debug("PyDreoFan:Detected speed range - %s", speed_range)
                            return speed_range

    def parse_preset_modes(self, details: Dict[str, list]) -> tuple[str, int]:
        """Parse the preset modes from the details."""
        preset_modes = []
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            control = controls_conf.get("control", None)
            if (control is not None):
                for control_item in control:
                    if (control_item is not None):
                        if control_item.get("type", None) == "Mode":
                            for mode_item in control_item.get("items", None):
                                text = mode_item.get("image", None).split("_")[1]
                                value = mode_item.get("value", None)
                                preset_modes.append((text, value))
            schedule = controls_conf.get("schedule", None)
            if (schedule is not None):
                modes = schedule.get("modes", None)
                if (modes is not None):
                    for mode_item in modes:
                        text = mode_item.get("icon", None).split("_")[1]
                        value = mode_item.get("value", None)
                        if (text, value) not in preset_modes:
                            preset_modes.append((text, value))

        preset_modes.sort(key=lambda tup: tup[1])  # sorts in place
        if (preset_modes.count is 0):
            _LOGGER.debug("PyDreoFan:No preset modes detected")
            preset_modes = None
        _LOGGER.debug("PyDreoFan:Detected preset modes - %s", preset_modes)
        return preset_modes
                        
    @property
    def speed_range(self):
        """Get the speed range"""
        return self._speed_range

    @property
    def preset_modes(self) -> list[str]:
        """Get the list of preset modes"""
        return Helpers.get_name_list(self._preset_modes)
    
    @property
    def is_on(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._is_on

    @is_on.setter
    def is_on(self, value: bool):
        """Set if the fan is on or off"""
        _LOGGER.debug("PyDreoFan:is_on.setter - %s", value)
        self._send_command(POWERON_KEY, value)

    @property
    def fan_speed(self):
        """Return the current fan speed"""
        return self._fan_speed

    @fan_speed.setter
    def fan_speed(self, fan_speed: int):
        """Set the fan speed."""
        if fan_speed < 1 or fan_speed > self._speed_range[1]:
            _LOGGER.error("Fan speed %s is not in the acceptable range: %s",
                          fan_speed,
                          self._speed_range)
            raise ValueError(f"fan_speed must be between {self._speed_range[0]} and {self._speed_range[1]}")
        self._send_command(WINDLEVEL_KEY, fan_speed)

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        mode = self._wind_mode
        if mode is None:
            mode = self._wind_type

        if mode is None:
            return None

        # If we can't match the preset mode, just return the first one.
        if mode > len(self.preset_modes):
            return self.preset_modes[0]

        return self.preset_modes[mode - 1]

    @preset_mode.setter
    def preset_mode(self, value: str) -> None:
        key: str = None

        if self._wind_type is not None:
            key = WINDTYPE_KEY
        elif self._wind_mode is not None:
            key = WIND_MODE_KEY
        else:
            raise NotImplementedError("Attempting to set preset_mode on a device that doesn't support.")

        if value in self.preset_modes:
            self._send_command(key, self.preset_modes.index(value) + 1)
        else:
            raise ValueError(f"Preset mode {value} is not in the acceptable list: {self.preset_modes}")

    @property
    def temperature(self):
        """Get the temperature"""
        return self._temperature

    @property
    def temperature_units(self) -> TemperatureUnit:
        """Get the temperature units."""
        # I'm not sure how the API returns in other regions, so I'm just auto-detecting
        # based on some reasonable range.

        # Going to return Celcius as the default.  None of this matters if there is no
        # temperature returned anyway
        if self._temperature is not None:
            if self._temperature > 50:
                return TemperatureUnit.FAHRENHEIT

        return TemperatureUnit.CELCIUS

    @property
    def oscillating(self) -> bool:
        """Returns `True` if either horizontal or vertical oscillation is on."""
        if self._shakehorizon is not None:
            return self._shakehorizon
        if self._horizontally_oscillating is not None:
            return self._horizontally_oscillating or self._vertically_oscillating
        if self._osc_mode is not None:
            return self._osc_mode != OscillationMode.OFF
        return None

    @oscillating.setter
    def oscillating(self, value: bool) -> None:

        """Enable or disable oscillation"""
        _LOGGER.debug("PyDreoFan:oscillating.setter")

        if self._shakehorizon is not None:
            self._send_command(SHAKEHORIZON_KEY, value)
        elif self._horizontally_oscillating is not None:
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
        _LOGGER.debug("PyDreoFan:horizontally_oscillating.setter")
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
        _LOGGER.debug("PyDreoFan:vertical_osc_angle_top.setter")
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
        _LOGGER.debug("PyDreoFan:vertical_osc_angle_bottom.setter")
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
        _LOGGER.debug("PyDreoFan:horizontal_osc_angle_right.setter")
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
        _LOGGER.debug("PyDreoFan:horizontal_osc_angle_left.setter")
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
    def shakehorizonangle(self) -> int:
        """Get the current oscillation angle"""
        if self._shakehorizonangle is not None:
            return self._shakehorizonangle

    @shakehorizonangle.setter
    def shakehorizonangle(self, value: int) -> None:
        """Set the oscillation angle."""
        _LOGGER.debug("PyDreoFan:shakehorizonangle.setter")
        if self._shakehorizonangle is not None:
            self._send_command(SHAKEHORIZONANGLE_KEY, value)            


    @property
    def display_auto_off(self) -> bool:
        """Is the display always on?"""
        if self._led_always_on is not None:
            return not self._led_always_on

        return None

    @display_auto_off.setter
    def display_auto_off(self, value: bool) -> None:
        """Set if the display is always on"""
        _LOGGER.debug("PyDreoFan:display_auto_off.setter")

        if self._led_always_on is not None:
            self._send_command(LEDALWAYSON_KEY, not value)
        else:
            raise NotImplementedError("Attempting to set display always on on a device that doesn't support.")

    @property
    def adaptive_brightness(self) -> bool:
        """Is the display always on?"""
        if (self._light_sensor_on is not None):
            return self._light_sensor_on
        else:
            return None

    @adaptive_brightness.setter
    def adaptive_brightness(self, value: bool) -> None:
        """Set if the display is always on"""
        _LOGGER.debug("PyDreoFan:adaptive_brightness.setter")

        if self._light_sensor_on is not None:
            self._send_command(LIGHTSENSORON_KEY, value)
        else:
            raise NotImplementedError("Attempting to set adaptive brightness on on a device that doesn't support.")

    @property
    def panel_sound(self) -> bool:
        """Is the panel sound on"""
        if self._voice_on is not None:
            return self._voice_on
        if self._mute_on is not None:
            return not self._mute_on
        return None

    @panel_sound.setter
    def panel_sound(self, value: bool) -> None:
        """Set if the panel sound"""
        _LOGGER.debug("PyDreoFan:panel_sound.setter")

        if self._voice_on is not None:
            self._send_command(VOICEON_KEY, value)
        elif self._mute_on is not None:
            self._send_command(MUTEON_KEY, not value)
        else:
            raise NotImplementedError("Attempting to set panel_sound on a device that doesn't support.")

    @property
    def horizontal_angle(self) -> int:
        """Get the current fixed horizontal angle."""
        if (self._fixed_conf is not None):
            return self._fixed_conf.split(",")[1]

    @horizontal_angle.setter
    def horizontal_angle(self, value: int) -> None:
        """Set the horizontal angle."""
        _LOGGER.debug("PyDreoFan:horizontal_angle.setter")
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
        _LOGGER.debug("PyDreoFan:vertical_angle.setter")
        if self._fixed_conf is not None:
            # Note that HA seems to send this in as a float, we need to convert to int just in case
            self._send_command(FIXEDCONF_KEY, f"{int(value)},{self._fixed_conf.split(',')[1]}")

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("PyDreoFan:update_state")
        super().update_state(state)

        self._fan_speed = self.get_state_update_value(state, WINDLEVEL_KEY)
        if self._fan_speed is None:
            _LOGGER.error("Unable to get fan speed from state. Check debug logs for more information.")

        self._temperature = self.get_state_update_value(state, TEMPERATURE_KEY)
        self._led_always_on = self.get_state_update_value(state, LEDALWAYSON_KEY)
        self._voice_on = self.get_state_update_value(state, VOICEON_KEY)
        self._shakehorizon = self.get_state_update_value(state, SHAKEHORIZON_KEY)
        self._shakehorizonangle = self.get_state_update_value(state, SHAKEHORIZONANGLE_KEY)
        self._wind_type = self.get_state_update_value(state, WINDTYPE_KEY)
        self._wind_mode = self.get_state_update_value(state, WIND_MODE_KEY)
        self._horizontally_oscillating = self.get_state_update_value(state, HORIZONTAL_OSCILLATION_KEY)
        self._vertically_oscillating = self.get_state_update_value(state, VERTICAL_OSCILLATION_KEY)
        self._osc_mode = self.get_state_update_value(state, OSCMODE_KEY)
        self._light_sensor_on = self.get_state_update_value(state, LIGHTSENSORON_KEY)
        self._mute_on = self.get_state_update_value(state, MUTEON_KEY)
        self._fixed_conf = self.get_state_update_value(state, FIXEDCONF_KEY)
        self._cruise_conf = self.get_state_update_value(state, CRUISECONF_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("PyDreoFan:handle_server_update")

        val_power_on = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_power_on, bool):
            self._is_on = val_power_on

        val_wind_level = self.get_server_update_key_value(message, WINDLEVEL_KEY)
        if isinstance(val_wind_level, int):
            self._fan_speed = val_wind_level

        val_temperature = self.get_server_update_key_value(message, TEMPERATURE_KEY)
        if isinstance(val_temperature, int):
            self._temperature = val_temperature

        val_display_always_on = self.get_server_update_key_value(message, LEDALWAYSON_KEY)
        if isinstance(val_display_always_on, bool):
            self._led_always_on = val_display_always_on

        val_panel_sound = self.get_server_update_key_value(message, VOICEON_KEY)
        if isinstance(val_panel_sound, bool):
            self._voice_on = val_panel_sound

        val_wind_mode = self.get_server_update_key_value(message, WIND_MODE_KEY)
        if isinstance(val_wind_mode, int):
            self._wind_mode = val_wind_mode

        val_wind_type = self.get_server_update_key_value(message, WINDTYPE_KEY)
        if isinstance(val_wind_type, int):
            self._wind_type = val_wind_type

        val_shakehorizon = self.get_server_update_key_value(message, SHAKEHORIZON_KEY)
        if isinstance(val_shakehorizon, bool):
            self._shakehorizon = val_shakehorizon

        val_shakehorizonangle = self.get_server_update_key_value(message, SHAKEHORIZONANGLE_KEY)
        if isinstance(val_shakehorizonangle, int):
            self._shakehorizonangle = val_shakehorizonangle

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

        val_light_sensor = self.get_server_update_key_value(message, LIGHTSENSORON_KEY)
        if isinstance(val_light_sensor, bool):
            self._light_sensor_on = val_light_sensor

        val_mute = self.get_server_update_key_value(message, MUTEON_KEY)
        if isinstance(val_mute, bool):
            self._mute_on = val_mute

        val_fixed_conf = self.get_server_update_key_value(message, FIXEDCONF_KEY)
        if isinstance(val_fixed_conf, str):
            self._fixed_conf = val_fixed_conf
