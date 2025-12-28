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
        fan.handle_server_update({ REPORTED_KEY: {FANON_KEY: True} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.light_on = True
            mock_send_command.assert_called_once_with(fan, {LIGHTON_KEY: True})
        fan.handle_server_update({ REPORTED_KEY: {LIGHTON_KEY: True} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.light_on = False
            mock_send_command.assert_called_once_with(fan, {LIGHTON_KEY: False})
        fan.handle_server_update({ REPORTED_KEY: {LIGHTON_KEY: False} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.brightness = 50
            mock_send_command.assert_called_once_with(fan, {BRIGHTNESS_KEY: 50})
        fan.handle_server_update({ REPORTED_KEY: {BRIGHTNESS_KEY: 50} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.color_temperature = 50
            mock_send_command.assert_called_once_with(fan, {COLORTEMP_KEY: 50})
        fan.handle_server_update({ REPORTED_KEY: {COLORTEMP_KEY: 50} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'natural'
            mock_send_command.assert_called_once_with(fan, {MODE_KEY: 2})
        fan.handle_server_update({ REPORTED_KEY: {MODE_KEY: 2} })

        with pytest.raises(ValueError):
            fan.preset_mode = 'not_a_mode'

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 3
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 3})
        fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 3} })

        with pytest.raises(ValueError):
            fan.fan_speed = 13

    def test_HCF002S(self):  # pylint: disable=invalid-name
        """Test DR-HCF002S ceiling fan with RGB atmosphere lights."""
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]
        
        # Test basic fan properties
        assert fan.model == "DR-HCF002S"
        assert fan.speed_range == (1, 12)
        assert fan.preset_modes == ['normal', 'natural', 'sleep', 'auto']
        
        # Test main light support
        assert fan.is_feature_supported('light_on') is True
        assert fan.is_feature_supported('brightness') is True
        assert fan.is_feature_supported('color_temperature') is True
        assert fan.brightness == 24
        assert fan.color_temperature == 60
        
        # Test atmosphere light support
        assert fan.is_feature_supported('atm_light') is True
        assert fan.atm_light_on is False
        assert fan.atm_brightness == 3
        assert fan.atm_color_rgb == (0, 255, 0)  # 65280 = 0x00FF00 = green
        assert fan.atm_mode == 1
        
        # Test atmosphere light commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_light_on = True
            mock_send_command.assert_called_once_with(fan, {ATMON_KEY: True})
        fan.handle_server_update({ REPORTED_KEY: {ATMON_KEY: True} })
        
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_brightness = 5
            mock_send_command.assert_called_once_with(fan, {ATMBRI_KEY: 5})
        fan.handle_server_update({ REPORTED_KEY: {ATMBRI_KEY: 5} })
        
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_color_rgb = (255, 0, 0)  # Red
            mock_send_command.assert_called_once_with(fan, {ATMCOLOR_KEY: 16711680})  # 0xFF0000
        fan.handle_server_update({ REPORTED_KEY: {ATMCOLOR_KEY: 16711680} })

