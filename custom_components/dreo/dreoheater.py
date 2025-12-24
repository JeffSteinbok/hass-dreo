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
    HEATER_MODE_OFF,
    HEATER_MODE_COOLAIR,
    HEATER_MODE_HOTAIR,
    HEATER_MODE_ECO,
    ECOLEVEL_RANGE,
    ANGLE_OSCANGLE_MAP,
    OSCANGLE_ANGLE_MAP,
)

from .const import (
    LOGGER,
    DOMAIN
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

_LOGGER = logging.getLogger(LOGGER)

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
        self._attr_hvac_mode = (
            HEATER_MODE_MAP[self.device.hvac_mode] if self.device.poweron else HVACMode.OFF
        )
        self._attr_hvac_modes = [
            HEATER_MODE_MAP[h] for h in self.device.device_definition.hvac_modes
        ]

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
            "htalevel": self.device.htalevel,
        }

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        supported_features = 0
        if self.device.ecolevel is not None:
            supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if self.device.oscon is not None:
            supported_features |= ClimateEntityFeature.SWING_MODE
        if self.device.poweron is not None:
            supported_features |= ClimateEntityFeature.TURN_OFF
            supported_features |= ClimateEntityFeature.TURN_ON

        return supported_features

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        _LOGGER.debug("DreoHeaterHA:turn_on(%s)", self.device.name)
        self.device.poweron = True
        self.device.hvac_mode = HVAC_MODE_MAP[self._last_hvac_mode]

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
        if self._attr_hvac_mode == HVACMode.AUTO:
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
            if self._attr_hvac_mode == HVACMode.AUTO
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
        # ensure hvac_mode is actually in sync with the device's moade
        self._attr_hvac_mode = (
            HEATER_MODE_MAP[self.device.hvac_mode] if self.device.poweron else HVACMode.OFF
        )
        return self._attr_hvac_mode

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac operation modes."""
        return self._attr_hvac_modes

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        _LOGGER.debug(
            "DreoHeaterHA:set_hvac_mode(%s) %s --> %s",
            self.device.name,
            hvac_mode,
            HVAC_MODE_MAP[hvac_mode],
        )
        self._last_hvac_mode = self._attr_hvac_mode

        if hvac_mode != HVACMode.OFF:
            self.device.poweron = True
        else:
            self.device.poweron = False

        self.device.hvac_mode = HVAC_MODE_MAP[hvac_mode]

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

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode (not supported by heaters)."""
        raise NotImplementedError("Preset mode is not supported by heaters")

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
