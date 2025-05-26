"""Tests for Dreo Evaporative Coolers"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

from custom_components.dreo.pydreo import PyDreoEvaporativeCooler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestPyDreoEvaporativeCooler(TestBase):
    """Test PyDreoEvaporativeCooler class."""

    def test_HEC002S(self): # pylint: disable=invalid-name
        """Load evaporative cooler and test sending commands."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        ec_fan : PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        assert ec_fan.humidity == 41
        assert ec_fan.speed_range == (1, 4)
        assert ec_fan.preset_modes == ['Normal', 'Natural', 'Sleep', 'Auto']
        assert ec_fan.oscillating is True
        assert ec_fan.childlockon is False
        assert ec_fan.preset_mode == 3
        assert ec_fan.work_time == 19
        assert ec_fan.water_level == 'Ok'
        
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.is_on = True
            mock_send_command.assert_called_once_with(ec_fan, {POWERON_KEY: True})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.fan_speed = 3
            mock_send_command.assert_called_once_with(ec_fan, {WINDLEVEL_KEY: 3})

        with pytest.raises(ValueError):
            ec_fan.fan_speed = 10
