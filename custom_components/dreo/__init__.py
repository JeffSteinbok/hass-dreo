"""Dreo HomeAssistant Integration."""

import logging
import time

from .haimports import *  # pylint: disable=W0401,W0614
from .const import (
    LOGGER,
    DOMAIN,
    PYDREO_MANAGER,
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
    from .pydreo.constant import DreoDeviceType # pylint: disable=C0415

    pydreo_manager = PyDreo(username, password, region)
    pydreo_manager.auto_reconnect = auto_reconnect

    login = await hass.async_add_executor_job(pydreo_manager.login)

    if not login:
        _LOGGER.error("Unable to login to the dreo server")
        return False

    load_devices = await hass.async_add_executor_job(pydreo_manager.load_devices)

    if not load_devices:
        _LOGGER.error("Unable to load devices from the dreo server")
        return False

    _LOGGER.debug("Checking for supported installed device types")
    device_types = set()
    for device in pydreo_manager.devices:
        device_types.add(device.type)   
    _LOGGER.debug("Device types found are: %s", device_types)
    _LOGGER.info("%d Dreo devices found", len(pydreo_manager.devices))

    platforms = set()
    if (DreoDeviceType.TOWER_FAN in device_types or 
        DreoDeviceType.AIR_CIRCULATOR in device_types or
        DreoDeviceType.AIR_PURIFIER in device_types or
        DreoDeviceType.CEILING_FAN in device_types):
        platforms.add(Platform.FAN)
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)

    if (DreoDeviceType.HEATER in device_types or 
        DreoDeviceType.AIR_CONDITIONER in device_types):
        platforms.add(Platform.CLIMATE)
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)

    if (DreoDeviceType.HUMIDIFIER in device_types):
        platforms.add(Platform.HUMIDIFIER)
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)

    if (DreoDeviceType.CHEF_MAKER in device_types):
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)

    pydreo_manager.start_transport()

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][PYDREO_MANAGER] = pydreo_manager
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
    pydreo_manager = hass.data[DOMAIN][PYDREO_MANAGER]
    if unload_ok := await hass.config_entries.async_unload_platforms(
        config_entry,
        hass.data[DOMAIN][DREO_PLATFORMS],
    ):
        hass.data.pop(DOMAIN)

    pydreo_manager.stop_transport()
    return unload_ok
