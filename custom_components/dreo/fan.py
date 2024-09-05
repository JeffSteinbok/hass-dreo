"""HomeAssistant fan platform for Dreo fans."""
from __future__ import annotations
import logging

from .haimports import * # pylint: disable=W0401,W0614

from .dreofan import DreoFanHA 
from .dreoairpurifier import DreoAirPurifierHA

from .const import (
    LOGGER,
    DOMAIN,
    PYDREO_MANAGER
)

from .pydreo import PyDreo
from .pydreo.constant import DreoDeviceType

_LOGGER = logging.getLogger(LOGGER)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    _discovery_info=None,
) -> None:
    """Set up the Dreo fan platform."""
    _LOGGER.info("Starting Dreo Fan Platform")
    _LOGGER.debug("Dreo Fan:async_setup_entry")

    pydreo_manager : PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    fan_entities_ha = []
    for pydreo_device in pydreo_manager.devices:
        if (pydreo_device.type == DreoDeviceType.TOWER_FAN or
            pydreo_device.type == DreoDeviceType.AIR_CIRCULATOR):
            fan_entities_ha.append(DreoFanHA(pydreo_device))

    _LOGGER.debug("Fan:async_setup_entry: Adding Fans: %s", fan_entities_ha)
    _LOGGER.debug("vdebu add to plat: %s", fan_entities_ha[0].add_to_platform_start)
    async_add_entities(fan_entities_ha)
