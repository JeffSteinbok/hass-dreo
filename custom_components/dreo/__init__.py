"""dreo integration."""
import logging
import threading

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_REGION, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, DREO_FANS, DREO_SENSORS, DREO_MANAGER

_LOGGER = logging.getLogger("dreo")

DOMAIN = "dreo"


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    _LOGGER.debug("async_setup")

    _LOGGER.debug(config_entry.data.get(CONF_USERNAME))
    username = config_entry.data.get(CONF_USERNAME)
    password = config_entry.data.get(CONF_PASSWORD)
    region = "us"

    from .pydreo import PyDreo

    manager = PyDreo(username, password, region)

    login = await hass.async_add_executor_job(manager.login)

    if not login:
        _LOGGER.error("Unable to login to the dreo server")
        return False

    load_devices = await hass.async_add_executor_job(manager.load_devices)

    if not load_devices:
        _LOGGER.error("Unable to load devices from the dreo server")
        return False

    device_dict = process_devices(manager)

    manager.start_monitoring()

    forward_setup = hass.config_entries.async_forward_entry_setup
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][DREO_MANAGER] = manager

    fans = hass.data[DOMAIN][DREO_FANS] = []
    platforms = []

    _LOGGER.debug(device_dict)
    if device_dict[DREO_FANS]:
        fans.extend(device_dict[DREO_FANS])
        platforms.append(Platform.FAN)
        platforms.append(Platform.SENSOR)  

    await hass.config_entries.async_forward_entry_setups(config_entry, platforms)
    return True

def process_devices(manager) -> dict:
    """Assign devices to proper component."""
    devices = {}
    devices[DREO_FANS] = []

    if manager.fans:
        devices[DREO_FANS].extend(manager.fans)
        # Expose fan sensors separately
        _LOGGER.info("%d Dreo fans found", len(manager.fans))

    return devices
