"""Tests for Dreo Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestPyDreoTowerFan(TestBase):
    """Test PyDreoFan class."""

    def test_HTF005S(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HTF005S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan = self.pydreo_manager.devices[0]
        
        # Test initial state values
        assert fan.speed_range == (1, 12)
        assert fan.preset_modes == ['normal', 'natural', 'sleep', 'auto']
        assert fan.oscillating is True
        assert fan.is_feature_supported("temperature_offset") is True
        assert fan.temperature_offset == -2
        assert fan.model == "DR-HTF005S"
        assert fan.device_name is not None
        assert fan.serial_number is not None
        assert fan.is_on is not None
        assert fan.fan_speed >= 1 and fan.fan_speed <= 12
        assert fan.preset_mode in fan.preset_modes

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})
        fan.handle_server_update({ REPORTED_KEY: {POWERON_KEY: False} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})
        fan.handle_server_update({ REPORTED_KEY: {POWERON_KEY: True} })

        # Test all preset mode commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'natural'
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 2})
        fan.handle_server_update({ REPORTED_KEY: {WINDTYPE_KEY: 2} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'sleep'
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 3})
        fan.handle_server_update({ REPORTED_KEY: {WINDTYPE_KEY: 3} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'auto'
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 4})
        fan.handle_server_update({ REPORTED_KEY: {WINDTYPE_KEY: 4} })

        with pytest.raises(ValueError):
            fan.preset_mode = 'not_a_mode'

        # Test fan speed commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 3
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 3})
        fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 3} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 6
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 6})
        fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 6} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 12
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 12})
        fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 12} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 1
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 1})

        # Test speed boundaries
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 13

        # Test oscillation commands (HTF005S uses shakehorizon key)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = False
            mock_send_command.assert_called_once_with(fan, {SHAKEHORIZON_KEY: False})
        fan.handle_server_update({ REPORTED_KEY: {SHAKEHORIZON_KEY: False} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            mock_send_command.assert_called_once_with(fan, {SHAKEHORIZON_KEY: True})

    def test_HTF010S(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HTF010S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan : PyDreoTowerFan = self.pydreo_manager.devices[0]
        
        # Test initial state values
        assert fan.speed_range == (1, 12)
        assert fan.preset_modes == ['normal', 'natural', 'sleep', 'auto']
        assert fan.oscillating is True
        assert fan.pm25 == 1
        assert fan.model == "DR-HTF010S"
        assert fan.device_name is not None
        assert fan.serial_number is not None
        assert fan.is_on is not None
        assert fan.fan_speed >= 1 and fan.fan_speed <= 12
        assert fan.preset_mode in fan.preset_modes

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})
        fan.handle_server_update({ REPORTED_KEY: {POWERON_KEY: True} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})
        fan.handle_server_update({ REPORTED_KEY: {POWERON_KEY: False} })

        # Test all preset mode commands (uses WIND_MODE_KEY instead of WINDTYPE_KEY)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'natural'
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 2})
        fan.handle_server_update({ REPORTED_KEY: {WIND_MODE_KEY: 2} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'sleep'
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 3})
        fan.handle_server_update({ REPORTED_KEY: {WIND_MODE_KEY: 3} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'auto'
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 4})
        fan.handle_server_update({ REPORTED_KEY: {WIND_MODE_KEY: 4} })

        with pytest.raises(ValueError):
            fan.preset_mode = 'not_a_mode'

        # Test fan speed commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 3
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 3})
        fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 3} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 6
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 6})
        fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 6} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 12
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 12})
        fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 12} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 1
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 1})

        # Test speed boundaries
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 13

        # Test oscillation commands (HTF010S uses oscon key)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = False
            mock_send_command.assert_called_once_with(fan, {OSCON_KEY: False})
        fan._oscillating = False  # pylint: disable=protected-access

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            mock_send_command.assert_called_once_with(fan, {OSCON_KEY: True})

    def test_HTF007S(self):  # pylint: disable=invalid-name
        """Load HTF007S tower fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HTF007S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan = self.pydreo_manager.devices[0]
        
        # Test initial state values
        assert fan.speed_range == (1, 4)
        assert fan.preset_modes == ['normal', 'natural', 'sleep', 'auto']
        assert fan.model == "DR-HTF007S"
        assert fan.device_name is not None
        assert fan.serial_number is not None

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})
        fan.handle_server_update({ REPORTED_KEY: {POWERON_KEY: True} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})
        fan.handle_server_update({ REPORTED_KEY: {POWERON_KEY: False} })

        # Test preset mode commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'natural'
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 2})
        fan.handle_server_update({ REPORTED_KEY: {WINDTYPE_KEY: 2} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'sleep'
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 3})
        fan.handle_server_update({ REPORTED_KEY: {WINDTYPE_KEY: 3} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'auto'
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 4})
        fan.handle_server_update({ REPORTED_KEY: {WINDTYPE_KEY: 4} })

        with pytest.raises(ValueError):
            fan.preset_mode = 'not_a_mode'

        # Test fan speed commands (1-4 speed range)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 2
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 2})
        fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 2} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 4
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 4})
        fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 4} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 1
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 1})

        # Test speed boundaries
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 5

    def test_HTF009S(self):  # pylint: disable=invalid-name
        """Load HTF009S tower fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HTF009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan = self.pydreo_manager.devices[0]
        
        # Test initial state values
        assert fan.speed_range == (1, 9)
        assert fan.preset_modes == ['normal', 'natural', 'sleep', 'auto']
        assert fan.model == "DR-HTF009S"
        assert fan.device_name is not None
        assert fan.serial_number is not None

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})
        fan.handle_server_update({ REPORTED_KEY: {POWERON_KEY: True} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})
        fan.handle_server_update({ REPORTED_KEY: {POWERON_KEY: False} })

        # Test preset mode commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'natural'
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 2})
        fan.handle_server_update({ REPORTED_KEY: {WINDTYPE_KEY: 2} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'sleep'
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 3})
        fan.handle_server_update({ REPORTED_KEY: {WINDTYPE_KEY: 3} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'auto'
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 4})
        fan.handle_server_update({ REPORTED_KEY: {WINDTYPE_KEY: 4} })

        with pytest.raises(ValueError):
            fan.preset_mode = 'not_a_mode'

        # Test fan speed commands (1-9 speed range)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 5
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 5})
        fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 5} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 9
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 9})
        fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 9} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 1
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 1})

        # Test speed boundaries
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 10
