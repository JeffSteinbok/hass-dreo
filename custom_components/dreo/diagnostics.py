"""Diagnostics support for the Dreo HomeAssistant Integration."""

# Suppress warnings about unused function arguments
# pylint: disable=W0613

from __future__ import annotations

import logging

from typing import Any

from .pydreo import PyDreo
from .haimports import * # pylint: disable=W0401,W0614
from .const import (
    DOMAIN,
    PYDREO_MANAGER,
    LOGGER
)

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
    "productId"
}

_LOGGER = logging.getLogger(LOGGER)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
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

def _redact_values(data: dict) -> dict:
    """Rebuild and redact values of a dictionary, recursively"""

    new_data = {}

    for key, item in data.items():
        if key not in KEYS_TO_REDACT:
            if isinstance(item, dict):
                new_data[key] = _redact_values(item)
            elif isinstance(item, list):
                new_data[key] = []
                for listitem in item:
                    if isinstance(listitem, dict):
                        new_data[key].append(_redact_values(listitem))
                    else:
                        new_data[key].append(listitem)
            else:
                new_data[key] = item
        else:
            new_data[key] = REDACTED

    return new_data
