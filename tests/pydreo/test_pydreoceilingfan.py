"""Tests for Dreo Ceiling Fans"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

CEILING_FAN_EXHAUSTIVE_MODELS = [
    "get_devices_HCF001S.json",
    "get_devices_HCF002S.json",
    "get_devices_HCF002S_CFRGB.json",
    "get_devices_HCF003S.json",
    "get_devices_HCF521S.json",
]


class TestPyDreoCeilingFan(TestBase):
    """Test PyDreoFan class."""

    def _exercise_all_settable_properties(self, fan: PyDreoCeilingFan):
        """Exercise all writable ceiling-fan properties that are supported by a model."""
        _ = fan.speed_range
        _ = fan.preset_modes
        _ = fan.is_on
        _ = fan.fan_speed
        _ = fan.preset_mode
        _ = fan.temperature
        _ = fan.temperature_units
        _ = fan.temperature_offset
        _ = fan.light_on
        _ = fan.brightness
        _ = fan.color_temperature
        _ = fan.atm_light_on
        _ = fan.atm_brightness
        _ = fan.atm_color_rgb
        _ = fan.atm_mode
        _ = fan.display_auto_off
        _ = fan.adaptive_brightness
        _ = fan.panel_sound
        _ = fan.pm25
        _ = fan.oscillating

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

        if fan.light_on is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.light_on = not fan.light_on
                mock_send_command.assert_called_once()

        if fan.brightness is not None:
            new_brightness = 1 if fan.brightness != 1 else 2
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.brightness = new_brightness
                mock_send_command.assert_called_once()

        if fan.color_temperature is not None:
            new_color_temperature = 1 if fan.color_temperature != 1 else 2
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.color_temperature = new_color_temperature
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

        with pytest.raises(NotImplementedError):
            fan.oscillating = True

    def test_HCF001S(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HCF001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]
        assert fan.speed_range == (1, 12)
        assert fan.preset_modes == ["normal", "natural", "sleep", "reverse"]
        assert fan.is_feature_supported("poweron") is False
        assert fan.is_feature_supported("light_on") is True
        assert fan.is_feature_supported("brightness") is True
        assert fan.is_feature_supported("color_temperature") is True
        assert fan.brightness == 64
        assert fan.color_temperature == 25

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {FANON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {FANON_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.light_on = True
            mock_send_command.assert_called_once_with(fan, {LIGHTON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.light_on = False
            mock_send_command.assert_called_once_with(fan, {LIGHTON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.brightness = 50
            mock_send_command.assert_called_once_with(fan, {BRIGHTNESS_KEY: 50})
        fan.handle_server_update({REPORTED_KEY: {BRIGHTNESS_KEY: 50}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.color_temperature = 50
            mock_send_command.assert_called_once_with(fan, {COLORTEMP_KEY: 50})
        fan.handle_server_update({REPORTED_KEY: {COLORTEMP_KEY: 50}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "natural"
            mock_send_command.assert_called_once_with(fan, {MODE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {MODE_KEY: 2}})

        with pytest.raises(ValueError):
            fan.preset_mode = "not_a_mode"

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 3
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 3}})

        with pytest.raises(ValueError):
            fan.fan_speed = 13

    def test_HCF002S(self):  # pylint: disable=invalid-name
        """Test DR-HCF002S ceiling fan with RGB atmosphere lights."""
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]

        # Test basic fan properties
        assert fan.model == "DR-HCF002S"
        assert fan.speed_range == (1, 12)
        assert fan.preset_modes == ["normal", "natural", "sleep", "auto"]

        # Test main light support
        assert fan.is_feature_supported("light_on") is True
        assert fan.is_feature_supported("brightness") is True
        assert fan.is_feature_supported("color_temperature") is True
        assert fan.brightness == 24
        assert fan.color_temperature == 60

        # Test atmosphere light support
        assert fan.is_feature_supported("atm_light") is True
        assert fan.atm_light_on is False
        assert fan.atm_brightness == 3
        assert fan.atm_color_rgb == (0, 255, 0)  # 65280 = 0x00FF00 = green
        assert fan.atm_mode == 1

        # Test atmosphere light commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_light_on = True
            mock_send_command.assert_called_once_with(fan, {ATMON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {ATMON_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_brightness = 5
            mock_send_command.assert_called_once_with(fan, {ATMBRI_KEY: 5})
        fan.handle_server_update({REPORTED_KEY: {ATMBRI_KEY: 5}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_color_rgb = (255, 0, 0)  # Red
            mock_send_command.assert_called_once_with(fan, {ATMCOLOR_KEY: 16711680})  # 0xFF0000
        fan.handle_server_update({REPORTED_KEY: {ATMCOLOR_KEY: 16711680}})

    def test_HCF002S_CFRGB(self):  # pylint: disable=invalid-name
        """Test DR-HCF002S RGBIC variant that has atmon/atmbri but no atmcolor in state.

        Regression test for https://github.com/JeffSteinbok/hass-dreo/issues/XXX:
        RGB color commands must be accepted even when the device never reported
        'atmcolor' in its state heartbeat (i.e. _atm_color is None on load).
        """
        self.get_devices_file_name = "get_devices_HCF002S_CFRGB.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]

        # Basic fan properties
        assert fan.model == "DR-HCF002S"
        assert fan.speed_range == (1, 12)
        assert fan.preset_modes == ["normal", "natural", "sleep", "auto"]

        # Main light and colour temperature are supported
        assert fan.is_feature_supported("light_on") is True
        assert fan.is_feature_supported("brightness") is True
        assert fan.is_feature_supported("color_temperature") is True
        assert fan.brightness == 10
        assert fan.color_temperature == 100

        # Atmosphere light is tracked (atmon present in state)
        assert fan.is_feature_supported("atm_light") is True
        assert fan.atm_light_on is True
        assert fan.atm_brightness == 1

        # atmcolor was NOT in the device state, so the current value is unknown
        assert fan.atm_color_rgb is None

        # atm_color_rgb must still be recognised as a settable feature because the
        # atmosphere light itself is present on the device.
        assert fan.is_feature_supported("atm_color_rgb") is True

        # Setting RGB colour must send the atmcolor command even though _atm_color is None
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_color_rgb = (255, 0, 0)  # Red
            mock_send_command.assert_called_once_with(fan, {ATMCOLOR_KEY: 16711680})  # 0xFF0000
        fan.handle_server_update({REPORTED_KEY: {ATMCOLOR_KEY: 16711680}})

        # After the server echoes the colour back, subsequent identical set should be skipped
        assert fan.atm_color_rgb == (255, 0, 0)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_color_rgb = (255, 0, 0)  # same colour – should NOT re-send
            mock_send_command.assert_not_called()

        # Setting a different colour after state is known must send the command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_color_rgb = (0, 255, 0)  # Green
            mock_send_command.assert_called_once_with(fan, {ATMCOLOR_KEY: 65280})  # 0x00FF00
        fan.handle_server_update({REPORTED_KEY: {ATMCOLOR_KEY: 65280}})

        # Colour temperature control must also work
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.color_temperature = 50
            mock_send_command.assert_called_once_with(fan, {COLORTEMP_KEY: 50})
        fan.handle_server_update({REPORTED_KEY: {COLORTEMP_KEY: 50}})

    def test_HCF003S(self):  # pylint: disable=invalid-name
        """Load HCF003S and test core fan/light command paths."""
        self.get_devices_file_name = "get_devices_HCF003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]

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

        if fan.light_on is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.light_on = not fan.light_on
                mock_send_command.assert_called_once()

    def test_HCF521S(self):  # pylint: disable=invalid-name
        """Load HCF521S and test fan commands."""
        self.get_devices_file_name = "get_devices_HCF521S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]
        assert fan.model == "DR-HCF521S"
        assert fan.speed_range == (1, 12)
        assert fan.preset_modes == ["normal", "natural", "sleep", "reverse"]
        assert fan.is_feature_supported("light_on") is True
        assert fan.is_feature_supported("brightness") is True
        assert fan.is_feature_supported("color_temperature") is True
        assert fan.brightness == 75
        assert fan.color_temperature == 50

        # Turn on when off - should send command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {FANON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {FANON_KEY: True}})

        # Turn on again when already on - should NOT send redundant command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_not_called()

        # Turn off when on - should send command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {FANON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {FANON_KEY: False}})

        # Turn off again when already off - should NOT send redundant command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_not_called()

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 8
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 8})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 8}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "natural"
            mock_send_command.assert_called_once_with(fan, {MODE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {MODE_KEY: 2}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "reverse"
            mock_send_command.assert_called_once_with(fan, {MODE_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {MODE_KEY: 4}})

        with pytest.raises(ValueError):
            fan.fan_speed = 13

    @pytest.mark.parametrize("devices_file", CEILING_FAN_EXHAUSTIVE_MODELS)
    def test_all_settable_properties_for_each_model(self, devices_file: str):
        """Exercise all writable properties for each ceiling fan model fixture in this file."""
        self.get_devices_file_name = devices_file
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) >= 1
        for device in self.pydreo_manager.devices:
            fan: PyDreoCeilingFan = device
            self._exercise_all_settable_properties(fan)
