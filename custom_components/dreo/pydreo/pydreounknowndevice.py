"""Dreo Device class for unknown devices."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME,
    DreoDeviceType
)

from .pydreobasedevice import PyDreoBaseDevice
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo

class PyDreoUnknownDevice(PyDreoBaseDevice):
    """Dreo Device class for unknown devices."""

    def __init__(self, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize the Dreo Device."""
        super().__init__(DreoDeviceDetails(device_type = DreoDeviceType.UNKNOWN), details, dreo)
