"""HomeAssistant fan platform for Dreo fans."""
from __future__ import annotations
import logging

from .haimports import * # pylint: disable=W0401,W0614
from .pydreo import PyDreo, PyDreoBaseDevice
from .pydreo.constant import DreoDeviceType
from .dreofan import DreoFanHA 

from .const import (
    LOGGER,
    DOMAIN,
    PYDREO_MANAGER
)

_LOGGER = logging.getLogger(LOGGER)

def get_entries(pydreo_devices : list[PyDreoBaseDevice]) -> list[DreoFanHA]:
    """Get the Dreo Fan entities for the devices."""
    fan_entities_ha : DreoFanHA = []

    for pydreo_device in pydreo_devices:
        if (pydreo_device.type == DreoDeviceType.TOWER_FAN or
            pydreo_device.type == DreoDeviceType.AIR_CIRCULATOR or
            pydreo_device.type == DreoDeviceType.AIR_PURIFIER or
            pydreo_device.type == DreoDeviceType.CEILING_FAN or
            pydreo_device.type == DreoDeviceType.DEHUMIDIFIER or
            pydreo_device.type == DreoDeviceType.EVAPORATIVE_COOLER):
            _LOGGER.debug("Fan:get_entries: Found a %s - %s", pydreo_device.type, pydreo_device.name)
            fan_entities_ha.append(DreoFanHA(pydreo_device))

    return fan_entities_ha

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry, # pylint: disable=unused-argument
    async_add_entities: AddEntitiesCallback,
    _discovery_info=None,
) -> None:
    """Set up the Dreo fan platform."""
    _LOGGER.info("Starting Dreo Fan Platform")
    _LOGGER.debug("Dreo Fan:async_setup_entry")

    pydreo_manager : PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    fan_entities_ha = get_entries(pydreo_manager.devices)

    _LOGGER.debug("Fan:async_setup_entry: Adding Fans (%s)", len(fan_entities_ha))
    async_add_entities(fan_entities_ha)
