"""Tests for the Dreo Dehumidifier HA class."""

from unittest.mock import patch

from custom_components.dreo.dreodehumidifier import DreoDehumidifierHA
from custom_components.dreo.haimports import HumidifierDeviceClass, HumidifierEntityFeature

from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"


class TestDreoDehumidifierHA(TestDeviceBase):
    """Test the Dreo Dehumidifier HA class."""

    def _create_dehumidifier(self, **overrides):
        """Helper to create a mocked dehumidifier device."""
        defaults = {
            "name": "Test Dehumidifier",
            "serial_number": "DH001",
            "type": "Dehumidifier",
            "features": {
                "is_on": True,
                "mode": "auto",
                "modes": ["auto", "manual", "dry_clothes", "sleep"],
                "humidity": 65,
                "target_humidity": 50,
                "brand": "Dreo",
                "series_name": "DR-HDH",
                "model": "DR-HDH001S",
                "product_name": "Dehumidifier",
                "device_name": "Test Dehumidifier",
            },
        }
        defaults.update(overrides)
        return self.create_mock_device(**defaults)

    def test_dehumidifier_basic_properties(self):
        """Test dehumidifier basic properties."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_dehumidifier()
            dehumidifier = DreoDehumidifierHA(device)

            assert dehumidifier.is_on is True
            assert dehumidifier.mode == "auto"
            assert dehumidifier.available_modes == ["auto", "manual", "dry_clothes", "sleep"]
            assert dehumidifier.current_humidity == 65
            assert dehumidifier.target_humidity == 50
            assert dehumidifier.min_humidity == 30
            assert dehumidifier.max_humidity == 85

    def test_dehumidifier_device_class(self):
        """Test dehumidifier returns correct device class."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_dehumidifier()
            dehumidifier = DreoDehumidifierHA(device)

            assert dehumidifier.device_class == HumidifierDeviceClass.DEHUMIDIFIER

    def test_dehumidifier_supported_features_with_modes(self):
        """Test supported features when modes are available."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_dehumidifier()
            dehumidifier = DreoDehumidifierHA(device)

            features = dehumidifier.supported_features
            assert features & HumidifierEntityFeature.MODES

    def test_dehumidifier_supported_features_without_modes(self):
        """Test supported features when modes are None."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_dehumidifier(
                features={
                    "is_on": True,
                    "mode": None,
                    "modes": None,
                    "humidity": 65,
                    "target_humidity": 50,
                    "brand": "Dreo",
                    "series_name": "DR-HDH",
                    "model": "DR-HDH001S",
                    "product_name": "Dehumidifier",
                    "device_name": "Test Dehumidifier",
                }
            )
            dehumidifier = DreoDehumidifierHA(device)

            features = dehumidifier.supported_features
            assert features == 0

    def test_dehumidifier_turn_on(self):
        """Test turning dehumidifier on."""
        with patch(PATCH_UPDATE_HA_STATE) as mock_update:
            device = self._create_dehumidifier(
                features={
                    "is_on": False,
                    "mode": "auto",
                    "modes": ["auto", "manual"],
                    "humidity": 65,
                    "target_humidity": 50,
                    "brand": "Dreo",
                    "series_name": "DR-HDH",
                    "model": "DR-HDH001S",
                    "product_name": "Dehumidifier",
                    "device_name": "Test Dehumidifier",
                }
            )
            dehumidifier = DreoDehumidifierHA(device)
            assert dehumidifier.is_on is False

            dehumidifier.turn_on()
            assert device.is_on is True
            mock_update.assert_called()

    def test_dehumidifier_turn_off(self):
        """Test turning dehumidifier off."""
        with patch(PATCH_UPDATE_HA_STATE) as mock_update:
            device = self._create_dehumidifier()
            dehumidifier = DreoDehumidifierHA(device)
            assert dehumidifier.is_on is True

            dehumidifier.turn_off()
            assert device.is_on is False
            mock_update.assert_called()

    def test_dehumidifier_set_mode(self):
        """Test setting dehumidifier mode."""
        with patch(PATCH_UPDATE_HA_STATE) as mock_update:
            device = self._create_dehumidifier()
            dehumidifier = DreoDehumidifierHA(device)

            dehumidifier.set_mode("manual")
            assert device.mode == "manual"
            mock_update.assert_called()

    def test_dehumidifier_set_mode_turns_on_if_off(self):
        """Test that setting mode turns on device if it's off."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_dehumidifier(
                features={
                    "is_on": False,
                    "mode": "auto",
                    "modes": ["auto", "manual"],
                    "humidity": 65,
                    "target_humidity": 50,
                    "brand": "Dreo",
                    "series_name": "DR-HDH",
                    "model": "DR-HDH001S",
                    "product_name": "Dehumidifier",
                    "device_name": "Test Dehumidifier",
                }
            )
            dehumidifier = DreoDehumidifierHA(device)

            dehumidifier.set_mode("manual")
            assert device.is_on is True
            assert device.mode == "manual"

    def test_dehumidifier_set_invalid_mode_raises(self):
        """Test that setting an invalid mode raises ValueError."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_dehumidifier()
            dehumidifier = DreoDehumidifierHA(device)

            import pytest

            with pytest.raises(ValueError):
                dehumidifier.set_mode("invalid_mode")

    def test_dehumidifier_set_humidity(self):
        """Test setting target humidity."""
        with patch(PATCH_UPDATE_HA_STATE) as mock_update:
            device = self._create_dehumidifier()
            dehumidifier = DreoDehumidifierHA(device)

            dehumidifier.set_humidity(55)
            assert device.target_humidity == 55
            mock_update.assert_called()

    def test_dehumidifier_set_humidity_converts_to_int(self):
        """Test that set_humidity converts float to int."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_dehumidifier()
            dehumidifier = DreoDehumidifierHA(device)

            dehumidifier.set_humidity(55.7)
            assert device.target_humidity == 55

    def test_dehumidifier_extra_state_attributes(self):
        """Test extra state attributes."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_dehumidifier(
                features={
                    "is_on": True,
                    "mode": "auto",
                    "modes": ["auto", "manual"],
                    "humidity": 65,
                    "target_humidity": 50,
                    "display_light": True,
                    "childlockon": False,
                    "auto_mode": True,
                    "panel_sound": True,
                    "temperature": 72,
                    "brand": "Dreo",
                    "series_name": "DR-HDH",
                    "model": "DR-HDH001S",
                    "product_name": "Dehumidifier",
                    "device_name": "Test Dehumidifier",
                }
            )
            dehumidifier = DreoDehumidifierHA(device)
            attrs = dehumidifier.extra_state_attributes

            assert "display_light" in attrs
            assert attrs["display_light"] is True
            assert "childlockon" in attrs
            assert attrs["childlockon"] is False
            assert "auto_mode" in attrs
            assert "panel_sound" in attrs
            assert "temperature" in attrs

    def test_dehumidifier_device_info(self):
        """Test device info."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_dehumidifier()
            dehumidifier = DreoDehumidifierHA(device)
            device_info = dehumidifier.device_info

            assert device_info is not None
