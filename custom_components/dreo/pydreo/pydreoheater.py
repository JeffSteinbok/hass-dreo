"""Dreo API for controling heaters."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    HTALEVEL_KEY,
    TEMPERATURE_KEY,
    MODE_KEY,
    OSCON_KEY,
    OSCANGLE_KEY,
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
    HEATER_MODE_COOLAIR,
    HEATER_MODE_HOTAIR,
    HEATER_MODE_OFF,
    HEATER_MODES,
    MODE_LEVEL_MAP,
    LEVEL_MODE_MAP,
    TemperatureUnit,
    HeaterOscillationAngles,
    FAN_ON,
    FAN_OFF
)

from .pydreobasedevice import PyDreoBaseDevice
from .models import DreoDeviceDetails, HEAT_RANGE, ECOLEVEL_RANGE

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo

class PyDreoHeater(PyDreoBaseDevice):
    """Base class for Dreo heater API Calls."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize heater devices."""
        super().__init__(device_definition, details, dreo)

        self._mode = None
        self._htalevel = None
        self._oscon = None
        self._oscangle = None
        self._temperature = None
        self._mute_on = None
        self._fixed_conf = None
        self._dev_on = None
        self._timer_on = None
        self._cooldown = None
        self._ptc_on = None
        self._light_on = None
        self._ctlstatus = None
        self._timer_off = None
        self._ecolevel = None
        self._childlockon = None
        self._tempoffset = None
        self._fixed_conf = None

        self._timeron = None

    @property
    def poweron(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._is_on

    @poweron.setter
    def poweron(self, value: bool):
        """Set if the heater is on or off"""
        _LOGGER.debug("PyDreoHeater:poweron.setter - %s", value)
        self._send_command(POWERON_KEY, value)

    @property
    def heat_range(self):
        """Get the heat range"""
        return self._device_definition.device_ranges[HEAT_RANGE]

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
        _LOGGER.debug("PyDreoHeater:dev_on.setter - %s", value)
        self._send_command(DEVON_KEY, value)

    @property
    def htalevel(self):
        """Return the current heat level"""
        return self._htalevel

    @htalevel.setter
    def htalevel(self, htalevel : int) :
        """Set the heat level."""
        _LOGGER.debug("PyDreoHeater:htalevel.setter(%s, %s)", self.name, htalevel)
        if (self._device_definition.device_ranges[HEAT_RANGE][0] > htalevel > self._device_definition.device_ranges[HEAT_RANGE][1]):
            _LOGGER.error("Heat level %s is not in the acceptable range: %s",
                            htalevel,
                            self._device_definition.device_ranges[HEAT_RANGE])
            return
        self.mode = HEATER_MODE_HOTAIR
        self._send_command(HTALEVEL_KEY, htalevel)

    @property 
    def ecolevel_range(self):
        """Get the ecolevel range"""
        return self._device_definition.device_ranges[ECOLEVEL_RANGE]

    @property
    def ecolevel(self):
        """Return the current target temperature"""
        return self._ecolevel

    @ecolevel.setter
    def ecolevel(self, ecolevel : int):
        """Set the target temperature."""
        _LOGGER.debug("PyDreoHeater:ecolevel(%s)", ecolevel)
        if self._device_definition.device_ranges[ECOLEVEL_RANGE][0] > ecolevel > self._device_definition.device_ranges[ECOLEVEL_RANGE][1]:
            _LOGGER.error("Target Temperature %s is not in the acceptable range: %s",
                            ecolevel,
                            self._device_definition.device_ranges[ECOLEVEL_RANGE])
            return
        self._send_command(ECOLEVEL_KEY, ecolevel)

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        return LEVEL_MODE_MAP[self._htalevel]

    @property
    def mode(self):
        """Return the current preset mode."""
        return self._mode

    @preset_mode.setter
    def preset_mode(self, level: str) -> None:
        _LOGGER.debug("PyDreoHeater:set_preset_mode(%s)", level)
        if level in self.preset_modes:
            # Don't need self.mode = HEATER_MODE_HOTAIR because the htalevel setter will set the mode
            self.htalevel = MODE_LEVEL_MAP[level]
        else:
            _LOGGER.error("Preset mode %s is not in the acceptable list: %s",
                            level,
                            self._device_definition.preset_modes)
            raise ValueError(f"preset_mode must be one of: {self.preset_modes}")

    @mode.setter
    def mode(self, mode: str) -> None:
        _LOGGER.debug("PyDreoHeater:mode(%s) --> %s", self.name, mode)
        self._send_command(MODE_KEY, mode)

    @property
    def fan_mode(self) -> str:
        """Return the current fan mode - if on, it means that we're in 'coolair' mode"""
        if self._mode is not None:
            return FAN_ON if self._mode == HEATER_MODE_COOLAIR else FAN_OFF

    @fan_mode.setter
    def fan_mode(self, mode: bool) -> None:
        """Set coolair mode if requested"""
        # TODO: set the state back to what it was before it was turned on (i.e., hotair or eco)
        self.mode = HEATER_MODE_COOLAIR if mode is True else HEATER_MODE_HOTAIR

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
    def oscon(self) -> bool:
        """Returns `True` if oscillation is on."""
        return self._oscon

    @oscon.setter
    def oscon(self, value: bool) -> None:

        """Enable or disable oscillation"""
        _LOGGER.debug("PyDreoHeater:oscon.setter(%s) -> %s", self.name, value)
        if self._oscon is not None:
            self._send_command(OSCON_KEY, value)
        else:
            _LOGGER.error("Attempting to set oscillation on on a device that doesn't support it.")
            raise ValueError("Attempting to set oscillation on on a device that doesn't support it.")

    @property
    def oscangle(self) -> HeaterOscillationAngles:
        """Get the oscillation angle"""
        return self._oscangle

    @oscangle.setter
    def oscangle(self, value: int) -> None:
        "Set the oscillation angle. I assume 0 means it oscillates"
        _LOGGER.debug("PyDreoHeater:oscangle.setter(%s) -> %d", self.name, value)
        if self._oscangle is not None:
            self._send_command(OSCANGLE_KEY, value)
        else:
            _LOGGER.error("Attempting to set oscillation angle on a device that doesn't support it.")
            return

    @property
    def ptcon(self) -> bool:
        """Returns `True` if PTC is on."""
        return self._ptc_on

    @ptcon.setter
    def ptcon(self, value: bool) -> None:

        """Enable or disable PTC"""
        _LOGGER.debug("PyDreoHeater:ptcon.setter(%s) --> %s", self.name, value)
        if self._ptc_on is not None:
            self._send_command(PTCON_KEY, value)
        else:
            _LOGGER.error("Attempting to set PTC on on a device that doesn't support it.")
            return

    @property
    def lighton(self) -> bool:
        """Returns `True` if Display Auto off is OFF."""
        return not self._light_on

    @lighton.setter
    def lighton(self, value: bool) -> None:

        """Enable or disable light"""
        _LOGGER.debug("PyDreoHeater:lighton.setter(%s) --> %s", self.name, value)
        if self._light_on is not None:
            self._send_command(LIGHTON_KEY, not value)
        else:
            _LOGGER.error("Attempting to set Display Auto Off on a device that doesn't support it.")
            return

    @property
    def ctlstatus(self) -> bool:
        """Returns `True` if ctlstatus is on."""
        return self._ctlstatus

    @ctlstatus.setter
    def ctlstatus(self, value: bool) -> None:

        """Enable or disable ctlstatus"""
        _LOGGER.debug("PyDreoHeater:ctlstatus.setter(%s) --> %s", self.name, value)
        if self._ctlstatus is not None:
            self._send_command(CTLSTATUS_KEY, value)
        else:
            _LOGGER.error("Attempting to set ctlstatus on on a device that doesn't support it.")
            return

    @property
    def childlockon(self) -> bool:
        """Returns `True` if Child Lock is on."""
        return self._childlockon

    @childlockon.setter
    def childlockon(self, value: bool) -> None:

        """Enable or disable Child Lock"""
        _LOGGER.debug("PyDreoHeater:childlockon.setter(%s) --> %s", self.name, value)
        if self._childlockon is not None:
            self._send_command(CHILDLOCKON_KEY, value)
        else:
            _LOGGER.error("Attempting to set child lock on on a device that doesn't support it.")
            return

    @property
    def panel_sound(self) -> bool:
        """Is the panel sound on"""
        if self._mute_on is not None:
            return not self._mute_on
        return None

    @panel_sound.setter
    def panel_sound(self, value: bool) -> None:
        """Set if the panel sound"""
        _LOGGER.debug("PyDreoHeater:panel_sound.setter(%s) --> %s", self.name, value)

        if self._mute_on is not None and value is not None:
            _LOGGER.debug("Setting _muteon to %s", not value)
            self._send_command(MUTEON_KEY, not value)
        else:
            _LOGGER.error("Attempting to set panel_sound on a device that doesn't support.")
            return


    def update_state(self, state: dict) :
        """Process the state dictionary from the REST API."""
        super().update_state(state) # handles _is_on

        _LOGGER.debug("update_state: %s", state)
        self._htalevel = self.get_state_update_value(state, HTALEVEL_KEY)
        if self._htalevel is None:
            _LOGGER.error("Unable to get heat level from state. Check debug logs for more information.")

        self._temperature = self.get_state_update_value(state, TEMPERATURE_KEY)
        self._mode = self.get_state_update_value(state, MODE_KEY)
        self._oscon = self.get_state_update_value(state, OSCON_KEY)
        self._oscangle = self.get_state_update_value(state, OSCANGLE_KEY)
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


    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("PyDreoHeater:handle_server_update(%s): %s", self.name, message)

        val_htalevel = self.get_server_update_key_value(message, HTALEVEL_KEY)
        if isinstance(val_htalevel, int):
            self._htalevel = val_htalevel

        # no base class method to handle _is_on
        val_power_on = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_power_on, bool):
            self._is_on = val_power_on
            if not self._is_on:
                self._mode = HEATER_MODE_OFF

        val_temperature = self.get_server_update_key_value(message, TEMPERATURE_KEY)
        if isinstance(val_temperature, int):
            self._temperature = val_temperature

        # Reported mode can be an empty string if the heater is off. Deal with that by
        # explicitly setting that to off.
        val_mode = self.get_server_update_key_value(message, MODE_KEY)
        if isinstance(val_mode, str):
            self._mode = val_mode if val_mode in HEATER_MODES else HEATER_MODE_OFF

        val_oscon = self.get_server_update_key_value(message, OSCON_KEY)
        if isinstance(val_oscon, bool):
            self._oscon = val_oscon

        val_oscangle = self.get_server_update_key_value(message, OSCANGLE_KEY)
        if isinstance(val_oscangle, int):
            self._oscangle = val_oscangle

        val_muteon = self.get_server_update_key_value(message, MUTEON_KEY)
        if isinstance(val_muteon, bool):
            self._mute_on = val_muteon

        val_devon = self.get_server_update_key_value(message, DEVON_KEY)
        if isinstance(val_devon, bool):
            self._dev_on = val_devon

        # TODO: This seems wrong; unsure if we need to parse DU out of this like we do in the intial state.
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
