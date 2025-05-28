"""Tests for Dreo Ceiling Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestPyDreoCeilingFan(TestBase):
    """Test PyDreoFan class."""
  
    def test_HCF001S(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HCF001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan : PyDreoCeilingFan = self.pydreo_manager.devices[0]
        assert fan.speed_range == (1, 12)
        assert fan.preset_modes == ['normal', 'natural', 'sleep', 'reverse']
        assert fan.is_feature_supported('poweron') is False
        assert fan.is_feature_supported('light_on') is True
        assert fan.is_feature_supported('brightness') is True
        assert fan.is_feature_supported('color_temperature') is True
        assert fan.brightness == 64
        assert fan.color_temperature == 25

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {FANON_KEY: True})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.light_on = True
            mock_send_command.assert_called_once_with(fan, {LIGHTON_KEY: True})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.light_on = True
            mock_send_command.assert_called_once_with(fan, {LIGHTON_KEY: True})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.brightness = 50
            mock_send_command.assert_called_once_with(fan, {BRIGHTNESS_KEY: 50})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.color_temperature = 50
            mock_send_command.assert_called_once_with(fan, {COLORTEMP_KEY: 50})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'normal'
            mock_send_command.assert_called_once_with(fan, {MODE_KEY: 1})

        with pytest.raises(ValueError):
            fan.preset_mode = 'not_a_mode'

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 3
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 3})

        with pytest.raises(ValueError):
            fan.fan_speed = 13
