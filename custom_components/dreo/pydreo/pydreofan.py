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
    HORIZONTAL_OSCILLATION_KEY,
    HORIZONTAL_OSCILLATION_ANGLE_KEY,
    VERTICAL_OSCILLATION_KEY,
    VERTICAL_OSCILLATION_ANGLE_KEY,
    OSCMODE_KEY,
    LIGHTSENSORON_KEY,
    MUTEON_KEY,
    FIXEDCONF_KEY,
    OscillationMode,
    TemperatureUnit
)

from .pydreobasedevice import PyDreoBaseDevice
from .models import DreoDeviceDetails, SPEED_RANGE

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo

class PyDreoFan(PyDreoBaseDevice):
    """Base class for Dreo Fan API Calls."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        super().__init__(device_definition, details, dreo)

        self._fan_speed = None

        self._wind_type = None
        self._wind_mode = None
        self._shakehorizon = None
        self._osc_mode = None

        self._horizontally_oscillating = None
        self._vertically_oscillating = None

        self._temperature = None
        self._led_always_on = None
        self._voice_on = None
        self._device_definition = device_definition
        self._wind_mode = None
        self._horizontally_oscillating = None
        self._vertically_oscillating = None
        self._light_sensor_on = None
        self._mute_on = None

        self._fixed_conf = None

    def __repr__(self):
        # Representation string of object.
        return "<{0}:{1}:{2}>".format(
            self.__class__.__name__, self._device_id, self._name
        )

    @property
    def speed_range(self):
        """Get the speed range"""
        return self._device_definition.range[SPEED_RANGE]

    @property
    def preset_modes(self):
        """Get the list of preset modes"""
        return self._device_definition.preset_modes

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
    def fan_speed(self, fan_speed : int) :
        """Set the fan speed."""
        if fan_speed < 1 or fan_speed > self._device_definition.range[SPEED_RANGE][1]:
            _LOGGER.error("Fan speed %s is not in the acceptable range: %s",
                          fan_speed,
                          self._device_definition.range[SPEED_RANGE])
            return
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
        key : str = None

        if self._wind_type is not None:
            key = WINDTYPE_KEY
        elif self._wind_mode is not None:
            key = WIND_MODE_KEY
        else:
            _LOGGER.error("Attempting to set preset_mode on a device that doesn't support.")
            return

        if value in self.preset_modes:
            self._send_command(key, self._device_definition.preset_modes.index(value) + 1)
        else:
            _LOGGER.error("Preset mode %s is not in the acceptable list: %s",
                          value,
                          self._device_definition.preset_modes)

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
            _LOGGER.error("Attempting to set oscillating on a device that doesn't support.")
            return

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
            _LOGGER.error("Horizontal oscillation is not supported.")
            return
        
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
            _LOGGER.error("Vertical oscillation is not supported.")
            return
    
    def set_horizontal_oscillation_angle(self, angle: int) -> None:
        """Set the horizontal oscillation angle."""
        _LOGGER.debug("PyDreoAirCirculatorFan:set_horizontal_oscillation_angle")
        if not self._horizontally_oscillating is None:
            _LOGGER.error("This device does not support horizontal oscillation")
            return
        self._send_command(HORIZONTAL_OSCILLATION_ANGLE_KEY, angle)

    def set_vertical_oscillation_angle(self, angle: int) -> None:
        """Set the vertical oscillation angle."""
        _LOGGER.debug("PyDreoAirCirculatorFan:set_vertical_oscillation_angle")
        if not self._vertically_oscillating is None:
            _LOGGER.error("This device does not support vertical oscillation")
            return

        self._send_command(VERTICAL_OSCILLATION_ANGLE_KEY, angle)

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
            _LOGGER.error("Attempting to set display always on on a device that doesn't support.")
            return

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
            self._send_command(LIGHTSENSORON_KEY,  value)
        else:
            _LOGGER.error("Attempting to set adaptive brightness on on a device that doesn't support.")
            return

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
            _LOGGER.error("Attempting to set panel_sound on a device that doesn't support.")
            return
        
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

    def update_state(self, state: dict) :
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
        self._wind_type = self.get_state_update_value(state, WINDTYPE_KEY)
        self._wind_mode = self.get_state_update_value(state, WIND_MODE_KEY)
        self._horizontally_oscillating = self.get_state_update_value(state, HORIZONTAL_OSCILLATION_KEY)
        self._vertically_oscillating = self.get_state_update_value(state, VERTICAL_OSCILLATION_KEY)
        self._osc_mode = self.get_state_update_value(state, OSCMODE_KEY)
        self._light_sensor_on = self.get_state_update_value(state, LIGHTSENSORON_KEY)
        self._mute_on = self.get_state_update_value(state, MUTEON_KEY)
        self._fixed_conf = self.get_state_update_value(state, FIXEDCONF_KEY)


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

        val_horiz_oscillation = self.get_server_update_key_value(message, HORIZONTAL_OSCILLATION_KEY)
        if isinstance(val_horiz_oscillation, bool):
            self._horizontally_oscillating = val_horiz_oscillation

        val_vert_oscillation = self.get_server_update_key_value(message, VERTICAL_OSCILLATION_KEY)
        if isinstance(val_vert_oscillation, bool):
            self._vertically_oscillating = val_vert_oscillation

        val_osc_mode = self.get_server_update_key_value(message, OSCMODE_KEY)
        if isinstance(val_osc_mode, int):
            self._osc_mode = val_osc_mode

        val_light_sensor = self.get_server_update_key_value(message, LIGHTSENSORON_KEY)
        if isinstance(val_light_sensor, bool):
            self._light_sensor_on = val_light_sensor

        val_mute = self.get_server_update_key_value(message, MUTEON_KEY)
        if isinstance(val_mute, bool):
            self._mute_on = val_mute

        val_fixed_conf = self.get_server_update_key_value(message, FIXEDCONF_KEY)  
        if isinstance(val_fixed_conf, str):
            self._fixed_conf = val_fixed_conf
    
