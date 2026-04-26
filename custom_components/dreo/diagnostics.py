"""Diagnostics support for the Dreo HomeAssistant Integration."""

# Suppress warnings about unused function arguments
# pylint: disable=W0613

from __future__ import annotations

import logging

from typing import Any

from .pydreo import PyDreo
from .haimports import *  # pylint: disable=W0401,W0614
from .const import DOMAIN, PYDREO_MANAGER

KEYS_TO_REDACT = {
    "sn",
    "_sn",
    "wifi_ssid",
    "module_hardware_mac",
    "password",
    "_password",
    "username",
    "_username",
    "token",
    "_token",
    "access_token",
    "productId",
    "deviceId",
}

# Keys whose values are non-serializable objects (live references, locks, callbacks)
# and should be excluded entirely from diagnostics output.
KEYS_TO_EXCLUDE = {
    "_dreo",
    "_device_definition",
    "_lock",
    "_attr_cbs",
}

_LOGGER = logging.getLogger(__name__)


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    pydreo_manager: PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    return _get_diagnostics(pydreo_manager)


def _get_diagnostics(pydreo_manager: PyDreo) -> dict[str, Any]:
    data = {
        DOMAIN: {
            "device_count": len(pydreo_manager.devices),
            "raw_devicelist": _redact_values(pydreo_manager.raw_response),
        },
        "devices": [_redact_values(device.__dict__) for device in pydreo_manager.devices],
    }

    return data


def _is_json_serializable(value) -> bool:
    """Check if a value is a JSON-safe primitive type."""
    return isinstance(value, (str, int, float, bool, type(None)))


def _redact_values(data) -> dict:
    """Rebuild and redact values of a dictionary, recursively."""

    if not isinstance(data, dict):
        return data

    new_data = {}

    for key, item in data.items():
        if key in KEYS_TO_EXCLUDE:
            continue
        if key in KEYS_TO_REDACT:
            new_data[key] = REDACTED
        elif isinstance(item, dict):
            new_data[key] = _redact_values(item)
        elif isinstance(item, list):
            new_data[key] = [
                _redact_values(li) if isinstance(li, dict) else li for li in item if _is_json_serializable(li) or isinstance(li, (dict, list))
            ]
        elif _is_json_serializable(item):
            new_data[key] = item
        # Skip non-serializable values (objects, locks, callbacks, etc.)

    return new_data
