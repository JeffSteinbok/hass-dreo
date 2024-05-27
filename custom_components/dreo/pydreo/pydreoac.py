"""Dreo API for controlling air conditioners."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    TEMPERATURE_KEY,
    TARGET_TEMPERATURE_KEY,
    MODE_KEY,
    OSCMODE_KEY,
    # OSCON_KEY, TODO remove
    # OSCANGLE_KEY, TODO remove
    MUTEON_KEY,
    POWERON_KEY,
    DEVON_KEY,
    TIMERON_KEY,
    COOLDOWN_KEY,
    PTCON_KEY,
    LIGHTON_KEY,
    CTLSTATUS_KEY,
    TIMEROFF_KEY,
    ECOLEVEL_KEY,
    CHILDLOCKON_KEY,
    TEMPOFFSET_KEY,
    FIXEDCONF_KEY,
    AC_MODE_OFF,
    AC_MODE_COOL,
    AC_MODE_FAN,
    AC_MODE_DRY,
    AC_MODE_ECO,
    TemperatureUnit,
    WINDLEVEL_KEY,
    HUMIDITY_KEY,
    TARGET_HUMIDITY_KEY,
)

from homeassistant.components.climate import (
    FAN_ON,
    FAN_OFF,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
)

AC_MODES = [
    1, # AC_MODE_COOL,
    2, # AC_MODE_DRY,
    3, # AC_MODE_FAN,
    5, # AC_MODE_ECO
]

AC_FAN_MODE_MAP = {
    1 : FAN_LOW,
    2 : FAN_MEDIUM,
    3 : FAN_HIGH,
    4 : FAN_AUTO,
    FAN_LOW : 1,
    FAN_MEDIUM : 2,
    FAN_HIGH : 3,
    FAN_AUTO : 4,
}

AC_OSC_ON = 2
AC_OSC_OFF = 0

from .pydreobasedevice import PyDreoBaseDevice
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo

class PyDreoAC(PyDreoBaseDevice):
    """Base class for Dreo air conditioner API Calls."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air conditioner devices."""
        super().__init__(device_definition, details, dreo)

        self._mode = None # Fan Mode # TODO
        self._temperature = None
        self._target_temperature = None
        self._mute_on = None
        self._fixed_conf = None
        self._dev_on = None
        self._timer_on = None
        self._cooldown = None
        self._ptc_on = None
        self._light_on = None
        self._ctlstatus = None
        self._timer_off = None
        self._ecolevel = None # TODO
        self._childlockon = None
        self._tempoffset = None
        self._fixed_conf = None
        self.preset_mode = None # TODO

        self._vertically_oscillating = None # TODO
        self._humidity = None # TODO
        self._target_humidity = None # TODO
        self._osc_mode = None # TODO
        self._fan_mode = None # TODO

    def __repr__(self):
        # Representation string of object.
        return "<{0}:{1}:{2}>".format(
            self.__class__.__name__, self._device_id, self._name
        )

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
        _LOGGER.debug("PyDreoAC:dev_on.setter - %s", value)
        self._send_command(DEVON_KEY, value)

    @property
    def ecolevel(self):
        """Return the current target temperature"""
        return self._ecolevel

    @ecolevel.setter
    def ecolevel(self, ecolevel: int):
        """Set the target temperature."""
        _LOGGER.debug("PyDreoAC:ecolevel(%s)", ecolevel)
        self._send_command(ECOLEVEL_KEY, ecolevel)

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
        self._send_command(WINDLEVEL_KEY, mode)

    @property
    def temperature(self):
        """Get the temperature"""
        return self._temperature

    @property
    def temperature_units(self) -> TemperatureUnit:
        """Get the temperature units."""
        # Auto-detect based on range.
        if self._temperature is not None:
            if self._temperature > 50:
                return TemperatureUnit.FAHRENHEIT

        return TemperatureUnit.CELCIUS

    @property
    def target_temperature(self):
        """Get the temperature"""
        return self._target_temperature
    
    @property
    def humidity(self):
        """Get the humidity"""
        return self._humidity
    @property
    def target_humidity(self):
        """Get the target_humidity"""
        return self._target_humidity

    @property
    def oscon(self) -> bool:
        """Returns `True` if oscillation is on."""
        return self._osc_mode is not None and self._osc_mode > 0

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
    def lighton(self) -> bool:
        """Returns `True` if Display Auto off is OFF."""
        return not self._light_on

    @lighton.setter
    def lighton(self, value: bool) -> None:
        """Enable or disable light"""
        _LOGGER.debug("PyDreoAC:lighton.setter(%s) --> %s", self.name, value)
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

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        super().update_state(state)  # handles _is_on

        _LOGGER.debug("PyDreoAC(%s):update_state: %s", self.name, state)
        self._temperature = self.get_state_update_value(state, TEMPERATURE_KEY)
        self._target_temperature = self.get_state_update_value(state, TARGET_TEMPERATURE_KEY)
        self._mode = self.get_state_update_value(state, MODE_KEY)
        self._oscon = self.get_state_update_value(state, OSCMODE_KEY)
        self._mute_on = self.get_state_update_value(state, MUTEON_KEY)
        self._dev_on = self.get_state_update_value(state, DEVON_KEY)
        timeron = self.get_state_update_value(state, TIMERON_KEY)
        self._timer_on = timeron["du"]
        self._cooldown = self.get_state_update_value(state, COOLDOWN_KEY)
        self._ptc_on = self.get_state_update_value(state, PTCON_KEY)
        self._light_on = self.get_state_update_value(state, LIGHTON_KEY)
        self._ctlstatus = self.get_state_update_value(state, CTLSTATUS_KEY)
        timeroff = self.get_state_update_value(state, TIMEROFF_KEY)
        self._timer_off = timeroff["du"]
        self._ecolevel = self.get_state_update_value(state, ECOLEVEL_KEY)
        self._childlockon = self.get_state_update_value(state, CHILDLOCKON_KEY)
        self._tempoffset = self.get_state_update_value(state, TEMPOFFSET_KEY)
        self._fixed_conf = self.get_state_update_value(state, FIXEDCONF_KEY)
        self._humidity = self.get_state_update_value(state, HUMIDITY_KEY)
        self._target_humidity = self.get_state_update_value(state, TARGET_HUMIDITY_KEY)
        #TODO ecopauserate, worktime

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
            self._target_temperature = val_target_temperature

        # Reported mode can be an empty string if the AC is off. Deal with that by
        # explicitly setting that to off.
        val_mode = self.get_server_update_key_value(message, MODE_KEY)
        if isinstance(val_mode, int):
            self._mode = val_mode if val_mode in AC_MODES else AC_MODE_OFF
            _LOGGER.debug("PyDreoAC:handle_server_update - mode is %s", self._mode)

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
            self._timeron = val_timeron

        val_cooldown = self.get_server_update_key_value(message, COOLDOWN_KEY)
        if isinstance(val_cooldown, int):
            self._cooldown = val_cooldown

        val_ptc_on = self.get_server_update_key_value(message, PTCON_KEY)
        if isinstance(val_ptc_on, bool):
            self._ptc_on = val_ptc_on

        val_light_on = self.get_server_update_key_value(message, LIGHTON_KEY)
        if isinstance(val_light_on, bool):
            self._light_on = val_light_on

        val_ctlstatus = self.get_server_update_key_value(message, CTLSTATUS_KEY)
        if isinstance(val_ctlstatus, str):
            self._ctlstatus = val_ctlstatus

        val_timer_off = self.get_server_update_key_value(message, TIMEROFF_KEY)
        if isinstance(val_timer_off, int):
            self._timer_off = val_timer_off

        val_ecolevel = self.get_server_update_key_value(message, ECOLEVEL_KEY)
        if isinstance(val_ecolevel, int):
            self._ecolevel = val_ecolevel

        val_childlockon = self.get_server_update_key_value(message, CHILDLOCKON_KEY)
        if isinstance(val_childlockon, bool):
            self._childlockon = val_childlockon

        val_tempoffset = self.get_server_update_key_value(message, TEMPOFFSET_KEY)
        if isinstance(val_tempoffset, int):
            self._tempoffset = val_tempoffset

        val_fixed_conf = self.get_server_update_key_value(message, FIXEDCONF_KEY)
        if isinstance(val_fixed_conf, str):
            self._fixed_conf = val_fixed_conf
