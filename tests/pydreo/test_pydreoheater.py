"""Tests for Dreo Heaters"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch, call
import pytest
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestPyDreoHeater(TestBase):
    """Test PyDreoHeater class."""

    def test_HSH009S(self):  # pylint: disable=invalid-name
        """Load heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF])
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"

    def test_HSH011(self):  # pylint: disable=invalid-name
        """Load DR-HSH011 oil radiator heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH011.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH011"
        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"

    def test_HSH010S(self):  # pylint: disable=invalid-name
        """Load oil radiator heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH010S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"

    def test_WH714S(self):  # pylint: disable=invalid-name
        """Load WH714S heater and test sending commands."""

        self.get_devices_file_name = "get_devices_WH714S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH034S"
        assert heater.series_name == "WH714S"
        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"

    def test_HSH011S(self):  # pylint: disable=invalid-name
        """Load HSH011S (OH521S) oil radiator heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH011S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH011S"
        assert heater.series_name == "OH521S"
        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"

    def test_HSH004S(self):  # pylint: disable=invalid-name
        """Load HSH004S (Atom One S) heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH004S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH004S"
        assert heater.series_name == "Atom One S"
        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF])

        # Test temperature offset is applied to temperature reading
        assert heater.temperature_offset == 2
        assert heater.temperature == 66  # raw 64 + offset 2

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 2
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 2})], True)
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 2}})

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"

    def test_HSH004S_temperature_offset_update(self):  # pylint: disable=invalid-name
        """Test that temperature offset from server updates is applied to temperature."""

        self.get_devices_file_name = "get_devices_HSH004S.json"
        self.pydreo_manager.load_devices()
        heater = self.pydreo_manager.devices[0]

        # Initial state: raw temp 64, offset 2 -> calibrated 66
        assert heater.temperature == 66

        # Simulate a WebSocket update with new temperature and offset
        heater.handle_server_update({REPORTED_KEY: {TEMPERATURE_KEY: 70, TEMPOFFSET_KEY: -3}})
        assert heater.temperature_offset == -3
        assert heater.temperature == 67  # raw 70 + offset -3

    def test_HSH009S_power_cycle_stale_state(self):  # pylint: disable=invalid-name
        """Test that poweron command is sent even when cached state is stale after power cycle."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        # Simulate device power cycle scenario:
        # 1. Device is physically OFF (power cycled)
        # 2. Cloud sends stale WebSocket state with poweron: true
        # 3. User calls poweron = True
        # 4. Command should be sent even though cached state shows ON

        # Simulate stale WebSocket update reporting device is ON (but it's actually OFF)
        message = {"method": "control-report", "devicesn": "HSH009S_1", "reported": {"poweron": True}}
        heater.handle_server_update(message)
        assert heater.poweron is True  # Cached state shows ON

        # User calls poweron = True - command should be sent despite cached state being ON
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = True  # Attempt to turn on
            # Command MUST be sent even though cached state matches
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: True})

    def test_HSH009S_handle_server_update_all_fields(self):  # pylint: disable=invalid-name
        """Test that handle_server_update correctly updates all device state fields."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        # temperature
        heater.handle_server_update({REPORTED_KEY: {TEMPERATURE_KEY: 70}})
        assert heater.temperature == 70

        # mode (string for heater)
        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: DreoHeaterMode.HOTAIR}})
        assert heater.mode == DreoHeaterMode.HOTAIR

        # oscon
        heater.handle_server_update({REPORTED_KEY: {OSCON_KEY: True}})
        assert heater.oscon is True

        # oscangle
        heater.handle_server_update({REPORTED_KEY: {OSCANGLE_KEY: 90}})
        assert heater.oscangle == 90

        # muteon
        heater.handle_server_update({REPORTED_KEY: {MUTEON_KEY: False}})
        assert heater._mute_on is False

        # ptcon (PTC on implies device on)
        heater._is_on = False
        heater.handle_server_update({REPORTED_KEY: {PTCON_KEY: True}})
        assert heater.ptcon is True
        assert heater.poweron is True  # inferred from PTC turning on

        # ptcon off does not force device off
        heater.handle_server_update({REPORTED_KEY: {PTCON_KEY: False}})
        assert heater.ptcon is False

        # lighton
        heater.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: False}})
        assert heater._light_on is False

        # ecolevel (target temperature)
        heater.handle_server_update({REPORTED_KEY: {ECOLEVEL_KEY: 75}})
        assert heater.ecolevel == 75

        # childlockon
        heater.handle_server_update({REPORTED_KEY: {CHILDLOCKON_KEY: True}})
        assert heater.childlockon is True

        # tempoffset
        heater.handle_server_update({REPORTED_KEY: {TEMPOFFSET_KEY: 2}})
        assert heater._tempoffset == 2

    def test_HSH009S_setters_send_commands(self):  # pylint: disable=invalid-name
        """Test that heater setters send the correct commands."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        # oscon setter
        heater._oscon = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.oscon = True
            mock_send_command.assert_called_once_with(heater, {OSCON_KEY: True})

        # Duplicate value -- no command
        heater._oscon = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.oscon = True
            mock_send_command.assert_not_called()

        # oscangle setter
        heater._oscangle = 120
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.oscangle = 90
            mock_send_command.assert_called_once_with(heater, {OSCANGLE_KEY: 90})

        # Duplicate value -- no command
        heater._oscangle = 90
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.oscangle = 90
            mock_send_command.assert_not_called()

        # panel_sound setter (inverts mute)
        heater._mute_on = True  # currently muted (sound off)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.panel_sound = True  # turn sound on -> muteon=False
            mock_send_command.assert_called_once_with(heater, {MUTEON_KEY: False})

        # Duplicate value -- no command
        heater._mute_on = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.panel_sound = True  # sound already on (muteon=False)
            mock_send_command.assert_not_called()

        # ptcon setter
        heater._ptc_on = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ptcon = True
            mock_send_command.assert_called_once_with(heater, {PTCON_KEY: True})

        # Duplicate value -- no command
        heater._ptc_on = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ptcon = True
            mock_send_command.assert_not_called()

        # childlockon setter
        heater._childlockon = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.childlockon = True
            mock_send_command.assert_called_once_with(heater, {CHILDLOCKON_KEY: True})

        # Duplicate value -- no command
        heater._childlockon = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.childlockon = True
            mock_send_command.assert_not_called()

    def test_HSH009S_ecolevel_setter(self):  # pylint: disable=invalid-name
        """Test ecolevel setter sends correct command."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ecolevel = 68
            mock_send_command.assert_called_once_with(heater, {ECOLEVEL_KEY: 68})

        # Duplicate value -- no command
        heater._ecolevel = 68
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ecolevel = 68
            mock_send_command.assert_not_called()

    def test_HSH009S_devon_setter(self):  # pylint: disable=invalid-name
        """Test devon setter sends correct command."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        heater._dev_on = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.devon = True
            mock_send_command.assert_called_once_with(heater, {DEVON_KEY: True})

        # Duplicate value -- no command
        heater._dev_on = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.devon = True
            mock_send_command.assert_not_called()

    def test_HSH009S_lighton_setter(self):  # pylint: disable=invalid-name
        """Test lighton setter sends the inverted display auto-off command."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        # Manually set _light_on to a non-None value to enable the setter
        # (HSH009S state may not have a lighton field; we simulate a device that supports it)
        heater._light_on = True  # auto-off is ON
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            # lighton property = not _light_on; setting lighton=True flips to auto-off OFF
            heater.lighton = True  # turn display auto-off OFF -> send LIGHTON_KEY: False
            mock_send_command.assert_called_once_with(heater, {LIGHTON_KEY: False})

        # Duplicate value -- no command (_light_on=False -> lighton property is True; already True)
        heater._light_on = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.lighton = True
            mock_send_command.assert_not_called()

    def test_HSH009S_poweron_mode_off(self):  # pylint: disable=invalid-name
        """Test that poweron=False sets mode to OFF."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        heater._mode = DreoHeaterMode.HOTAIR
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
        assert heater.poweron is False
        assert heater.mode == DreoHeaterMode.OFF

    def test_HSH009S_htalevel_range_validation(self):  # pylint: disable=invalid-name
        """Test that htalevel rejects values outside the valid range."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        # Range is (1, 3) for HSH009S
        assert heater.htalevel_range == (1, 3)

        # Value below range should be rejected (no command sent)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 0
            mock_send_command.assert_not_called()

        # Value above range should be rejected (no command sent)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 4
            mock_send_command.assert_not_called()

        # Value within range should be accepted
        heater._htalevel = None  # reset to avoid duplicate check
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 2
            mock_send_command.assert_called_once_with(heater, {HTALEVEL_KEY: 2})

    def test_HSH009S_ecolevel_range_validation(self):  # pylint: disable=invalid-name
        """Test that ecolevel rejects values outside the valid range."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        eco_range = heater.ecolevel_range

        # Value below range should be rejected
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ecolevel = eco_range[0] - 1
            mock_send_command.assert_not_called()

        # Value above range should be rejected
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ecolevel = eco_range[1] + 1
            mock_send_command.assert_not_called()

        # Boundary values should be accepted
        heater._ecolevel = None
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ecolevel = eco_range[0]
            mock_send_command.assert_called_once_with(heater, {ECOLEVEL_KEY: eco_range[0]})

    def test_HSH009S_timer_parsing_safe(self):  # pylint: disable=invalid-name
        """Test that timer parsing handles None and missing 'du' gracefully."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        heater = self.pydreo_manager.devices[0]

        # Timer with valid dict
        heater.update_state({TIMERON_KEY: {"state": {"du": 120}}, TIMEROFF_KEY: {"state": {"du": 60}}})
        assert heater._timer_on == 120
        assert heater._timer_off == 60

        # Timer with None value in state
        heater.update_state({TIMERON_KEY: {"state": None}, TIMEROFF_KEY: {"state": None}})
        assert heater._timer_on is None
        assert heater._timer_off is None

        # Timer key absent from state entirely
        heater.update_state({})
        assert heater._timer_on is None
        assert heater._timer_off is None

        # Timer with dict missing 'du' key
        heater.update_state({TIMERON_KEY: {"state": {"other": 1}}, TIMEROFF_KEY: {"state": {"other": 2}}})
        assert heater._timer_on is None
        assert heater._timer_off is None
