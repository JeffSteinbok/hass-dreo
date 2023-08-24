"""Dreo HomeAssistant Integration."""
import logging
import time

from .haimports import * # pylint: disable=W0401,W0614
from .const import (
    LOGGER,
    DOMAIN,
    DREO_FANS,
    DREO_MANAGER,
    CONF_AUTO_RECONNECT
)

_LOGGER = logging.getLogger(LOGGER)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    "HomeAssistant EntryPoint"
    _LOGGER.debug("async_setup_entry")

    _LOGGER.debug(config_entry.data.get(CONF_USERNAME))
    username = config_entry.data.get(CONF_USERNAME)
    password = config_entry.data.get(CONF_PASSWORD)
    auto_reconnect = config_entry.options.get(CONF_AUTO_RECONNECT)
    if (auto_reconnect is None):
        _LOGGER.debug("auto_reconnect is None.  Default to True")
        auto_reconnect = True

    region = "us"

    from .pydreo import PyDreo # pylint: disable=C0415

    manager = PyDreo(username, password, region)
    manager.auto_reconnect = auto_reconnect

    login = await hass.async_add_executor_job(manager.login)

    if not login:
        _LOGGER.error("Unable to login to the dreo server")
        return False

    load_devices = await hass.async_add_executor_job(manager.load_devices)

    if not load_devices:
        _LOGGER.error("Unable to load devices from the dreo server")
        return False

    device_dict = process_devices(manager)

    manager.start_transport()
    
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][DREO_MANAGER] = manager

    fans = hass.data[DOMAIN][DREO_FANS] = []
    platforms = []

    _LOGGER.debug(device_dict)
    if device_dict[DREO_FANS]:
        fans.extend(device_dict[DREO_FANS])
        platforms.append(Platform.FAN)
        platforms.append(Platform.SENSOR)
        platforms.append(Platform.SWITCH)
        platforms.append(Platform.NUMBER)

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
