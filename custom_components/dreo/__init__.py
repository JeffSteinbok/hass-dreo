"""Dreo HomeAssistant Integration."""
import logging
import time

from .haimports import * # pylint: disable=W0401,W0614
from .const import (
    LOGGER,
    DOMAIN,
    DREO_FANS,
    DREO_HEATERS,
    DREO_ACS,
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
    acs = hass.data[DOMAIN][DREO_ACS] = []
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

    if device_dict[DREO_ACS]:
        acs.extend(device_dict[DREO_ACS])
        platforms.add(Platform.CLIMATE)
        platforms.add(Platform.SENSOR)
        platforms.add(Platform.SWITCH)
        platforms.add(Platform.NUMBER)

    _LOGGER.debug("Platforms are: %s", platforms)

    for platform in platforms:
        await hass.config_entries.async_forward_entry_setup(config_entry, platform)

    return True

def process_devices(manager) -> dict:
    """Assign devices to proper component."""
    devices = {}
    devices[DREO_FANS] = []
    devices[DREO_HEATERS] = []
    devices[DREO_ACS] = []

    if manager.fans:
        devices[DREO_FANS].extend(manager.fans)
        # Expose fan sensors separately
        _LOGGER.info("%d Dreo fans found", len(manager.fans))

    if manager.heaters:
        devices[DREO_HEATERS].extend(manager.heaters)
        _LOGGER.info("%d Dreo heaters found", len(manager.heaters))

    if manager.acs:
        devices[DREO_ACS].extend(manager.acs)
        _LOGGER.info("%d Dreo ACs found", len(manager.acs))

    return devices
