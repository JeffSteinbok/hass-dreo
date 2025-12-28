"""Supports Dreo heaters."""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613

from typing import Any
import logging

from .haimports import *  # pylint: disable=W0401,W0614
from .dreobasedevice import DreoBaseDeviceHA
from .pydreo import (
    PyDreoHeater,
    ECOLEVEL_RANGE,
    ANGLE_OSCANGLE_MAP,
    OSCANGLE_ANGLE_MAP,
)

from .pydreo.constant import DreoHeaterMode

from .const import (
    LOGGER,
    DOMAIN,
)

from homeassistant.components.climate import (
    PRESET_ECO
)

_LOGGER = logging.getLogger(LOGGER)

# Heat level preset modes
PRESET_H1 = "H1"
PRESET_H2 = "H2"
PRESET_H3 = "H3"

# Map Dreo Heater modes to Home Assistant HVAC modes
DREO_HEATER_MODE_TO_HVAC_MODE = {
    DreoHeaterMode.COOLAIR: HVACMode.FAN_ONLY,
    DreoHeaterMode.HOTAIR: HVACMode.HEAT,
    DreoHeaterMode.ECO: HVACMode.HEAT,
    DreoHeaterMode.OFF: HVACMode.OFF,
}

# Map Dreo Heater modes to Home Assistant preset modes
DREO_HEATER_MODE_TO_PRESET = {
    DreoHeaterMode.ECO: PRESET_ECO,
}

# Reverse mapping: preset to Dreo mode
HVAC_PRESET_TO_DREO_HEATER_MODE = {
    PRESET_ECO: DreoHeaterMode.ECO,
}

# Map heat level to preset mode
HEAT_LEVEL_TO_PRESET = {
    1: PRESET_H1,
    2: PRESET_H2,
    3: PRESET_H3,
}

# Reverse mapping: preset to heat level
PRESET_TO_HEAT_LEVEL = {
    PRESET_H1: 1,
    PRESET_H2: 2,
    PRESET_H3: 3,
}

# Implementation of the heater
class DreoHeaterHA(DreoBaseDeviceHA, ClimateEntity):
    """Representation of a Dreo heater as a climate entity."""

    _attr_precision = PRECISION_WHOLE
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_target_temperature = None
    _attr_current_temperature = None
    _attr_name = None
    _attr_has_entity_name = True
    _attr_hvac_mode = HVACMode.OFF
    _attr_hvac_modes = None
    _last_hvac_mode = HVACMode.OFF
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, pyDreoDevice: PyDreoHeater) -> None:
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice
        _LOGGER.info(
            "DreoHeaterHA:__init__(%s) shows pyDreoDevice as: current_temp(%s), target_temp(%s)",
            pyDreoDevice.name,
            pyDreoDevice.temperature,
            pyDreoDevice.ecolevel
        )

        self._attr_name = "Heater"
        self._attr_unique_id = f"{super().unique_id}-{self.device.device_id}"
        self._attr_target_temperature = self.device.ecolevel
        self._attr_current_temperature = self.device.temperature
        self._attr_swing_mode = self.device.device_definition.swing_modes[0] if self.device.device_definition.swing_modes else None
        self._attr_swing_modes = self.device.device_definition.swing_modes
        
        # Map device mode to HVAC mode using new mappings
        self._attr_hvac_mode = DREO_HEATER_MODE_TO_HVAC_MODE.get(DreoHeaterMode(self.device.mode), HVACMode.OFF) if self.device.poweron else HVACMode.OFF
        
        # Build list of unique HVAC modes from device mode_names
        hvac_modes_set = {DREO_HEATER_MODE_TO_HVAC_MODE.get(mode) 
                          for mode in self.device.modes
                          if mode in DREO_HEATER_MODE_TO_HVAC_MODE}
        self._attr_hvac_modes = list(hvac_modes_set)
        
        # Build preset modes from device modes that have presets, plus PRESET_NONE and heat level presets
        preset_modes_set = {DREO_HEATER_MODE_TO_PRESET.get(mode)
                            for mode in self.device.modes
                            if mode in DREO_HEATER_MODE_TO_PRESET}
        # Add heat level presets (H1, H2, H3) if the device supports htalevel
        heat_level_presets = [PRESET_H1, PRESET_H2, PRESET_H3] if self.device.htalevel is not None else []
        self._attr_preset_modes = list(preset_modes_set) + heat_level_presets

        _LOGGER.info(
            "new DreoHeaterHA instance(%s), unique ID %s, HVAC mode %s, target temp %s, current temp %s, swing mode %s, swing modes [%s]",
            self._attr_name,
            self._attr_unique_id,
            self._attr_hvac_mode,
            self._attr_target_temperature,
            self._attr_current_temperature,
            self._attr_swing_mode,
            self._attr_swing_modes
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this heater."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device.serial_number)},
            manufacturer=self.device.brand,
            model=f"{self.device.series_name} ({self.device.model}) {self.device.product_name}",
            name=self.device.device_name,
        )

    @property
    def is_on(self) -> bool:
        """Return True if device is on."""
        return self.device.poweron

    @property
    def oscon(self) -> bool:
        """This represents horizontal oscillation only"""
        return self.device.oscon

    @property
    def oscangle(self) -> str | None:
        """Retrieve and map the value of the oscillation angle"""
        return (
            ANGLE_OSCANGLE_MAP[self.device.oscangle]
            if self.device.oscangle in ANGLE_OSCANGLE_MAP
            else None
        )

    @property
    def htalevels_count(self) -> int:
        """Return the number of heat levels the heater supports."""
        return int_states_in_range(self.device.heat_range)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the heater."""
        return {
            "model": self.device.model,
        }

    @property
    def preset_modes(self) -> list[str]:
        """Get the list of available preset modes."""
        return self._attr_preset_modes

    @property
    def preset_mode(self) -> str | None:
        """Get the current preset mode based on device mode and heat level."""
        # If the device is on and in HOTAIR mode, return heat level preset (H1/H2/H3)
        if self.device.poweron and self.device.mode == DreoHeaterMode.HOTAIR:
            if self.device.htalevel is not None and self.device.htalevel in HEAT_LEVEL_TO_PRESET:
                preset = HEAT_LEVEL_TO_PRESET[self.device.htalevel]
                _LOGGER.debug("DreoHeaterHA:preset_mode(%s): %s (htalevel: %s)", 
                              self.device.name, preset, self.device.htalevel)
                return preset
        
        # Map device mode to preset if it has one, otherwise PRESET_NONE
        device_mode = DreoHeaterMode(self.device.mode) if self.device.poweron else None
        preset = DREO_HEATER_MODE_TO_PRESET.get(device_mode, PRESET_NONE)
        _LOGGER.debug("DreoHeaterHA:preset_mode(%s): %s (device.mode: %s)", 
                      self.device.name, preset, self.device.mode)
        return preset
    
    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _LOGGER.debug("DreoHeaterHA:set_preset_mode(%s) --> %s", self.device.name, preset_mode)
        
        # Check if this is a heat level preset (H1/H2/H3)
        if preset_mode in PRESET_TO_HEAT_LEVEL:
            heat_level = PRESET_TO_HEAT_LEVEL[preset_mode]
            _LOGGER.debug("DreoHeaterHA:set_preset_mode(%s) setting heat level to %s", 
                          self.device.name, heat_level)
            # Set heat level and ensure we're in HEAT mode
            self.device.poweron = True
            self.device.mode = DreoHeaterMode.HOTAIR
            self.device.htalevel = heat_level
            self.schedule_update_ha_state()
            return
        
        # Map preset to Dreo mode
        dreo_mode = HVAC_PRESET_TO_DREO_HEATER_MODE.get(preset_mode)
        
        if dreo_mode is not None:
            self.device.poweron = True
            self.device.mode = dreo_mode
            self.schedule_update_ha_state()
        elif preset_mode != PRESET_NONE:
            _LOGGER.warning("DreoHeaterHA:set_preset_mode(%s) invalid preset: %s",
                          self.device.name, preset_mode)

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        supported_features = 0
        if self.preset_mode == PRESET_ECO and self.device.ecolevel is not None:
            supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if self.device.oscon is not None:
            supported_features |= ClimateEntityFeature.SWING_MODE
        if self.device.poweron is not None:
            supported_features |= ClimateEntityFeature.TURN_OFF
            supported_features |= ClimateEntityFeature.TURN_ON
        if len(self._attr_preset_modes) > 1:  # More than just PRESET_NONE
            supported_features |= ClimateEntityFeature.PRESET_MODE

        return supported_features

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        _LOGGER.debug("DreoHeaterHA:turn_on(%s)", self.device.name)
        self.device.poweron = True
        # Use preset if ECO, otherwise map HVAC mode to Dreo mode
        current_preset = self.preset_mode or PRESET_NONE
        if current_preset == PRESET_ECO:
            self.device.mode = DreoHeaterMode.ECO
        elif self._last_hvac_mode == HVACMode.HEAT:
            self.device.mode = DreoHeaterMode.HOTAIR
        elif self._last_hvac_mode == HVACMode.FAN_ONLY:
            self.device.mode = DreoHeaterMode.COOLAIR
        else:
            self.device.mode = DreoHeaterMode.HOTAIR

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        _LOGGER.debug("DreoHeaterHA:turn_off(%s)", self.device.name)
        self.device.poweron = False
        self._last_hvac_mode = self._attr_hvac_mode

    @oscon.setter
    def oscon(self, oscon: bool) -> None:
        """Oscillate the fan."""
        _LOGGER.debug("DreoHeaterHA::oscon(%s) --> %s", self.device.name, oscon)
        self.device.oscon = oscon

    @oscangle.setter
    def oscangle(self, oscangle: str) -> None:
        """Set the oscillation angle"""
        _LOGGER.debug("DreoHeaterHA::oscangle(%s) -> %s", self.device.name, oscangle)
        self.device.oscangle = OSCANGLE_ANGLE_MAP[oscangle]

    def panel_sound(self, panel_sound: bool) -> None:
        _LOGGER.debug(
            "DreoHeaterHA::panel_sound(%s) --> %s", self.device.name, panel_sound
        )
        self.device.muteon = not panel_sound

    def muteon(self, muteon: bool) -> None:
        _LOGGER.debug("DreoHeaterHA::muteon(%s) --> %s", self.device.name, muteon)
        self.device.muteon = muteon

    ### Implementation of climate methods
    @property
    def current_temperature(self) -> int:
        return self.device.temperature

    def set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if self._attr_hvac_mode == HVACMode.HEAT:
            self.device.ecolevel = self._attr_target_temperature = int(kwargs.get(
                ATTR_TEMPERATURE
            ))
        else:
            self._attr_target_temperature = 4  # self.device.temperature
            self.schedule_update_ha_state()

    @property
    def target_temperature(self) -> int | None:
        return (
            self.device.ecolevel
            if self.preset_mode == PRESET_ECO
            else self.device.temperature
        )

    @property
    def min_temp(self) -> int | None:
        return self.device.device_definition.device_ranges[ECOLEVEL_RANGE][0]

    @property
    def max_temp(self) -> int | None:
        return self.device.device_definition.device_ranges[ECOLEVEL_RANGE][1]

    @property
    def target_temperature_step(self) -> float | None:
        return 1

    @property
    def hvac_mode(self) -> HVACMode:
        # ensure hvac_mode is actually in sync with the device's mode
        self._attr_hvac_mode = DREO_HEATER_MODE_TO_HVAC_MODE.get(DreoHeaterMode(self.device.mode), HVACMode.OFF) if self.device.poweron else HVACMode.OFF
        _LOGGER.debug("DreoHeaterHA:hvac_mode(%s): %s (device.mode: %s)", 
                      self.device.name, 
                      self._attr_hvac_mode,
                      self.device.mode)
        return self._attr_hvac_mode

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac operation modes."""
        return self._attr_hvac_modes

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        _LOGGER.debug("DreoHeaterHA:set_hvac_mode(%s) %s --> %s", self.device.name, self._last_hvac_mode, hvac_mode)
        
        # Validate that the requested HVAC mode is supported
        if hvac_mode not in self._attr_hvac_modes:
            _LOGGER.error("DreoHeaterHA:set_hvac_mode(%s) - Requested HVAC mode %s is not supported. Supported modes: %s",
                          self.device.name, hvac_mode, self._attr_hvac_modes)
            return
        
        self._last_hvac_mode = self._attr_hvac_mode

        # Unsure if both of these are needed to be honest.
        if hvac_mode == HVACMode.OFF:
            self.device.poweron = False
            self.device.mode = DreoHeaterMode.OFF
            self._attr_hvac_mode = HVACMode.OFF
        else:
            # Map HVAC mode to Dreo mode
            self.device.poweron = True
            if hvac_mode == HVACMode.HEAT:
                # Only change mode if not already in HOTAIR or ECO
                if self.device.mode not in [DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO]:
                    self.device.mode = DreoHeaterMode.HOTAIR
            elif hvac_mode == HVACMode.FAN_ONLY:
                self.device.mode = DreoHeaterMode.COOLAIR
            else:
                # Nothing to do here....
                pass
            self._attr_hvac_mode = hvac_mode

        self.schedule_update_ha_state()

    @property
    def swing_modes(self) -> list[str] | None:
        """Return the list of available swing modes."""
        return self._attr_swing_modes

    @property
    def swing_mode(self) -> str | None:
        if self.device.oscon is not None and self.device.oscon is True:
            self._attr_swing_mode = SWING_ON
        elif self.device.oscangle is not None:
            self._attr_swing_mode = ANGLE_OSCANGLE_MAP[self.device.oscangle]
        else:
            self._attr_swing_mode = SWING_OFF
        return self._attr_swing_mode

    def set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing operation."""
        _LOGGER.debug(
            "DreoHeaterHA:set_swing_mode(%s) -> %s", self.device.name, swing_mode
        )
        if self.device.oscon is not None:
            self.oscon = False if swing_mode != SWING_ON and swing_mode in self._attr_swing_modes else True
        elif self.device.oscangle is not None:
            self.oscangle = swing_mode

    def set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode (not supported by heaters)."""
        raise NotImplementedError("Fan mode is not supported by heaters")

    def set_humidity(self, humidity: int) -> None:
        """Set target humidity (not supported by heaters)."""
        raise NotImplementedError("Humidity control is not supported by heaters")

    def set_swing_horizontal_mode(self, swing_horizontal_mode: str) -> None:
        """Set horizontal swing mode (not supported by heaters)."""
        raise NotImplementedError("Horizontal swing mode is not supported by heaters")

    def toggle(self) -> None:
        """Toggle the heater on/off."""
        if self.device.poweron:
            self.turn_off()
        else:
            self.turn_on()

    def turn_aux_heat_off(self) -> None:
        """Turn auxiliary heater off (not supported by heaters)."""
        raise NotImplementedError("Auxiliary heat is not supported by heaters")

    def turn_aux_heat_on(self) -> None:
        """Turn auxiliary heater on (not supported by heaters)."""
        raise NotImplementedError("Auxiliary heat is not supported by heaters")
