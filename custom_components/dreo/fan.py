"""Support for Dreo fans."""
from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    int_states_in_range,
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .basedevice import DreoBaseDeviceHA
from .const import DOMAIN, DREO_DISCOVERY, DREO_FANS, DREO_MANAGER
from .pydreo.constant import *
from .pydreo.pydreofan import PyDreoFan

_LOGGER = logging.getLogger("dreo")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    _discovery_info=None,
) -> None:
    """Set up the Dreo fan platform."""
    _LOGGER.info("Starting Dreo Fan Platform")
    _LOGGER.debug("Dreo Fan:async_setup_platform")

    manager = hass.data[DOMAIN][DREO_MANAGER]

    fansHAs = []
    for fanEntity in manager.fans:
        fansHAs.append(DreoFanHA(fanEntity))

    async_add_entities(fansHAs)


class DreoFanHA(DreoBaseDeviceHA, FanEntity):
    """Representation of a Dreo fan."""

    def __init__(self, pyDreoFan: PyDreoFan):
        """Initialize the Dreo fan device."""
        super().__init__(pyDreoFan)
        self.device = pyDreoFan

    @property
    def percentage(self) -> int | None:
        """Return the current speed."""
        return ranged_value_to_percentage(
            self.device.speed_range, self.device.fan_speed
        )

    @property
    def is_on(self) -> bool:
        """Return True if device is on."""
        return self.device.is_on

    @property
    def oscillating(self) -> bool:
        """This represents horizontal oscillation only"""
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
        if (self.device.supports_preset_modes):
            return self.device.preset_mode
        else:
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the fan."""
        attr = {"temperature": self.device.temperature,
            'model': self.device.model,
            'sn': self.device.sn}
        return attr

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        supported_features = FanEntityFeature.SET_SPEED 
        
        if (self.device.supports_preset_modes):
            supported_features = supported_features | FanEntityFeature.PRESET_MODE
        if (self.device.supports_oscillation):
            supported_features = supported_features | FanEntityFeature.OSCILLATE

        return supported_features

    def turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the device on."""
        _LOGGER.debug("DreoFanHA:turn_on")
        self.device.set_power(True)

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        _LOGGER.debug("DreoFanHA:turn_off")
        self.device.set_power(False)

    def set_percentage(self, percentage: int) -> None:
        """Set the speed of the device."""
        if percentage == 0:
            self.device.set_power(False)
            return

        if not self.device.is_on:
            self.device.set_power(True)

        self.device.change_fan_speed(
            math.ceil(percentage_to_ranged_value(self.device.speed_range, percentage))
        )
        self.schedule_update_ha_state()

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of device."""
        if preset_mode not in self.preset_modes:
            raise ValueError(
                f"{preset_mode} is not one of the valid preset modes: "
                f"{self.preset_modes}"
            )

        if not self.device.is_on:
            self.device.set_power(True)

        self.device.set_preset_mode(preset_mode)

        self.schedule_update_ha_state()

    def oscillate(self, oscillating: bool) -> None:
        """Oscillate the fan."""
        self.device.oscillate(oscillating)
        self.schedule_update_ha_state()

    async def async_added_to_hass(self):
        """Register callbacks."""

        @callback
        def update_state():
            _LOGGER.debug("callback:" + self._attr_name)
            # Tell HA we're ready to update
            self.async_schedule_update_ha_state()

        _LOGGER.debug("DreoBaseDeviceHA: %s registering callbacks", self._attr_name)
        self.device.add_attr_callback(update_state)
