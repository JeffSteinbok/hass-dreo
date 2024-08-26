"""Support climate control for some Dreo devices"""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613

from typing import Any
from dataclasses import dataclass
import logging

from .haimports import *  # pylint: disable=W0401,W0614
from .basedevice import DreoBaseDeviceHA
from .pydreo import (
    PyDreo,
    PyDreoHeater,
    PyDreoAC,
    HEATER_MODE_OFF,
    HEATER_MODE_COOLAIR,
    HEATER_MODE_HOTAIR,
    HEATER_MODE_ECO,
    MODE_LEVEL_MAP,
    LEVEL_MODE_MAP,
    ECOLEVEL_RANGE,
    ANGLE_OSCANGLE_MAP,
    OSCANGLE_ANGLE_MAP,
    TEMP_RANGE,
    TARGET_TEMP_RANGE,
    TARGET_TEMP_RANGE_ECO,
    HUMIDITY_RANGE,
)

from .const import (
    LOGGER,
    DOMAIN,
    DREO_MANAGER,
)

HVAC_MODE_MAP = {
    HVACMode.OFF: HEATER_MODE_OFF,
    HVACMode.FAN_ONLY: HEATER_MODE_COOLAIR,
    HVACMode.AUTO: HEATER_MODE_ECO,
    HVACMode.HEAT: HEATER_MODE_HOTAIR,
}

HEATER_MODE_MAP = {
    HEATER_MODE_OFF: HVACMode.OFF,
    HEATER_MODE_COOLAIR: HVACMode.FAN_ONLY,
    HEATER_MODE_HOTAIR: HVACMode.HEAT,
    HEATER_MODE_ECO: HVACMode.AUTO,
}

AC_MODE_MAP = {
    1: HVACMode.COOL,
    2: HVACMode.DRY,
    3: HVACMode.FAN_ONLY,
    5: HVACMode.COOL,
    HVACMode.COOL: 1,
    HVACMode.DRY: 2,
    HVACMode.FAN_ONLY: 3,
}

HVAC_AC_MODE_MAP = {
    HVACMode.COOL: 1,
    HVACMode.DRY: 2,
    HVACMode.FAN_ONLY: 3,
}

from homeassistant.components.climate import (
    SWING_ON,
    SWING_OFF,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    PRESET_ECO,
    PRESET_NONE,
    HVACMode,
)

from .pydreo.pydreoac import (
    DREO_AC_MODE_COOL,
    DREO_AC_MODE_DRY,
)

_LOGGER = logging.getLogger(LOGGER)


def add_device_entries(devices) -> []:
    ha_collection = []

    for de in devices:
        _LOGGER.debug("Adding climate entity for %s", de)
        if isinstance(de, PyDreoHeater):
            ha_collection.append(DreoHeaterHA(de))
        elif isinstance(de, PyDreoAC):
            ha_collection.append(DreoACHA(de))

    return ha_collection


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Climate platform."""
    _LOGGER.info("Starting Dreo Climate Platform")
    _LOGGER.debug("Dreo Climate:async_setup_entry")

    manager: PyDreo = hass.data[DOMAIN][DREO_MANAGER]

    async_add_entities(add_device_entries(manager.heaters))
    async_add_entities(add_device_entries(manager.acs))

    platform = entity_platform.async_get_current_platform()


# Implementation of the heater
class DreoHeaterHA(DreoBaseDeviceHA, ClimateEntity):
    """Representation of a Dreo heater as a climate entity."""

    _attr_precision = PRECISION_WHOLE
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT  # TODO
    _attr_target_temperature = None
    _attr_current_temperature = None
    _attr_fan_mode = None
    _attr_fan_modes = [FAN_ON, FAN_OFF]
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
            "DreoHeaterHA:__init__(%s) shows pyDreoDevice as: current_temp(%s), target_temp(%s), mode(%s)",
            pyDreoDevice.name,
            pyDreoDevice.temperature,
            pyDreoDevice.ecolevel,
            pyDreoDevice.mode,
        )

        self._attr_name = "Heater"
        self._attr_unique_id = f"{super().unique_id}-{self.device.device_id}"
        self._attr_preset_mode = LEVEL_MODE_MAP[self.device.htalevel]
        self._attr_target_temperature = self.device.ecolevel
        self._attr_current_temperature = self.device.temperature
        self._attr_swing_mode = self.device.device_definition.swing_modes[0]
        self._attr_swing_modes = self.device.device_definition.swing_modes
        self._attr_hvac_mode = (
            HEATER_MODE_MAP[self.device.mode] if self.device.poweron else HVACMode.OFF
        )
        self._attr_preset_modes = pyDreoDevice.preset_modes
        self._attr_hvac_modes = [
            HEATER_MODE_MAP[h] for h in self.device.device_definition.hvac_modes
        ]

        _LOGGER.info(
            "new DreoHeaterHA instance(%s), unique ID %s, HVAC mode %s, target temp %s, current temp %s, swing mode %s, preset mode %s, swing modes [%s], preset_modes [%s]",
            self._attr_name,
            self._attr_unique_id,
            self._attr_hvac_mode,
            self._attr_target_temperature,
            self._attr_current_temperature,
            self._attr_swing_mode,
            self._attr_preset_mode,
            self._attr_swing_modes,
            self._attr_preset_modes,
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
    def fan_mode(self) -> str:
        """Return the current fan mode - if on, it means that we're in 'coolair' mode"""
        return self.device.fan_mode

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
    def preset_modes(self) -> list[str]:
        """Get the list of available preset modes."""
        return self.device.preset_modes

    @property
    def preset_mode(self) -> str | None:
        """Get the current preset mode."""
        return self.device.preset_mode

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the heater."""
        return {
            "current_temperature": self.device.temperature,
            "model": self.device.model,
            "htalevel": self.device.htalevel,
        }

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        supported_features = 0
        if self.device.ecolevel is not None:
            supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if self.device.preset_mode is not None:
            supported_features |= ClimateEntityFeature.PRESET_MODE
        if self.device.oscon is not None:
            supported_features |= ClimateEntityFeature.SWING_MODE
        if self.device.fan_mode is not None:
            supported_features |= ClimateEntityFeature.FAN_MODE
        if self.device.poweron is not None:
            supported_features |= ClimateEntityFeature.TURN_OFF
            supported_features |= ClimateEntityFeature.TURN_ON

        return supported_features

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        _LOGGER.debug("DreoHeaterHA:turn_on(%s)", self.device.name)
        self.device.poweron = True
        self.device.mode = HVAC_MODE_MAP[self._last_hvac_mode]
        self.device._attr_hvac_mode = self._last_hvac_mode

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        _LOGGER.debug("DreoHeaterHA:turn_off(%s)", self.device.name)
        self.device.poweron = False
        self._last_hvac_mode = self._attr_hvac_mode

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the device."""
        _LOGGER.debug(
            "DreoHeaterHA:set_preset_mode(%s) --> %s", self.device.name, preset_mode
        )
        self._last_hvac_mode = self._attr_hvac_mode
        if not self.device.poweron:
            self.device.poweron = True

        if preset_mode not in self.preset_modes:
            raise ValueError(
                f"{preset_mode} is not one of the valid preset modes: {self.preset_modes}"
            )

        self.device.preset_mode = preset_mode
        self.device.htalevel = MODE_LEVEL_MAP[preset_mode]
        self.device.mode = HEATER_MODE_HOTAIR

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
    def current_temperature(self) -> float:
        return self.device.temperature

    def set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if self._attr_hvac_mode == HVACMode.AUTO:
            self.device.ecolevel = self._attr_target_temperature = kwargs.get(
                ATTR_TEMPERATURE
            )
        else:
            self._attr_target_temperature = 4  # self.device.temperature
            self.schedule_update_ha_state()

    @property
    def target_temperature(self) -> float | None:
        return (
            self.device.ecolevel
            if self._attr_hvac_mode == HVACMode.AUTO
            else self.device.temperature
        )

    @property
    def min_temp(self) -> float | None:
        return self.device.device_definition.range[ECOLEVEL_RANGE][0]

    @property
    def max_temp(self) -> float | None:
        return self.device.device_definition.range[ECOLEVEL_RANGE][1]

    @property
    def target_temperature_step(self) -> float | None:
        return 1

    @property
    def hvac_mode(self):
        # ensure hvac_mode is actually in sync with the device's moade
        self._attr_hvac_mode = (
            HEATER_MODE_MAP[self.device.mode] if self.device.poweron else HVACMode.OFF
        )
        return self._attr_hvac_mode

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac operation modes."""
        return self._attr_hvac_modes

    def set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        _LOGGER.debug(
            "DreoHeaterHA:set_fan_mode(%s) --> %s", self.device.name, fan_mode
        )
        self.device.fan_mode = True if fan_mode == FAN_ON else False
        self._last_hvac_mode = self._attr_hvac_mode

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        _LOGGER.debug(
            "DreoHeaterHA:set_hvac_mode(%s) %s --> %s",
            self.device.name,
            hvac_mode,
            HVAC_MODE_MAP[hvac_mode],
        )
        self._last_hvac_mode = self._attr_hvac_mode
        self.device.mode = HVAC_MODE_MAP[hvac_mode]

        if hvac_mode != HVACMode.OFF:
            self.device.poweron = True
        else:
            self.device.poweron = False

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


# Implementation of the air conditioner
class DreoACHA(DreoBaseDeviceHA, ClimateEntity):
    """Representation of a Dreo air conditioner as a climate entity."""
    _attr_precision = PRECISION_WHOLE
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT  # TODO
    _attr_target_temperature = None
    _attr_current_temperature = None
    _attr_fan_mode = None
    _attr_fan_modes = [FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO]
    _attr_name = None
    _attr_has_entity_name = True
    _attr_hvac_mode = HVACMode.OFF
    _attr_hvac_modes = None
    _last_hvac_mode = HVACMode.OFF
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, pyDreoDevice: PyDreoAC) -> None:
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice
        _LOGGER.info(
            "DreoACHA:__init__(%s) shows pyDreoDevice as: current_temp(%s), target_temp(%s), mode(%s), oscon(%s), fan_mode(%s)",
            pyDreoDevice.name,
            pyDreoDevice.temperature,
            pyDreoDevice.target_temperature,
            pyDreoDevice.mode,
            pyDreoDevice.oscon,
            pyDreoDevice.fan_mode,
        )

        self._attr_name = "Air Conditioner"
        self._attr_unique_id = f"{super().unique_id}-{self.device.device_id}"
        self._attr_target_temperature = self.device.target_temperature
        self._attr_current_temperature = self.device.temperature
        self._attr_swing_mode = self.device.device_definition.swing_modes[0]
        self._attr_swing_modes = self.device.device_definition.swing_modes
        self._attr_hvac_mode = AC_MODE_MAP[self.device.mode] if self.device.poweron else HVACMode.OFF
        self._attr_hvac_modes = self.device.device_definition.hvac_modes
        self._attr_preset_modes = self.device.device_definition.preset_modes
        self._attr_fan_modes = self.device.device_definition.fan_modes
        self._attr_fan_mode = self.device.fan_mode
        self._attr_oscon = self.device.oscon

        _LOGGER.info(
            "new DreoACHA instance(%s), unique ID %s, HVAC mode %s, target temp %s, current temp %s, swing mode %s, swing modes [%s], oscon %s, fan_mode %s",
            self._attr_name,
            self._attr_unique_id,
            self._attr_hvac_mode,
            self._attr_target_temperature,
            self._attr_current_temperature,
            self._attr_swing_mode,
            self._attr_swing_modes,
            self._attr_oscon,
            self._attr_fan_mode,
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this air conditioner."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device.serial_number)},
            manufacturer=self.device.brand,
            model=f"{self.device.series_name} ({self.device.model}) {self.device.product_name}",
            name=self.device.device_name,
        )

    @property
    def fan_mode(self) -> str:
        """Return the current fan mode - if on, it means that we're in 'coolair' mode"""
        _LOGGER.debug("DreoACHA:fan_mode(%s): %s", self.device.name, self.device.fan_mode)
        return self.device.fan_mode

    def set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        _LOGGER.debug("DreoACHA:set_fan_mode(%s) --> %s", self.device.name, fan_mode)
        self.device.fan_mode = fan_mode
        self._attr_fan_mode = fan_mode

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
        return ANGLE_OSCANGLE_MAP[self.device.oscangle] if self.device.oscangle in ANGLE_OSCANGLE_MAP else None

    @property
    def preset_modes(self) -> list[str]:
        """Get the list of available preset modes."""
        _LOGGER.debug("DreoACHA:preset_mode(%s): %s", self.device.name, self.device.preset_mode)
        return self.device.preset_modes

    @property
    def preset_mode(self) -> str | None:
        """Get the current preset mode."""
        return self.device.preset_mode

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the device."""
        _LOGGER.debug("DreoACHA:set_preset_mode(%s) --> %s", self.device.name, preset_mode)
        if preset_mode == PRESET_ECO:
            self.device.mode = DREO_AC_MODE_COOL
            self.device.preset_mode = preset_mode
        else:
            self.device.preset_mode = PRESET_NONE

        self._attr_preset_mode = preset_mode

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the air conditioner."""
        return {
            "current_temperature": self.device.temperature,
            "target_temperature": self.device.target_temperature,
            "model": self.device.model,
        }

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        supported_features = 0
        if self.device.target_temperature is not None and self.device.mode == DREO_AC_MODE_COOL:
            supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if (self.device.preset_mode is not None or self.device.device_definition.preset_modes is not None) and self.device.mode == DREO_AC_MODE_COOL:
            supported_features |= ClimateEntityFeature.PRESET_MODE
        if self.device.oscon is not None:
            supported_features |= ClimateEntityFeature.SWING_MODE
        if self.device.fan_mode is not None or self.device.device_definition.fan_modes is not None:
            supported_features |= ClimateEntityFeature.FAN_MODE
        if self.device.poweron is not None:
            supported_features |= ClimateEntityFeature.TURN_OFF
            supported_features |= ClimateEntityFeature.TURN_ON
        if self.device.target_humidity is not None and self.device.mode == DREO_AC_MODE_DRY:
            supported_features |= ClimateEntityFeature.TARGET_HUMIDITY
        
        _LOGGER.debug("DreoACHA:supported_features(%s): %s (device.mode: %s)", self, supported_features, self.device.mode)
        
        return supported_features

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        _LOGGER.debug("DreoACHA:turn_on(%s)", self.device.name)
        self.device.poweron = True
        self.device.mode = HVAC_AC_MODE_MAP[self._last_hvac_mode]
        self.device._attr_hvac_mode = self._last_hvac_mode

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        _LOGGER.debug("DreoACHA:turn_off(%s)", self.device.name)
        self.device.poweron = False
        self._last_hvac_mode = self._attr_hvac_mode

    @oscon.setter
    def oscon(self, oscon: bool) -> None:
        """Oscillate the fan."""
        _LOGGER.debug("DreoACHA::oscon(%s) --> %s", self.device.name, oscon)
        self.device.oscon = oscon

    @oscangle.setter
    def oscangle(self, oscangle: str) -> None:
        """Set the oscillation angle"""
        _LOGGER.debug("DreoACHA::oscangle(%s) -> %s", self.device.name, oscangle)
        self.device.oscangle = OSCANGLE_ANGLE_MAP[oscangle]

    def panel_sound(self, panel_sound: bool) -> None:
        _LOGGER.debug("DreoACHA::panel_sound(%s) --> %s", self.device.name, panel_sound)
        self.device.muteon = not panel_sound

    def muteon(self, muteon: bool) -> None:
        _LOGGER.debug("DreoACHA::muteon(%s) --> %s", self.device.name, muteon)
        self.device.muteon = muteon

    ### Implementation of climate methods
    @property
    def current_temperature(self) -> float:
        return self.device.temperature
    
    @property
    def min_temp(self) -> float | None:
        return self.device.device_definition.range[TEMP_RANGE][0]

    @property
    def max_temp(self) -> float | None:
        return self.device.device_definition.range[TEMP_RANGE][1]
    
    def set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        self.device.target_temperature = kwargs.get(ATTR_TEMPERATURE)
        _LOGGER.debug("DreoACHA::set_temperature(%s) %s --> %s", 
                      self.device.name, 
                      self._attr_target_temperature, 
                      self.device.target_temperature)
        self._attr_target_temperature = self.device.target_temperature
        self.schedule_update_ha_state()

    @property
    def target_temperature(self) -> float | None:
        return self.device.target_temperature
    
    @property
    def target_temperature_low(self) -> float | None:
        if self.device.preset_mode == PRESET_ECO:
            range_key = TARGET_TEMP_RANGE_ECO
        else:
            range_key = TARGET_TEMP_RANGE
        return self.device.device_definition.range[range_key][0]

    @property
    def target_temperature_high(self) -> float | None:
        if self.device.preset_mode == PRESET_ECO:
            range_key = TARGET_TEMP_RANGE_ECO
        else:
            range_key = TARGET_TEMP_RANGE
        return self.device.device_definition.range[range_key][1]

    @property
    def target_temperature_step(self) -> float | None:
        return 1

    @property
    def current_humidity(self) -> float:
        return self.device.humidity

    def set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""
        _LOGGER.debug("DreoACHA::set_humidity(%s) %s --> %s", self.device.name, self._attr_target_humidity, humidity)
        self.device.target_humidity = humidity
        self._attr_target_humidity = humidity
        self.schedule_update_ha_state()

    @property
    def target_humidity(self) -> int | None:
        return self.device.target_humidity

    @property
    def min_humidity(self) -> float | None:
        return self.device.device_definition.range[HUMIDITY_RANGE][0]

    @property
    def max_humidity(self) -> float | None:
        return self.device.device_definition.range[HUMIDITY_RANGE][1]

    @property
    def hvac_mode(self):
        # ensure hvac_mode is actually in sync with the device's mode
        self._attr_hvac_mode = AC_MODE_MAP[self.device.mode] if self.device.poweron else HVACMode.OFF
        _LOGGER.debug("DreoACHA:hvac_mode(%s): %s (device.mode: %s)", 
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
        _LOGGER.debug("DreoACHA:set_hvac_mode(%s) %s --> %s", self.device.name, self._last_hvac_mode, hvac_mode)
        self._last_hvac_mode = self._attr_hvac_mode
        self.device.mode = HVAC_AC_MODE_MAP[hvac_mode]

        if hvac_mode != HVACMode.OFF:
            self.device.poweron = True
        else:
            self.device.poweron = False
            
        self.schedule_update_ha_state()

    @property
    def swing_modes(self) -> list[str] | None:
        """Return the list of available swing modes."""
        return self._attr_swing_modes

    @property
    def swing_mode(self) -> str | None:
        if self.device.oscon is not None and self.device.oscon is True:
            self._attr_swing_mode = SWING_ON
        else:
            self._attr_swing_mode = SWING_OFF
        return self._attr_swing_mode

    def set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing operation."""
        _LOGGER.debug("DreoACHA:set_swing_mode(%s) -> %s", self.device.name, swing_mode)

        if self.device.oscon is not None:
            self.oscon = (
                False
                if swing_mode != SWING_ON and swing_mode in self._attr_swing_modes
                else True
            )
        elif self.device.oscangle is not None:
            self.oscangle = swing_mode
