"""Constants for Dreo Integration for HomeAssistant."""

LOGGER = "dreo"
DOMAIN = "dreo"
DREO_DISCOVERY = "dreo_discovery_{}"
SERVICE_UPDATE_DEVS = "update_devices"
PYDREO_MANAGER = "pydreo_manager"
DREO_PLATFORMS = "platforms"

CONF_AUTO_RECONNECT = "auto_reconnect"

from .const_debug_test_mode import *  # pylint: disable=W0401,W0614