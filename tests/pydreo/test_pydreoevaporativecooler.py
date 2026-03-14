"""Tests for Dreo Evaporative Coolers"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

from custom_components.dreo.pydreo import PyDreoEvaporativeCooler
from custom_components.dreo.pydreo.pydreoevaporativecooler import (
    WIND_MODE_KEY,
    HUMIDIFY_MODE_KEY,
    HUMIDITY_TARGET_KEY,
    WINDMODE_MAP,
)

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

    def test_HEC002S_preset_mode_setter(self): # pylint: disable=invalid-name
        """Test preset_mode setter sends correct command and validates input."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan : PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.preset_mode = "Normal"
            mock_send_command.assert_called_once_with(ec_fan, {WIND_MODE_KEY: WINDMODE_MAP["Normal"]})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.preset_mode = "Auto"
            mock_send_command.assert_called_once_with(ec_fan, {WIND_MODE_KEY: WINDMODE_MAP["Auto"]})

        with pytest.raises(ValueError):
            ec_fan.preset_mode = "InvalidMode"

    def test_HEC002S_handle_server_update_wind_mode_is_int(self): # pylint: disable=invalid-name
        """Test that handle_server_update stores wind_mode as int (type consistency)."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan : PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        # Send a WebSocket update with windmode as int
        ec_fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 3}})
        # _wind_mode must be stored as int to match update_state behavior
        assert isinstance(ec_fan.preset_mode, int)
        assert ec_fan.preset_mode == 3

    def test_HEC002S_handle_server_update_humidity(self): # pylint: disable=invalid-name
        """Test handle_server_update updates humidity and target_humidity."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan : PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        ec_fan.handle_server_update({REPORTED_KEY: {HUMIDITY_KEY: 55}})
        assert ec_fan.humidity == 55

        ec_fan.handle_server_update({REPORTED_KEY: {HUMIDITY_TARGET_KEY: 60}})
        assert ec_fan.target_humidity == 60

    def test_HEC002S_handle_server_update_humidify(self): # pylint: disable=invalid-name
        """Test handle_server_update correctly maps humidify mode."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan : PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        ec_fan.handle_server_update({REPORTED_KEY: {HUMIDIFY_MODE_KEY: 2}})
        assert ec_fan.humidify

        ec_fan.handle_server_update({REPORTED_KEY: {HUMIDIFY_MODE_KEY: 0}})
        assert not ec_fan.humidify

    def test_HEC002S_handle_server_update_oscillating(self): # pylint: disable=invalid-name
        """Test handle_server_update updates oscillating state."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan : PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        ec_fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: False}})
        assert ec_fan.oscillating is False

        ec_fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: True}})
        assert ec_fan.oscillating is True

    def test_HEC002S_handle_server_update_childlockon(self): # pylint: disable=invalid-name
        """Test handle_server_update updates childlockon state."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan : PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        ec_fan.handle_server_update({REPORTED_KEY: {CHILDLOCKON_KEY: True}})
        assert ec_fan.childlockon is True

    def test_HEC002S_handle_server_update_poweron(self): # pylint: disable=invalid-name
        """Test handle_server_update updates power state."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan : PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        ec_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert ec_fan.is_on is True

        ec_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
        assert ec_fan.is_on is False

    def test_HEC002S_target_humidity_setter(self): # pylint: disable=invalid-name
        """Test target_humidity setter sends command."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan : PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.target_humidity = 65
            mock_send_command.assert_called_once_with(ec_fan, {HUMIDITY_TARGET_KEY: 65})
