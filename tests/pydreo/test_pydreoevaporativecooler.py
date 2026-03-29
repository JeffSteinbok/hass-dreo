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
    WATER_LEVEL_STATUS_KEY,
    WORKTIME_KEY,
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
        assert ec_fan.preset_mode == "Sleep"
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

    def test_HEC002S_humidify_setter(self):  # pylint: disable=invalid-name
        """Test humidify setter sends correct mapped command."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan: PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        # Initial state has humidify=True (rhmode=2); set to False first
        ec_fan._humidify = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.humidify = True
            mock_send_command.assert_called_once_with(ec_fan, {HUMIDIFY_MODE_KEY: 2})

        # Disable humidify -> sends mode 0
        ec_fan._humidify = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.humidify = False
            mock_send_command.assert_called_once_with(ec_fan, {HUMIDIFY_MODE_KEY: 0})

        # Duplicate value -- no command sent
        ec_fan._humidify = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.humidify = False
            mock_send_command.assert_not_called()

    def test_HEC002S_target_humidity_setter(self):  # pylint: disable=invalid-name
        """Test target_humidity setter sends correct command."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan: PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.target_humidity = 60
            mock_send_command.assert_called_once_with(ec_fan, {HUMIDITY_TARGET_KEY: 60})

        # Duplicate value -- no command sent
        ec_fan._target_humidity = 60
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.target_humidity = 60
            mock_send_command.assert_not_called()

    def test_HEC002S_oscillating_setter(self):  # pylint: disable=invalid-name
        """Test oscillating setter sends correct command."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan: PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        # Currently oscillating=True; set False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.oscillating = False
            mock_send_command.assert_called_once_with(ec_fan, {HORIZONTAL_OSCILLATION_KEY: False})

        # Duplicate value -- no command sent
        ec_fan._oscillating = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.oscillating = False
            mock_send_command.assert_not_called()

    def test_HEC002S_childlockon_setter(self):  # pylint: disable=invalid-name
        """Test childlockon setter sends correct command."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan: PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.childlockon = True
            mock_send_command.assert_called_once_with(ec_fan, {CHILDLOCKON_KEY: True})

        # Duplicate value -- no command sent
        ec_fan._childlockon = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.childlockon = True
            mock_send_command.assert_not_called()

    def test_HEC002S_preset_mode_setter(self):  # pylint: disable=invalid-name
        """Test preset_mode setter maps string to int and sends correct command."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan: PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        # "Normal" -> WINDMODE_MAP["Normal"] = 1
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.preset_mode = "Normal"
            mock_send_command.assert_called_once_with(ec_fan, {WIND_MODE_KEY: 1})

        # "Auto" -> WINDMODE_MAP["Auto"] = 2
        ec_fan._wind_mode = 1
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.preset_mode = "Auto"
            mock_send_command.assert_called_once_with(ec_fan, {WIND_MODE_KEY: 2})

        # Duplicate value -- no command sent (current is 3=Sleep, set Sleep again)
        ec_fan._wind_mode = 3
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ec_fan.preset_mode = "Sleep"
            mock_send_command.assert_not_called()

    def test_HEC002S_handle_server_update(self):  # pylint: disable=invalid-name
        """Test handle_server_update processes all WebSocket fields correctly."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan: PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        # poweron
        ec_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert ec_fan.is_on is True

        # temperature_offset
        ec_fan.handle_server_update({REPORTED_KEY: {TEMPOFFSET_KEY: 2}})
        assert ec_fan.temperature_offset == 2

        # oscillating
        ec_fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: False}})
        assert ec_fan.oscillating is False

        # humidity
        ec_fan.handle_server_update({REPORTED_KEY: {HUMIDITY_KEY: 55}})
        assert ec_fan.humidity == 55

        # humidify (rhmode=2 -> True)
        ec_fan.handle_server_update({REPORTED_KEY: {HUMIDIFY_MODE_KEY: 2}})
        assert ec_fan.humidify is True

        # humidify (rhmode=0 -> False)
        ec_fan.handle_server_update({REPORTED_KEY: {HUMIDIFY_MODE_KEY: 0}})
        assert ec_fan.humidify is False

        # target humidity
        ec_fan.handle_server_update({REPORTED_KEY: {HUMIDITY_TARGET_KEY: 70}})
        assert ec_fan.target_humidity == 70

        # childlockon
        ec_fan.handle_server_update({REPORTED_KEY: {CHILDLOCKON_KEY: True}})
        assert ec_fan.childlockon is True

        # wind_mode -- WebSocket sends int 1-4; should be stored as int in _wind_mode
        ec_fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 2}})
        assert ec_fan._wind_mode == 2  # internal state stored as int, consistent with update_state

        # work_time
        ec_fan.handle_server_update({REPORTED_KEY: {WORKTIME_KEY: 25}})
        assert ec_fan.work_time == 25

        # water_level: 0 -> "Ok", 1 -> "Empty"
        ec_fan.handle_server_update({REPORTED_KEY: {WATER_LEVEL_STATUS_KEY: 0}})
        assert ec_fan.water_level == "Ok"

        ec_fan.handle_server_update({REPORTED_KEY: {WATER_LEVEL_STATUS_KEY: 1}})
        assert ec_fan.water_level == "Empty"

    def test_HEC002S_map_wind_mode_from_rest(self):  # pylint: disable=invalid-name
        """Test the extracted _map_wind_mode_from_rest helper method."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan: PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        # Valid 0-based REST indices -> internal int values
        assert ec_fan._map_wind_mode_from_rest(0) == 1   # "Normal" -> 1
        assert ec_fan._map_wind_mode_from_rest(1) == 4   # "Natural" -> 4
        assert ec_fan._map_wind_mode_from_rest(2) == 3   # "Sleep" -> 3
        assert ec_fan._map_wind_mode_from_rest(3) == 2   # "Auto" -> 2

        # Invalid indices return None
        assert ec_fan._map_wind_mode_from_rest(None) is None
        assert ec_fan._map_wind_mode_from_rest(-1) is None
        assert ec_fan._map_wind_mode_from_rest(4) is None

    def test_HEC002S_wind_mode_consistency(self):  # pylint: disable=invalid-name
        """Test that _wind_mode is always an int regardless of update path."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()
        ec_fan: PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        # After update_state (REST API path): _wind_mode should be int
        assert isinstance(ec_fan._wind_mode, int), (
            "update_state should store _wind_mode as int"
        )

        # After handle_server_update (WebSocket path): _wind_mode should still be int
        ec_fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 1}})
        assert isinstance(ec_fan._wind_mode, int), (
            "handle_server_update should store _wind_mode as int"
        )
        assert ec_fan._wind_mode == 1

    def test_HEC002S_temperature_offset(self): # pylint: disable=invalid-name
        """Test that temperature offset is applied to evaporative cooler temperature."""
        self.get_devices_file_name = "get_devices_HEC002S.json"
        self.pydreo_manager.load_devices()

        ec_fan : PyDreoEvaporativeCooler = self.pydreo_manager.devices[0]

        # Initial state: raw temp 76, offset 0 -> calibrated 76
        assert ec_fan.temperature_offset == 0
        assert ec_fan.temperature == 76

        # Simulate a WebSocket update with new temperature and offset
        ec_fan.handle_server_update({ REPORTED_KEY: {TEMPERATURE_KEY: 80, TEMPOFFSET_KEY: -4} })
        assert ec_fan.temperature_offset == -4
        assert ec_fan.temperature == 76  # raw 80 + offset -4
