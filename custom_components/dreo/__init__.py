"""dreo integration."""
import logging
import threading

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    DOMAIN,
    SERVICE_UPDATE_DEVS,
    DREO_DISCOVERY,
    DREO_FANS,
    DREO_MANAGER
)

_LOGGER = logging.getLogger("dreo")


DOMAIN = "dreo"
COMPONENT_DOMAIN = "dreo"
COMPONENT_DATA = "dreo-data"
COMPONENT_ATTRIBUTION = "Data provided by Dreo servers."
COMPONENT_BRAND = "Dreo"

CONFIG_SCHEMA = vol.Schema(
    {
        COMPONENT_DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        ),
    },
    extra=vol.ALLOW_EXTRA
)

async def async_setup(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:

    _LOGGER.debug("async_setup")

    """Set up dreo as config entry."""
    username = config_entry[COMPONENT_DOMAIN].get(CONF_USERNAME)
    password = config_entry[COMPONENT_DOMAIN].get(CONF_PASSWORD)
    _LOGGER.debug(username)

    from .pydreo import PyDreo
    manager = PyDreo(username, password)

    login = await hass.async_add_executor_job(manager.login)

    if not login:
        _LOGGER.error("Unable to login to the dreo server")
        return False
    
    load_devices = await hass.async_add_executor_job(manager.load_devices)

    if not load_devices:
        _LOGGER.error("Unable to load devices from the dreo server")
        return False

    # TODO: What's the difference?
    #device_dict = await hass.async_add_executor_job(async_process_devices, hass, manager)
    device_dict = await async_process_devices(hass, manager)

    # TODO: Move all of this into the manager init?
    manager.start_monitoring()

    #forward_setup = hass.config_entries.async_forward_entry_setup
    hass.data[COMPONENT_DATA] = manager
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][DREO_MANAGER] = manager

    fans = hass.data[DOMAIN][DREO_FANS] = []
    platforms = []

    _LOGGER.debug(device_dict)
    if device_dict[DREO_FANS]:
        fans.extend(device_dict[DREO_FANS])
        platforms.append(Platform.FAN)

    #await hass.config_entries.async_forward_entry_setups(config_entry, platforms)

    async def async_new_device_discovery(service: ServiceCall) -> None:
        """Discover if new devices should be added."""
        manager = hass.data[DOMAIN][DREO_MANAGER]
        fans = hass.data[DOMAIN][DREO_FANS]
        
        dev_dict = await async_process_devices(hass, manager)
        fan_devs = dev_dict.get(DREO_FANS, [])

        fan_set = set(fan_devs)
        new_fans = list(fan_set.difference(fans))
        if new_fans and fans:
            fans.extend(new_fans)
            async_dispatcher_send(hass, DREO_DISCOVERY.format(DREO_FANS), new_fans)
            return
        if new_fans and not fans:
            fans.extend(new_fans)
            hass.async_create_task(forward_setup(config_entry, Platform.FAN))


        manager.start_monitoring()

    return True

async def async_process_devices(hass, manager):
    """Assign devices to proper component."""
    devices = {}
    devices[DREO_FANS] = []

    if manager.fans:
        devices[DREO_FANS].extend(manager.fans)
        # Expose fan sensors separately
        _LOGGER.info("%d Dreo fans found", len(manager.fans))

    return devices