"""Tests for Dreo Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

from custom_components.dreo.pydreo import PyDreoAC
from custom_components.dreo.pydreo.pydreoairconditioner import DreoACMode

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestPyDreoAirConditioner(TestBase):
    """Test TestPyDreoAirConditioner class."""

    def test_HAC006S(self): # pylint: disable=invalid-name
        """Load air conditioner and test sending commands."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        ac : PyDreoAC = self.pydreo_manager.devices[0]

        assert sorted(ac.modes) == sorted([DreoACMode.COOL, DreoACMode.DRY, DreoACMode.FAN, DreoACMode.ECO, DreoACMode.SLEEP])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.poweron = True
            mock_send_command.assert_called_once_with(ac, {POWERON_KEY: True})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.fan_mode = DreoACFanMode.AUTO
            mock_send_command.assert_called_once_with(ac, {WINDLEVEL_KEY: 4})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.mode = DreoACMode.ECO
            mock_send_command.assert_called_once_with(ac, {WIND_MODE_KEY: 5})

        # Test sleep preset mode
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.mode = DreoACMode.SLEEP
            mock_send_command.assert_called_once_with(ac, {WIND_MODE_KEY: 4})

        # TODO: Fix this in the AC class
        # with pytest.raises(ValueError):
        #    ac.preset_mode = 'not_a_mode'