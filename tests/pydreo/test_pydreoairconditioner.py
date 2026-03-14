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
        ac.handle_server_update({ REPORTED_KEY: {POWERON_KEY: True} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.mode = DreoACMode.ECO
            mock_send_command.assert_called_once_with(ac, {WIND_MODE_KEY: 5})
        ac.handle_server_update({ REPORTED_KEY: {WIND_MODE_KEY: 5} })

        # Test sleep preset mode
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.mode = DreoACMode.SLEEP
            mock_send_command.assert_called_once_with(ac, {WIND_MODE_KEY: 4})
        ac.handle_server_update({ REPORTED_KEY: {WIND_MODE_KEY: 4} })

        # TODO: Fix this in the AC class
        # with pytest.raises(ValueError):
        #    ac.preset_mode = 'not_a_mode'

    def test_HAC006S_handle_server_update_poweron(self): # pylint: disable=invalid-name
        """Test handle_server_update updates power state."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        ac.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert ac.poweron is True

        ac.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
        assert ac.poweron is False

    def test_HAC006S_handle_server_update_temperature(self): # pylint: disable=invalid-name
        """Test handle_server_update updates temperature and target_temperature."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        ac.handle_server_update({REPORTED_KEY: {TEMPERATURE_KEY: 72}})
        assert ac.temperature == 72

        ac.handle_server_update({REPORTED_KEY: {TARGET_TEMPERATURE_KEY: 70}})
        assert ac.target_temperature == 70

    def test_HAC006S_handle_server_update_mode(self): # pylint: disable=invalid-name
        """Test handle_server_update updates operating mode."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        ac.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: DreoACMode.COOL}})
        assert ac.mode == DreoACMode.COOL

    def test_HAC006S_handle_server_update_fan_mode(self): # pylint: disable=invalid-name
        """Test handle_server_update updates fan mode."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        ac.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 2}})
        assert ac.fan_mode == 2

    def test_HAC006S_handle_server_update_childlockon(self): # pylint: disable=invalid-name
        """Test handle_server_update updates childlockon state."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        ac.handle_server_update({REPORTED_KEY: {CHILDLOCKON_KEY: True}})
        assert ac.childlockon is True

    def test_HAC006S_oscon_setter(self): # pylint: disable=invalid-name
        """Test oscon setter sends correct command."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.oscon = True
            mock_send_command.assert_called_once_with(ac, {OSCMODE_KEY: 2})

    def test_HAC006S_childlockon_setter(self): # pylint: disable=invalid-name
        """Test childlockon setter sends correct command."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.childlockon = True
            mock_send_command.assert_called_once_with(ac, {CHILDLOCKON_KEY: True})