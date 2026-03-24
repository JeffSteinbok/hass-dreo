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
            humidifier.mode = 'manual'
            mock_send_command.assert_called_once_with(humidifier, {MODE_KEY: 0})
        humidifier.handle_server_update({ REPORTED_KEY: {MODE_KEY: 0} })

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

    def test_HHM003S(self):  # pylint: disable=invalid-name
        """Load HHM003S (HM713S/813S) and test humidity properties."""

        self.get_devices_file_name = "get_devices_HHM003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.model == 'DR-HHM003S'
        assert humidifier.series_name == 'HM713S/813S'
        assert humidifier.modes == ['manual', 'auto', 'sleep']
        assert humidifier.is_feature_supported('is_on') is True
        assert humidifier.is_feature_supported('humidity') is True
        assert humidifier.is_feature_supported('target_humidity') is True
        assert humidifier.is_feature_supported('worktime') is True
        assert humidifier.humidity == 40
        assert humidifier.target_humidity == 50
        assert humidifier.worktime == 10

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.mode = 'manual'
            mock_send_command.assert_called_once_with(humidifier, {MODE_KEY: 0})
        humidifier.handle_server_update({ REPORTED_KEY: {MODE_KEY: 0} })

    def test_HHM003S_websocket_updates(self):  # pylint: disable=invalid-name
        """Test that humidity values are updated from websocket messages for HHM003S."""
        self.get_devices_file_name = "get_devices_HHM003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
        
        # Initial values
        assert humidifier.humidity == 40
        assert humidifier.target_humidity == 50
        
        # Simulate websocket update for humidity
        message = {
            "method": "control-report",
            "devicesn": "HHM003S_1",
            "reported": {
                "rh": 65
            }
        }
        humidifier.handle_server_update(message)
        assert humidifier.humidity == 65
        
        # Simulate websocket update for target_humidity
        message = {
            "method": "control-report",
            "devicesn": "HHM003S_1",
            "reported": {
                "rhautolevel": 75
            }
        }
        humidifier.handle_server_update(message)
        assert humidifier.target_humidity == 75
        
        # Simulate websocket update for worktime
        message = {
            "method": "control-report",
            "devicesn": "HHM003S_1",
            "reported": {
                "worktime": 50
            }
        }
        humidifier.handle_server_update(message)
        assert humidifier.worktime == 50

    def test_HHM003S_water_level_property(self):  # pylint: disable=invalid-name
        """Test that water_level property works correctly for HHM003S."""
        self.get_devices_file_name = "get_devices_HHM003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
        
        # Check that water_level is accessible and returns the expected value
        assert humidifier.is_feature_supported('water_level') is True
        assert humidifier.water_level == "Ok"

    def test_HHM015S(self):  # pylint: disable=invalid-name
        """Load HHM015S (HM755S) and test humidity properties."""

        self.get_devices_file_name = "get_devices_HHM015S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.model == 'DR-HHM015S'
        assert humidifier.series_name == 'HM755S'
        assert humidifier.is_feature_supported('is_on') is True
        assert humidifier.is_feature_supported('humidity') is True
        assert humidifier.is_feature_supported('target_humidity') is True
        assert humidifier.is_on is False
        assert humidifier.humidity == 31
        assert humidifier.target_humidity == 60
        # HHM015S has no modes configured - modes should return None, not an empty list or error
        assert humidifier.modes is None
        assert humidifier.mode is None

    def test_HHM015S_websocket_updates(self):  # pylint: disable=invalid-name
        """Test that humidity values are updated from websocket messages for HHM015S."""
        self.get_devices_file_name = "get_devices_HHM015S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]

        # Initial values
        assert humidifier.humidity == 31
        assert humidifier.target_humidity == 60

        # Simulate websocket update for humidity
        message = {
            "method": "control-report",
            "devicesn": "HHM015S_1",
            "reported": {
                "rh": 45
            }
        }
        humidifier.handle_server_update(message)
        assert humidifier.humidity == 45

        # Simulate websocket update for target_humidity
        message = {
            "method": "control-report",
            "devicesn": "HHM015S_1",
            "reported": {
                "rhautolevel": 65
            }
        }
        humidifier.handle_server_update(message)
        assert humidifier.target_humidity == 65

    def test_HHM015S_water_level_property(self):  # pylint: disable=invalid-name
        """Test that water_level property works correctly for HHM015S."""
        self.get_devices_file_name = "get_devices_HHM015S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]

        # Check that water_level is accessible and returns the expected value
        assert humidifier.is_feature_supported('water_level') is True
        assert humidifier.water_level == "Ok"

    def test_HHM001S_power_cycle_stale_state(self):  # pylint: disable=invalid-name
        """Test that turn_on command is sent even when cached state is stale after power cycle."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
        
        # Simulate device power cycle scenario:
        # 1. Device is physically OFF (power cycled)
        # 2. Cloud sends stale WebSocket state with poweron: true
        # 3. User calls turn_on
        # 4. Command should be sent even though cached state shows ON
        
        # Simulate stale WebSocket update reporting device is ON (but it's actually OFF)
        message = {
            "method": "control-report",
            "devicesn": "HHM001S_1",
            "reported": {
                "poweron": True
            }
        }
        humidifier.handle_server_update(message)
        assert humidifier.is_on is True  # Cached state shows ON
        
        # User calls turn_on - command should be sent despite cached state being ON
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.is_on = True  # Attempt to turn on
            # Command MUST be sent even though cached state matches
            mock_send_command.assert_called_once_with(humidifier, {POWERON_KEY: True})

    def test_HHM003S_power_cycle_stale_state(self):  # pylint: disable=invalid-name
        """Test that turn_on command is sent even when cached state is stale for HHM003S."""
        self.get_devices_file_name = "get_devices_HHM003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
        
        # Simulate stale WebSocket update reporting device is ON
        message = {
            "method": "control-report",
            "devicesn": "HHM003S_1",
            "reported": {
                "poweron": True
            }
        }
        humidifier.handle_server_update(message)
        assert humidifier.is_on is True
        
        # Command should be sent even when cached state matches
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.is_on = True
            mock_send_command.assert_called_once_with(humidifier, {POWERON_KEY: True})
