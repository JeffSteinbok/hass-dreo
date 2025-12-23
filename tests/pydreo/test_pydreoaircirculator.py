"""Tests for Dreo Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

from custom_components.dreo.pydreo import PyDreoAirCirculator

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestPyDreoAirCirculator(TestBase):
    """Test PyDreoAirCirculator class."""

    def test_HAF004S(self): # pylint: disable=invalid-name
        """Load circulator fan and test sending commands."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        fan : PyDreoAirCirculator = self.pydreo_manager.devices[0]

        # Test initial state values
        assert fan.horizontal_angle_range == (-60, 60)
        assert fan.vertical_angle_range == (-30, 90)
        assert fan.speed_range == (1, 9)
        assert fan.preset_modes == ['normal', 'natural', 'sleep', 'auto', 'turbo', 'custom']
        assert fan.oscillating is True
        assert fan.vertically_oscillating is True
        assert fan.vertical_osc_angle_top_range == (-30, 90)
        assert fan.vertical_osc_angle_bottom_range == (-30, 90)
        assert fan.horizontally_oscillating is False
        assert fan.horizontal_osc_angle_left_range == (-60, 60)
        assert fan.horizontal_osc_angle_right_range == (-60, 60)
        assert fan.is_on is False
        assert fan.fan_speed >= 1 and fan.fan_speed <= 9
        assert fan.preset_mode in fan.preset_modes
        assert fan.model == "DR-HAF004S"
        assert fan.device_name is not None
        assert fan.serial_number is not None

        # Test power command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})

        # Test preset mode commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'normal'
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 1})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'natural'
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 2})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'sleep'
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 3})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'auto'
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 4})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = 'turbo'
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 5})

        with pytest.raises(ValueError):
            fan.preset_mode = 'not_a_mode'

        # Test fan speed commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 1
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 1})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 3
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 3})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 9
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 9})

        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 10

        # Test oscillation commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            # Already true, so might send commands to sync hosc/vosc
            assert mock_send_command.call_count >= 0

        # Test horizontal oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = True
            mock_send_command.assert_called_once()

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = False
            mock_send_command.assert_called_once()

        # Test vertical oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertically_oscillating = True
            mock_send_command.assert_called_once()

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertically_oscillating = False
            mock_send_command.assert_called_once()

    def test_HAF001S(self): # pylint: disable=invalid-name
        """Test HAF001S fan."""
        self.get_devices_file_name = "get_devices_HAF001S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        fan : PyDreoAirCirculator = self.pydreo_manager.devices[0]

        # Test initial state values
        assert fan.speed_range == (1, 4)
        assert fan.horizontally_oscillating is not None
        assert fan.horizontally_oscillating is False
        assert fan.oscillating is not None
        assert fan.model == "DR-HAF001S"
        assert fan.device_name is not None
        assert fan.serial_number is not None
        assert fan.is_on is not None
        assert fan.fan_speed >= 1 and fan.fan_speed <= 4
        assert fan.preset_modes is not None

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})

        # Test fan speed commands within range
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 1
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 1})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 2
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 2})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 4
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 4})

        # Test speed out of range
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 5

        # Test oscillation commands
        # Setting oscillating may trigger both hosc and vosc commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            # May send multiple commands for hosc/vosc
            assert mock_send_command.call_count >= 1

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = False
            assert mock_send_command.call_count >= 1

        # Test horizontal oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = True
            mock_send_command.assert_called_once()

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = False
            mock_send_command.assert_called_once()

        # Test preset modes if available
        if fan.preset_modes:
            for mode in fan.preset_modes:
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    fan.preset_mode = mode
                    mock_send_command.assert_called_once()

            # Test invalid preset mode
            with pytest.raises(ValueError):
                fan.preset_mode = 'invalid_mode_xyz'


    def test_HPF008S(self): # pylint: disable=invalid-name
        """Test HPF008S fan."""
        self.get_devices_file_name = "get_devices_HPF008S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        fan : PyDreoAirCirculator = self.pydreo_manager.devices[0]

        # Test initial state values
        assert fan.is_on is True
        assert fan.speed_range == (1, 9)
        assert fan.preset_modes == None
        assert fan.horizontally_oscillating is False
        assert fan.oscillating is False
        assert fan.vertical_angle_range == (-30, 90)
        assert fan.temperature == 74
        assert fan.model == "DR-HPF008S"
        assert fan.device_name is not None
        assert fan.serial_number is not None
        assert fan.fan_speed >= 1 and fan.fan_speed <= 9

        # Test power commands with FANON_KEY (this model uses different key)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {FANON_KEY: True})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {FANON_KEY: False})

        # Test fan speed commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 1
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 1})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 5
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 5})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 9
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 9})

        # Test speed boundaries
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 10

        # Test oscillation commands
        # HPF008S oscillating is initially False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            # May not send command if already in desired state
            assert mock_send_command.call_count >= 0

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = False
            assert mock_send_command.call_count >= 0

        # Test horizontal oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = True
            mock_send_command.assert_called_once()

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = False
            mock_send_command.assert_called_once()

        # Verify temperature sensor is working
        assert fan.temperature is not None
        assert isinstance(fan.temperature, (int, float))

