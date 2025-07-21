"""Support climate control for some Dreo devices"""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613

from typing import Any
import logging

from .haimports import *  # pylint: disable=W0401,W0614
from .dreobasedevice import DreoBaseDeviceHA

from .pydreo import (
    PyDreoAC,
    ANGLE_OSCANGLE_MAP,
    OSCANGLE_ANGLE_MAP,
    TEMP_RANGE,
    TARGET_TEMP_RANGE,
    TARGET_TEMP_RANGE_ECO,
    HUMIDITY_RANGE,
    PRESET_SLEEP,
)

from .pydreo.pydreoairconditioner import (
    DREO_AC_MODE_COOL,
    DREO_AC_MODE_DRY,
)

from .const import (
    LOGGER,
    DOMAIN,
)

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

_LOGGER = logging.getLogger(LOGGER)

# Implementation of the air conditioner
class DreoAirConditionerHA(DreoBaseDeviceHA, ClimateEntity):
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
            "DreoAirConditionerHA:__init__(%s) shows pyDreoDevice as: current_temp(%s), target_temp(%s), mode(%s), oscon(%s), fan_mode(%s)",
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
            "new DreoAirConditionerHA instance(%s), unique ID %s, HVAC mode %s, target temp %s, current temp %s, swing mode %s, swing modes [%s], oscon %s, fan_mode %s",
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

    async def async_added_to_hass(self) -> None:
        """Configure temperature mapping after entity is added to HA."""
        await super().async_added_to_hass()
        
        # Configure temperature mapping based on HA's unit configuration
        ha_uses_celsius = self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS
        self.device.set_ha_temperature_unit_is_celsius(ha_uses_celsius)

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
        _LOGGER.debug("DreoAirConditionerHA:fan_mode(%s): %s", self.device.name, self.device.fan_mode)
        return self.device.fan_mode

    def set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        _LOGGER.debug("DreoAirConditionerHA:set_fan_mode(%s) --> %s", self.device.name, fan_mode)
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
        _LOGGER.debug("DreoAirConditionerHA:preset_mode(%s): %s", self.device.name, self.device.preset_mode)
        return self.device.preset_modes

    @property
    def preset_mode(self) -> str | None:
        """Get the current preset mode."""
        return self.device.preset_mode

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the device."""
        _LOGGER.debug("DreoAirConditionerHA:set_preset_mode(%s) --> %s", self.device.name, preset_mode)
        if preset_mode == PRESET_ECO:
            self.device.mode = DREO_AC_MODE_COOL
            self.device.preset_mode = preset_mode
        elif preset_mode == PRESET_SLEEP:
            self.device.mode = DREO_AC_MODE_COOL
            self.device.preset_mode = preset_mode
        else:
            self.device.preset_mode = PRESET_NONE

        self._attr_preset_mode = preset_mode

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the air conditioner."""
        return {
            "model": self.device.model,
        }

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        supported_features = 0
        if self.device.target_temperature is not None and self.device.mode == DREO_AC_MODE_COOL:
            supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if ((self.device.preset_mode is not None or self.device.device_definition.preset_modes is not None) and 
            self.device.mode == DREO_AC_MODE_COOL):
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
        
        _LOGGER.debug("DreoAirConditionerHA:supported_features(%s): %s (device.mode: %s)", self, supported_features, self.device.mode)
        
        return supported_features

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        _LOGGER.debug("DreoAirConditionerHA:turn_on(%s)", self.device.name)
        self.device.poweron = True
        self.device.mode = HVAC_AC_MODE_MAP[self._last_hvac_mode]
        self.device._attr_hvac_mode = self._last_hvac_mode

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        _LOGGER.debug("DreoAirConditionerHA:turn_off(%s)", self.device.name)
        self.device.poweron = False
        self._last_hvac_mode = self._attr_hvac_mode

    @oscon.setter
    def oscon(self, oscon: bool) -> None:
        """Oscillate the fan."""
        _LOGGER.debug("DreoAirConditionerHA::oscon(%s) --> %s", self.device.name, oscon)
        self.device.oscon = oscon

    @oscangle.setter
    def oscangle(self, oscangle: str) -> None:
        """Set the oscillation angle"""
        _LOGGER.debug("DreoAirConditionerHA::oscangle(%s) -> %s", self.device.name, oscangle)
        self.device.oscangle = OSCANGLE_ANGLE_MAP[oscangle]

    def panel_sound(self, panel_sound: bool) -> None:
        """Turn the panel sound on or off."""
        _LOGGER.debug("DreoAirConditionerHA::panel_sound(%s) --> %s", self.device.name, panel_sound)
        self.device.muteon = not panel_sound

    def muteon(self, muteon: bool) -> None:
        """Turn the sound on or off."""
        _LOGGER.debug("DreoAirConditionerHA::muteon(%s) --> %s", self.device.name, muteon)
        self.device.muteon = muteon

    ### Implementation of climate methods
    @property
    def current_temperature(self) -> int:
        return self.device.temperature
    
    @property
    def min_temp(self) -> float | None:
        return self.device.device_definition.device_ranges[TEMP_RANGE][0]

    @property
    def max_temp(self) -> int | None:
        return self.device.device_definition.device_ranges[TEMP_RANGE][1]
    
    def set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        self.device.target_temperature = int(kwargs.get(ATTR_TEMPERATURE))
        _LOGGER.debug("DreoAirConditionerHA::set_temperature(%s) %s --> %s", 
                      self.device.name, 
                      self._attr_target_temperature, 
                      self.device.target_temperature)
        self._attr_target_temperature = self.device.target_temperature
        self.schedule_update_ha_state()

    @property
    def target_temperature(self) -> int | None:
        return self.device.target_temperature
    
    @property
    def target_temperature_low(self) -> int | None:
        if self.device.preset_mode == PRESET_ECO:
            range_key = TARGET_TEMP_RANGE_ECO
        else:
            range_key = TARGET_TEMP_RANGE
        return self.device.device_definition.device_ranges[range_key][0]

    @property
    def target_temperature_high(self) -> int | None:
        if self.device.preset_mode == PRESET_ECO:
            range_key = TARGET_TEMP_RANGE_ECO
        else:
            range_key = TARGET_TEMP_RANGE
        return self.device.device_definition.device_ranges[range_key][1]

    @property
    def target_temperature_step(self) -> int | None:
        return 1

    @property
    def current_humidity(self) -> float:
        return self.device.humidity

    def set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""
        _LOGGER.debug("DreoAirConditionerHA::set_humidity(%s) %s --> %s", self.device.name, self._attr_target_humidity, humidity)
        self.device.target_humidity = humidity
        self._attr_target_humidity = humidity
        self.schedule_update_ha_state()

    @property
    def target_humidity(self) -> int | None:
        return self.device.target_humidity

    @property
    def min_humidity(self) -> float | None:
        return self.device.device_definition.device_ranges[HUMIDITY_RANGE][0]

    @property
    def max_humidity(self) -> float | None:
        return self.device.device_definition.device_ranges[HUMIDITY_RANGE][1]

    @property
    def hvac_mode(self):
        # ensure hvac_mode is actually in sync with the device's mode
        self._attr_hvac_mode = AC_MODE_MAP[self.device.mode] if self.device.poweron else HVACMode.OFF
        _LOGGER.debug("DreoAirConditionerHA:hvac_mode(%s): %s (device.mode: %s)", 
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
        _LOGGER.debug("DreoAirConditionerHA:set_hvac_mode(%s) %s --> %s", self.device.name, self._last_hvac_mode, hvac_mode)
        self._last_hvac_mode = self._attr_hvac_mode

        if hvac_mode == HVACMode.OFF:
            self.device.poweron = False
            self._attr_hvac_mode = HVACMode.OFF
        else:
            self.device.mode = HVAC_AC_MODE_MAP[hvac_mode]
            self.device.poweron = True
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
        else:
            self._attr_swing_mode = SWING_OFF
        return self._attr_swing_mode

    def set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing operation."""
        _LOGGER.debug("DreoAirConditionerHA:set_swing_mode(%s) -> %s", self.device.name, swing_mode)

        if self.device.oscon is not None:
            self.oscon = (
                False
                if swing_mode != SWING_ON and swing_mode in self._attr_swing_modes
                else True
            )
        elif self.device.oscangle is not None:
            self.oscangle = swing_mode
