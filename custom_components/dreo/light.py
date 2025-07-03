"""HomeAssistant fan platform for Dreo fans."""
from __future__ import annotations
import logging

from custom_components.dreo.pydreo.mixins.ledmixin import LedMixin


from .haimports import * # pylint: disable=W0401,W0614
from .pydreo import PyDreo, PyDreoBaseDevice
from .dreolight import DreoLightHA 

from .const import (
    LOGGER,
    DOMAIN,
    PYDREO_MANAGER
)

_LOGGER = logging.getLogger(LOGGER)

def get_entries(pydreo_devices : list[PyDreoBaseDevice]) -> list[DreoLightHA]:
    light_entities_ha: list[DreoLightHA] = []

    for pydreo_device in pydreo_devices:
        if isinstance(pydreo_device, LedMixin):
            _LOGGER.debug("Light:get_entries: Found a %s - %s", pydreo_device.type, pydreo_device.name)
            light_entities_ha.append(DreoLightHA(pydreo_device))

    return light_entities_ha

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry, # pylint: disable=unused-argument
    async_add_entities: AddEntitiesCallback,
    _discovery_info=None,
) -> None:
    """Set up the Dreo fan platform."""
    _LOGGER.info("Starting Dreo Light Platform")
    _LOGGER.debug("Dreo Light:async_setup_entry")

    pydreo_manager : PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    light_entities_ha = get_entries(pydreo_manager.devices)

    _LOGGER.debug("Light:async_setup_entry: Adding Lights (%s)", len(light_entities_ha))
    async_add_entities(light_entities_ha)
