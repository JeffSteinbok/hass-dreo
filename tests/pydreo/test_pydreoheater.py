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
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, 
                                               DreoHeaterMode.HOTAIR, 
                                               DreoHeaterMode.ECO, 
                                               DreoHeaterMode.OFF])
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({ REPORTED_KEY: {POWERON_KEY: False} })

        with (patch(PATCH_SEND_COMMAND) as mock_send_command):
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({ REPORTED_KEY: {HTALEVEL_KEY: 1} })

        with pytest.raises(ValueError):
            heater.mode = 'not_a_mode'

    def test_HSH010S(self): # pylint: disable=invalid-name
        """Load oil radiator heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH010S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, 
                                               DreoHeaterMode.HOTAIR, 
                                               DreoHeaterMode.ECO, 
                                               DreoHeaterMode.OFF])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({ REPORTED_KEY: {POWERON_KEY: False} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({ REPORTED_KEY: {HTALEVEL_KEY: 1} })

        with pytest.raises(ValueError):
            heater.mode = 'not_a_mode'

    def test_WH714S(self): # pylint: disable=invalid-name
        """Load WH714S heater and test sending commands."""

        self.get_devices_file_name = "get_devices_WH714S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH034S"
        assert heater.series_name == "WH714S"
        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, 
                                               DreoHeaterMode.HOTAIR, 
                                               DreoHeaterMode.ECO, 
                                               DreoHeaterMode.OFF])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({ REPORTED_KEY: {POWERON_KEY: False} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({ REPORTED_KEY: {HTALEVEL_KEY: 1} })

        with pytest.raises(ValueError):
            heater.mode = 'not_a_mode'

    def test_HSH011S(self): # pylint: disable=invalid-name
        """Load HSH011S (OH521S) oil radiator heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH011S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH011S"
        assert heater.series_name == "OH521S"
        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR,
                                               DreoHeaterMode.HOTAIR,
                                               DreoHeaterMode.ECO,
                                               DreoHeaterMode.OFF])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({ REPORTED_KEY: {POWERON_KEY: False} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({ REPORTED_KEY: {HTALEVEL_KEY: 1} })

        with pytest.raises(ValueError):
            heater.mode = 'not_a_mode'

    def test_HSH004S(self): # pylint: disable=invalid-name
        """Load HSH004S (Atom One S) heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH004S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH004S"
        assert heater.series_name == "Atom One S"
        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, 
                                               DreoHeaterMode.HOTAIR, 
                                               DreoHeaterMode.ECO, 
                                               DreoHeaterMode.OFF])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({ REPORTED_KEY: {POWERON_KEY: False} })

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 2
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 2})], True)
        heater.handle_server_update({ REPORTED_KEY: {HTALEVEL_KEY: 2} })

        with pytest.raises(ValueError):
            heater.mode = 'not_a_mode'

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
        message = {
            "method": "control-report",
            "devicesn": "HSH009S_1",
            "reported": {
                "poweron": True
            }
        }
        heater.handle_server_update(message)
        assert heater.poweron is True  # Cached state shows ON
        
        # User calls poweron = True - command should be sent despite cached state being ON
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = True  # Attempt to turn on
            # Command MUST be sent even though cached state matches
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: True})

    def test_HSH009S_handle_server_update_temperature(self):  # pylint: disable=invalid-name
        """Test handle_server_update updates temperature."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        heater = self.pydreo_manager.devices[0]

        heater.handle_server_update({REPORTED_KEY: {TEMPERATURE_KEY: 75}})
        assert heater.temperature == 75

    def test_HSH009S_handle_server_update_mode_valid(self):  # pylint: disable=invalid-name
        """Test handle_server_update updates mode with valid mode string."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        heater = self.pydreo_manager.devices[0]

        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: DreoHeaterMode.HOTAIR}})
        assert heater.mode == DreoHeaterMode.HOTAIR

    def test_HSH009S_handle_server_update_mode_invalid_becomes_off(self):  # pylint: disable=invalid-name
        """Test handle_server_update sets mode to OFF when receiving an unknown mode."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        heater = self.pydreo_manager.devices[0]

        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: "unknown_mode"}})
        assert heater.mode == DreoHeaterMode.OFF

    def test_HSH009S_handle_server_update_ecolevel(self):  # pylint: disable=invalid-name
        """Test handle_server_update updates ecolevel (target temperature)."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        heater = self.pydreo_manager.devices[0]

        heater.handle_server_update({REPORTED_KEY: {ECOLEVEL_KEY: 75}})
        assert heater.ecolevel == 75

    def test_HSH009S_handle_server_update_ptcon_implies_power_on(self):  # pylint: disable=invalid-name
        """Test that handle_server_update infers device is on when PTC turns on."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        heater = self.pydreo_manager.devices[0]

        # Power off device first
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
        assert heater.poweron is False

        # PTC turning on implies device is powered on
        heater.handle_server_update({REPORTED_KEY: {PTCON_KEY: True}})
        assert heater.ptcon is True
        assert heater.poweron is True

    def test_HSH009S_handle_server_update_childlockon(self):  # pylint: disable=invalid-name
        """Test handle_server_update updates childlockon state."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        heater = self.pydreo_manager.devices[0]

        heater.handle_server_update({REPORTED_KEY: {CHILDLOCKON_KEY: True}})
        assert heater.childlockon is True

    def test_HSH009S_mode_setter_invalid_raises(self):  # pylint: disable=invalid-name
        """Test that mode setter raises ValueError for invalid mode."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        heater = self.pydreo_manager.devices[0]

        with pytest.raises(ValueError):
            heater.mode = "totally_invalid_mode"
