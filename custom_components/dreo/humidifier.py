"""HomeAssistant Humidifier platform for Dreo Humidifiers."""
from __future__ import annotations
import logging

from .haimports import * # pylint: disable=W0401,W0614
from .pydreo import PyDreo, PyDreoBaseDevice, PyDreoHumidifier, PyDreoDehumidifier
from .pydreo.constant import DreoDeviceType
from .dreobasedevice import DreoBaseDeviceHA

from .dreodehumidifier import DreoDehumidifierHA
from .dreohumidifier import DreoHumidifierHA

from .const import (
    LOGGER,
    DOMAIN,
    PYDREO_MANAGER
)

_LOGGER = logging.getLogger(LOGGER)

def get_entries(pydreo_devices : list[PyDreoBaseDevice]) -> list:
    """Get the Dreo Humidifier entities for the devices."""
    humidifier_entities_ha = []

    for pydreo_device in pydreo_devices:
        if (pydreo_device.type == DreoDeviceType.HUMIDIFIER):
            _LOGGER.debug("Humidifier:get_entries: Found a %s - %s", pydreo_device.type, pydreo_device.name)
            humidifier_entities_ha.append(DreoHumidifierHA(pydreo_device))
        elif (pydreo_device.type == DreoDeviceType.DEHUMIDIFIER):
            _LOGGER.debug("Humidifier:get_entries: Found a %s - %s", pydreo_device.type, pydreo_device.name)
            humidifier_entities_ha.append(DreoDehumidifierHA(pydreo_device))

    return humidifier_entities_ha

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry, # pylint: disable=unused-argument
    async_add_entities: AddEntitiesCallback,
    _discovery_info=None,
) -> None:
    """Set up the Dreo Humidifier platform."""
    _LOGGER.info("Starting Dreo Humidifier Platform")
    _LOGGER.debug("Dreo Humidifier:async_setup_entry")

    pydreo_manager : PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    humidifier_entities_ha = get_entries(pydreo_manager.devices)

    _LOGGER.debug("Humidifier:async_setup_entry: Adding Humidifiers (%s)", len(humidifier_entities_ha))
    async_add_entities(humidifier_entities_ha)

