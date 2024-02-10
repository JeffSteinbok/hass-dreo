"""Support additionl switches for some Dreo devices"""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613
from __future__ import annotations

from typing import Any
from dataclasses import dataclass
import logging

from .haimports import * # pylint: disable=W0401,W0614
from .basedevice import DreoBaseDeviceHA
from .pydreo import PyDreo
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
    icon: str = None

SWITCHES: tuple[DreoSwitchEntityDescription, ...] = (
    DreoSwitchEntityDescription(
        key="Horizontally Oscillating",
        translation_key="horizontally_oscillating",
        attr_name="horizontally_oscillating",
        icon="mdi:rotate-360"
    ),
    DreoSwitchEntityDescription(
        key="Vertically Oscillating",
        translation_key="vertically_oscillating",
        attr_name="vertically_oscillating",
        icon="mdi:rotate-360"
    ),
    DreoSwitchEntityDescription(
        key="Display Auto Off",
        translation_key="display_auto_off",
        attr_name="display_auto_off",
        icon="mdi:monitor"
    ),
    DreoSwitchEntityDescription(
        key="Panel Sound",
        translation_key="panel_sound",
        attr_name="panel_sound",
        icon="mdi:volume-high"
    ),
    DreoSwitchEntityDescription(
        key="Adaptive Brightness",
        translation_key="adaptive_brightness",
        attr_name="adaptive_brightness",
        icon="mdi:monitor"
    ),
    DreoSwitchEntityDescription(
        key="Device Power",
        translation_key="poweron",
        attr_name="poweron",
        icon="mdi:power"
    ),
    DreoSwitchEntityDescription(
        key="Panel Mute",
        translation_key="mute_on",
        attr_name="mute_on",
        icon="mdi:volume-high"
    ),
    DreoSwitchEntityDescription(
        key="Oscillating",
        translation_key="oscon",
        attr_name="oscon",
        icon="mdi:rotate-360"
    ),
    DreoSwitchEntityDescription(
        key="PTC",
        translation_key="ptcon",
        attr_name="ptcon",
        icon="mdi:help"
    ),
    DreoSwitchEntityDescription(
        key="Display Auto Off",
        translation_key="lighton",
        attr_name="lighton",
        icon="mdi:led-on"
    ),
    DreoSwitchEntityDescription(
        key="Child Lock",
        translation_key="childlockon",
        attr_name="childlockon",
        icon="mdi:lock"
    )
)


def add_device_entries(devices) -> []:
    switch_ha_collection = []
    
    for de in devices:
        _LOGGER.debug("Adding switches for %s", de.name)
        for switch_definition in SWITCHES:
            if (de.is_feature_supported(switch_definition.attr_name)):
                _LOGGER.debug("Adding switch %s", switch_definition.key)
                switch_ha_collection.append(DreoSwitchHA(de,switch_definition))
    
    return switch_ha_collection


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Switch platform."""
    _LOGGER.info("Starting Dreo Switch Platform")

    manager : PyDreo = hass.data[DOMAIN][DREO_MANAGER]

    async_add_entities(add_device_entries(manager.fans))
    async_add_entities(add_device_entries(manager.heaters))


class DreoSwitchHA(DreoBaseDeviceHA, SwitchEntity):
    """Representation of a Switch describing a read-only property of a Dreo device."""

    def __init__(self, 
                 pyDreoDevice: PyDreoBaseDevice,
                 description: DreoSwitchEntityDescription) -> None:
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice

        # Note this is a "magic" HA property.  Don't rename
        self.entity_description = description

        self._attr_name = super().name + " " + description.key
        self._attr_unique_id = f"{super().unique_id}-{description.key}"

    @property
    def is_on(self) -> bool:
        """Return True if device is on."""
        _LOGGER.debug("DreoSwitchHA:is_on")
        attr = getattr(self.device, self.entity_description.attr_name)
        return attr


    def turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the device on."""
        return setattr(self.device, self.entity_description.attr_name, True)

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        return setattr(self.device, self.entity_description.attr_name, False)
