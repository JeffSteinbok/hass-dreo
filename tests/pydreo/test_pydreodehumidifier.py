"""Tests for Dreo Dehumidifiers"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

from custom_components.dreo.pydreo import PyDreoDehumidifier

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Dehumidifier-specific keys used in commands and WebSocket messages
RHAUTOLEVEL_KEY = "rhautolevel"
AUTOON_KEY = "autoon"


class TestPyDreoDehumidifier(TestBase):
    """Test PyDreoDehumidifier class."""

    def test_HDH005S_initial_state(self):  # pylint: disable=invalid-name
        """Load dehumidifier and verify initial state from REST API."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1

        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        assert dehumidifier.is_on is False
        assert dehumidifier.humidity == 60
        assert dehumidifier.target_humidity == 55
        assert dehumidifier.wind_level == 2
        assert dehumidifier.fan_speed == 2
        assert dehumidifier.panel_sound is True  # muteon=False → panel_sound=True
        assert dehumidifier.display_light is True  # lighton=True
        assert dehumidifier.childlockon is False
        assert dehumidifier.auto_mode is False
        assert dehumidifier.temperature == 72
        assert dehumidifier.mode == "Auto"  # mode=1 → "Auto"
        assert dehumidifier.oscillating is False

    def test_HDH005S_speed_range(self):  # pylint: disable=invalid-name
        """Test speed_range and preset_modes."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        assert dehumidifier.speed_range == (1, 3)
        assert dehumidifier.preset_modes == ["Low", "Medium", "High"]
        # wind_level=2 → "Medium"
        assert dehumidifier.preset_mode == "Medium"

    def test_HDH005S_is_on_setter(self):  # pylint: disable=invalid-name
        """Test that is_on setter sends the correct command."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.is_on = True
            mock_send_command.assert_called_once_with(dehumidifier, {POWERON_KEY: True})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.is_on = False
            mock_send_command.assert_called_once_with(dehumidifier, {POWERON_KEY: False})

    def test_HDH005S_target_humidity_setter(self):  # pylint: disable=invalid-name
        """Test that target_humidity setter validates range and sends commands."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        # Valid value — sends command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.target_humidity = 60
            mock_send_command.assert_called_once_with(dehumidifier, {RHAUTOLEVEL_KEY: 60})

        # Out-of-range values raise ValueError
        with pytest.raises(ValueError):
            dehumidifier.target_humidity = 29

        with pytest.raises(ValueError):
            dehumidifier.target_humidity = 86

        # Duplicate value — no command sent
        dehumidifier._target_humidity = 60
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.target_humidity = 60
            mock_send_command.assert_not_called()

    def test_HDH005S_wind_level_setter(self):  # pylint: disable=invalid-name
        """Test that wind_level setter validates range and sends commands."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.wind_level = 1
            mock_send_command.assert_called_once_with(dehumidifier, {WINDLEVEL_KEY: 1})

        # Out-of-range values raise ValueError
        with pytest.raises(ValueError):
            dehumidifier.wind_level = 0

        with pytest.raises(ValueError):
            dehumidifier.wind_level = 4

        # Duplicate value — no command sent
        dehumidifier._wind_level = 3
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.wind_level = 3
            mock_send_command.assert_not_called()

    def test_HDH005S_fan_speed_setter(self):  # pylint: disable=invalid-name
        """Test that fan_speed setter delegates to wind_level."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.fan_speed = 3
            mock_send_command.assert_called_once_with(dehumidifier, {WINDLEVEL_KEY: 3})

        with pytest.raises(ValueError):
            dehumidifier.fan_speed = 5

    def test_HDH005S_panel_sound_setter(self):  # pylint: disable=invalid-name
        """Test that panel_sound setter sends the correct inverted mute command."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        # Turn sound off → muteon=True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.panel_sound = False
            mock_send_command.assert_called_once_with(dehumidifier, {MUTEON_KEY: True})

        # Duplicate value — no command sent (muteon is currently False → sound is True)
        dehumidifier._mute_on = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.panel_sound = True  # already True (muteon=False)
            mock_send_command.assert_not_called()

    def test_HDH005S_display_light_setter(self):  # pylint: disable=invalid-name
        """Test that display_light setter sends the correct command."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.display_light = False
            mock_send_command.assert_called_once_with(dehumidifier, {LIGHTON_KEY: False})

        # Duplicate value — no command sent
        dehumidifier._light_on = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.display_light = False
            mock_send_command.assert_not_called()

    def test_HDH005S_childlockon_setter(self):  # pylint: disable=invalid-name
        """Test that childlockon setter sends the correct command."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.childlockon = True
            mock_send_command.assert_called_once_with(dehumidifier, {CHILDLOCKON_KEY: True})

        # Duplicate value — no command sent
        dehumidifier._child_lock_on = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.childlockon = True
            mock_send_command.assert_not_called()

    def test_HDH005S_auto_mode_setter(self):  # pylint: disable=invalid-name
        """Test that auto_mode setter sends the correct command."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.auto_mode = True
            mock_send_command.assert_called_once_with(dehumidifier, {AUTOON_KEY: True})

        # Duplicate value — no command sent
        dehumidifier._auto_on = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.auto_mode = True
            mock_send_command.assert_not_called()

    def test_HDH005S_mode_setter(self):  # pylint: disable=invalid-name
        """Test that mode setter sends the correct command and raises on invalid mode."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        assert dehumidifier.modes == ["Auto", "Continuous"]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.mode = "Continuous"
            mock_send_command.assert_called_once_with(dehumidifier, {MODE_KEY: 2})

        # Invalid mode raises ValueError
        with pytest.raises(ValueError):
            dehumidifier.mode = "invalid_mode"

        # Duplicate value — no command sent
        dehumidifier._mode = 2
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.mode = "Continuous"
            mock_send_command.assert_not_called()

    def test_HDH005S_set_preset_mode(self):  # pylint: disable=invalid-name
        """Test that set_preset_mode maps preset strings to wind_level commands."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.set_preset_mode("Low")
            mock_send_command.assert_called_once_with(dehumidifier, {WINDLEVEL_KEY: 1})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.set_preset_mode("Medium")
            mock_send_command.assert_called_once_with(dehumidifier, {WINDLEVEL_KEY: 2})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.set_preset_mode("High")
            mock_send_command.assert_called_once_with(dehumidifier, {WINDLEVEL_KEY: 3})

        with pytest.raises(ValueError):
            dehumidifier.set_preset_mode("Turbo")

    def test_HDH005S_preset_mode_property(self):  # pylint: disable=invalid-name
        """Test that preset_mode property returns the correct string for each wind level."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        dehumidifier._wind_level = 1
        assert dehumidifier.preset_mode == "Low"

        dehumidifier._wind_level = 2
        assert dehumidifier.preset_mode == "Medium"

        dehumidifier._wind_level = 3
        assert dehumidifier.preset_mode == "High"

        dehumidifier._wind_level = None
        assert dehumidifier.preset_mode is None

    def test_HDH005S_handle_server_update(self):  # pylint: disable=invalid-name
        """Test that handle_server_update correctly updates all device state from WebSocket."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        # poweron
        dehumidifier.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert dehumidifier.is_on is True

        # mode
        dehumidifier.handle_server_update({REPORTED_KEY: {MODE_KEY: 2}})
        assert dehumidifier._mode == 2

        # humidity (rh)
        dehumidifier.handle_server_update({REPORTED_KEY: {HUMIDITY_KEY: 45}})
        assert dehumidifier.humidity == 45

        # target humidity
        dehumidifier.handle_server_update({REPORTED_KEY: {RHAUTOLEVEL_KEY: 65}})
        assert dehumidifier.target_humidity == 65

        # wind_level
        dehumidifier.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 3}})
        assert dehumidifier.wind_level == 3

        # muteon → panel_sound
        dehumidifier.handle_server_update({REPORTED_KEY: {MUTEON_KEY: True}})
        assert dehumidifier.panel_sound is False  # muted → sound off

        # lighton → display_light
        dehumidifier.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: False}})
        assert dehumidifier.display_light is False

        # childlockon
        dehumidifier.handle_server_update({REPORTED_KEY: {CHILDLOCKON_KEY: True}})
        assert dehumidifier.childlockon is True

        # autoon → auto_mode
        dehumidifier.handle_server_update({REPORTED_KEY: {AUTOON_KEY: True}})
        assert dehumidifier.auto_mode is True

        # temperature
        dehumidifier.handle_server_update({REPORTED_KEY: {TEMPERATURE_KEY: 75}})
        assert dehumidifier.temperature == 75

    def test_HDH005S_power_cycle_stale_state(self):  # pylint: disable=invalid-name
        """Test that is_on command is always sent even when cached state matches."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        # Simulate stale WebSocket update reporting device is ON
        dehumidifier.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert dehumidifier.is_on is True

        # Command MUST be sent even though cached state matches
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            dehumidifier.is_on = True
            mock_send_command.assert_called_once_with(dehumidifier, {POWERON_KEY: True})

    def test_HDH002S_initial_state(self):  # pylint: disable=invalid-name
        """Load HDH002S dehumidifier and verify initial state."""
        self.get_devices_file_name = "get_devices_HDH002S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1

        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        assert dehumidifier.is_on is False
        assert dehumidifier.humidity == 66
        assert dehumidifier.target_humidity == 50
        assert dehumidifier.wind_level == 2
        assert dehumidifier.temperature == 67
        assert dehumidifier.childlockon is False
        assert dehumidifier.auto_mode is False

    def test_HDH005S_panel_sound_none_mute(self):  # pylint: disable=invalid-name
        """Test panel_sound returns None when _mute_on is not initialised."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        dehumidifier._mute_on = None
        assert dehumidifier.panel_sound is None

    def test_HDH005S_mode_unknown_value(self):  # pylint: disable=invalid-name
        """Test that mode property returns None when internal mode value has no match."""
        self.get_devices_file_name = "get_devices_HDH005S.json"
        self.pydreo_manager.load_devices()
        dehumidifier: PyDreoDehumidifier = self.pydreo_manager.devices[0]

        dehumidifier._mode = 99  # not in [(Auto, 1), (Continuous, 2)]
        assert dehumidifier.mode is None
