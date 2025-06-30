"""Dreo API for controlling air conditioners."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    TEMPERATURE_KEY,
    TARGET_TEMPERATURE_KEY,
    SLEEPTEMPOFFSET_KEY,
    MODE_KEY,
    OSCMODE_KEY,
    MUTEON_KEY,
    POWERON_KEY,
    DEVON_KEY,
    TIMERON_KEY,
    COOLDOWN_KEY,
    PTCON_KEY,
    LIGHTON_KEY,
    CTLSTATUS_KEY,
    TIMEROFF_KEY,
    CHILDLOCKON_KEY,
    TEMPOFFSET_KEY,
    FIXEDCONF_KEY,
    TemperatureUnit,
    WINDLEVEL_KEY,
    HUMIDITY_KEY,
    TARGET_HUMIDITY_KEY,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    PRESET_NONE,
    PRESET_ECO,
    PRESET_SLEEP
)
from .pydreobasedevice import PyDreoBaseDevice
from .models import DreoDeviceDetails

DREO_AC_MODE_COOL = 1
DREO_AC_MODE_DRY = 2
DREO_AC_MODE_FAN = 3
DREO_AC_MODE_SLEEP = 4
DREO_AC_MODE_ECO = 5

DREO_AC_MODES = [
    DREO_AC_MODE_COOL,
    DREO_AC_MODE_FAN,
    DREO_AC_MODE_DRY,
    DREO_AC_MODE_SLEEP,
    DREO_AC_MODE_ECO,
]

DREO_AC_FAN_MODE_MAP = {
    1: FAN_LOW,
    2: FAN_MEDIUM,
    3: FAN_HIGH,
    4: FAN_AUTO,
    FAN_LOW: 1,
    FAN_MEDIUM: 2,
    FAN_HIGH: 3,
    FAN_AUTO: 4,
}

AC_OSC_ON = 2
AC_OSC_OFF = 0

WORK_TIME = "worktime"
TEMP_TARGET_REACHED = "reachtarget"

# Map: Celsius setting → Fahrenheit value to send to API
# This is based on actual Fahrenheit values sent to the AC when using the remote control while AC is set to Celsius
CELSIUS_TO_FAHRENHEIT_MAP = {
    16: 61,   # Set 16°C → Send 61°F
    17: 63,   # Set 17°C → Send 63°F  
    18: 65,   # Set 18°C → Send 65°F
    19: 67,   # Set 19°C → Send 67°F
    20: 68,   # Set 20°C → Send 68°F
    21: 70,   # Set 21°C → Send 70°F
    22: 72,   # Set 22°C → Send 72°F
    23: 74,   # Set 23°C → Send 74°F
    24: 76,   # Set 24°C → Send 76°F
    25: 77,   # Set 25°C → Send 77°F
    26: 79,   # Set 26°C → Send 79°F
    27: 81,   # Set 27°C → Send 81°F
    28: 83,   # Set 28°C → Send 83°F
    29: 85,   # Set 29°C → Send 85°F
    30: 86,   # Set 30°C → Send 86°F
}

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo

class PyDreoAC(PyDreoBaseDevice):
    """Base class for Dreo air conditioner API Calls."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air conditioner devices."""
        super().__init__(device_definition, details, dreo)

        self._mode = None
        self._temperature = None
        self._target_temperature = None
        self._mute_on = None
        self._fixed_conf = None
        self._dev_on = None
        self._timer_on = None
        self._cooldown = None
        self._ptc_on = None
        self._display_auto_off = None
        self._ctlstatus = None
        self._timer_off = None
        self._childlockon = None
        self._tempoffset = None
        self._fixed_conf = None
        self._preset_mode = None

        self._humidity = None
        self._target_humidity = None
        self._osc_mode = None
        self._fan_mode = None
        self.work_time = None
        self.temp_target_reached = None
        self._sleep_preset_initialization_temp = None
        
    @property
    def poweron(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._is_on

    @poweron.setter
    def poweron(self, value: bool):
        """Set if the air conditioner is on or off"""
        _LOGGER.debug("PyDreoAC:poweron.setter - %s", value)
        self._send_command(POWERON_KEY, value)

    @property
    def preset_modes(self):
        """Get the list of preset modes"""
        return self._device_definition.preset_modes

    @property
    def hvac_modes(self):
        """Get the list of supported HVAC modes"""
        return self._device_definition.hvac_modes

    @property
    def devon(self):
        """Returns `True` if devon is true, `False` otherwise. Whatever devon is"""
        return self._dev_on

    @devon.setter
    def devon(self, value: bool):
        _LOGGER.debug("PyDreoAC:devon.setter - %s", value)
        self._send_command(DEVON_KEY, value)

    @property
    def mode(self):
        """Return the current preset mode."""
        return self._mode

    @mode.setter
    def mode(self, mode: str) -> None:
        _LOGGER.debug("PyDreoAC:mode(%s) --> %s", self.name, mode)
        self._send_command(MODE_KEY, mode)

    @property
    def fan_mode(self) -> str:
        """Return the current fan mode"""
        return self._fan_mode

    @fan_mode.setter
    def fan_mode(self, mode: str) -> None:
        """Set fan mode if requested"""
        _LOGGER.debug("PyDreoAC:fan_mode.setter(%s) %s --> %s", self.name, self._fan_mode, mode)
        self._fan_mode = mode
        self._send_command(WINDLEVEL_KEY, DREO_AC_FAN_MODE_MAP[mode])

    @property
    def temperature(self):
        """Get the temperature"""
        return self._temperature

    # @temperature.setter
    # def temperature(self, value: int) -> None:
    #     """Set the temperature"""
    #     _LOGGER.debug("PyDreoAC:temperature.setter(%s) --> %s", self.name, value)
    #     self._temperature = value
    #     self._send_command(TARGET_TEMPERATURE_KEY, value)

    @property
    def temperature_units(self) -> TemperatureUnit:
        """Get the temperature units for the device display."""
        # Use HA's configured unit if available, otherwise auto-detect from device values
        if hasattr(self, '_ha_uses_celsius') and self._ha_uses_celsius is not None:
            return TemperatureUnit.CELSIUS if self._ha_uses_celsius else TemperatureUnit.FAHRENHEIT
        
        # Fallback: auto-detect based on current temperature range  
        if self._temperature is not None and self._temperature > 50:
            return TemperatureUnit.FAHRENHEIT
        return TemperatureUnit.CELSIUS

    @property
    def target_temperature(self):
        """Get the temperature"""
        return self._target_temperature

    @target_temperature.setter
    def target_temperature(self, value: int) -> None:
        """Set the target temperature with empirical mapping for Celsius conversions."""
        # Handle SLEEP mode with sleeptempoffset
        if self._preset_mode == PRESET_SLEEP and self._sleep_preset_initialization_temp is not None:
            if self.temperature_units == TemperatureUnit.CELSIUS:
                celsius_equivalent = round((value - 32) * 5/9)
                mapped_fahrenheit = CELSIUS_TO_FAHRENHEIT_MAP.get(celsius_equivalent, value)
                sleeptempoffset = mapped_fahrenheit - self._sleep_preset_initialization_temp
                _LOGGER.debug("PyDreoAC:target_temperature.setter(%s) SLEEP Celsius mode: %s°F (%s°C) --> offset %s (init temp: %s)", 
                              self, value, celsius_equivalent, sleeptempoffset, self._sleep_preset_initialization_temp)
                self._target_temperature = mapped_fahrenheit
                self._send_command(SLEEPTEMPOFFSET_KEY, sleeptempoffset)
            else:
                # HA uses Fahrenheit - calculate offset directly
                sleeptempoffset = value - self._sleep_preset_initialization_temp
                _LOGGER.debug("PyDreoAC:target_temperature.setter(%s) SLEEP Fahrenheit mode: %s°F --> offset %s (init temp: %s)", 
                              self, value, sleeptempoffset, self._sleep_preset_initialization_temp)
                self._target_temperature = value
                self._send_command(SLEEPTEMPOFFSET_KEY, sleeptempoffset)
        else:
            # Normal mode (non-SLEEP) - use regular templevel
            if self.temperature_units == TemperatureUnit.CELSIUS:
                celsius_equivalent = round((value - 32) * 5/9)
                mapped_fahrenheit = CELSIUS_TO_FAHRENHEIT_MAP.get(celsius_equivalent, value)
                _LOGGER.debug("PyDreoAC:target_temperature.setter(%s) Celsius mode: %s°F (%s°C) --> %s°F", 
                              self, value, celsius_equivalent, mapped_fahrenheit)
                self._target_temperature = mapped_fahrenheit
                self._send_command(TARGET_TEMPERATURE_KEY, mapped_fahrenheit)
            else:
                # HA uses Fahrenheit - pass through directly
                _LOGGER.debug("PyDreoAC:target_temperature.setter(%s) Fahrenheit mode: %s°F", self, value)
                self._target_temperature = value
                self._send_command(TARGET_TEMPERATURE_KEY, value)

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
        _LOGGER.debug("PyDreoAC:target_humidity.setter(%s) %s --> %s", self, self._target_humidity, value)
        self._target_humidity = value
        self._send_command(TARGET_HUMIDITY_KEY, value)

    @property
    def oscon(self) -> bool:
        """Returns `True` if oscillation is on."""
        return self._osc_mode is not None and self._osc_mode == AC_OSC_ON

    @oscon.setter
    def oscon(self, value: bool) -> None:
        """Enable or disable oscillation"""
        set_val = AC_OSC_ON if value else AC_OSC_OFF
        _LOGGER.debug("PyDreoAC:oscon.setter(%s) -> %s (%s)", self.name, value, set_val)
        self._osc_mode = set_val
        self._send_command(OSCMODE_KEY, set_val)

    @property
    def ptcon(self) -> bool:
        """Returns `True` if PTC is on."""
        return self._ptc_on

    @ptcon.setter
    def ptcon(self, value: bool) -> None:
        """Enable or disable PTC"""
        _LOGGER.debug("PyDreoAC:ptcon.setter(%s) --> %s", self.name, value)
        self._send_command(PTCON_KEY, value)

    @property
    def display_auto_off(self) -> bool:
        """Returns `True` if Display Auto off is OFF."""
        return self._display_auto_off

    @display_auto_off.setter
    def display_auto_off(self, value: bool) -> None:
        """Enable or disable display auto-off"""
        _LOGGER.debug("PyDreoAC:display_auto_off.setter(%s) --> %s", self.name, value)
        self._send_command(LIGHTON_KEY, not value)

    @property
    def ctlstatus(self) -> bool:
        """Returns `True` if ctlstatus is on."""
        return self._ctlstatus

    @ctlstatus.setter
    def ctlstatus(self, value: bool) -> None:
        """Enable or disable ctlstatus"""
        _LOGGER.debug("PyDreoAC:ctlstatus.setter(%s) --> %s", self.name, value)
        self._send_command(CTLSTATUS_KEY, value)

    @property
    def childlockon(self) -> bool:
        """Returns `True` if Child Lock is on."""
        return self._childlockon

    @childlockon.setter
    def childlockon(self, value: bool) -> None:
        """Enable or disable Child Lock"""
        _LOGGER.debug("PyDreoAC:childlockon.setter(%s) --> %s", self.name, value)
        self._send_command(CHILDLOCKON_KEY, value)

    @property
    def panel_sound(self) -> bool:
        """Is the panel sound on"""
        if self._mute_on is not None:
            return not self._mute_on
        return None

    @panel_sound.setter
    def panel_sound(self, value: bool) -> None:
        """Set if the panel sound"""
        _LOGGER.debug("PyDreoAC:panel_sound.setter(%s) --> %s", self.name, value)
        self._send_command(MUTEON_KEY, not value)
        
    @property
    def preset_mode(self) -> str:
        """Return the current preset mode."""
        return self._preset_mode

    @preset_mode.setter
    def preset_mode(self, mode: str) -> None:
        """Set the preset mode."""
        _LOGGER.debug("PyDreoAC:preset_mode.setter(%s) %s --> %s", self.name, self._preset_mode, mode)
        
        if mode == PRESET_ECO:
            self._send_command(MODE_KEY, DREO_AC_MODE_ECO)
        elif mode == PRESET_SLEEP:
            # Store the current target temperature as the sleep initialization temperature
            self._sleep_preset_initialization_temp = self._target_temperature
            _LOGGER.debug("PyDreoAC:preset_mode.setter(%s) Sleep mode - storing init temp: %s", 
                          self.name, self._sleep_preset_initialization_temp)
            self._send_command(MODE_KEY, DREO_AC_MODE_SLEEP)
        else:
            self._send_command(MODE_KEY, DREO_AC_MODE_COOL)
        
        self._preset_mode = mode

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        super().update_state(state)  # handles _is_on

        _LOGGER.debug("PyDreoAC(%s):update_state: %s", self.name, state)
        self._temperature = self.get_state_update_value(state, TEMPERATURE_KEY)
        self._target_temperature = self.get_state_update_value(state, TARGET_TEMPERATURE_KEY)
        
        mode = self.get_state_update_value(state, MODE_KEY)
        if mode == DREO_AC_MODE_ECO:
            mode = DREO_AC_MODE_COOL
            self._preset_mode = PRESET_ECO
        elif mode == DREO_AC_MODE_SLEEP:
            mode = DREO_AC_MODE_COOL
            self._preset_mode = PRESET_SLEEP
        else:
            self._preset_mode = PRESET_NONE
        self._mode = mode
        
        self._fan_mode = DREO_AC_FAN_MODE_MAP[self.get_state_update_value(state, WINDLEVEL_KEY)]
        self._osc_mode = self.get_state_update_value(state, OSCMODE_KEY)
        self._mute_on = self.get_state_update_value(state, MUTEON_KEY)
        self._dev_on = self.get_state_update_value(state, DEVON_KEY)
        timeron = self.get_state_update_value(state, TIMERON_KEY)
        self._timer_on = timeron["du"]
        self._cooldown = self.get_state_update_value(state, COOLDOWN_KEY)
        self._ptc_on = self.get_state_update_value(state, PTCON_KEY)
        self._display_auto_off = not self.get_state_update_value(state, LIGHTON_KEY)
        self._ctlstatus = self.get_state_update_value(state, CTLSTATUS_KEY)
        timeroff = self.get_state_update_value(state, TIMEROFF_KEY)
        self._timer_off = timeroff["du"]
        self._childlockon = self.get_state_update_value(state, CHILDLOCKON_KEY)
        self._tempoffset = self.get_state_update_value(state, TEMPOFFSET_KEY)
        self._fixed_conf = self.get_state_update_value(state, FIXEDCONF_KEY)
        self._humidity = self.get_state_update_value(state, HUMIDITY_KEY)
        self._target_humidity = self.get_state_update_value(state, TARGET_HUMIDITY_KEY)
        self.work_time = self.get_state_update_value(state, WORK_TIME)
        self.temp_target_reached = "Yes" if self.get_state_update_value(state, TEMP_TARGET_REACHED) > 0 else "No"
        # TODO ecopauserate

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("PyDreoAC:handle_server_update(%s): %s", self.name, message)

        val_poweron = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_poweron, bool):
            self._is_on = val_poweron  # Ensure poweron state is updated
            _LOGGER.debug("PyDreoAC:handle_server_update - poweron is %s", self._is_on)

        val_temperature = self.get_server_update_key_value(message, TEMPERATURE_KEY)
        if isinstance(val_temperature, int):
            self._temperature = val_temperature

        val_target_temperature = self.get_server_update_key_value(message, TARGET_TEMPERATURE_KEY)
        if isinstance(val_target_temperature, int):
            _LOGGER.debug("PyDreoAC(%s):handle_server_update - target_temperature: %s --> %s", 
                          self, 
                          self._target_temperature, 
                          val_target_temperature)
            self._target_temperature = val_target_temperature

        # Reported mode can be an empty string if the AC is off. Deal with that by
        # explicitly setting that to off.
        val_mode = self.get_server_update_key_value(message, MODE_KEY)
        if isinstance(val_mode, int):
            target_mode = val_mode
            if target_mode == 5:
                target_mode = DREO_AC_MODE_COOL
                self._preset_mode = PRESET_ECO
            elif target_mode == 4:
                target_mode = DREO_AC_MODE_COOL
                self._preset_mode = PRESET_SLEEP
            else:
                self._preset_mode = PRESET_NONE
            _LOGGER.debug("PyDreoAC(%s):handle_server_update - mode: %s --> %s", 
                          self, 
                          self._mode, 
                          target_mode)
            self._mode = target_mode

        val_fan_mode = self.get_server_update_key_value(message, WINDLEVEL_KEY)
        if isinstance(val_fan_mode, int):
            val_fan_mode = DREO_AC_FAN_MODE_MAP[val_fan_mode]
            _LOGGER.debug("PyDreoAC(%s):handle_server_update - fan_mode: %s --> %s", self, self._fan_mode, val_fan_mode)
            self._fan_mode = val_fan_mode

        val_osc_mode = self.get_server_update_key_value(message, OSCMODE_KEY)
        if isinstance(val_osc_mode, int):
            self._osc_mode = val_osc_mode

        val_muteon = self.get_server_update_key_value(message, MUTEON_KEY)
        if isinstance(val_muteon, bool):
            self._mute_on = val_muteon

        val_devon = self.get_server_update_key_value(message, DEVON_KEY)
        if isinstance(val_devon, bool):
            self._dev_on = val_devon

        val_timeron = self.get_server_update_key_value(message, TIMERON_KEY)
        if isinstance(val_timeron, int):
            self._timer_on = val_timeron

        val_cooldown = self.get_server_update_key_value(message, COOLDOWN_KEY)
        if isinstance(val_cooldown, int):
            self._cooldown = val_cooldown

        val_ptc_on = self.get_server_update_key_value(message, PTCON_KEY)
        if isinstance(val_ptc_on, bool):
            self._ptc_on = val_ptc_on

        val_lighton = self.get_server_update_key_value(message, LIGHTON_KEY)
        if isinstance(val_lighton, bool):
            self._display_auto_off = not val_lighton

        val_ctlstatus = self.get_server_update_key_value(message, CTLSTATUS_KEY)
        if isinstance(val_ctlstatus, str):
            self._ctlstatus = val_ctlstatus

        val_timer_off = self.get_server_update_key_value(message, TIMEROFF_KEY)
        if isinstance(val_timer_off, int):
            self._timer_off = val_timer_off

        val_childlockon = self.get_server_update_key_value(message, CHILDLOCKON_KEY)
        if isinstance(val_childlockon, bool):
            self._childlockon = val_childlockon

        val_tempoffset = self.get_server_update_key_value(message, TEMPOFFSET_KEY)
        if isinstance(val_tempoffset, int):
            self._tempoffset = val_tempoffset

        val_fixed_conf = self.get_server_update_key_value(message, FIXEDCONF_KEY)
        if isinstance(val_fixed_conf, str):
            self._fixed_conf = val_fixed_conf

        val_work_time = self.get_server_update_key_value(message, WORK_TIME)
        if isinstance(val_work_time, int):
            self.work_time = val_work_time

        val_temp_target_reached = self.get_server_update_key_value(message, TEMP_TARGET_REACHED)
        if isinstance(val_work_time, int):
            self.temp_target_reached = "Yes" if val_temp_target_reached > 0 else "No"

    def set_ha_temperature_unit_is_celsius(self, is_celsius: bool) -> None:
        """Set whether Home Assistant uses Celsius (called by HA climate entity)"""
        self._ha_uses_celsius = is_celsius
