"""Tests for Dreo Fans"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

from custom_components.dreo.pydreo import PyDreoAirCirculator

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

AIRCIRCULATOR_EXHAUSTIVE_MODELS = [
    "get_devices_HAF001S.json",
    "get_devices_HAF003S.json",
    "get_devices_HAF004S.json",
    "get_devices_HAF004S_2REVS.json",
    "get_devices_HAF008S.json",
    "get_devices_HPF002S.json",
    "get_devices_HPF004S.json",
    "get_devices_HPF005S.json",
    "get_devices_HPF007S.json",
    "get_devices_HPF008S.json",
    "get_devices_HPF015S.json",
    "get_devices_HPF020S.json",
    "get_devices_HPF022S.json",
    "get_devices_HPF025S.json",
]


class TestPyDreoAirCirculator(TestBase):
    """Test PyDreoAirCirculator class."""

    def _exercise_all_settable_properties(self, fan: PyDreoAirCirculator):
        """Exercise all writable air-circulator properties supported by a model."""
        _ = fan.speed_range
        _ = fan.preset_modes
        _ = fan.is_on
        _ = fan.fan_speed
        _ = fan.preset_mode
        _ = fan.temperature
        _ = fan.temperature_units
        _ = fan.temperature_offset
        _ = fan.oscillating
        _ = fan.horizontally_oscillating
        _ = fan.vertically_oscillating
        _ = fan.horizontal_angle
        _ = fan.vertical_angle
        _ = fan.horizontal_oscillation_angle
        _ = fan.vertical_oscillation_angle
        _ = fan.horizontal_osc_angle_left
        _ = fan.horizontal_osc_angle_right
        _ = fan.vertical_osc_angle_top
        _ = fan.vertical_osc_angle_bottom
        _ = fan.display_auto_off
        _ = fan.adaptive_brightness
        _ = fan.panel_sound
        _ = fan.pm25
        _ = fan.atm_light_on
        _ = fan.atm_brightness
        _ = fan.atm_color_rgb
        _ = fan.atm_mode

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = not bool(fan.is_on)
            mock_send_command.assert_called_once()

        low, high = fan.speed_range
        new_speed = low if fan.fan_speed != low else high
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = new_speed
            mock_send_command.assert_called_once()

        if fan.preset_modes:
            for mode in fan.preset_modes:
                if mode != fan.preset_mode:
                    with patch(PATCH_SEND_COMMAND) as mock_send_command:
                        fan.preset_mode = mode
                        mock_send_command.assert_called_once()
                    break

        if fan.oscillating is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.oscillating = not bool(fan.oscillating)
                assert mock_send_command.call_count >= 1

        if fan.horizontally_oscillating is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.horizontally_oscillating = not bool(fan.horizontally_oscillating)
                mock_send_command.assert_called_once()

        if fan.vertically_oscillating is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.vertically_oscillating = not bool(fan.vertically_oscillating)
                mock_send_command.assert_called_once()

        if fan.horizontal_angle is not None:
            new_horizontal_angle = fan.horizontal_angle + 1
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.horizontal_angle = new_horizontal_angle
                mock_send_command.assert_called_once()

        if fan.vertical_angle is not None:
            new_vertical_angle = fan.vertical_angle + 1
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.vertical_angle = new_vertical_angle
                mock_send_command.assert_called_once()

        if fan.horizontal_oscillation_angle is not None:
            new_horizontal_oscillation_angle = fan.horizontal_oscillation_angle + 1
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.horizontal_oscillation_angle = new_horizontal_oscillation_angle
                mock_send_command.assert_called_once()

        if fan.vertical_oscillation_angle is not None:
            new_vertical_oscillation_angle = fan.vertical_oscillation_angle + 1
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.vertical_oscillation_angle = new_vertical_oscillation_angle
                mock_send_command.assert_called_once()

        if fan.vertical_osc_angle_top is not None and fan.vertical_osc_angle_bottom is not None:
            new_top = fan.vertical_osc_angle_bottom + 30
            if new_top == fan.vertical_osc_angle_top:
                new_top += 1
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.vertical_osc_angle_top = new_top
                mock_send_command.assert_called_once()

            new_bottom = fan.vertical_osc_angle_top - 30
            if new_bottom == fan.vertical_osc_angle_bottom:
                new_bottom -= 1
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.vertical_osc_angle_bottom = new_bottom
                mock_send_command.assert_called_once()

        if fan.horizontal_osc_angle_right is not None and fan.horizontal_osc_angle_left is not None:
            new_right = fan.horizontal_osc_angle_left + 30
            if new_right == fan.horizontal_osc_angle_right:
                new_right += 1
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.horizontal_osc_angle_right = new_right
                mock_send_command.assert_called_once()

            new_left = fan.horizontal_osc_angle_right - 30
            if new_left == fan.horizontal_osc_angle_left:
                new_left -= 1
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.horizontal_osc_angle_left = new_left
                mock_send_command.assert_called_once()

        if fan.display_auto_off is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.display_auto_off = not bool(fan.display_auto_off)
                mock_send_command.assert_called_once()

        if fan.adaptive_brightness is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.adaptive_brightness = not bool(fan.adaptive_brightness)
                mock_send_command.assert_called_once()

        if fan.panel_sound is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.panel_sound = not bool(fan.panel_sound)
                mock_send_command.assert_called_once()

        if fan.pm25 is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.pm25 = fan.pm25 + 1
                mock_send_command.assert_called_once()

        if fan.atm_light_on is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.atm_light_on = not fan.atm_light_on
                mock_send_command.assert_called_once()

        if fan.atm_brightness is not None:
            new_atm_brightness = 1 if fan.atm_brightness != 1 else 2
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.atm_brightness = new_atm_brightness
                mock_send_command.assert_called_once()

        if fan.atm_color_rgb is not None:
            new_color = (255, 0, 0) if fan.atm_color_rgb != (255, 0, 0) else (0, 255, 0)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.atm_color_rgb = new_color
                mock_send_command.assert_called_once()

    def test_HAF004S(self):  # pylint: disable=invalid-name
        """Load circulator fan and test sending commands."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]

        # Test initial state values
        assert fan.horizontal_angle_range == (-60, 60)
        assert fan.vertical_angle_range == (0, 90)
        assert fan.speed_range == (1, 9)
        assert fan.preset_modes == ["normal", "natural", "sleep", "auto", "turbo", "custom"]
        assert fan.oscillating is True
        assert fan.vertically_oscillating is True
        assert fan.vertical_osc_angle_top_range == (0, 90)
        assert fan.vertical_osc_angle_bottom_range == (0, 90)
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
            fan.preset_mode = "natural"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 2}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 3}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "auto"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 4}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "turbo"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 5})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 5}})

        with pytest.raises(ValueError):
            fan.preset_mode = "not_a_mode"

        # Test fan speed commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 1
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 1})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 1}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 3
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 3}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 9
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 9})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 9}})

        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 10

        # Test oscillation commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            # oscmode is currently 2 (VERTICAL), setting to True will make it HORIZONTAL (1)
            mock_send_command.assert_called_once_with(fan, {OSCMODE_KEY: 1})
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 1}})

        # Test horizontal oscillation - turn it off
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = False
            mock_send_command.assert_called_once_with(fan, {OSCMODE_KEY: 0})
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 0}})

        # Test vertical oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertically_oscillating = True
            mock_send_command.assert_called_once_with(fan, {OSCMODE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 2}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertically_oscillating = False
            mock_send_command.assert_called_once_with(fan, {OSCMODE_KEY: 0})
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 0}})

    def test_HAF004S_oscillation_angle_validation(self):  # pylint: disable=invalid-name
        """Test that oscillation angle setters reject angles that are too close together."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]

        # Initial cruise_conf is "60,45,0,-45" (top=60, right=45, bottom=0, left=-45)
        assert fan.vertical_osc_angle_top == 60
        assert fan.vertical_osc_angle_bottom == 0
        assert fan.horizontal_osc_angle_right == 45
        assert fan.horizontal_osc_angle_left == -45

        # Top angle too close to bottom (difference < 30)
        with pytest.raises(ValueError):
            fan.vertical_osc_angle_top = 29  # bottom is 0, 29-0=29 < 30

        # Bottom angle too close to top (difference < 30)
        with pytest.raises(ValueError):
            fan.vertical_osc_angle_bottom = 31  # top is 60, 60-31=29 < 30

        # Right angle too close to left (difference < 30)
        with pytest.raises(ValueError):
            fan.horizontal_osc_angle_right = -16  # left is -45, -16-(-45)=29 < 30

        # Left angle too close to right (difference < 30)
        with pytest.raises(ValueError):
            fan.horizontal_osc_angle_left = 16  # right is 45, 45-16=29 < 30

        # Boundary: exactly at MIN_OSC_ANGLE_DIFFERENCE should succeed
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertical_osc_angle_top = 30  # bottom is 0, 30-0=30 == MIN
            mock_send_command.assert_called_once()

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontal_osc_angle_right = -15  # left is -45, -15-(-45)=30 == MIN
            mock_send_command.assert_called_once()

    def test_HAF001S(self):  # pylint: disable=invalid-name
        """Test HAF001S fan."""
        self.get_devices_file_name = "get_devices_HAF001S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]

        # Test initial state values
        assert fan.speed_range == (1, 4)
        assert fan.horizontally_oscillating is not None
        assert fan.horizontally_oscillating is False
        assert fan.oscillating is not None
        assert fan.model == "DR-HAF001S"
        assert fan.device_name is not None
        assert fan.serial_number is not None
        assert fan.is_on is True
        assert fan.fan_speed >= 1 and fan.fan_speed <= 4
        assert fan.preset_modes is not None
        assert fan.preset_modes == ["normal", "natural", "sleep", "auto"]

        # Test display_auto_off (ledkepton: False initially means display auto-off is enabled)
        assert fan.display_auto_off is not None
        assert fan.display_auto_off is True  # ledkepton=False → display_auto_off=True

        # Test child lock (childlockon: False initially)
        assert fan.childlockon is not None
        assert fan.childlockon is False

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        # Test fan speed commands within range
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 1
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 1})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 1}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 2
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 2}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 4
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 4}})

        # Test speed out of range
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 5

        # Test oscillation commands
        # HAF001S uses hoscon/voscon model. Setting oscillating = True sends
        # horizontally_oscillating = True AND vertically_oscillating = False (2 commands)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            assert mock_send_command.call_count == 2
        fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = False
            assert mock_send_command.call_count == 2
        fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: False}})

        # Test horizontal oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = True
            mock_send_command.assert_called_once()
        fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = False
            mock_send_command.assert_called_once()
        fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: False}})

        # Test preset mode commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "natural"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 2}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 3}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "auto"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 4}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "normal"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 1})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 1}})

        # Test invalid preset mode
        with pytest.raises(ValueError):
            fan.preset_mode = "invalid_mode_xyz"

        # Test display_auto_off commands (uses ledkepton key)
        # display_auto_off=True → ledkepton=False (do not keep LED on)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.display_auto_off = False
            mock_send_command.assert_called_once_with(fan, {LEDKEPTON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {LEDKEPTON_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.display_auto_off = True
            mock_send_command.assert_called_once_with(fan, {LEDKEPTON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {LEDKEPTON_KEY: False}})

        # Test child lock commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.childlockon = True
            mock_send_command.assert_called_once_with(fan, {CHILDLOCKON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {CHILDLOCKON_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.childlockon = False
            mock_send_command.assert_called_once_with(fan, {CHILDLOCKON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {CHILDLOCKON_KEY: False}})

    def test_HAF008S(self):  # pylint: disable=invalid-name
        """Test HAF008S air circulator (565S series, empty controlsConf)."""
        self.get_devices_file_name = "get_devices_HAF008S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]

        # Test initial state values
        assert fan.speed_range == (1, 9)
        assert fan.preset_modes == ["normal", "natural", "sleep", "auto", "turbo"]
        assert fan.preset_mode == "normal"  # Initial mode is 1
        assert fan.model == "DR-HAF008S"
        assert fan.device_name is not None
        assert fan.serial_number is not None
        assert fan.is_on is False
        assert fan.fan_speed == 3

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        # Test fan speed commands within range
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 1
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 1})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 1}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 9
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 9})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 9}})

        # Test speed out of range
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 10

        # Test preset mode commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "natural"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 2}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 3}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "auto"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 4}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "turbo"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 5})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 5}})
        assert fan.preset_mode == "turbo"

        with pytest.raises(ValueError):
            fan.preset_mode = "not_a_mode"

        # Test oscillation commands (oscmode-based)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            mock_send_command.assert_called_once_with(fan, {OSCMODE_KEY: 1})
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 1}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = False
            mock_send_command.assert_called_once_with(fan, {OSCMODE_KEY: 0})
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 0}})

    def test_HPF002S(self):  # pylint: disable=invalid-name
        """Test HPF002S fan."""
        self.get_devices_file_name = "get_devices_HPF002S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]

        # Test initial state values
        assert fan.is_on is False
        assert fan.speed_range == (1, 8)
        assert fan.preset_modes == ["normal", "natural", "sleep", "auto", "turbo", "custom"]
        assert fan.preset_mode == "sleep"  # Initial mode is 3 which is "sleep"
        assert fan.temperature == 82
        assert fan.model == "DR-HPF002S"
        assert fan.device_name is not None
        assert fan.serial_number is not None
        assert fan.fan_speed == 1
        assert fan.angle_preset == "0,0"
        assert fan.angle_preset_options == ["0,0"]

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        # Test fan speed commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 4
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 4}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 8
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 8})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 8}})

        # Test speed boundaries
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 9

        # Test oscillation commands (HPF002S uses oscmode, initial state is 1/on)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = False
            assert mock_send_command.call_count == 1
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 0}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            assert mock_send_command.call_count == 1
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 1}})

        # Test preset mode commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "normal"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 1})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 1}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "turbo"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 5})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 5}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "custom"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 6})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 6}})

        # Test 3D angle preset handling
        fan.handle_server_update({REPORTED_KEY: {FIXEDCONF_KEY: "-15,-5"}})
        assert fan.angle_preset == "-15,-5"
        assert fan.angle_preset_options == ["0,0", "-15,-5"]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.angle_preset = "0,0"
            mock_send_command.assert_called_once_with(fan, {FIXEDCONF_KEY: "0,0"})

    def test_HPF008S(self):  # pylint: disable=invalid-name
        """Test HPF008S fan."""
        self.get_devices_file_name = "get_devices_HPF008S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]

        # Test initial state values
        assert fan.is_on is True
        assert fan.speed_range == (1, 9)
        assert fan.preset_modes == ["normal", "natural", "sleep", "auto", "turbo"]
        assert fan.preset_mode == "normal"  # Initial mode is 1 which is "normal"
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
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {FANON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {FANON_KEY: False}})

        # Test fan speed commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 1
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 1})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 1}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 5
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 5})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 5}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 9
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 9})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 9}})

        # Test speed boundaries
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 10

        # Test oscillation commands
        # HPF008S uses oscmode model. Initially oscillating is False (oscmode=0)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            assert mock_send_command.call_count == 1
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 1}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = False
            assert mock_send_command.call_count == 1
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 0}})

        # Test horizontal oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = True
            mock_send_command.assert_called_once()
        fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = False
            mock_send_command.assert_called_once()
        fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: False}})

        # Test preset mode commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "auto"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 4}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 3}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "natural"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 2}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "turbo"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 5})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 5}})

        # Test invalid preset mode
        with pytest.raises(ValueError):
            fan.preset_mode = "invalid_mode"

        # Verify temperature sensor is working
        assert fan.temperature is not None
        assert isinstance(fan.temperature, (int, float))

        # Test atmosphere (RGB) light support - HPF008S has atm light
        assert fan.is_feature_supported("atm_light") is True
        assert fan.atm_light_on is False  # Initial state from JSON: atmon=false
        assert fan.atm_brightness == 1  # Initial state from JSON: atmbri=1
        assert fan.atm_color_rgb is not None
        assert fan.atm_mode == 1  # Initial state from JSON: atmmode=1

        # Test atm_light_on command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_light_on = True
            mock_send_command.assert_called_once_with(fan, {ATMON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {ATMON_KEY: True}})
        assert fan.atm_light_on is True

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_light_on = False
            mock_send_command.assert_called_once_with(fan, {ATMON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {ATMON_KEY: False}})

        # Test atm_brightness command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_brightness = 5
            mock_send_command.assert_called_once_with(fan, {ATMBRI_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {ATMBRI_KEY: 3}})
        assert fan.atm_brightness == 3

        # Test atm_color_rgb command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_color_rgb = (255, 0, 0)  # Red
            mock_send_command.assert_called_once_with(fan, {ATMCOLOR_KEY: 16711680})  # 0xFF0000
        fan.handle_server_update({REPORTED_KEY: {ATMCOLOR_KEY: 16711680}})
        assert fan.atm_color_rgb == (255, 0, 0)

    def test_HPF015S(self):  # pylint: disable=invalid-name
        """Test HPF015S fan with empty controlsConf."""
        self.get_devices_file_name = "get_devices_HPF015S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]

        assert fan.model == "DR-HPF015S"
        assert fan.speed_range == (1, 12)
        assert fan.horizontal_angle_range == (-75, 75)
        assert fan.preset_modes == ["normal", "natural", "sleep", "auto", "turbo", "custom"]
        assert fan.preset_mode == "auto"
        assert fan.fan_speed == 6
        assert fan.is_on is False
        assert fan.oscillating is True

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "turbo"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 5})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 5}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 12
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 12})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 12}})

        with pytest.raises(ValueError):
            fan.preset_mode = "not_a_mode"

        with pytest.raises(ValueError):
            fan.fan_speed = 13

    def test_HPF017S(self):  # pylint: disable=invalid-name
        """Test HPF017S uses fanon for both commands and state (no poweron key)."""
        self.get_devices_file_name = "get_devices_HPF017S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]

        assert fan.model == "DR-HPF017S"
        assert fan.is_on is True
        assert fan.speed_range == (1, 12)
        assert fan._power_on_key == FANON_KEY  # pylint: disable=protected-access

        # Command must use fanon key (device does not respond to poweron)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {FANON_KEY: False})

        # Websocket updates also use fanon
        fan.handle_server_update({REPORTED_KEY: {FANON_KEY: False}})
        assert fan.is_on is False

        fan.handle_server_update({REPORTED_KEY: {FANON_KEY: True}})
        assert fan.is_on is True

        # Calling update_state again (as happens in set_device_setting) must
        # preserve fanon as the power key
        self.pydreo_manager.load_device_state(fan)
        assert fan._power_on_key == FANON_KEY  # pylint: disable=protected-access

    def test_HPF004S(self):  # pylint: disable=invalid-name
        """Test HPF004S TurboPoly 704S air circulator fan."""
        self.get_devices_file_name = "get_devices_HPF004S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]

        # Test initial state values
        assert fan.is_on is False
        assert fan.speed_range == (1, 9)
        assert fan.preset_modes == ["normal", "natural", "sleep", "auto", "turbo", "custom"]
        assert fan.preset_mode == "normal"  # Initial mode is 1
        assert fan.horizontal_angle_range == (-75, 75)
        assert fan.vertical_angle_range == (-30, 90)
        assert fan.temperature == 75
        assert fan.model == "DR-HPF004S"
        assert fan.device_name is not None
        assert fan.serial_number is not None
        assert fan.fan_speed >= 1 and fan.fan_speed <= 9

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        # Test fan speed commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 1
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 1})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 1}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 9
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 9})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 9}})

        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 10

        # Test preset mode commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "natural"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 2}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 3}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "auto"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 4}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "turbo"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 5})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 5}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "custom"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 6})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 6}})

        with pytest.raises(ValueError):
            fan.preset_mode = "invalid_mode"

        # Test oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = True
            mock_send_command.assert_called_once()
        fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = False
            mock_send_command.assert_called_once()
        fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: False}})

        assert fan.temperature is not None

    def test_HPF025S(self):  # pylint: disable=invalid-name
        """Test HPF025S tall air circulator fan."""
        self.get_devices_file_name = "get_devices_HPF025S.json"
        self.pydreo_manager.load_devices()

        assert len(self.pydreo_manager.devices) == 1

        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]

        # Test initial state values
        assert fan.is_on is True
        assert fan.speed_range == (1, 9)
        assert fan.preset_modes == ["normal", "auto", "sleep", "natural", "turbo"]
        assert fan.preset_mode == "normal"
        assert fan.horizontal_angle_range == (-60, 60)
        assert fan.vertical_angle_range == (-30, 90)
        assert fan.temperature == 74
        assert fan.model == "DR-HPF025S"
        assert fan.device_name is not None
        assert fan.serial_number is not None
        assert fan.fan_speed >= 1 and fan.fan_speed <= 9

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        # Test fan speed commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 1
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 1})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 1}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 5
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 5})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 5}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 9
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 9})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 9}})

        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 10

        # Test preset mode commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "auto"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 2}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 3}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "natural"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 4}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "turbo"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 5})
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 5}})

        with pytest.raises(ValueError):
            fan.preset_mode = "invalid_mode"

        # Test oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = True
            mock_send_command.assert_called_once()
        fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = False
            mock_send_command.assert_called_once()
        fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: False}})

        assert fan.temperature is not None
        assert isinstance(fan.temperature, (int, float))

        assert fan.temperature is not None
        assert isinstance(fan.temperature, (int, float))

    def test_HPF007S_presence_sensor(self):  # pylint: disable=invalid-name
        """Verify HPF007S exposes locatemeon and sends commands for presence tracking."""
        self.get_devices_file_name = "get_devices_HPF007S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1

        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]
        assert fan.locatemeon is False

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.locatemeon = True
            mock_send_command.assert_called_once_with(fan, {LOCATEMEON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {LOCATEMEON_KEY: True}})
        assert fan.locatemeon is True

    @pytest.mark.parametrize("devices_file", ["get_devices_HPF005S.json", "get_devices_HPF007S.json", "get_devices_HPF020S.json"])
    def test_additional_hpf_models(self, devices_file: str):  # pylint: disable=invalid-name
        """Load additional HPF models and test core command paths."""
        self.get_devices_file_name = devices_file
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = not bool(fan.is_on)
            mock_send_command.assert_called_once()

        low, high = fan.speed_range
        new_speed = low if fan.fan_speed != low else high
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = new_speed
            mock_send_command.assert_called_once()

        if fan.preset_modes:
            for mode in fan.preset_modes:
                if mode != fan.preset_mode:
                    with patch(PATCH_SEND_COMMAND) as mock_send_command:
                        fan.preset_mode = mode
                        mock_send_command.assert_called_once()
                    break

    def test_HPF007S_follow_me(self):  # pylint: disable=invalid-name
        """Verify HPF007S exposes presence-based follow mode (hwfpon) and telemetry."""
        self.get_devices_file_name = "get_devices_HPF007S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]

        assert fan.follow_me is False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.follow_me = True
            mock_send_command.assert_called_once_with(fan, {HWFPON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {HWFPON_KEY: True}})
        assert fan.follow_me is True

        fan.handle_server_update({REPORTED_KEY: {HWFPANGLE_KEY: 30, HBODYCNT_KEY: 2}})
        assert fan.follow_me_angle == 30
        assert fan.people_detected == 2

    def test_HPF015S_display_light(self):  # pylint: disable=invalid-name
        """Verify HPF015S exposes the panel display light (lighton)."""
        self.get_devices_file_name = "get_devices_HPF015S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan: PyDreoAirCirculator = self.pydreo_manager.devices[0]

        assert fan.display_light is False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.display_light = True
            mock_send_command.assert_called_once_with(fan, {LIGHTON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: True}})
        assert fan.display_light is True

    def test_HAF003S(self):  # pylint: disable=invalid-name
        """Load HAF003S (two fixtures) and test core command paths."""
        self.get_devices_file_name = "get_devices_HAF003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 2

        for fan in self.pydreo_manager.devices:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.is_on = not bool(fan.is_on)
                mock_send_command.assert_called_once()

            low, high = fan.speed_range
            new_speed = low if fan.fan_speed != low else high
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.fan_speed = new_speed
                mock_send_command.assert_called_once()

            if fan.preset_modes:
                for mode in fan.preset_modes:
                    if mode != fan.preset_mode:
                        with patch(PATCH_SEND_COMMAND) as mock_send_command:
                            fan.preset_mode = mode
                            mock_send_command.assert_called_once()
                        break

    def test_HAF004S_2REVS(self):  # pylint: disable=invalid-name
        """Load HAF004S_2REVS fixtures and test core command paths for both revisions."""
        self.get_devices_file_name = "get_devices_HAF004S_2REVS.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 2

        for fan in self.pydreo_manager.devices:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.is_on = not bool(fan.is_on)
                mock_send_command.assert_called_once()

            low, high = fan.speed_range
            new_speed = low if fan.fan_speed != low else high
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.fan_speed = new_speed
                mock_send_command.assert_called_once()

            if fan.preset_modes:
                for mode in fan.preset_modes:
                    if mode != fan.preset_mode:
                        with patch(PATCH_SEND_COMMAND) as mock_send_command:
                            fan.preset_mode = mode
                            mock_send_command.assert_called_once()
                        break

    # ---- Coverage tests below ----

    def test_static_rgb_helpers(self):  # pylint: disable=invalid-name
        """Test static RGB helper methods."""
        assert PyDreoAirCirculator._clamp_rgb_tuple((300, -10, 128.7)) == (255, 0, 129)
        assert PyDreoAirCirculator._pack_rgb_to_int((255, 0, 0)) == 16711680
        assert PyDreoAirCirculator._pack_rgb_to_int((0, 255, 0)) == 65280
        assert PyDreoAirCirculator._pack_rgb_to_int((0, 0, 255)) == 255
        assert PyDreoAirCirculator._unpack_int_to_rgb(16711680) == (255, 0, 0)
        assert PyDreoAirCirculator._unpack_int_to_rgb(65280) == (0, 255, 0)
        assert PyDreoAirCirculator._unpack_int_to_rgb(255) == (0, 0, 255)

    def test_parse_swing_angle_range_missing_controls_conf(self):  # pylint: disable=invalid-name
        """Test parse_swing_angle_range with no controlsConf."""
        result = PyDreoAirCirculator.parse_swing_angle_range({}, "hor")
        assert result is None

    def test_parse_swing_angle_range_no_swing_angle(self):  # pylint: disable=invalid-name
        """Test parse_swing_angle_range with no swingAngle."""
        result = PyDreoAirCirculator.parse_swing_angle_range({"controlsConf": {}}, "hor")
        assert result is None

    def test_parse_swing_angle_range_no_fixed_angle(self):  # pylint: disable=invalid-name
        """Test parse_swing_angle_range with no fixedAngle."""
        result = PyDreoAirCirculator.parse_swing_angle_range({"controlsConf": {"swingAngle": {}}}, "hor")
        assert result is None

    def test_parse_swing_angle_range_missing_angle_values(self):  # pylint: disable=invalid-name
        """Test parse_swing_angle_range with missing angle or zeroAngle."""
        result = PyDreoAirCirculator.parse_swing_angle_range({"controlsConf": {"swingAngle": {"fixedAngle": {"horAngle": 90}}}}, "hor")
        assert result is None

    def test_parse_swing_angle_range_valid(self):  # pylint: disable=invalid-name
        """Test parse_swing_angle_range with valid data."""
        result = PyDreoAirCirculator.parse_swing_angle_range(
            {"controlsConf": {"swingAngle": {"fixedAngle": {"horAngle": 150, "horZeroAngle": 75}}}}, "hor"
        )
        assert result == (-75, 75)

    def test_parse_preset_modes_empty(self):  # pylint: disable=invalid-name
        """Test parse_preset_modes returns None when no modes found."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        result = fan.parse_preset_modes({})
        assert result is None

    def test_oscillating_oscmode_skip(self):  # pylint: disable=invalid-name
        """Test oscillating setter skips when oscmode already matches."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        # Set oscmode to HORIZONTAL (1)
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 1}})
        # Setting oscillating=True should be no-op since already HORIZONTAL
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            mock_send_command.assert_not_called()

    def test_oscillating_no_support_raises(self):  # pylint: disable=invalid-name
        """Test oscillating setter raises when no oscillation support."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan._horizontally_oscillating = None
        fan._osc_mode = None
        with pytest.raises(NotImplementedError):
            fan.oscillating = True

    def test_horizontally_oscillating_oscmode_bitwise(self):  # pylint: disable=invalid-name
        """Test horizontally_oscillating with oscmode bitwise operations."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        # Set oscmode to OFF (0)
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 0}})
        # Enable horizontal -> should set bit 1
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = True
            mock_send_command.assert_called_once_with(fan, {OSCMODE_KEY: 1})
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 1}})
        # Skip when already set
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontally_oscillating = True
            mock_send_command.assert_not_called()

    def test_horizontally_oscillating_no_support_raises(self):  # pylint: disable=invalid-name
        """Test horizontally_oscillating raises when no support."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan._horizontally_oscillating = None
        fan._osc_mode = None
        with pytest.raises(NotImplementedError):
            fan.horizontally_oscillating = True

    def test_vertically_oscillating_hoscon_device(self):  # pylint: disable=invalid-name
        """Test vertically_oscillating on hoscon/voscon device."""
        self.get_devices_file_name = "get_devices_HAF001S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        # Skip when already same value
        fan._vertically_oscillating = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertically_oscillating = False
            mock_send_command.assert_not_called()
        # Set new value
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertically_oscillating = True
            mock_send_command.assert_called_once()

    def test_vertically_oscillating_oscmode_bitwise(self):  # pylint: disable=invalid-name
        """Test vertically_oscillating with oscmode bitwise operations."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 0}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertically_oscillating = True
            mock_send_command.assert_called_once_with(fan, {OSCMODE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 2}})
        # Skip when already set
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertically_oscillating = True
            mock_send_command.assert_not_called()

    def test_vertically_oscillating_no_support_raises(self):  # pylint: disable=invalid-name
        """Test vertically_oscillating raises when no support."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan._horizontally_oscillating = None
        fan._osc_mode = None
        with pytest.raises(NotImplementedError):
            fan.vertically_oscillating = True

    def test_set_horizontal_oscillation_angle(self):  # pylint: disable=invalid-name
        """Test set_horizontal_oscillation_angle."""
        self.get_devices_file_name = "get_devices_HAF001S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.set_horizontal_oscillation_angle(45)
            mock_send_command.assert_called_once()

    def test_set_horizontal_oscillation_angle_no_support(self):  # pylint: disable=invalid-name
        """Test set_horizontal_oscillation_angle raises when not supported."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        with pytest.raises(NotImplementedError):
            fan.set_horizontal_oscillation_angle(45)

    def test_set_vertical_oscillation_angle(self):  # pylint: disable=invalid-name
        """Test set_vertical_oscillation_angle."""
        self.get_devices_file_name = "get_devices_HAF001S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan._vertically_oscillating = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.set_vertical_oscillation_angle(30)
            mock_send_command.assert_called_once()

    def test_set_vertical_oscillation_angle_no_support(self):  # pylint: disable=invalid-name
        """Test set_vertical_oscillation_angle raises when not supported."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        with pytest.raises(NotImplementedError):
            fan.set_vertical_oscillation_angle(30)

    def test_cruise_conf_angles(self):  # pylint: disable=invalid-name
        """Test cruise conf angle getters and setters."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        # Set cruise conf: top,right,bottom,left
        fan.handle_server_update({REPORTED_KEY: {CRUISECONF_KEY: "90,60,-30,-60"}})
        assert fan.vertical_osc_angle_top == 90
        assert fan.vertical_osc_angle_bottom == -30
        assert fan.horizontal_osc_angle_right == 60
        assert fan.horizontal_osc_angle_left == -60

        # Test setters
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertical_osc_angle_top = 80
            mock_send_command.assert_called_once()
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertical_osc_angle_bottom = -40
            mock_send_command.assert_called_once()
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontal_osc_angle_right = 50
            mock_send_command.assert_called_once()
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontal_osc_angle_left = -50
            mock_send_command.assert_called_once()

    def test_cruise_conf_angle_skip_same_value(self):  # pylint: disable=invalid-name
        """Test cruise conf setters skip when value unchanged."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan.handle_server_update({REPORTED_KEY: {CRUISECONF_KEY: "90,60,-30,-60"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertical_osc_angle_top = 90
            mock_send_command.assert_not_called()
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertical_osc_angle_bottom = -30
            mock_send_command.assert_not_called()
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontal_osc_angle_right = 60
            mock_send_command.assert_not_called()
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontal_osc_angle_left = -60
            mock_send_command.assert_not_called()

    def test_cruise_conf_angle_validation(self):  # pylint: disable=invalid-name
        """Test cruise conf setters validate min angle difference."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan.handle_server_update({REPORTED_KEY: {CRUISECONF_KEY: "90,60,-30,-60"}})
        with pytest.raises(ValueError):
            fan.vertical_osc_angle_top = -25  # too close to bottom (-30)
        with pytest.raises(ValueError):
            fan.vertical_osc_angle_bottom = 85  # too close to top (90)
        with pytest.raises(ValueError):
            fan.horizontal_osc_angle_right = -55  # too close to left (-60)
        with pytest.raises(ValueError):
            fan.horizontal_osc_angle_left = 55  # too close to right (60)

    def test_fixed_conf_angles(self):  # pylint: disable=invalid-name
        """Test fixed conf angle getters and setters."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan.handle_server_update({REPORTED_KEY: {FIXEDCONF_KEY: "10,20"}})
        assert fan.vertical_angle == 10
        assert fan.horizontal_angle == 20
        # Set new values
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertical_angle = 30
            mock_send_command.assert_called_once()
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontal_angle = 40
            mock_send_command.assert_called_once()
        # Skip when same
        fan.handle_server_update({REPORTED_KEY: {FIXEDCONF_KEY: "30,40"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertical_angle = 30
            mock_send_command.assert_not_called()
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontal_angle = 40
            mock_send_command.assert_not_called()

    def test_HPF025S_fixed_conf_supports_negative_vertical_angles(self):  # pylint: disable=invalid-name
        """Test HPF025S fixedconf supports negative vertical angles."""
        self.get_devices_file_name = "get_devices_HPF025S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan.handle_server_update({REPORTED_KEY: {FIXEDCONF_KEY: "-30,20"}})
        assert fan.vertical_angle_range == (-30, 90)
        assert fan.vertical_angle == -30
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertical_angle = -25
            mock_send_command.assert_called_once_with(fan, {FIXEDCONF_KEY: "-25,20"})

    def test_horizontal_oscillation_angle_property(self):  # pylint: disable=invalid-name
        """Test horizontal_oscillation_angle property and setter."""
        self.get_devices_file_name = "get_devices_HAF001S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        # Set hoscangle via server update
        fan.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_ANGLE_KEY: 45}})
        assert fan.horizontal_oscillation_angle == 45
        # Skip same value
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontal_oscillation_angle = 45
            mock_send_command.assert_not_called()
        # Set new value
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontal_oscillation_angle = 60
            mock_send_command.assert_called_once()

    def test_vertical_oscillation_angle_property(self):  # pylint: disable=invalid-name
        """Test vertical_oscillation_angle property and setter."""
        self.get_devices_file_name = "get_devices_HAF001S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan.handle_server_update({REPORTED_KEY: {VERTICAL_OSCILLATION_ANGLE_KEY: 30}})
        assert fan.vertical_oscillation_angle == 30
        # Skip same value
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertical_oscillation_angle = 30
            mock_send_command.assert_not_called()
        # Set new
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.vertical_oscillation_angle = 60
            mock_send_command.assert_called_once()

    def test_hangleadj_horizontal_angle(self):  # pylint: disable=invalid-name
        """Test horizontal angle via hangleadj path."""
        self.get_devices_file_name = "get_devices_HPF025S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan._horizontal_angle_adj = 10
        assert fan.horizontal_angle == 10
        # horizontal_oscillation_angle returns None when hangleadj is used
        assert fan.horizontal_oscillation_angle is None
        assert fan.horizontal_oscillation_angle_range is None
        # Setter uses hangleadj
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontal_angle = 20
            mock_send_command.assert_called_once()
        # Skip same
        fan._horizontal_angle_adj = 20
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.horizontal_angle = 20
            mock_send_command.assert_not_called()
        # horizontal_oscillation_angle setter raises
        with pytest.raises(NotImplementedError):
            fan.horizontal_oscillation_angle = 45

    def test_vertical_osc_angle_disabled(self):  # pylint: disable=invalid-name
        """Test vertical oscillation angle disabled when hangleadj present and voscangle=0."""
        self.get_devices_file_name = "get_devices_HPF025S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan._horizontal_angle_adj = 10
        fan._vertical_oscillation_angle = 0
        assert fan.vertical_oscillation_angle is None
        assert fan.vertical_oscillation_angle_range is None
        with pytest.raises(NotImplementedError):
            fan.vertical_oscillation_angle = 30

    def test_atm_light_unsupported(self):  # pylint: disable=invalid-name
        """Test ATM light setters on device without ATM support."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        assert fan.is_feature_supported("atm_light") is False
        # Setters should be no-ops
        fan.atm_light_on = True  # no crash
        fan.atm_brightness = 3  # no crash
        fan.atm_color_rgb = (255, 0, 0)  # no crash

    def test_atm_light_skip_same_value(self):  # pylint: disable=invalid-name
        """Test ATM light setters skip when value unchanged."""
        self.get_devices_file_name = "get_devices_HPF008S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan.handle_server_update({REPORTED_KEY: {ATMON_KEY: True}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_light_on = True
            mock_send_command.assert_not_called()
        fan.handle_server_update({REPORTED_KEY: {ATMBRI_KEY: 3}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_brightness = 3
            mock_send_command.assert_not_called()
        fan.handle_server_update({REPORTED_KEY: {ATMCOLOR_KEY: 16711680}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_color_rgb = (255, 0, 0)
            mock_send_command.assert_not_called()

    def test_atm_brightness_clamping(self):  # pylint: disable=invalid-name
        """Test ATM brightness is clamped to model range."""
        self.get_devices_file_name = "get_devices_HPF008S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan.handle_server_update({REPORTED_KEY: {ATMBRI_KEY: 1}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_brightness = 10  # should clamp to model max
            mock_send_command.assert_called_once_with(fan, {ATMBRI_KEY: 3})

    def test_handle_server_update_all_keys(self):  # pylint: disable=invalid-name
        """Test handle_server_update covers all air circulator keys."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        # Update all keys in one message
        fan.handle_server_update(
            {
                REPORTED_KEY: {
                    OSCMODE_KEY: 3,
                    CRUISECONF_KEY: "80,50,-20,-50",
                    FIXEDCONF_KEY: "15,25",
                    HORIZONTAL_OSCILLATION_ANGLE_KEY: 45,
                    VERTICAL_OSCILLATION_ANGLE_KEY: 30,
                    HORIZONTAL_ANGLE_ADJ_KEY: 10,
                    ATMON_KEY: True,
                    ATMBRI_KEY: 4,
                    ATMCOLOR_KEY: 65280,
                    ATMMODE_KEY: 2,
                }
            }
        )
        assert fan._osc_mode == 3
        assert fan._cruise_conf == "80,50,-20,-50"
        assert fan._fixed_conf == "15,25"
        assert fan._horizontal_oscillation_angle == 45
        assert fan._vertical_oscillation_angle == 30
        assert fan._horizontal_angle_adj == 10
        assert fan._atm_light_on is True
        assert fan._atm_brightness == 4
        assert fan._atm_color == 65280
        assert fan._atm_mode == 2

    def test_is_feature_supported_atm(self):  # pylint: disable=invalid-name
        """Test is_feature_supported for atm_light."""
        self.get_devices_file_name = "get_devices_HPF008S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        assert fan.is_feature_supported("atm_light") is True
        assert fan.is_feature_supported("unknown_feature") is False

    def test_oscillating_property_hoscon_both(self):  # pylint: disable=invalid-name
        """Test oscillating property with hoscon device - both directions."""
        self.get_devices_file_name = "get_devices_HAF001S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan._horizontally_oscillating = False
        fan._vertically_oscillating = True
        assert fan.oscillating is True
        fan._vertically_oscillating = False
        assert fan.oscillating is False

    def test_angle_range_properties(self):  # pylint: disable=invalid-name
        """Test angle range convenience properties."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        assert fan.horizontal_osc_angle_left_range == fan.horizontal_angle_range
        assert fan.horizontal_osc_angle_right_range == fan.horizontal_angle_range
        assert fan.vertical_osc_angle_top_range == fan.vertical_angle_range
        assert fan.vertical_osc_angle_bottom_range == fan.vertical_angle_range

    def test_cruise_conf_none_returns_none(self):  # pylint: disable=invalid-name
        """Test cruise conf getters return None when no cruise conf."""
        self.get_devices_file_name = "get_devices_HAF001S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan._cruise_conf = None
        assert fan.vertical_osc_angle_top is None
        assert fan.vertical_osc_angle_bottom is None
        assert fan.horizontal_osc_angle_right is None
        assert fan.horizontal_osc_angle_left is None

    def test_fixed_conf_none_returns_none(self):  # pylint: disable=invalid-name
        """Test fixed conf getters return None when no fixed conf."""
        self.get_devices_file_name = "get_devices_HAF001S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan._fixed_conf = None
        fan._horizontal_angle_adj = None
        assert fan.vertical_angle is None
        assert fan.horizontal_angle is None

    def test_vertically_oscillating_property_oscmode(self):  # pylint: disable=invalid-name
        """Test vertically_oscillating property via oscmode."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 2}})
        assert fan.vertically_oscillating is True
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 1}})
        assert fan.vertically_oscillating is False
        fan.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 3}})
        assert fan.vertically_oscillating is True

    def test_vertically_oscillating_property_none(self):  # pylint: disable=invalid-name
        """Test vertically_oscillating returns None when no support."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan._vertically_oscillating = None
        fan._osc_mode = None
        assert fan.vertically_oscillating is None

    def test_horizontally_oscillating_property_none(self):  # pylint: disable=invalid-name
        """Test horizontally_oscillating returns None when no support."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan._horizontally_oscillating = None
        fan._osc_mode = None
        assert fan.horizontally_oscillating is None

    def test_oscillating_property_none(self):  # pylint: disable=invalid-name
        """Test oscillating returns None when no support."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan._horizontally_oscillating = None
        fan._osc_mode = None
        assert fan.oscillating is None

    def test_update_state_hoscangle_string_ignored(self):  # pylint: disable=invalid-name
        """Test that non-integer hoscangle values are ignored in update_state."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        fan._horizontal_oscillation_angle = None
        # Simulate a string value for hoscangle (some devices report "0,0")
        fan.update_state({HORIZONTAL_OSCILLATION_ANGLE_KEY: {"state": "0,0", "timestamp": 123}})
        assert fan._horizontal_oscillation_angle is None

    @pytest.mark.parametrize("devices_file", AIRCIRCULATOR_EXHAUSTIVE_MODELS)
    def test_all_settable_properties_for_each_model(self, devices_file: str):
        """Exercise all writable properties for each air circulator model fixture in this file."""
        self.get_devices_file_name = devices_file
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) >= 1
        for device in self.pydreo_manager.devices:
            fan: PyDreoAirCirculator = device
            self._exercise_all_settable_properties(fan)
