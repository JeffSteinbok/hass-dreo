"""Tests for the Dreo Base Device HA class."""

from unittest.mock import patch, MagicMock

from custom_components.dreo.dreobasedevice import DreoBaseDeviceHA
from custom_components.dreo.const import DOMAIN

from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"


class TestDreoBaseDeviceHA(TestDeviceBase):
    """Test the Dreo Base Device HA class."""

    def test_base_device_init(self):
        """Test base device initialization."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Test Device",
                serial_number="DEV001",
            )

            base = DreoBaseDeviceHA(device)
            assert base._attr_name == "Test Device"
            assert base._attr_unique_id == "DEV001"
            assert base.pydreo_device == device

    def test_base_device_info(self):
        """Test device_info property."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Test Device", serial_number="DEV001", features={"model": "DR-HTF001S"})

            base = DreoBaseDeviceHA(device)
            info = base.device_info

            assert info is not None
            assert info["manufacturer"] == "Dreo"
            assert (DOMAIN, "DEV001") in info["identifiers"]

    def test_base_device_available(self):
        """Test available property returns True when connected is None (unknown)."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Test Device",
                serial_number="DEV001",
            )
            device.connected = None
            base = DreoBaseDeviceHA(device)
            assert base.available is True

    def test_base_device_available_when_connected(self):
        """Test available property returns True when device is connected."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Test Device",
                serial_number="DEV001",
            )
            device.connected = True
            base = DreoBaseDeviceHA(device)
            assert base.available is True

    def test_base_device_available_when_disconnected(self):
        """Test available property returns False when device is not connected."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Test Device",
                serial_number="DEV001",
            )
            device.connected = False
            base = DreoBaseDeviceHA(device)
            assert base.available is False

    def test_base_device_should_poll(self):
        """Test should_poll returns False (push-based via WebSocket)."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Test Device",
                serial_number="DEV001",
            )

            base = DreoBaseDeviceHA(device)
            assert base.should_poll is False
