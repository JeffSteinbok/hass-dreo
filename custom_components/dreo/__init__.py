"""Dreo HomeAssistant Integration."""

import logging
import time

from .haimports import *  # pylint: disable=W0401,W0614
from .const import (
    LOGGER,
    DOMAIN,
    DREO_FANS,
    DREO_HEATERS,
    DREO_AIRCONDITIONERS,
    DREO_COOKERS,
    DREO_MANAGER,
    DREO_PLATFORMS,
    CONF_AUTO_RECONNECT,
)

_LOGGER = logging.getLogger(LOGGER)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    "HomeAssistant EntryPoint"
    _LOGGER.debug("async_setup_entry")

    _LOGGER.debug(config_entry.data.get(CONF_USERNAME))
    username = config_entry.data.get(CONF_USERNAME)
    password = config_entry.data.get(CONF_PASSWORD)
    auto_reconnect = config_entry.options.get(CONF_AUTO_RECONNECT)
    if auto_reconnect is None:
        _LOGGER.debug("auto_reconnect is None.  Default to True")
        auto_reconnect = True

    region = "us"

    from .pydreo import PyDreo  # pylint: disable=C0415

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
    _LOGGER.debug("Device dict is: %s", device_dict)

    manager.start_transport()

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][DREO_MANAGER] = manager

    fans = hass.data[DOMAIN][DREO_FANS] = []
    heaters = hass.data[DOMAIN][DREO_HEATERS] = []
    acs = hass.data[DOMAIN][DREO_AIRCONDITIONERS] = []
    cookers = hass.data[DOMAIN][DREO_COOKERS] = []
    platforms = set()

    if device_dict[DREO_FANS]:
        fans.extend(device_dict[DREO_FANS])
        platforms.add(Platform.FAN)
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)

    if device_dict[DREO_HEATERS]:
        heaters.extend(device_dict[DREO_HEATERS])
        platforms.add(Platform.CLIMATE)
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)

    if device_dict[DREO_AIRCONDITIONERS]:
        acs.extend(device_dict[DREO_AIRCONDITIONERS])
        platforms.add(Platform.CLIMATE)
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)

    if device_dict[DREO_COOKERS]:
        cookers.extend(device_dict[DREO_COOKERS])
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)
        
    hass.data[DOMAIN][DREO_PLATFORMS] = platforms

    _LOGGER.debug("Platforms are: %s", platforms)

    await hass.config_entries.async_forward_entry_setups(config_entry, platforms)

    async def _update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
        """Handle options update."""
        await hass.config_entries.async_reload(config_entry.entry_id)

    ## Create update listener
    config_entry.async_on_unload(config_entry.add_update_listener(_update_listener))

    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    manager = hass.data[DOMAIN][DREO_MANAGER]
    if unload_ok := await hass.config_entries.async_unload_platforms(
        config_entry,
        hass.data[DOMAIN][DREO_PLATFORMS],
    ):
        hass.data.pop(DOMAIN)

    manager.stop_transport()
    return unload_ok

def process_devices(manager) -> dict:
    """Assign devices to proper component."""
    devices = {}
    devices[DREO_FANS] = []
    devices[DREO_HEATERS] = []
    devices[DREO_AIRCONDITIONERS] = []
    devices[DREO_COOKERS] = []

    if manager.fans:
        devices[DREO_FANS].extend(manager.fans)
        # Expose fan sensors separately
        _LOGGER.info("%d Dreo fans found", len(manager.fans))

    if manager.heaters:
        devices[DREO_HEATERS].extend(manager.heaters)
        _LOGGER.info("%d Dreo heaters found", len(manager.heaters))

    if manager.acs:
        devices[DREO_AIRCONDITIONERS].extend(manager.acs)
        _LOGGER.info("%d Dreo ACs found", len(manager.acs))

    if manager.cookers:
        devices[DREO_COOKERS].extend(manager.cookers)
        _LOGGER.info("%d Dreo cookers found", len(manager.cookers))

    return devices
