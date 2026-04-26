"""Tests for Dreo Air Conditioners"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

from custom_components.dreo.pydreo import PyDreoAC
from custom_components.dreo.pydreo.pydreoairconditioner import DreoACMode, AC_OSC_ON, AC_OSC_OFF

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestPyDreoAirConditioner(TestBase):
    """Test TestPyDreoAirConditioner class."""

    def test_HAC006S(self):  # pylint: disable=invalid-name
        """Load air conditioner and test sending commands."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        ac: PyDreoAC = self.pydreo_manager.devices[0]

        assert sorted(ac.modes) == sorted([DreoACMode.COOL, DreoACMode.DRY, DreoACMode.FAN, DreoACMode.ECO, DreoACMode.SLEEP])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.poweron = True
            mock_send_command.assert_called_once_with(ac, {POWERON_KEY: True})
        ac.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.mode = DreoACMode.ECO
            mock_send_command.assert_called_once_with(ac, {WIND_MODE_KEY: 5})
        ac.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 5}})

        # Test sleep preset mode
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.mode = DreoACMode.SLEEP
            mock_send_command.assert_called_once_with(ac, {WIND_MODE_KEY: 4})
        ac.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 4}})

    def test_HAC006S_initial_state(self):  # pylint: disable=invalid-name
        """Verify initial state loaded from REST API."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        assert ac.poweron is False
        assert ac.temperature == 74
        assert ac.target_temperature == 76
        assert ac.humidity == 45
        assert ac.target_humidity == 50
        assert ac.childlockon is False
        assert ac.ptcon is False
        assert ac.display_auto_off is False  # lighton=True → display_auto_off=False
        assert ac.oscon is False  # oscmode=0 → off

    def test_HAC006S_fan_mode_setter(self):  # pylint: disable=invalid-name
        """Test that fan_mode setter sends the correct command."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        # Initial fan_mode is 4; set to a different value
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.fan_mode = 1
            mock_send_command.assert_called_once_with(ac, {WINDLEVEL_KEY: 1})

        # Duplicate value -- no command
        ac._fan_mode = 1
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.fan_mode = 1
            mock_send_command.assert_not_called()

    def test_HAC006S_target_humidity_setter(self):  # pylint: disable=invalid-name
        """Test that target_humidity setter sends the correct command."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.target_humidity = 55
            mock_send_command.assert_called_once_with(ac, {TARGET_HUMIDITY_KEY: 55})

        # Duplicate value -- no command
        ac._target_humidity = 55
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.target_humidity = 55
            mock_send_command.assert_not_called()

    def test_HAC006S_oscon_setter(self):  # pylint: disable=invalid-name
        """Test that oscon setter sends the correct mapped command."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        # Enable oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.oscon = True
            mock_send_command.assert_called_once_with(ac, {OSCMODE_KEY: AC_OSC_ON})

        # Disable oscillation
        ac._osc_mode = AC_OSC_ON
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.oscon = False
            mock_send_command.assert_called_once_with(ac, {OSCMODE_KEY: AC_OSC_OFF})

        # Duplicate value -- no command
        ac._osc_mode = AC_OSC_OFF
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.oscon = False
            mock_send_command.assert_not_called()

    def test_HAC006S_ptcon_setter(self):  # pylint: disable=invalid-name
        """Test that ptcon setter sends the correct command."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.ptcon = True
            mock_send_command.assert_called_once_with(ac, {PTCON_KEY: True})

        # Duplicate value -- no command
        ac._ptc_on = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.ptcon = True
            mock_send_command.assert_not_called()

    def test_HAC006S_display_auto_off_setter(self):  # pylint: disable=invalid-name
        """Test that display_auto_off setter sends the inverted lighton command."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        # Enable auto-off (lighton=False)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.display_auto_off = True
            mock_send_command.assert_called_once_with(ac, {LIGHTON_KEY: False})

        # Disable auto-off (lighton=True)
        ac._display_auto_off = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.display_auto_off = False
            mock_send_command.assert_called_once_with(ac, {LIGHTON_KEY: True})

        # Duplicate value -- no command
        ac._display_auto_off = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.display_auto_off = False
            mock_send_command.assert_not_called()

    def test_HAC006S_target_temperature_fahrenheit(self):  # pylint: disable=invalid-name
        """Test target_temperature setter in Fahrenheit mode (passthrough)."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        # Force Fahrenheit mode
        ac._ha_uses_celsius = False
        ac._mode = DreoACMode.COOL  # non-SLEEP mode

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.target_temperature = 72
            mock_send_command.assert_called_once_with(ac, {TARGET_TEMPERATURE_KEY: 72})

        # Duplicate value -- no command
        ac._target_temperature = 72
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.target_temperature = 72
            mock_send_command.assert_not_called()

    def test_HAC006S_handle_server_update_all_fields(self):  # pylint: disable=invalid-name
        """Test handle_server_update processes all WebSocket fields correctly."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        # poweron
        ac.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert ac.poweron is True

        # temperature
        ac.handle_server_update({REPORTED_KEY: {TEMPERATURE_KEY: 78}})
        assert ac.temperature == 78

        # target_temperature
        ac.handle_server_update({REPORTED_KEY: {TARGET_TEMPERATURE_KEY: 70}})
        assert ac.target_temperature == 70

        # mode
        ac.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 2}})
        assert ac.mode == 2

        # fan_mode (windlevel)
        ac.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 3}})
        assert ac.fan_mode == 3

        # osc_mode
        ac.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: AC_OSC_ON}})
        assert ac.oscon is True

        # muteon
        ac.handle_server_update({REPORTED_KEY: {MUTEON_KEY: False}})
        assert ac._mute_on is False

        # devon
        ac.handle_server_update({REPORTED_KEY: {DEVON_KEY: False}})
        assert ac.devon is False

        # cooldown
        ac.handle_server_update({REPORTED_KEY: {COOLDOWN_KEY: 5}})
        assert ac._cooldown == 5

        # ptcon
        ac.handle_server_update({REPORTED_KEY: {PTCON_KEY: True}})
        assert ac.ptcon is True

        # lighton → display_auto_off (inverted)
        ac.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: False}})
        assert ac.display_auto_off is True

        ac.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: True}})
        assert ac.display_auto_off is False

        # childlockon
        ac.handle_server_update({REPORTED_KEY: {CHILDLOCKON_KEY: True}})
        assert ac.childlockon is True

        # tempoffset
        ac.handle_server_update({REPORTED_KEY: {TEMPOFFSET_KEY: 2}})
        assert ac._tempoffset == 2

        # work_time
        ac.handle_server_update({REPORTED_KEY: {WORKTIME_KEY: 1800}})
        assert ac.work_time == 1800

    def test_HAC006S_mode_duplicate_no_command(self):  # pylint: disable=invalid-name
        """Test that setting the same mode sends no command."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        # Set mode to COOL first
        ac._mode = DreoACMode.COOL
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.mode = DreoACMode.COOL
            mock_send_command.assert_not_called()

    def test_HAC006S_power_cycle_always_sends(self):  # pylint: disable=invalid-name
        """Test that poweron command is always sent even when cached state matches."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        # Simulate stale state
        ac.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert ac.poweron is True

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.poweron = True
            mock_send_command.assert_called_once_with(ac, {POWERON_KEY: True})
        # TODO: Fix this in the AC class
        # with pytest.raises(ValueError):
        #    ac.preset_mode = 'not_a_mode'

    def test_HAC006S_temperature_offset(self):  # pylint: disable=invalid-name
        """Test that temperature offset is applied to air conditioner temperature."""
        self.get_devices_file_name = "get_devices_HAC006S.json"
        self.pydreo_manager.load_devices()

        ac: PyDreoAC = self.pydreo_manager.devices[0]

        # Initial state: raw temp 74, offset 0 -> calibrated 74
        assert ac.temperature_offset == 0
        assert ac.temperature == 74

        # Simulate a WebSocket update with new temperature and offset
        ac.handle_server_update({REPORTED_KEY: {TEMPERATURE_KEY: 80, TEMPOFFSET_KEY: -5}})
        assert ac.temperature_offset == -5
        assert ac.temperature == 75  # raw 80 + offset -5
