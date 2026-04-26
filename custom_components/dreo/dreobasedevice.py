"""BaseDevice utilities for Dreo Component."""

from datetime import timedelta

from .pydreo.pydreobasedevice import PyDreoBaseDevice
from .haimports import *  # pylint: disable=W0401,W0614

from .const import DOMAIN


SCAN_INTERVAL = timedelta(minutes=5)
"""How often HA polls each entity to refresh device state from the REST API.

Push notifications (WebSocket) handle real-time state changes, but the poll
provides a safety net to detect devices that go offline without sending a
WebSocket disconnect notification (e.g. a device that is abruptly unplugged).
"""

class DreoBaseDeviceHA(Entity):
    """Base class for Dreo Entity Representations."""

    def __init__(self, pydreo_base_device: PyDreoBaseDevice) -> None:
        """Initialize the Dreo device."""
        self.pydreo_device = pydreo_base_device
        self._attr_unique_id = self.pydreo_device.serial_number
        self._attr_name = pydreo_base_device.name

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""

        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.pydreo_device.serial_number)
            },
            name=self.pydreo_device.name,
            manufacturer="Dreo",
            model=self.pydreo_device.model,
        )

    @property
    def available(self) -> bool:
        """Return True if device is available."""
        connected = self.pydreo_device.connected
        if connected is None:
            return True
        return connected

    @property
    def should_poll(self):
        return True

    def update(self) -> None:
        """Fetch the latest device state from the REST API.

        Called by HA at the SCAN_INTERVAL cadence.  Multiple entities may share
        a single PyDreo device object; PyDreoBaseDevice.refresh_state() is
        internally throttled so only one REST API call is made per device per
        poll cycle regardless of how many entities request an update.
        """
        self.pydreo_device.refresh_state()

    async def async_added_to_hass(self):
        """Register callbacks."""

        # Create a callback to update state in HA and add it a callback in
        # the PyDreo device. This will cause all handle_server_update responses
        # to update the state in HA.
        @callback
        def update_state():
            # Tell HA we're ready to update
            self.schedule_update_ha_state(True)

        self.pydreo_device.add_attr_callback(update_state)
