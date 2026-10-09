"""Dreo API for controling heaters."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    HTALEVEL_KEY,
    TEMPERATURE_KEY,
    MODE_KEY,
    OSCON_KEY,
    OSCANGLE_KEY,
    OSCMODE_KEY,
    MUTEON_KEY,
    POWERON_KEY,
    DEVON_KEY,
    TIMERON_KEY,
    COOLDOWN_KEY,
    PTCON_KEY,
    LIGHTON_KEY,
    AIRFLOWMODE_KEY,
    WINOPENON_KEY,
    RGBON_KEY,
    RGB_BRI,
    MCU_FIRMWARE_VERSION_KEY,
    MCU_HARDWARE_MODEL_KEY,
    CTLSTATUS_KEY,
    TIMEROFF_KEY,
    ECOLEVEL_KEY,
    CHILDLOCKON_KEY,
    TEMPOFFSET_KEY,
    FIXEDCONF_KEY,
    HTAMODE_KEY,
    COOLMODE_KEY,
    COOLLEVEL_KEY,
    LIGHTMODE_KEY,
    HORIZONTAL_OSCILLATION_KEY,
    HORIZONTAL_OSCILLATION_ANGLE_KEY,
    HORIZONTAL_ANGLE_ADJ_KEY,
    DreoHeaterMode,
    DreoHeaterFunction,
    DreoHeaterHeatMode,
    DreoHeaterFanMode,
    TemperatureUnit,
    HeaterOscillationAngles,
    HEATER_OSCMODE_SWING_MAP,
    HEATER_SWING_OSCMODE_MAP,
    SWING_OFF,
)

from .pydreobasedevice import PyDreoBaseDevice
from .models import DreoHeaterDeviceDetails, HEAT_RANGE, ECOLEVEL_RANGE, TEMPERATURE_OFFSET_RANGE, COOL_RANGE

_LOGGER = logging.getLogger(__name__)

# "airflowmode" values (checked on a DR-HSH040S): direct heat from the front outlet only,
# or "360° airflow" (as the Dreo app calls it) with the top raised so heat comes out all around.
AIRFLOWMODE_DIRECT = 1
AIRFLOWMODE_360 = 2

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoHeater(PyDreoBaseDevice):
    """Base class for Dreo heater API Calls."""

    def __init__(self, device_definition: DreoHeaterDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize heater devices."""
        super().__init__(device_definition, details, dreo)

        self._heaterDeviceDefinition: DreoHeaterDeviceDetails = device_definition
        self._mode = None
        self._htalevel = None
        self._oscon = None
        self._oscangle = None
        self._oscmode = None
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
        self._airflowmode = None
        self._winopenon = None
        self._rgbon = None
        self._rgbbri = None
        self._mcu_firmware_version = None
        self._mcu_hardware_model = None

        self._htalevel_range = None

        # Tower fan/heater combos (DR-HSH016S): the function (heat/fan) and heat sub-mode arrive as
        # integers and are folded into _mode; the fan function has its own mode and speed level.
        self._function = None
        self._htamode = None
        self._coolmode = None
        self._coollevel = None
        self._coollevel_range = None
        self._lightmode = None
        self._hoscon = None
        self._hoscangle = None
        self._hangleadj = None

        # Check if the device has a speed range defined in the device definition
        # If not, parse the speed range from the details
        if device_definition.device_ranges is not None and HEAT_RANGE in device_definition.device_ranges:
            self._htalevel_range = device_definition.device_ranges[HEAT_RANGE]
        if device_definition.device_ranges is not None and COOL_RANGE in device_definition.device_ranges:
            self._coollevel_range = device_definition.device_ranges[COOL_RANGE]

        self._timeron = None

    @property
    def poweron(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._is_on

    @poweron.setter
    def poweron(self, value: bool):
        """Set if the heater is on or off"""
        _LOGGER.debug("poweron: poweron.setter - %s", value)
        self._send_command(POWERON_KEY, value)

    @property
    def htalevel_range(self):
        """Get the heat range"""
        return self._htalevel_range

    @property
    def modes(self) -> list[DreoHeaterMode]:
        """Get the list of supported modes"""
        return self._heaterDeviceDefinition.modes

    @property
    def devon(self):
        """Returns `True` if devon is true, `False` otherwise. Whatever devon is"""
        return self._dev_on

    @devon.setter
    def devon(self, value: bool):
        _LOGGER.debug("devon: dev_on.setter - %s", value)
        if self._dev_on == value:
            _LOGGER.debug("devon: devon - value already %s, skipping command", value)
            return
        self._send_command(DEVON_KEY, value)

    @property
    def htalevel(self):
        """Return the current heat level"""
        return self._htalevel

    @htalevel.setter
    def htalevel(self, htalevel: int):
        """Set the heat level."""
        htalevel = int(htalevel)  # ensure it's an int
        _LOGGER.debug("htalevel: htalevel.setter(%s, %s)", self.name, htalevel)
        if not (self._device_definition.device_ranges[HEAT_RANGE][0] <= htalevel <= self._device_definition.device_ranges[HEAT_RANGE][1]):
            _LOGGER.error("htalevel: Heat level %s is not in the acceptable range: %s", htalevel, self._device_definition.device_ranges[HEAT_RANGE])
            return
        if self._htalevel == htalevel:
            _LOGGER.debug("htalevel: htalevel - value already %s, skipping command", htalevel)
            return
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
    def ecolevel(self, ecolevel: int):
        """Set the target temperature."""
        _LOGGER.debug("ecolevel: ecolevel(%s)", ecolevel)
        if not (self._device_definition.device_ranges[ECOLEVEL_RANGE][0] <= ecolevel <= self._device_definition.device_ranges[ECOLEVEL_RANGE][1]):
            _LOGGER.error(
                "ecolevel: Target Temperature %s is not in the acceptable range: %s", ecolevel, self._device_definition.device_ranges[ECOLEVEL_RANGE]
            )
            return
        if self._ecolevel == ecolevel:
            _LOGGER.debug("ecolevel: ecolevel - value already %s, skipping command", ecolevel)
            return
        self._send_command(ECOLEVEL_KEY, ecolevel)

    @property
    def mode(self):
        """Return the current mode."""
        return self._mode

    @mode.setter
    def mode(self, value: DreoHeaterMode) -> None:
        if value in self.modes:
            if self.is_fan_heater:
                params = self._function_params(value)
                if params is None:
                    _LOGGER.debug("mode: mode - %s is not a function of a tower fan/heater combo, use poweron", value)
                    return
                # Compare the raw function and heat sub-mode, not the derived mode: an unknown value reads as
                # power heat but must still be replaced when power heat is requested
                if self._function == params[MODE_KEY] and self._htamode == params.get(HTAMODE_KEY, self._htamode):
                    _LOGGER.debug("mode: mode - value already %s, skipping command", value)
                    return
                self._send_command_batch(params)
            else:
                if self._mode == value:
                    _LOGGER.debug("mode: mode - value already %s, skipping command", value)
                    return
                self._send_command(MODE_KEY, value)
        else:
            raise ValueError(f"Mode {value} is not in the acceptable list: {self.modes}")

    @property
    def temperature(self):
        """Get the temperature"""
        temp = self._temperature
        if temp is not None and self.temperature_offset is not None and not self._heaterDeviceDefinition.temperature_includes_offset:
            temp += self.temperature_offset
        return temp

    @property
    def temperature_offset(self):
        """Get the temperature calibration value"""
        return self._tempoffset

    @temperature_offset.setter
    def temperature_offset(self, value: int) -> None:
        """Set the temperature calibration value, in the device's unit (°F)."""
        _LOGGER.debug("temperature_offset: temperature_offset.setter(%s) --> %s", self.name, value)
        value = int(value)
        offset_range = self.temperature_offset_range
        if offset_range is None:
            _LOGGER.error("temperature_offset: Attempting to set temperature offset on a device that doesn't support it.")
            return
        if not offset_range[0] <= value <= offset_range[1]:
            _LOGGER.error("temperature_offset: Offset %s is not in the acceptable range: %s", value, offset_range)
            return
        if self._tempoffset == value:
            _LOGGER.debug("temperature_offset: temperature_offset - value already %s, skipping command", value)
            return
        self._send_command(TEMPOFFSET_KEY, value)

    @property
    def temperature_offset_range(self) -> tuple | None:
        """Get the settable temperature offset range in °F, on models that support setting it."""
        return (self._device_definition.device_ranges or {}).get(TEMPERATURE_OFFSET_RANGE)

    @property
    def temperature_units(self) -> TemperatureUnit:
        """Get the temperature units."""
        # I'm not sure how the API returns in other regions, so I'm just auto-detecting
        # based on some reasonable range.

        # Going to return Celsius as the default.  None of this matters if there is no
        # temperature returned anyway
        if self._temperature is not None:
            if self._temperature > 50:
                return TemperatureUnit.FAHRENHEIT

        return TemperatureUnit.CELSIUS

    @property
    def oscon(self) -> bool:
        """Returns `True` if oscillation is on."""
        return self._oscon

    @oscon.setter
    def oscon(self, value: bool) -> None:
        """Enable or disable oscillation"""
        _LOGGER.debug("oscon: oscon.setter(%s) -> %s", self.name, value)
        if self._oscon is not None:
            if self._oscon == value:
                _LOGGER.debug("oscon: oscon - value already %s, skipping command", value)
                return
            self._send_command(OSCON_KEY, value)
        else:
            _LOGGER.error("oscon: Attempting to set oscillation on on a device that doesn't support it.")
            raise ValueError("Attempting to set oscillation on on a device that doesn't support it.")

    @property
    def oscangle(self) -> HeaterOscillationAngles:
        """Get the oscillation angle"""
        return self._oscangle

    @oscangle.setter
    def oscangle(self, value: int) -> None:
        "Set the oscillation angle. I assume 0 means it oscillates"
        _LOGGER.debug("oscangle: oscangle.setter(%s) -> %d", self.name, value)
        if self._oscangle is not None:
            if self._oscangle == value:
                _LOGGER.debug("oscangle: oscangle - value already %s, skipping command", value)
                return
            self._send_command(OSCANGLE_KEY, value)
        else:
            _LOGGER.error("oscangle: Attempting to set oscillation angle on a device that doesn't support it.")
            return

    @property
    def oscmode(self) -> int | None:
        """Get the oscmode integer value (used by newer heater firmware)."""
        return self._oscmode

    @oscmode.setter
    def oscmode(self, value: int) -> None:
        """Set the oscmode value."""
        _LOGGER.debug("oscmode: oscmode.setter(%s) -> %s", self.name, value)
        if self._oscmode is not None:
            if self._oscmode == value:
                _LOGGER.debug("oscmode: oscmode - value already %s, skipping command", value)
                return
            self._send_command(OSCMODE_KEY, value)
        else:
            _LOGGER.error("oscmode: Attempting to set oscmode on a device that doesn't support it.")
            raise ValueError("Attempting to set oscmode on a device that doesn't support it.")

    @property
    def ptcon(self) -> bool | None:
        """Returns `True` if PTC is on."""
        if self._heaterDeviceDefinition.ptc_read_only:
            return None
        return self._ptc_on

    @property
    def heating(self) -> bool | None:
        """Returns `True` while the heating element is drawing power, on models where PTC is read-only."""
        if not self._heaterDeviceDefinition.ptc_read_only:
            return None
        return self._ptc_on

    @ptcon.setter
    def ptcon(self, value: bool) -> None:
        """Enable or disable PTC"""
        _LOGGER.debug("ptcon: ptcon.setter(%s) --> %s", self.name, value)
        if self._heaterDeviceDefinition.ptc_read_only:
            _LOGGER.error("ptcon: PTC is read-only on this device.")
            return
        if self._ptc_on is not None:
            if self._ptc_on == value:
                _LOGGER.debug("ptcon: ptcon - value already %s, skipping command", value)
                return
            self._send_command(PTCON_KEY, value)
        else:
            _LOGGER.error("ptcon: Attempting to set PTC on on a device that doesn't support it.")
            return

    @property
    def display_auto_off(self) -> bool | None:
        """Returns `True` if Display Auto Off is enabled (the device reports it inverted as `lighton`)."""
        # Models with has_display_light use lighton as a plain display on/off, exposed by display_light.
        if self._light_on is None or self._heaterDeviceDefinition.has_display_light:
            return None
        return not self._light_on

    @display_auto_off.setter
    def display_auto_off(self, value: bool) -> None:
        """Enable or disable display auto-off"""
        _LOGGER.debug("display_auto_off: display_auto_off.setter(%s) --> %s", self.name, value)
        if self.display_auto_off is not None:
            if self._light_on == (not value):
                _LOGGER.debug("display_auto_off: display_auto_off - value already %s, skipping command", value)
                return
            self._send_command(LIGHTON_KEY, not value)
        else:
            _LOGGER.error("display_auto_off: Attempting to set Display Auto Off on a device that doesn't support it.")
            return

    @property
    def display_light(self) -> bool | None:
        """Returns `True` if the display is on, on models that expose it."""
        if not self._heaterDeviceDefinition.has_display_light:
            return None
        return self._light_on

    @display_light.setter
    def display_light(self, value: bool) -> None:
        """Turn the display on or off."""
        _LOGGER.debug("display_light: display_light.setter(%s) --> %s", self.name, value)
        if self.display_light is None:
            _LOGGER.error("display_light: Attempting to set display light on a device that doesn't support it.")
            return
        if self.display_light == value:
            _LOGGER.debug("display_light: display_light - value already %s, skipping command", value)
            return
        self._send_command(LIGHTON_KEY, value)

    @property
    def airflow_360(self) -> bool | None:
        """Returns `True` if 360° airflow is on: the top is raised and heat comes out all around."""
        if self._airflowmode is None:
            return None
        return self._airflowmode == AIRFLOWMODE_360

    @airflow_360.setter
    def airflow_360(self, value: bool) -> None:
        """Turn 360° airflow on, or off for direct heat from the front outlet only."""
        _LOGGER.debug("airflow_360: airflow_360.setter(%s) --> %s", self.name, value)
        if self._airflowmode is None:
            _LOGGER.error("airflow_360: Attempting to set 360° airflow on a device that doesn't support it.")
            return
        if self.airflow_360 == value:
            _LOGGER.debug("airflow_360: airflow_360 - value already %s, skipping command", value)
            return
        self._send_command(AIRFLOWMODE_KEY, AIRFLOWMODE_360 if value else AIRFLOWMODE_DIRECT)

    @property
    def rgblevel(self) -> int | None:
        """Ambient light brightness level (rgbbri), or 0 when the light is off."""
        if self._heaterDeviceDefinition.ambient_light_levels is None or self._rgbon is None:
            return None
        if not self._rgbon:
            return 0
        return self._rgbbri if self._rgbbri is not None else max(self._heaterDeviceDefinition.ambient_light_levels)

    @rgblevel.setter
    def rgblevel(self, value: int) -> None:
        """Turn the ambient light off (0), or on at the given brightness level."""
        _LOGGER.debug("rgblevel: rgblevel.setter(%s) --> %s", self.name, value)
        if self.rgblevel is None:
            _LOGGER.error("rgblevel: Attempting to set the ambient light on a device that doesn't support it.")
            return
        level = int(value)
        if level > 0 and level != self._rgbbri:
            self._send_command(RGB_BRI, level)
        if self._rgbon != (level > 0):
            self._send_command(RGBON_KEY, level > 0)

    @property
    def window_detection(self) -> bool | None:
        """Returns `True` if open window detection is enabled."""
        return self._winopenon

    @window_detection.setter
    def window_detection(self, value: bool) -> None:
        """Enable or disable open window detection."""
        _LOGGER.debug("window_detection: window_detection.setter(%s) --> %s", self.name, value)
        if self._winopenon is None:
            _LOGGER.error("window_detection: Attempting to set window detection on a device that doesn't support it.")
            return
        if self._winopenon == value:
            _LOGGER.debug("window_detection: window_detection - value already %s, skipping command", value)
            return
        self._send_command(WINOPENON_KEY, value)

    @property
    def mcu_firmware_version(self) -> str | None:
        """Get the MCU firmware version."""
        return self._mcu_firmware_version

    @property
    def mcu_hardware_model(self) -> str | None:
        """Get the MCU hardware model."""
        return self._mcu_hardware_model

    @property
    def ctlstatus(self) -> bool:
        """Returns `True` if ctlstatus is on."""
        return self._ctlstatus

    @ctlstatus.setter
    def ctlstatus(self, value: bool) -> None:
        """Enable or disable ctlstatus"""
        _LOGGER.debug("ctlstatus: ctlstatus.setter(%s) --> %s", self.name, value)
        if self._ctlstatus is not None:
            if self._ctlstatus == value:
                _LOGGER.debug("ctlstatus: ctlstatus - value already %s, skipping command", value)
                return
            self._send_command(CTLSTATUS_KEY, value)
        else:
            _LOGGER.error("ctlstatus: Attempting to set ctlstatus on on a device that doesn't support it.")
            return

    @property
    def childlockon(self) -> bool:
        """Returns `True` if Child Lock is on."""
        return self._childlockon

    @childlockon.setter
    def childlockon(self, value: bool) -> None:
        """Enable or disable Child Lock"""
        _LOGGER.debug("childlockon: childlockon.setter(%s) --> %s", self.name, value)
        if self._childlockon is not None:
            if self._childlockon == value:
                _LOGGER.debug("childlockon: childlockon - value already %s, skipping command", value)
                return
            self._send_command(CHILDLOCKON_KEY, value)
        else:
            _LOGGER.error("childlockon: Attempting to set child lock on on a device that doesn't support it.")
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
        _LOGGER.debug("panel_sound: panel_sound.setter(%s) --> %s", self.name, value)

        if self._mute_on is not None and value is not None:
            if self._mute_on == (not value):
                _LOGGER.debug("panel_sound: panel_sound - value already %s, skipping command", value)
                return
            _LOGGER.debug("panel_sound: Setting _muteon to %s", not value)
            self._send_command(MUTEON_KEY, not value)
        else:
            _LOGGER.error("panel_sound: Attempting to set panel_sound on a device that doesn't support.")
            return

    @property
    def is_fan_heater(self) -> bool:
        """Returns `True` for tower fan/heater combos, which report an integer function instead of a mode string."""
        return self._coollevel_range is not None

    def _mode_from_function(self) -> DreoHeaterMode:
        """Derive the heater mode from the function and heat sub-mode of a tower fan/heater combo.

        An unknown function or heat sub-mode (logged by _int_enum) is reported as power heat so the
        climate entity always has a valid mode; the next known report corrects it.
        """
        if self._function == DreoHeaterFunction.FAN:
            return DreoHeaterMode.COOLAIR
        if self._function == DreoHeaterFunction.HEAT and self._htamode == DreoHeaterHeatMode.ECO:
            return DreoHeaterMode.ECO
        return DreoHeaterMode.HOTAIR

    @staticmethod
    def _function_params(mode: DreoHeaterMode) -> dict | None:
        """Translate a heater mode into the function and heat sub-mode keys a tower fan/heater combo expects.

        "off" is not a function; it is handled by poweron, so it has no command.
        """
        if mode == DreoHeaterMode.COOLAIR:
            return {MODE_KEY: DreoHeaterFunction.FAN}
        if mode == DreoHeaterMode.HOTAIR:
            return {MODE_KEY: DreoHeaterFunction.HEAT, HTAMODE_KEY: DreoHeaterHeatMode.POWER}
        if mode == DreoHeaterMode.ECO:
            return {MODE_KEY: DreoHeaterFunction.HEAT, HTAMODE_KEY: DreoHeaterHeatMode.ECO}
        return None

    @property
    def coolmode(self) -> DreoHeaterFanMode | None:
        """Return the fan function sub-mode (normal/natural/sleep/auto) of a tower fan/heater combo."""
        return self._coolmode

    @coolmode.setter
    def coolmode(self, value: DreoHeaterFanMode) -> None:
        """Set the fan function sub-mode."""
        _LOGGER.debug("coolmode: coolmode.setter(%s) --> %s", self.name, value)
        if self._coolmode is None:
            _LOGGER.error("coolmode: Attempting to set fan mode on a device that doesn't support it.")
            raise ValueError("Attempting to set fan mode on a device that doesn't support it.")
        value = DreoHeaterFanMode(value)
        if self._coolmode == value:
            _LOGGER.debug("coolmode: coolmode - value already %s, skipping command", value)
            return
        self._send_command(COOLMODE_KEY, value)

    @property
    def coollevel_range(self):
        """Get the fan speed range of the fan function"""
        return self._coollevel_range

    @property
    def coollevel(self):
        """Return the fan speed of the fan function"""
        return self._coollevel

    @coollevel.setter
    def coollevel(self, coollevel: int):
        """Set the fan speed of the fan function."""
        coollevel = int(coollevel)  # ensure it's an int
        _LOGGER.debug("coollevel: coollevel.setter(%s) --> %s", self.name, coollevel)
        if self._coollevel is None or self._coollevel_range is None:
            _LOGGER.error("coollevel: Attempting to set fan speed on a device that doesn't support it.")
            raise ValueError("Attempting to set fan speed on a device that doesn't support it.")
        if not (self._coollevel_range[0] <= coollevel <= self._coollevel_range[1]):
            _LOGGER.error("coollevel: Fan speed %s is not in the acceptable range: %s", coollevel, self._coollevel_range)
            return
        if self._coollevel == coollevel:
            _LOGGER.debug("coollevel: coollevel - value already %s, skipping command", coollevel)
            return
        self._send_command(COOLLEVEL_KEY, coollevel)

    @property
    def horizontally_oscillating(self) -> bool:
        """Returns `True` if horizontal oscillation is on."""
        return self._hoscon

    @horizontally_oscillating.setter
    def horizontally_oscillating(self, value: bool) -> None:
        """Enable or disable horizontal oscillation"""
        _LOGGER.debug("horizontally_oscillating: horizontally_oscillating.setter(%s) --> %s", self.name, value)
        if self._hoscon is not None:
            if self._hoscon == value:
                _LOGGER.debug("horizontally_oscillating: horizontally_oscillating - value already %s, skipping command", value)
                return
            self._send_command(HORIZONTAL_OSCILLATION_KEY, value)
        else:
            _LOGGER.error("horizontally_oscillating: Attempting to set horizontal oscillation on a device that doesn't support it.")
            return

    @property
    def horizontal_osc_angle_left(self) -> int | None:
        """Get the left bound of the horizontal oscillation range, in degrees"""
        return self._hoscangle[0] if self._hoscangle is not None else None

    @horizontal_osc_angle_left.setter
    def horizontal_osc_angle_left(self, value: int) -> None:
        """Set the left bound of the horizontal oscillation range"""
        self.set_horizontal_oscillation_range(int(value), self.horizontal_osc_angle_right)

    @property
    def horizontal_osc_angle_right(self) -> int | None:
        """Get the right bound of the horizontal oscillation range, in degrees"""
        return self._hoscangle[1] if self._hoscangle is not None else None

    @horizontal_osc_angle_right.setter
    def horizontal_osc_angle_right(self, value: int) -> None:
        """Set the right bound of the horizontal oscillation range"""
        self.set_horizontal_oscillation_range(self.horizontal_osc_angle_left, int(value))

    def set_horizontal_oscillation_range(self, left: int, right: int) -> None:
        """Set the horizontal oscillation range. The device takes "left,right" in degrees, e.g. "-60,60" for 120 degrees.

        Both bounds travel in one key, so the range is kept locally once sent: a left and a right change made
        back to back then compose instead of the second overwriting the first. It is always sent, so a failed
        command can simply be repeated.
        """
        _LOGGER.debug("set_horizontal_oscillation_range(%s) --> %s,%s", self.name, left, right)
        if self._hoscangle is None:
            _LOGGER.error("set_horizontal_oscillation_range: Attempting to set oscillation range on a device that doesn't support it.")
            return
        if left >= right:
            _LOGGER.error("set_horizontal_oscillation_range: Left bound %s must be below the right bound %s", left, right)
            return
        self._send_command(HORIZONTAL_OSCILLATION_ANGLE_KEY, f"{left},{right}")
        self._hoscangle = (left, right)

    @property
    def horizontal_angle(self) -> int | None:
        """Get the fixed horizontal direction used while not oscillating, in degrees"""
        return self._hangleadj

    @horizontal_angle.setter
    def horizontal_angle(self, value: int) -> None:
        """Set the fixed horizontal direction"""
        value = int(value)
        _LOGGER.debug("horizontal_angle: horizontal_angle.setter(%s) --> %s", self.name, value)
        if self._hangleadj is None:
            _LOGGER.error("horizontal_angle: Attempting to set horizontal angle on a device that doesn't support it.")
            return
        if self._hangleadj == value:
            _LOGGER.debug("horizontal_angle: horizontal_angle - value already %s, skipping command", value)
            return
        self._send_command(HORIZONTAL_ANGLE_ADJ_KEY, value)

    @property
    def lightmode(self) -> int | None:
        """Get the display mode: 0 off, 1 on, 2 auto-brightness"""
        return self._lightmode

    @lightmode.setter
    def lightmode(self, value: int) -> None:
        """Set the display mode"""
        value = int(value)
        _LOGGER.debug("lightmode: lightmode.setter(%s) --> %s", self.name, value)
        if self._lightmode is None:
            _LOGGER.error("lightmode: Attempting to set display mode on a device that doesn't support it.")
            return
        if self._lightmode == value:
            _LOGGER.debug("lightmode: lightmode - value already %s, skipping command", value)
            return
        self._send_command(LIGHTMODE_KEY, value)

    @staticmethod
    def _int_enum(enum_type, value):
        """Convert a device integer into the given IntEnum, keeping the raw value if it is not a known member."""
        if value is None:
            return None
        try:
            return enum_type(value)
        except ValueError:
            _LOGGER.warning("_int_enum: Unknown %s value %s", enum_type.__name__, value)
            return value

    @staticmethod
    def _parse_hoscangle(value) -> tuple[int, int] | None:
        """Parse a "left,right" oscillation range string into a tuple of degrees."""
        if not isinstance(value, str) or "," not in value:
            return None
        try:
            left, right = (int(part) for part in value.split(",", 1))
        except ValueError:
            return None
        return (left, right)

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        super().update_state(state)  # handles _is_on

        _LOGGER.debug("update_state: %s", state)
        self._htalevel = self.get_state_update_value(state, HTALEVEL_KEY)
        if self._htalevel is None:
            _LOGGER.error("update_state: Unable to get heat level from state. Check debug logs for more information.")

        self._temperature = self.get_state_update_value(state, TEMPERATURE_KEY)
        mode = self.get_state_update_value(state, MODE_KEY)
        self._htamode = self._int_enum(DreoHeaterHeatMode, self.get_state_update_value(state, HTAMODE_KEY))
        if self.is_fan_heater:
            # Tower fan/heater combo: an integer function plus a heat sub-mode instead of a mode string
            self._function = self._int_enum(DreoHeaterFunction, mode)
            self._mode = self._mode_from_function()
        else:
            self._mode = mode
        self._coolmode = self._int_enum(DreoHeaterFanMode, self.get_state_update_value(state, COOLMODE_KEY))
        self._coollevel = self.get_state_update_value(state, COOLLEVEL_KEY)
        self._lightmode = self.get_state_update_value(state, LIGHTMODE_KEY)
        self._hoscon = self.get_state_update_value(state, HORIZONTAL_OSCILLATION_KEY)
        self._hoscangle = self._parse_hoscangle(self.get_state_update_value(state, HORIZONTAL_OSCILLATION_ANGLE_KEY))
        self._hangleadj = self.get_state_update_value(state, HORIZONTAL_ANGLE_ADJ_KEY)
        self._oscon = self.get_state_update_value(state, OSCON_KEY)
        self._oscangle = self.get_state_update_value(state, OSCANGLE_KEY)
        self._oscmode = self.get_state_update_value(state, OSCMODE_KEY)
        self._mute_on = self.get_state_update_value(state, MUTEON_KEY)
        self._dev_on = self.get_state_update_value(state, DEVON_KEY)
        timeron = self.get_state_update_value(state, TIMERON_KEY)
        self._timer_on = timeron.get("du") if isinstance(timeron, dict) else None
        self._cooldown = self.get_state_update_value(state, COOLDOWN_KEY)
        self._ptc_on = self.get_state_update_value(state, PTCON_KEY)
        self._light_on = self.get_state_update_value(state, LIGHTON_KEY)
        self._ctlstatus = self.get_state_update_value(state, CTLSTATUS_KEY)
        timeroff = self.get_state_update_value(state, TIMEROFF_KEY)
        self._timer_off = timeroff.get("du") if isinstance(timeroff, dict) else None
        self._ecolevel = self.get_state_update_value(state, ECOLEVEL_KEY)
        self._childlockon = self.get_state_update_value(state, CHILDLOCKON_KEY)
        self._tempoffset = self.get_state_update_value(state, TEMPOFFSET_KEY)
        self._airflowmode = self.get_state_update_value(state, AIRFLOWMODE_KEY)
        self._winopenon = self.get_state_update_value(state, WINOPENON_KEY)
        self._rgbon = self.get_state_update_value(state, RGBON_KEY)
        self._rgbbri = self.get_state_update_value(state, RGB_BRI)
        self._mcu_firmware_version = self.get_state_update_value(state, MCU_FIRMWARE_VERSION_KEY)
        self._mcu_hardware_model = self.get_state_update_value(state, MCU_HARDWARE_MODEL_KEY)
        self._fixed_conf = self.get_state_update_value(state, FIXEDCONF_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("handle_server_update: handle_server_update(%s): %s", self.name, message)

        val_htalevel = self.get_server_update_key_value(message, HTALEVEL_KEY)
        if isinstance(val_htalevel, int):
            self._htalevel = val_htalevel

        # no base class method to handle _is_on
        val_power_on = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_power_on, bool):
            self._is_on = val_power_on
            # Do NOT reset _mode to OFF here. The hvac_mode property already returns
            # HVACMode.OFF when _is_on is False, regardless of _mode. Resetting _mode
            # to OFF causes hvac_mode to show OFF after the device powers on if the
            # power-on WebSocket ACK doesn't include the mode (a common occurrence).

        val_temperature = self.get_server_update_key_value(message, TEMPERATURE_KEY)
        if isinstance(val_temperature, int):
            self._temperature = val_temperature

        # Reported mode can be an empty string if the heater is off. Ignore empty
        # mode strings to preserve the last known active mode so that hvac_mode
        # correctly reflects the device state when it powers back on.
        val_mode = self.get_server_update_key_value(message, MODE_KEY)
        if isinstance(val_mode, str) and val_mode:
            self._mode = val_mode if val_mode in self.device_definition.modes else DreoHeaterMode.OFF
        elif self.is_fan_heater and isinstance(val_mode, int) and not isinstance(val_mode, bool):
            self._function = self._int_enum(DreoHeaterFunction, val_mode)
            self._mode = self._mode_from_function()

        val_htamode = self.get_server_update_key_value(message, HTAMODE_KEY)
        if isinstance(val_htamode, int) and not isinstance(val_htamode, bool):
            self._htamode = self._int_enum(DreoHeaterHeatMode, val_htamode)
            if self.is_fan_heater:
                self._mode = self._mode_from_function()

        val_coolmode = self.get_server_update_key_value(message, COOLMODE_KEY)
        if isinstance(val_coolmode, int) and not isinstance(val_coolmode, bool):
            self._coolmode = self._int_enum(DreoHeaterFanMode, val_coolmode)

        val_coollevel = self.get_server_update_key_value(message, COOLLEVEL_KEY)
        if isinstance(val_coollevel, int) and not isinstance(val_coollevel, bool):
            self._coollevel = val_coollevel

        val_lightmode = self.get_server_update_key_value(message, LIGHTMODE_KEY)
        if isinstance(val_lightmode, int) and not isinstance(val_lightmode, bool):
            self._lightmode = val_lightmode

        val_hoscon = self.get_server_update_key_value(message, HORIZONTAL_OSCILLATION_KEY)
        if isinstance(val_hoscon, bool):
            self._hoscon = val_hoscon

        val_hoscangle = self._parse_hoscangle(self.get_server_update_key_value(message, HORIZONTAL_OSCILLATION_ANGLE_KEY))
        if val_hoscangle is not None:
            self._hoscangle = val_hoscangle

        val_hangleadj = self.get_server_update_key_value(message, HORIZONTAL_ANGLE_ADJ_KEY)
        if isinstance(val_hangleadj, int) and not isinstance(val_hangleadj, bool):
            self._hangleadj = val_hangleadj

        val_oscon = self.get_server_update_key_value(message, OSCON_KEY)
        if isinstance(val_oscon, bool):
            self._oscon = val_oscon

        val_oscangle = self.get_server_update_key_value(message, OSCANGLE_KEY)
        if isinstance(val_oscangle, int):
            self._oscangle = val_oscangle

        val_oscmode = self.get_server_update_key_value(message, OSCMODE_KEY)
        if isinstance(val_oscmode, int):
            self._oscmode = val_oscmode

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
            # If PTC (heating element) is on, the device must be powered on
            # This handles cases where the WebSocket update includes ptcon but not poweron
            if val_ptc_on and not self._is_on:
                _LOGGER.debug("handle_server_update: PTC turned on, inferring device is powered on")
                self._is_on = True

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

        val_airflowmode = self.get_server_update_key_value(message, AIRFLOWMODE_KEY)
        if isinstance(val_airflowmode, int):
            self._airflowmode = val_airflowmode

        val_rgbon = self.get_server_update_key_value(message, RGBON_KEY)
        if isinstance(val_rgbon, bool):
            self._rgbon = val_rgbon

        val_rgbbri = self.get_server_update_key_value(message, RGB_BRI)
        if isinstance(val_rgbbri, int):
            self._rgbbri = val_rgbbri

        val_winopenon = self.get_server_update_key_value(message, WINOPENON_KEY)
        if isinstance(val_winopenon, bool):
            self._winopenon = val_winopenon

        val_fixed_conf = self.get_server_update_key_value(message, FIXEDCONF_KEY)
        if isinstance(val_fixed_conf, str):
            self._fixed_conf = val_fixed_conf
