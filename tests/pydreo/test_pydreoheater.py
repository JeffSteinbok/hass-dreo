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

    def test_HSH011(self): # pylint: disable=invalid-name
        """Load DR-HSH011 oil radiator heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH011.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH011"
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
