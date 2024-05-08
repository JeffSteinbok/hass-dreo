"""BaseDevice utilities for Dreo Component."""
import logging

from .pydreo.pydreobasedevice import PyDreoBaseDevice
from .haimports import * # pylint: disable=W0401,W0614

from .const import (
    LOGGER,
    DOMAIN
)

_LOGGER = logging.getLogger(LOGGER)

class DreoBaseDeviceHA(Entity):
    """Base class for Dreo Entity Representations."""

    def __init__(self, pydreo_base_device: PyDreoBaseDevice) -> None:
        """Initialize the Dreo device."""
        self.device = pydreo_base_device
        self._attr_unique_id = self.device.sn
        self._attr_name = pydreo_base_device.name

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""

        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.device.sn)
            },
            name=self.device.name,
            manufacturer="Dreo",
            model=self.device.model
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
            # Tell HA we're ready to update
            self.async_schedule_update_ha_state(True)

        self.device.add_attr_callback(update_state)
