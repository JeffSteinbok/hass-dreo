"""Tests for Dreo Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch, call
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from . import call_json
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestPyDreoHeater(TestBase):
    """Test PyDreoHeater class."""
    def test_HSH009S(self):
        """Load heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.heat_range == (1, 3)
        assert heater.preset_modes == ['H1', 'H2', 'H3']

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = True
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: True})

        with (patch(PATCH_SEND_COMMAND) as mock_send_command):
            heater.preset_mode = 'H1'
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)

        with pytest.raises(ValueError):
            heater.preset_mode = 'not_a_mode'



