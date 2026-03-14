"""Tests for Dreo Dehumidifiers"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

from custom_components.dreo.pydreo import PyDreoDehumidifier
from custom_components.dreo.pydreo.pydreodehumidifier import (
    RHAUTOLEVEL_KEY,
    AUTOON_KEY,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestPyDreoDehumidifier(TestBase):
    """Test PyDreoDehumidifier class."""

    def test_HDH002S_basic_properties(self): # pylint: disable=invalid-name
        """Load HDH002S dehumidifier and verify basic properties."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        assert dehumidifier.is_on is False
        assert dehumidifier.humidity == 66
        assert dehumidifier.target_humidity == 50
        assert dehumidifier.wind_level == 2
        assert dehumidifier.temperature == 67
        assert dehumidifier.modes == ["Auto", "Continuous"]

    def test_HDH002S_power_on_off(self): # pylint: disable=invalid-name
        """Test power on/off commands are sent correctly."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.is_on = True
            mock_send_command.assert_called_once_with(dehumidifier, {POWERON_KEY: True})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.is_on = False
            mock_send_command.assert_called_once_with(dehumidifier, {POWERON_KEY: False})

    def test_HDH002S_target_humidity_setter(self): # pylint: disable=invalid-name
        """Test target_humidity setter with valid and boundary values."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.target_humidity = 55
            mock_send_command.assert_called_once_with(dehumidifier, {RHAUTOLEVEL_KEY: 55})

        # Boundary: minimum value
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.target_humidity = 30
            mock_send_command.assert_called_once_with(dehumidifier, {RHAUTOLEVEL_KEY: 30})

        # Boundary: maximum value
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.target_humidity = 85
            mock_send_command.assert_called_once_with(dehumidifier, {RHAUTOLEVEL_KEY: 85})

    def test_HDH002S_target_humidity_validation(self): # pylint: disable=invalid-name
        """Test target_humidity raises ValueError for out-of-range values."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with pytest.raises(ValueError):
            dehumidifier.target_humidity = 29

        with pytest.raises(ValueError):
            dehumidifier.target_humidity = 86

    def test_HDH002S_wind_level_setter(self): # pylint: disable=invalid-name
        """Test wind_level setter with valid values."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.wind_level = 1
            mock_send_command.assert_called_once_with(dehumidifier, {WINDLEVEL_KEY: 1})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.wind_level = 3
            mock_send_command.assert_called_once_with(dehumidifier, {WINDLEVEL_KEY: 3})

    def test_HDH002S_wind_level_validation(self): # pylint: disable=invalid-name
        """Test wind_level raises ValueError for out-of-range values."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with pytest.raises(ValueError):
            dehumidifier.wind_level = 0

        with pytest.raises(ValueError):
            dehumidifier.wind_level = 4

    def test_HDH002S_fan_speed_setter(self): # pylint: disable=invalid-name
        """Test fan_speed setter (alias for wind_level)."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        # Initial wind_level is 2; set to a different value to trigger command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.fan_speed = 1
            mock_send_command.assert_called_once_with(dehumidifier, {WINDLEVEL_KEY: 1})

    def test_HDH002S_mode_setter_valid(self): # pylint: disable=invalid-name
        """Test mode setter with valid modes."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        # Initial mode is 1 (Auto); switch to Continuous (2)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.mode = "Continuous"
            mock_send_command.assert_called_once_with(dehumidifier, {MODE_KEY: 2})

        # Simulate server confirming mode change, then switch back
        dehumidifier.handle_server_update({REPORTED_KEY: {MODE_KEY: 2}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.mode = "Auto"
            mock_send_command.assert_called_once_with(dehumidifier, {MODE_KEY: 1})

    def test_HDH002S_mode_setter_invalid(self): # pylint: disable=invalid-name
        """Test mode setter raises ValueError for invalid modes."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with pytest.raises(ValueError):
            dehumidifier.mode = "InvalidMode"

    def test_HDH002S_preset_modes_and_mode(self): # pylint: disable=invalid-name
        """Test preset_modes list and preset_mode mapped from wind_level."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        assert dehumidifier.preset_modes == ["Low", "Medium", "High"]
        # wind_level=2 → "Medium"
        assert dehumidifier.preset_mode == "Medium"

    def test_HDH002S_set_preset_mode(self): # pylint: disable=invalid-name
        """Test set_preset_mode with valid and invalid modes."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.set_preset_mode("Low")
            mock_send_command.assert_called_once_with(dehumidifier, {WINDLEVEL_KEY: 1})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.set_preset_mode("High")
            mock_send_command.assert_called_once_with(dehumidifier, {WINDLEVEL_KEY: 3})

        with pytest.raises(ValueError):
            dehumidifier.set_preset_mode("SuperFast")

    def test_HDH002S_childlockon_setter(self): # pylint: disable=invalid-name
        """Test childlockon setter sends correct command."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.childlockon = True
            mock_send_command.assert_called_once_with(dehumidifier, {CHILDLOCKON_KEY: True})

    def test_HDH002S_display_light_setter(self): # pylint: disable=invalid-name
        """Test display_light setter sends correct command."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.display_light = False
            mock_send_command.assert_called_once_with(dehumidifier, {LIGHTON_KEY: False})

    def test_HDH002S_auto_mode_setter(self): # pylint: disable=invalid-name
        """Test auto_mode setter sends correct command."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.auto_mode = True
            mock_send_command.assert_called_once_with(dehumidifier, {AUTOON_KEY: True})

    def test_HDH002S_handle_server_update_poweron(self): # pylint: disable=invalid-name
        """Test handle_server_update updates power state."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        dehumidifier.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert dehumidifier.is_on is True

        dehumidifier.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
        assert dehumidifier.is_on is False

    def test_HDH002S_handle_server_update_mode(self): # pylint: disable=invalid-name
        """Test handle_server_update updates operating mode."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        dehumidifier.handle_server_update({REPORTED_KEY: {MODE_KEY: 2}})
        assert dehumidifier.mode == "Continuous"

        dehumidifier.handle_server_update({REPORTED_KEY: {MODE_KEY: 1}})
        assert dehumidifier.mode == "Auto"

    def test_HDH002S_handle_server_update_humidity(self): # pylint: disable=invalid-name
        """Test handle_server_update updates humidity and target_humidity."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        dehumidifier.handle_server_update({REPORTED_KEY: {HUMIDITY_KEY: 75}})
        assert dehumidifier.humidity == 75

        dehumidifier.handle_server_update({REPORTED_KEY: {RHAUTOLEVEL_KEY: 60}})
        assert dehumidifier.target_humidity == 60

    def test_HDH002S_handle_server_update_wind_level(self): # pylint: disable=invalid-name
        """Test handle_server_update updates wind level."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        dehumidifier.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 1}})
        assert dehumidifier.wind_level == 1

    def test_HDH002S_handle_server_update_childlockon(self): # pylint: disable=invalid-name
        """Test handle_server_update updates childlockon state."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        dehumidifier.handle_server_update({REPORTED_KEY: {CHILDLOCKON_KEY: True}})
        assert dehumidifier.childlockon is True

    def test_HDH002S_handle_server_update_light(self): # pylint: disable=invalid-name
        """Test handle_server_update updates display light state."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        dehumidifier.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: False}})
        assert dehumidifier.display_light is False

        dehumidifier.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: True}})
        assert dehumidifier.display_light is True

    def test_HDH002S_handle_server_update_auto(self): # pylint: disable=invalid-name
        """Test handle_server_update updates auto mode state."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        dehumidifier.handle_server_update({REPORTED_KEY: {AUTOON_KEY: True}})
        assert dehumidifier.auto_mode is True

    def test_HDH002S_handle_server_update_temperature(self): # pylint: disable=invalid-name
        """Test handle_server_update updates temperature."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        dehumidifier.handle_server_update({REPORTED_KEY: {TEMPERATURE_KEY: 72}})
        assert dehumidifier.temperature == 72

    def test_HDH002S_oscillating_returns_false(self): # pylint: disable=invalid-name
        """Test that oscillating always returns False for dehumidifier."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        assert dehumidifier.oscillating is False

    def test_HDH005S_basic_properties(self): # pylint: disable=invalid-name
        """Load HDH005S dehumidifier and verify basic properties."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        assert dehumidifier.is_on is False
        assert dehumidifier.humidity == 60
        assert dehumidifier.target_humidity == 55
        assert dehumidifier.wind_level == 2
        assert dehumidifier.temperature == 72

    def test_HDH002S_power_cycle_stale_state(self): # pylint: disable=invalid-name
        """Test that power-on command is sent even when cached state appears stale."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        # Simulate stale WebSocket state indicating device is ON
        dehumidifier.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert dehumidifier.is_on is True

        # Command should always be sent for power-on
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.is_on = True
            mock_send_command.assert_called_once_with(dehumidifier, {POWERON_KEY: True})

    def test_HDH002S_panel_sound_setter(self): # pylint: disable=invalid-name
        """Test panel_sound setter sends muteon command correctly."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        # Initial muteon is False (panel_sound=True); set panel_sound=False → muteon=True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.panel_sound = False
            mock_send_command.assert_called_once_with(dehumidifier, {MUTEON_KEY: True})

        # Simulate server confirming mute change, then re-enable sound
        dehumidifier.handle_server_update({REPORTED_KEY: {MUTEON_KEY: True}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.panel_sound = True
            mock_send_command.assert_called_once_with(dehumidifier, {MUTEON_KEY: False})
