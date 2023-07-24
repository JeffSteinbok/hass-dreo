"""Support additionl switches for some Dreo devices"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from .basedevice import DreoBaseDeviceHA
from .fan import DreoFanHA
from .pydreo.pydreobasedevice import PyDreoBaseDevice

_LOGGER = logging.getLogger("dreo")

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import *

@dataclass
class DreoSwitchEntityDescription(SwitchEntityDescription):
    """Describe Dreo Switch entity."""
    attr_name: str = None

SWITCHES: tuple[DreoSwitchEntityDescription, ...] = (
    DreoSwitchEntityDescription(
        key="hosc",
        translation_key="hosc",
        attr_name="hosc"
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

    switchHAs = []
    for fanEntity in manager.fans:
        # Really ugly hack since there is just one Switch for now...
        switchHAs.append(DreoSwitchHA(fanEntity, SWITCHES[0]))

    async_add_entities(switchHAs)


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
