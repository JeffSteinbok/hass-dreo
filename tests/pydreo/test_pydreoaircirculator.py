"""Tests for Dreo Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from . import call_json
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LOGIN_RESPONSE = call_json.LOGIN_RET_BODY


class TestPyDreoAirCirculator(TestBase):
    """Test PyDreoAirCirculator class."""

    def test_HAF004S(self): # pylint: disable=invalid-name
        """Load circulator fan and test sending commands."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        fan : PyDreoAirCirculator = self.pydreo_manager.devices[0]

        assert fan.speed_range == (1, 9)
        assert fan.preset_modes == ['normal', 'natural', 'sleep', 'auto', 'turbo', 'custom']
        assert fan.oscillating is True
        assert fan.vertically_oscillating is True
        assert fan.horizontally_oscillating is False

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'normal'
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 1})

        with pytest.raises(ValueError):
            fan.preset_mode = 'not_a_mode'

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 3
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 3})

        with pytest.raises(ValueError):
            fan.fan_speed = 10
