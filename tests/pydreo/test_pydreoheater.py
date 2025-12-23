"""Tests for Dreo Heaters"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch, call
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestPyDreoHeater(TestBase):
    """Test PyDreoHeater class."""
    def test_HSH009S(self): # pylint: disable=invalid-name
        """Load heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.htalevel_range == (1, 3)
        assert heater.hvac_modes == ['coolair', 'hotair', 'eco', 'off']

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = True
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: True})

        with (patch(PATCH_SEND_COMMAND) as mock_send_command):
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)

        with pytest.raises(ValueError):
            heater.hvac_mode = 'not_a_mode'

    def test_HSH010S(self): # pylint: disable=invalid-name
        """Load oil radiator heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH010S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.htalevel_range == (1, 3)
        assert heater.hvac_modes == ['hotair', 'eco', 'off']

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = True
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: True})

        with (patch(PATCH_SEND_COMMAND) as mock_send_command):
            heater.htalevel = 2
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 2})], True)

        with pytest.raises(ValueError):
            heater.hvac_mode = 'not_a_mode'
