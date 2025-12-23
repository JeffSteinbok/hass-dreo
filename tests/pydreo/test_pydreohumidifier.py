"""Tests for Dreo Ceiling Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from  .imports import * # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestPyDreoHumidifier(TestBase):
    """Test PyDreoHumidifier class."""
    
    def test_HHM001S(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.modes == ['manual', 'auto', 'sleep']
        assert humidifier.is_feature_supported('is_on') is True
        assert humidifier.is_feature_supported('humidity') is True
        assert humidifier.is_feature_supported('target_humidity') is True
        assert humidifier.humidity == 47
        assert humidifier.target_humidity == 60

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.mode = 'auto'
            mock_send_command.assert_called_once_with(humidifier, {MODE_KEY: 1})

    def test_HHM001S_websocket_updates(self):  # pylint: disable=invalid-name
        """Test that humidity values are updated from websocket messages."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
        
        # Initial values
        assert humidifier.humidity == 47
        assert humidifier.target_humidity == 60
        
        # Simulate websocket update for humidity
        message = {
            "method": "control-report",
            "devicesn": "HHM001S_1",
            "reported": {
                "rh": 55
            }
        }
        humidifier.handle_server_update(message)
        assert humidifier.humidity == 55
        
        # Simulate websocket update for target_humidity
        message = {
            "method": "control-report",
            "devicesn": "HHM001S_1",
            "reported": {
                "rhautolevel": 70
            }
        }
        humidifier.handle_server_update(message)
        assert humidifier.target_humidity == 70

    def test_HHM001S_water_level_property(self):  # pylint: disable=invalid-name
        """Test that water_level property works correctly."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
        
        # Check that water_level is accessible and returns the expected value
        assert humidifier.is_feature_supported('water_level') is True
        assert humidifier.water_level == "Ok"
