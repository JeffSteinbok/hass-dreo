"""BaseDevice utilities for Dreo Component."""
import logging
from typing import Any

#from .pydreo.pydreobasedevice import PyDreoBaseDevice

from homeassistant.helpers.entity import DeviceInfo, Entity, ToggleEntity
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, DREO_FANS

_LOGGER = logging.getLogger("dreo")

from .pydreo.pydreobasedevice import PyDreoBaseDevice

class DreoBaseDeviceHA(Entity):
    """Base class for Dreo Entity Representations."""

    def __init__(self, pyDreoBaseDevice : PyDreoBaseDevice) -> None:
        """Initialize the Dreo device."""
        self.device = pyDreoBaseDevice
        self._attr_unique_id = self.device.sn
        self._attr_name = pyDreoBaseDevice.name

    @property
    def available(self) -> bool:
        """Return True if device is available."""
        #return self.device.connection_status == "online"
        return True

    @property
    def should_poll(self):
        return False

