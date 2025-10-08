"""Tests for Dreo Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

from custom_components.dreo.pydreo import PyDreoAC

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@pytest.mark.skip(reason="Test disabled for v2.x")
class TestPyDreoAirConditioner(TestBase):
    """Test TestPyDreoAirConditioner class."""

    def test_HAC006S(self): # pylint: disable=invalid-name
        """Load air conditioner and test sending commands."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        ac : PyDreoAC = self.pydreo_manager.devices[0]

        assert ac.preset_modes == ['none', 'eco', 'sleep']

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.poweron = True
            mock_send_command.assert_called_once_with(ac, {DreoApiKeys.POWER_SWITCH: True})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.fan_mode = 'auto'
            mock_send_command.assert_called_once_with(ac, {WINDLEVEL_KEY: 4})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.preset_mode = 'eco'
            mock_send_command.assert_called_once_with(ac, {WIND_MODE_KEY: 5})

        # Test sleep preset mode
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.preset_mode = 'sleep'
            mock_send_command.assert_called_once_with(ac, {WIND_MODE_KEY: 4})
            assert ac.preset_mode == 'sleep'  # Verify mode was set

        # TODO: Fix this in the AC class
        # with pytest.raises(ValueError):
        #    ac.preset_mode = 'not_a_mode'