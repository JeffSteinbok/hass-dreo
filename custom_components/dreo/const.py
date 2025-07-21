"""Constants for Dreo Integration for HomeAssistant."""

LOGGER = "dreo"
DOMAIN = "dreo"
DREO_DISCOVERY = "dreo_discovery_{}"
SERVICE_UPDATE_DEVS = "update_devices"
PYDREO_MANAGER = "pydreo_manager"
DREO_PLATFORMS = "platforms"

CONF_AUTO_RECONNECT = "auto_reconnect"

DEBUG_TEST_MODE : bool = False
# Uncomment to enable test mode.
# Tests will not pass if this is set to True to prevent accidental commits.
# DEBUG_TEST_MODE = True
DEBUG_TEST_MODE_DIRECTORY_NAME = "e2e_test_data"
DEBUG_TEST_MODE_DEVICES_FILE_NAME = "get_devices.json"
