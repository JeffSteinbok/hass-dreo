"""Support for Dreo fans."""

from __future__ import annotations

import logging
import math
from typing import Any

from .haimports import *  # pylint: disable=W0401,W0614

from .dreobasedevice import DreoBaseDeviceHA
from .pydreo.constant import DreoDeviceType, TemperatureUnit  # pylint: disable=C0415

from .pydreo.pydreofanbase import PyDreoFanBase

_LOGGER = logging.getLogger(__name__)


class DreoFanHA(DreoBaseDeviceHA, FanEntity):
    """Representation of a Dreo fan."""

    def __init__(self, pyDreoFan: PyDreoFanBase):
        """Initialize the Dreo fan device."""
        super().__init__(pyDreoFan)
        self.device = pyDreoFan
        self._attr_translation_key = "fan"
        if self.device.type is DreoDeviceType.CEILING_FAN:
            self._attr_icon = "mdi:ceiling-fan"
        elif self.device.type is DreoDeviceType.DEHUMIDIFIER:
            # Localize the sub-entity name via has_entity_name + translation_key
            # instead of hardcoding an English string. The base class sets
            # _attr_name to the device name; delete it so the translation_key is
            # used instead.
            self._attr_has_entity_name = True
            del self._attr_name
            self._attr_translation_key = "fan_speed"

    @property
    def percentage(self) -> int | None:
        """Return the current speed."""
        if self.device.type is DreoDeviceType.DEHUMIDIFIER:
            if self.device.preset_mode == "low":
                return 33
            elif self.device.preset_mode == "medium":
                return 67
            elif self.device.preset_mode == "high":
                return 100
            return None
        if self.device.speed_range is None or self.device.fan_speed is None:
            return None
        return ranged_value_to_percentage(self.device.speed_range, self.device.fan_speed)

    @property
    def is_on(self) -> bool:
        """Return True if device is on."""
        return self.device.is_on

    @property
    def oscillating(self) -> bool:
        """This represents horizontal oscillation only"""
        if self.device.type is DreoDeviceType.DEHUMIDIFIER:
            return False
        return self.device.oscillating

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return int_states_in_range(self.device.speed_range)

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
        """Return the state attributes of the fan."""
        attr = {"model": self.device.model, "sn": self.device.serial_number}
        temp = self.device.temperature
        if temp is not None:
            device_temp_unit = self.device.temperature_units
            if device_temp_unit is None:
                device_temp_unit = TemperatureUnit.CELSIUS
            source_unit = UnitOfTemperature.CELSIUS if device_temp_unit == TemperatureUnit.CELSIUS else UnitOfTemperature.FAHRENHEIT
            attr["temperature"] = round(
                TemperatureConverter.convert(
                    temp,
                    source_unit,
                    self.hass.config.units.temperature_unit,
                ),
                1,
            )
        return attr

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        supported_features = FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        if self.device.preset_modes is not None:
            supported_features = supported_features | FanEntityFeature.PRESET_MODE
        if self.device.oscillating is not None and self.device.type is not DreoDeviceType.DEHUMIDIFIER:
            supported_features = supported_features | FanEntityFeature.OSCILLATE

        return supported_features

    def turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the device on."""
        _LOGGER.debug("turn_on: turn_on")
        if preset_mode is not None:
            self.set_preset_mode(preset_mode)
        if percentage is not None:
            self.set_percentage(percentage)
        if preset_mode is None and percentage is None:
            self.device.is_on = True

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        _LOGGER.debug("turn_off: turn_off")
        self.device.is_on = False

    def set_percentage(self, percentage: int) -> None:
        """Set the speed of the device."""
        if percentage == 0:
            self.device.is_on = False
            return

        if not self.device.is_on:
            self.device.is_on = True

        if self.device.type is DreoDeviceType.DEHUMIDIFIER:
            if percentage <= 33:
                self.device.set_preset_mode("low")
            elif percentage <= 67:
                self.device.set_preset_mode("medium")
            else:
                self.device.set_preset_mode("high")
        else:
            if self.device.speed_range is None:
                _LOGGER.error("set_percentage: speed_range not available for %s", self.device.name)
                return
            self.device.fan_speed = math.ceil(percentage_to_ranged_value(self.device.speed_range, percentage))

        self.schedule_update_ha_state()

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of device."""
        if preset_mode not in self.preset_modes:
            raise ValueError(f"{preset_mode} is not one of the valid preset modes: {self.preset_modes}")

        if not self.device.is_on:
            self.device.is_on = True

        if self.device.type is DreoDeviceType.DEHUMIDIFIER:
            self.device.set_preset_mode(preset_mode)
        else:
            self.device.preset_mode = preset_mode

        self.schedule_update_ha_state()

    def oscillate(self, oscillating: bool) -> None:
        """Oscillate the fan."""
        self.device.oscillating = oscillating
        self.schedule_update_ha_state()

    def set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        raise NotImplementedError
