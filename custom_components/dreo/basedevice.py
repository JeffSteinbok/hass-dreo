"""BaseDevice utilities for Dreo Component."""
import logging
from typing import Any

# from .pydreo.pydreobasedevice import PyDreoBaseDevice

from homeassistant.helpers.entity import DeviceInfo, Entity, ToggleEntity
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, DREO_FANS

_LOGGER = logging.getLogger("dreo")

from .pydreo.pydreobasedevice import PyDreoBaseDevice


class DreoBaseDeviceHA(Entity):
    """Base class for Dreo Entity Representations."""

    def __init__(self, pyDreoBaseDevice: PyDreoBaseDevice) -> None:
        """Initialize the Dreo device."""
        self.device = pyDreoBaseDevice
        self._attr_unique_id = self.device.sn
        self._attr_name = pyDreoBaseDevice.name

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""

        #TODO: Return more field; customize by subclass.
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.device.sn)
            },
            name=self.device.name,
            manufacturer="Dreo"
        )

    @property
    def available(self) -> bool:
        """Return True if device is available."""
        # return self.device.connection_status == "online"
        return True

    @property
    def should_poll(self):
        return False

    async def async_added_to_hass(self):
        """Register callbacks."""

        @callback
        def update_state():
            _LOGGER.debug("callback:" + self._attr_name)
            # Tell HA we're ready to update
            self.async_schedule_update_ha_state()

        _LOGGER.debug("DreoBaseDeviceHA: %s registering callbacks", self._attr_name)
        self.device.add_attr_callback(update_state)