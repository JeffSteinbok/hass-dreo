"""Support additionl Numberes for some Dreo devices"""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613
from __future__ import annotations
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
class DreoNumberEntityDescription(NumberEntityDescription):
    """Describe Dreo Number entity."""
    attr_name: str = None
    icon: str = None

NUMBERS: tuple[DreoNumberEntityDescription, ...] = (
    DreoNumberEntityDescription(
        key="Horizontal Angle",
        translation_key="horizontal_angle",
        attr_name="horizontal_angle",
        icon="mdi:angle-acute",
        min_value=-60,
        max_value=60,
    ),
    DreoNumberEntityDescription(
        key="Vertical Angle",
        translation_key="vertical_angle",
        attr_name="vertical_angle",
        icon="mdi:angle-acute",
        min_value=0,
        max_value=90
    )
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Number platform."""
    _LOGGER.info("Starting Dreo Number Platform")
    _LOGGER.debug("Dreo Number:async_setup_platform")

    manager : PyDreo = hass.data[DOMAIN][DREO_MANAGER]

    number_ha_colletion = []
    for fan_entity in manager.fans:
        _LOGGER.debug("Adding Numbers for %s", fan_entity.name)
        for number_definition in NUMBERS:
            if (fan_entity.is_feature_supported(number_definition.attr_name)):
                _LOGGER.debug("Adding Number %s", number_definition.key)
                number_ha_colletion.append(DreoNumberHA(fan_entity,number_definition))

    async_add_entities(number_ha_colletion)


class DreoNumberHA(DreoBaseDeviceHA, NumberEntity):
    """Representation of a Number describing a read-only property of a Dreo device."""

    def __init__(self, 
                 pyDreoDevice: PyDreoBaseDevice,
                 description: DreoNumberEntityDescription) -> None:
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice

        # Note this is a "magic" HA property.  Don't rename
        self.entity_description = description

        self._attr_name = super().name + " " + description.key
        self._attr_unique_id = f"{super().unique_id}-{description.key}"

        self._attr_native_min_value = description.min_value
        self._attr_native_max_value = description.max_value

    @property
    def native_value(self) -> float:
        """Return the state of the number."""
        return getattr(self.device, self.entity_description.attr_name)

    def set_native_value(self, value: float) -> None:
        return setattr(self.device, self.entity_description.attr_name, value)
