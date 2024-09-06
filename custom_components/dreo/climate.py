"""HomeAssistant Climate platform for Dreo fans."""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613
import logging

from .haimports import *  # pylint: disable=W0401,W0614
from .pydreo import PyDreo
from .pydreo.constant import DreoDeviceType
from .dreoairconditioner import DreoAirConditionerHA
from .dreoheater import DreoHeaterHA

from .const import (
    LOGGER,
    DOMAIN,
    PYDREO_MANAGER,
)

_LOGGER = logging.getLogger(LOGGER)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Climate platform."""
    _LOGGER.info("Starting Dreo Climate Platform")
    _LOGGER.debug("Dreo Climate:async_setup_entry")

    pydreo_manager: PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    climate_entities_ha = []
    for pydreo_device in pydreo_manager.devices:
        if pydreo_device.type == DreoDeviceType.HEATER:
            climate_entities_ha.append(DreoHeaterHA(pydreo_device))
        elif pydreo_device.type == DreoDeviceType.AIR_CONDITIONER:
            climate_entities_ha.append(DreoAirConditionerHA(pydreo_device))

    _LOGGER.debug("Climate:async_setup_entry: Adding Climate Devices (%s)", climate_entities_ha.count)
    async_add_entities(climate_entities_ha)
