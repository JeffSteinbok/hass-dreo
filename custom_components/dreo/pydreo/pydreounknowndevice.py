"""Dreo Device class for unknown devices."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import (
    LOGGER_NAME
)

from .pydreobasedevice import PyDreoBaseDevice
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(LOGGER_NAME)

if TYPE_CHECKING:
    from pydreo import PyDreo

class PyDreoUnknownDevice(PyDreoBaseDevice):
    """Dreo Device class for unknown devices."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):  #pylint: disable=useless-super-delegation
        """Initialize the Dreo Device."""
        super().__init__(device_definition, details, dreo)
