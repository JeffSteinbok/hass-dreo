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

    def __repr__(self):
        # Representation string of object.
        return "<{0}:{1}:{2}>".format(
            self.__class__.__name__, self.attr_name, self.key
        )


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
    ),
    DreoNumberEntityDescription(
        key="Target Temperature",
        translation_key="target_temp",
        attr_name="ecolevel",
        icon="mdi:temperature",
        min_value=0,
        max_value=100
    )
)


def add_entries(devices) -> []:
    number_ha_collection = []
    
    for de in devices:
        _LOGGER.debug("Number:add_entries: Adding Numbers for %s", de.name)
        for number_definition in NUMBERS:
            _LOGGER.debug("Number:add_entries: checking attribute: %s on %s", number_definition.attr_name, de.name)
            if de.is_feature_supported(number_definition.attr_name):
                _LOGGER.debug("Number:add_entries: Adding Number %s for %s", number_definition.key, number_definition.attr_name)
                if hasattr(de.device_definition.range, number_definition.attr_name + "_range") and \
                        de.device_definition.range[number_definition.attr_name + "_range"] is not None:
                    n_range = de.device_definition.range[number_definition.attr_name + "_range"]
                    _LOGGER.debug("Number:add_entries: range %s is %s", number_definition.attr_name + "_range", n_range)
                    if isinstance(n_range, tuple):
                        dned = DreoNumberEntityDescription(key=number_definition.key,
                                                           translation_key=number_definition.translation_key,
                                                           attr_name=number_definition.attr_name,
                                                           icon=number_definition.icon,
                                                           min_value=n_range[0],
                                                           max_value=n_range[1])
                        number_ha_collection.append(DreoNumberHA(de, dned))
                else:
                    number_ha_collection.append(DreoNumberHA(de,number_definition))
    
    return number_ha_collection
    

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Number platform."""
    _LOGGER.info("Starting Dreo Number Platform")

    manager : PyDreo = hass.data[DOMAIN][DREO_MANAGER]

    async_add_entities(add_entries(manager.fans))
    async_add_entities(add_entries(manager.heaters))


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