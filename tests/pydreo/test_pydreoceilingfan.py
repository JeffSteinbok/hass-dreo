"""Tests for Dreo Ceiling Fans"""

# pylint: disable=used-before-assignment
import logging
import threading
import time
from unittest.mock import patch
import pytest
from custom_components.dreo.pydreo.commandoutbox import OutboxTiming
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

CEILING_FAN_EXHAUSTIVE_MODELS = [
    "get_devices_HCF001S.json",
    "get_devices_HCF002S.json",
    "get_devices_HCF002S_CFRGB.json",
    "get_devices_HCF003S.json",
    "get_devices_HCF007S.json",
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

        # Test atmosphere light commands. The fixture is gated off (poweron False),
        # so switching a load on must be one atomic command that opens the gate and
        # explicitly forces the other loads off - `poweron: True` alone would
        # re-energise every retained-on load (hardware-validated).
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_light_on = True
            mock_send_command.assert_called_once_with(fan, {ATMON_KEY: True, POWERON_KEY: True, FANON_KEY: False, LIGHTON_KEY: False})
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
        """Test DR-HCF002S RGBIC variant that uses preset-based RGB instead of direct color.

        RGBIC ceiling fans have rgbpresetsel/rgbpresetnum instead of atmcolor.
        They should expose rgb_preset feature, NOT atm_color_rgb.
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

        # Atmosphere light is tracked (atmon present in state). The fixture is
        # gated off (poweron False) with atmon retained True: the hardware keeps
        # load states across a power-off, so the gated result must read OFF.
        assert fan.is_feature_supported("atm_light") is True
        assert fan.atm_light_on is False
        # Gate-open re-energises the retained atm light without any atmon key
        # in the message (observed device behavior).
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert fan.atm_light_on is True
        assert fan.atm_brightness == 1

        # This is an RGBIC preset device - atm_color_rgb is NOT supported
        assert fan.atm_color_rgb is None
        assert fan.is_feature_supported("atm_color_rgb") is False

        # RGBIC preset feature IS supported
        assert fan.is_feature_supported("rgb_preset") is True
        assert fan.rgb_preset_sel == 0
        assert fan.rgb_preset_num == 4

        # Setting preset must send the rgbpresetsel command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.rgb_preset_sel = 2
            mock_send_command.assert_called_once_with(fan, {RGBPRESETSEL_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {RGBPRESETSEL_KEY: 2}})

        # After update, preset should be tracked
        assert fan.rgb_preset_sel == 2

        # Setting same preset should skip command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.rgb_preset_sel = 2
            mock_send_command.assert_not_called()

        # Setting different preset must send command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.rgb_preset_sel = 0
            mock_send_command.assert_called_once_with(fan, {RGBPRESETSEL_KEY: 0})
        fan.handle_server_update({REPORTED_KEY: {RGBPRESETSEL_KEY: 0}})

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

        # Turn on when off - should send command (no gate keys: HCF521S has no poweron)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {FANON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {FANON_KEY: True}})

        # Redundant same-value sends are deliberately NOT skipped any more: a skip
        # decided on a stale cache made entities permanently unreachable (some units
        # stop reporting individual load keys while control keeps working), and
        # redundant commands are hardware-validated no-ops on the device side.
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {FANON_KEY: True})

        # Turn off when on - should send command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {FANON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {FANON_KEY: False}})

        # Same: off-when-off still sends (harmless no-op beats a stale-cache skip)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {FANON_KEY: False})

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

    def test_HCF007S(self):  # pylint: disable=invalid-name
        """Load HCF007S (CF521S RGBIC) and verify RGBIC preset capabilities.

        HCF007S uses rgbpresetsel/rgbpresetnum for RGB LED control.  The
        rgbeffectid field is read-only metadata and does NOT respond to write
        commands; direct ATMCOLOR_KEY colour control is also not supported.
        """
        self.get_devices_file_name = "get_devices_HCF007S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]
        assert fan.model == "DR-HCF007S"
        assert fan.speed_range == (1, 12)
        assert fan.preset_modes == ["normal", "natural", "sleep", "reverse"]

        # HCF007S uses the RGBIC preset system for pattern selection; direct colour
        # writes via ATMCOLOR_KEY are also supported (write-only, no state echo).
        assert fan.is_feature_supported("atm_light") is True
        assert fan.is_feature_supported("atm_color_rgb") is False  # no atmcolor in state
        assert fan.is_feature_supported("atm_color_rgb_write") is True  # write-only colour control
        # rgb_effect_id is NOT enabled (rgb_effect_range removed from model)
        assert fan.is_feature_supported("rgb_effect_id") is False
        assert fan.is_feature_supported("rgb_preset") is True
        assert fan.rgb_preset_sel == 0
        assert fan.rgb_preset_num == 4

        # HCF007S uses a 1-100 brightness range (not the default 1-5)
        assert fan.atm_brightness_range == (1, 100)
        assert fan.atm_brightness == 1

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 12
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 12})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 12}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "reverse"
            mock_send_command.assert_called_once_with(fan, {MODE_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {MODE_KEY: 4}})

        # RGBIC preset control
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.rgb_preset_sel = 3
            mock_send_command.assert_called_once_with(fan, {RGBPRESETSEL_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {RGBPRESETSEL_KEY: 3}})
        assert fan.rgb_preset_sel == 3

        # HCF007S uses 1-100 brightness range; values up to 100 should be sent as-is
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_brightness = 50
            mock_send_command.assert_called_once_with(fan, {ATMBRI_KEY: 50})
        fan.handle_server_update({REPORTED_KEY: {ATMBRI_KEY: 50}})
        assert fan.atm_brightness == 50

        # Values above 100 are clamped to 100 for HCF007S
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.atm_brightness = 120
            mock_send_command.assert_called_once_with(fan, {ATMBRI_KEY: 100})
        fan.handle_server_update({REPORTED_KEY: {ATMBRI_KEY: 100}})
        assert fan.atm_brightness == 100

    @pytest.mark.parametrize("devices_file", CEILING_FAN_EXHAUSTIVE_MODELS)
    def test_all_settable_properties_for_each_model(self, devices_file: str):
        """Exercise all writable properties for each ceiling fan model fixture in this file."""
        self.get_devices_file_name = devices_file
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) >= 1
        for device in self.pydreo_manager.devices:
            fan: PyDreoCeilingFan = device
            self._exercise_all_settable_properties(fan)

    def test_poweron_false_overrides_fanon_true_via_state(self):  # pylint: disable=invalid-name
        """Regression test for issue #727: poweron=false must win over fanon=true in REST state.

        The DR-HCF002S (and similar ceiling fans) retains the last fanon value when the
        device is turned off via the physical remote. The REST state poll therefore reports
        poweron=false AND fanon=true simultaneously. Before the fix, _is_on was set to True
        (wrong). After the fix it must be False.
        """
        self.get_devices_file_name = "get_devices_HCF002S_poweron_off.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]

        # poweron=false in state despite fanon=true; device must report as off
        assert fan.is_on is False

    def test_poweron_false_overrides_fanon_true_via_ws(self):  # pylint: disable=invalid-name
        """Regression test for issue #727 under the gate model.

        The device retains load states across a gate close and re-energises them on
        gate open (hardware-validated on DR-HCF002S), so `poweron` acts as a gate
        over the retained `fanon` value in any message order or combination.
        """
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]

        # Hardware bundles the gate key with the load delta on gate-open.
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True, FANON_KEY: True}})
        assert fan.is_on is True

        # Remote turns off the whole device: only poweron is reported, fanon is retained.
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
        assert fan.is_on is False

        # Gate-open alone re-energises the retained fan (observed: bare poweron True).
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert fan.is_on is True

        # poweron=false wins even when fanon=true rides in the same message (#727).
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False, FANON_KEY: True}})
        assert fan.is_on is False

    def test_gate_model_light_state(self):
        """The main light state must be `poweron AND lighton`.

        Fixes the observed field bug where HA showed the light ON while the whole
        device was powered off (`is_on=False light_on=True` from raw lighton).
        """
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]

        # Fixture is gated off. A lighton delta while gated registers as retained
        # state but must not show the light as on.
        assert fan.light_on is False
        fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: True}})
        assert fan.light_on is False

        # Gate-open with no lighton key at all: the retained light comes back on.
        # (This is exactly what the app's light button produces on this hardware.)
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert fan.light_on is True

        # Whole-device off: light shows off, retained value survives underneath.
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
        assert fan.light_on is False

    def test_wake_command_is_atomic(self):
        """Turning one load on from gated-off must wake the gate and force the
        other loads off in a single command - poweron alone re-energises every
        retained-on load (a light press would start the fan)."""
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]

        # Retained fanon True + gate closed: the hazardous case from the field.
        fan.handle_server_update({REPORTED_KEY: {FANON_KEY: True}})
        assert fan.is_on is False

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.light_on = True
            mock_send_command.assert_called_once_with(fan, {LIGHTON_KEY: True, POWERON_KEY: True, FANON_KEY: False, ATMON_KEY: False})

        # Optimistic application: some units never report load keys, so our own
        # write is the state source - no echo required.
        assert fan.light_on is True
        assert fan.is_on is False

    def test_last_load_off_closes_gate(self):
        """The device never closes the gate itself: switching off the last active
        load must send poweron False in the same command."""
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]

        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True, LIGHTON_KEY: True}})
        assert fan.light_on is True and fan.is_on is False

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.light_on = False
            mock_send_command.assert_called_once_with(fan, {LIGHTON_KEY: False, POWERON_KEY: False})
        assert fan.light_on is False

    def test_mid_sequence_off_keeps_gate(self):
        """Switching off a load while another load is running must not touch the gate."""
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]

        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True, FANON_KEY: True, LIGHTON_KEY: True}})
        assert fan.is_on is True and fan.light_on is True

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.light_on = False
            mock_send_command.assert_called_once_with(fan, {LIGHTON_KEY: False})
        assert fan.is_on is True

    def test_turn_light_on_wakes_gated_device(self):
        """turn_light_on (the combined Adaptive-Lighting path) must include the
        wake keys when the device is gated off."""
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.turn_light_on(brightness=50, color_temp=80)
            mock_send_command.assert_called_once_with(
                fan,
                {BRIGHTNESS_KEY: 50, COLORTEMP_KEY: 80, LIGHTON_KEY: True, POWERON_KEY: True, FANON_KEY: False, ATMON_KEY: False},
            )
        assert fan.light_on is True

    def _get_batching_fan(self) -> PyDreoCeilingFan:
        """Load the HCF002S fixture and switch its outbox to async collect mode."""
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]
        fan._outbox.timing = OutboxTiming(quiet_period=0.03, max_wait=0.12, min_interval=0.0)  # pylint: disable=protected-access
        return fan

    def test_wake_preserves_co_arriving_load(self):
        """The order-dependence trap: a wake derived from the merged batch must not
        clobber a load that arrived in the same window.

        light-on while gated off wakes the device and forces other loads off - but
        atmon arrived in the same burst, so it is the caller's intent and must
        survive as True in the single combined command."""
        fan = self._get_batching_fan()
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True, LIGHTON_KEY: False, ATMON_KEY: False, FANON_KEY: False}})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        sends = []
        with patch(PATCH_SEND_COMMAND, side_effect=lambda _d, p: sends.append(p)):
            fan.light_on = True
            fan.atm_light_on = True
            assert self.wait_for(lambda: len(sends) >= 1), "batch never flushed"
            time.sleep(0.15)  # several quiet periods: a second send would have fired by now

        assert sends == [{LIGHTON_KEY: True, ATMON_KEY: True, POWERON_KEY: True, FANON_KEY: False}]

    def test_all_loads_off_closes_gate_once(self):
        """Both loads switched off in one window -> one command that also closes the
        gate (the wall-switch field failure, now atomic)."""
        fan = self._get_batching_fan()
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True, LIGHTON_KEY: True, ATMON_KEY: True, FANON_KEY: False}})

        sends = []
        with patch(PATCH_SEND_COMMAND, side_effect=lambda _d, p: sends.append(p)):
            fan.light_on = False
            fan.atm_light_on = False
            assert self.wait_for(lambda: len(sends) >= 1), "batch never flushed"
            time.sleep(0.15)

        assert sends == [{LIGHTON_KEY: False, ATMON_KEY: False, POWERON_KEY: False}]

    def test_params_only_batch_never_wakes_device(self):
        """A parameter-only batch (e.g. Adaptive Lighting adjusting brightness while
        the light is off at 2am) must pass through with no gate keys added."""
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True, BRIGHTNESS_KEY: 100, LIGHTON_KEY: False, ATMON_KEY: False, FANON_KEY: False}})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.brightness = 42
            mock_send_command.assert_called_once_with(fan, {BRIGHTNESS_KEY: 42})

    def test_explicit_poweron_passes_through(self):
        """A batch that already contains poweron is the caller's explicit intent;
        finalize must not add forced-off keys on top of it."""
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True, LIGHTON_KEY: False, ATMON_KEY: False, FANON_KEY: False}})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan._send_command_batch({LIGHTON_KEY: True, POWERON_KEY: True})  # pylint: disable=protected-access
            mock_send_command.assert_called_once_with(fan, {LIGHTON_KEY: True, POWERON_KEY: True})

    def test_concurrent_setters_serialize_last_load_decision(self):
        """Field regression: two off-commands 4 ms apart (linked wall switches).

        Thread B's RGB-off lands in the outbox while thread A's light-off send
        is still in flight; the drain step then flushes it against A's already
        applied optimistic state, judges it the last active load, and closes
        the gate. Without this, B decided against A's stale state and left the
        gate open. Also pins the drain guarantee: a key enqueued during an
        in-flight send goes out afterwards with no further enqueue needed.
        """
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]

        # Light + RGB on, fan off, gate open (the state before the user's flip).
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True, LIGHTON_KEY: True, ATMON_KEY: True}})

        sent = []
        send_started = threading.Event()

        def slow_send(_device, params):
            sent.append(params)
            send_started.set()
            time.sleep(0.15)  # hold thread A inside send_command, as the real ack wait does

        with patch(PATCH_SEND_COMMAND, side_effect=slow_send):
            thread_a = threading.Thread(target=lambda: setattr(fan, "light_on", False))
            thread_a.start()
            send_started.wait(timeout=2)
            thread_b = threading.Thread(target=lambda: setattr(fan, "atm_light_on", False))
            thread_b.start()
            thread_a.join(timeout=5)
            thread_b.join(timeout=5)

        assert sent[0] == {LIGHTON_KEY: False}
        # B waited for A's lock, saw the light already off, and closed the gate.
        assert sent[1] == {ATMON_KEY: False, POWERON_KEY: False}

    def test_min_command_interval_paces_consecutive_batches(self):
        """Field regression: the device silently drops a command arriving <~250 ms
        after the previous one. When two writes are too far apart to merge into
        one batch, the flush timer must re-arm until the pacing floor is
        satisfied instead of sending immediately."""
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]
        # Fan running so neither command touches the gate; keeps sends single-key.
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True, FANON_KEY: True, LIGHTON_KEY: False, ATMON_KEY: False}})
        fan._outbox.timing = OutboxTiming(quiet_period=0.02, max_wait=0.05, min_interval=0.2)  # pylint: disable=protected-access

        send_times = []
        sends = []

        def record(_device, params):
            send_times.append(time.monotonic())
            sends.append(params)

        with patch(PATCH_SEND_COMMAND, side_effect=record):
            fan.light_on = True
            assert self.wait_for(lambda: len(send_times) == 1), "first batch never flushed"
            fan.atm_light_on = True
            assert self.wait_for(lambda: len(send_times) == 2), "second batch never flushed"

        assert sends == [{LIGHTON_KEY: True}, {ATMON_KEY: True}]
        gap = send_times[1] - send_times[0]
        assert gap >= 0.18, f"sends not paced: gap={gap:.3f}s"
