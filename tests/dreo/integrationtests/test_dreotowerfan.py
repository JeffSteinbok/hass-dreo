"""Tests for Dreo Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestDreoTowerFan(IntegrationTestBase):
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
        assert fan.model == "DR-HTF005S"
        assert fan.serial_number is not None
        assert fan.is_on is not None
        assert fan.is_on is True

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        # Test all preset modes
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'natural'
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 2}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'sleep'
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 3}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'auto'
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 4}})

        with pytest.raises(ValueError):
            fan.preset_mode = 'not_a_mode'

        # Test speed commands at various levels
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 3
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 3}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 6
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 6})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 6}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 12
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 12})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 12}})

        # Test speed boundaries
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 13

        # Test oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = False
            mock_send_command.assert_called_once_with(fan, {SHAKEHORIZON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {SHAKEHORIZON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            mock_send_command.assert_called_once_with(fan, {SHAKEHORIZON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {SHAKEHORIZON_KEY: True}})
