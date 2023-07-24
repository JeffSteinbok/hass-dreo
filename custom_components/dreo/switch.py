"""Support additionl switches for some Dreo devices"""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613
from __future__ import annotations

from collections.abc import Callable
from typing import Any
from dataclasses import dataclass
import logging

from .haimports import * # pylint: disable=W0401,W0614
from .basedevice import DreoBaseDeviceHA
from .pydreo.pydreobasedevice import PyDreoBaseDevice


from .const import (
    LOGGER,
    DOMAIN,
    DREO_MANAGER
)

_LOGGER = logging.getLogger(LOGGER)

@dataclass
class DreoSwitchEntityDescription(SwitchEntityDescription):
    """Describe Dreo Switch entity."""
    attr_name: str = None

SWITCHES: tuple[DreoSwitchEntityDescription, ...] = (
    DreoSwitchEntityDescription(
        key="hosc",
        translation_key="hosc",
        attr_name="oscillating"
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Switch platform."""
    _LOGGER.info("Starting Dreo Switch Platform")
    _LOGGER.debug("Dreo Switch:async_setup_platform")

    manager = hass.data[DOMAIN][DREO_MANAGER]

    switch_ha_colletion = []
    for fan_entity in manager.fans:
        # Really ugly hack since there is just one Switch for now...
        switch_ha_colletion.append(DreoSwitchHA(fan_entity, SWITCHES[0]))

    async_add_entities(switch_ha_colletion)


class DreoSwitchHA(DreoBaseDeviceHA, SwitchEntity):
    """Representation of a Switch describing a read-only property of a Dreo device."""

    def __init__(self, 
                 pyDreoDevice: PyDreoBaseDevice,
                 definition: DreoSwitchEntityDescription) -> None:
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice
        self.entity_definition = definition
        self._attr_name = super().name + " " + definition.key
        self._attr_unique_id = f"{super().unique_id}-{definition.key}"

    @property
    def is_on(self) -> bool:
        """Return True if device is on."""
        _LOGGER.debug("DreoSwitchHA:is_on")
        return getattr(self.device, self.entity_definition.attr_name)

    def turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the device on."""
        _LOGGER.debug("DreoSwitchHA:turn_on")
        return setattr(self.device, self.entity_definition.attr_name, True)

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        _LOGGER.debug("DreoSwitchHA:turn_off")
        return setattr(self.device, self.entity_definition.attr_name, False)
