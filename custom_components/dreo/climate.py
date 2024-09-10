"""HomeAssistant Climate platform for Dreo fans."""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613
import logging

from .haimports import *  # pylint: disable=W0401,W0614
from .pydreo import PyDreo, PyDreoBaseDevice
from .pydreo.constant import DreoDeviceType
from .dreoairconditioner import DreoAirConditionerHA
from .dreoheater import DreoHeaterHA

from .const import (
    LOGGER,
    DOMAIN,
    PYDREO_MANAGER,
)

_LOGGER = logging.getLogger(LOGGER)


def get_entries(
    pydreo_devices: list[PyDreoBaseDevice],
) -> list[DreoHeaterHA | DreoAirConditionerHA]:
    """Get the Dreo climate entities for the devices."""
    climate_entities_ha: DreoHeaterHA | DreoAirConditionerHA = []

    for pydreo_device in pydreo_devices:
        for pydreo_device in pydreo_devices:
            if pydreo_device.type == DreoDeviceType.HEATER:
                _LOGGER.debug(
                    "climate:get_entries: Found a Heater - %s", pydreo_device.name
                )
                climate_entities_ha.append(DreoHeaterHA(pydreo_device))
            elif pydreo_device.type == DreoDeviceType.AIR_CONDITIONER:
                _LOGGER.debug(
                    "climate:get_entries: Found an Air Conditioner - %s",
                    pydreo_device.name,
                )
                climate_entities_ha.append(DreoAirConditionerHA(pydreo_device))

    return climate_entities_ha


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Climate platform."""
    _LOGGER.info("Starting Dreo Climate Platform")
    _LOGGER.debug("Dreo Climate:async_setup_entry")

    pydreo_manager: PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    climate_entities_ha = get_entries(pydreo_manager.devices)

    _LOGGER.debug(
        "Climate:async_setup_entry: Adding Climate Devices (%s)",
        len(climate_entities_ha),
    )
    async_add_entities(climate_entities_ha)
