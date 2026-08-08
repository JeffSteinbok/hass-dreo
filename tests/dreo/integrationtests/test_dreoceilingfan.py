"""Integration Tests for Dreo Ceiling Fans"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import binary_sensor
from custom_components.dreo import fan
from custom_components.dreo import switch
from custom_components.dreo import number
from custom_components.dreo import light
from custom_components.dreo.haimports import ColorMode, ATTR_RGB_COLOR, EntityCategory
from .imports import *  # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase, PATCH_SEND_COMMAND

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_SCHEDULE_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestDreoCeilingFan(IntegrationTestBase):
    """Test Dreo Ceiling Fan class and PyDreo together."""

    def test_HCF001S(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HCF001S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_fan = self.pydreo_manager.devices[0]
            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert ha_fan.is_on is False
            assert ha_fan.speed_count == 12
            assert ha_fan.unique_id is not None
            assert pydreo_fan.model == "DR-HCF001S"
            assert pydreo_fan.speed_range == (1, 12)

            # Test power commands
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: True})
            pydreo_fan.handle_server_update({REPORTED_KEY: {FANON_KEY: True}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: False})
            pydreo_fan.handle_server_update({REPORTED_KEY: {FANON_KEY: False}})

            # Turn fan back on for speed tests
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: True})
            pydreo_fan.handle_server_update({REPORTED_KEY: {FANON_KEY: True}})

            # Test speed settings
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(25)  # Speed ~3
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 3})
            pydreo_fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 3}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(50)  # Speed ~6
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 6})
            pydreo_fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 6}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)  # Speed 12 (max)
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 12})
            pydreo_fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 12}})

            # Check to see what switches are added to ceiling fans
            switches = switch.get_entries([pydreo_fan])
            self.verify_expected_entities(switches, ["Panel Sound"])

            # Check to see what numbers are added to ceiling fans
            numbers = number.get_entries([pydreo_fan])
            self.verify_expected_entities(numbers, [])

            lights = light.get_entries([pydreo_fan])
            self.verify_expected_entities(lights, ["Light"])
            light_switch = self.get_entity_by_key(lights, "Light")

            # Test light control
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                light_switch.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: True})
            pydreo_fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: True}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                light_switch.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: False})
            pydreo_fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: False}})

            # Test brightness if supported
            if hasattr(light_switch, "brightness") and light_switch.brightness is not None:
                # Turn light on first - light_switch.turn_on(brightness=X) turns light on if off
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    light_switch.turn_on()
                    mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: True})
                pydreo_fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: True}})

                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    # Brightness is converted from HA's 0-255 scale to device's 1-100 scale
                    # 128/255 * 100 = ~50.2, which gets rounded to 50. lighton rides along:
                    # skipping it on a cached "already on" strands the light on a stale cache.
                    light_switch.turn_on(brightness=128)
                    mock_send_command.assert_called_once_with(pydreo_fan, {BRIGHTNESS_KEY: 50, LIGHTON_KEY: True})

    def test_HCF001S_light_atomic_turn_on(self):  # pylint: disable=invalid-name
        """Issue #846: turning the light on together with a brightness change (as Adaptive
        Lighting does) must be delivered as a single combined command containing both the
        brightness and lighton=True, not as two separate sequential commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HCF001S.json"
            self.pydreo_manager.load_devices()
            pydreo_fan = self.pydreo_manager.devices[0]

            lights = light.get_entries([pydreo_fan])
            light_switch = self.get_entity_by_key(lights, "Light")

            # Known starting state: light off, brightness 100.
            pydreo_fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: False, BRIGHTNESS_KEY: 100}})

            # Turning on with a new brightness must send ONE combined command.
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                light_switch.turn_on(brightness=128)  # 128/255*100 ≈ 50
                mock_send_command.assert_called_once_with(pydreo_fan, {BRIGHTNESS_KEY: 50, LIGHTON_KEY: True})

            # Turning on with no attributes still sends just lighton=True.
            pydreo_fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: False}})
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                light_switch.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: True})

            # Light already on and brightness unchanged: lighton is STILL sent. A
            # same-value skip on a stale cache made the light unreachable in the
            # field; a redundant lighton is a harmless no-op that self-heals it.
            pydreo_fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: True, BRIGHTNESS_KEY: 50}})
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                light_switch.turn_on(brightness=128)  # still 50 on device scale
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: True})

    def test_HCF002S(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HCF002S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_fan = self.pydreo_manager.devices[0]
            ha_fan = fan.DreoFanHA(pydreo_fan)

            # Test basic fan properties
            assert pydreo_fan.model == "DR-HCF002S"
            assert pydreo_fan.speed_range == (1, 12)
            assert ha_fan.speed_count == 12
            assert pydreo_fan.preset_modes == ["normal", "natural", "sleep", "auto"]

            # Test fan commands. Fixture is gated off (poweron False): turning the
            # fan on must be one atomic command that opens the gate and explicitly
            # forces the other loads off (poweron alone re-energises retained loads).
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: True, POWERON_KEY: True, LIGHTON_KEY: False, ATMON_KEY: False})

            # Test preset modes (fan is now on after the wake above, so only mode is sent)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("auto")
                mock_send_command.assert_called_once_with(pydreo_fan, {MODE_KEY: 5})

            # Check switches
            switches = switch.get_entries([pydreo_fan])
            self.verify_expected_entities(switches, ["Panel Sound"])

            # Check lights - should have both main light and RGB light
            lights = light.get_entries([pydreo_fan])
            self.verify_expected_entities(lights, ["Light", "RGB Light"])

            # Test main light
            main_light = self.get_entity_by_key(lights, "Light")
            assert main_light is not None
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                main_light.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: True})

            # Test RGB light
            rgb_light = self.get_entity_by_key(lights, "RGB Light")
            assert rgb_light is not None
            assert rgb_light.is_on is False
            assert rgb_light.rgb_color == (0, 255, 0)  # Green from state

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                rgb_light.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {ATMON_KEY: True})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                rgb_light.turn_on(rgb_color=(255, 0, 0))  # Red
                # Should send atmcolor command (atmon sent first automatically)
                assert mock_send_command.call_count == 2  # atmon + atmcolor

    def test_HCF002S_CFRGB(self):  # pylint: disable=invalid-name
        """Load DR-HCF002S RGBIC variant (CFRGB control type) and verify that RGB colour
        and colour-temperature commands are generated even when 'atmcolor' was absent
        from the device's initial state.
        """
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HCF002S_CFRGB.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_fan = self.pydreo_manager.devices[0]
            ha_fan = fan.DreoFanHA(pydreo_fan)

            assert pydreo_fan.model == "DR-HCF002S"
            assert pydreo_fan.speed_range == (1, 12)
            assert ha_fan.speed_count == 12
            assert pydreo_fan.preset_modes == ["normal", "natural", "sleep", "auto"]

            # Both main light and RGBIC light entities should be created
            lights = light.get_entries([pydreo_fan])
            self.verify_expected_entities(lights, ["Light", "RGBIC Light"])

            # ---- Main light (colour temperature) ----
            main_light = self.get_entity_by_key(lights, "Light")
            assert main_light is not None

            # Fixture is gated off (poweron False): waking the main light must be one
            # atomic command opening the gate and forcing the other loads off.
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                main_light.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: True, POWERON_KEY: True, FANON_KEY: False, ATMON_KEY: False})
            pydreo_fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: True}})

            # Setting brightness while the light is already on resends lighton too -
            # no same-value skips on load keys (a stale-cache skip strands the entity).
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                main_light.turn_on(brightness=128)
                mock_send_command.assert_called_once_with(pydreo_fan, {BRIGHTNESS_KEY: 50, LIGHTON_KEY: True})

            # ---- RGBIC atmosphere light (preset-based, not direct RGB) ----
            rgbic_light = self.get_entity_by_key(lights, "RGBIC Light")
            assert rgbic_light is not None
            # RGBIC preset device - rgb_color is not supported
            assert rgbic_light.rgb_color is None
            # atmon was retained True in the fixture, but the device was gated off and
            # the main-light wake above explicitly forced atmon off - so the RGBIC
            # light reads OFF here. The device then reports it back on.
            assert rgbic_light.is_on is False
            pydreo_fan.handle_server_update({REPORTED_KEY: {ATMON_KEY: True}})
            assert rgbic_light.is_on is True
            # RGBIC light should have effect list with presets
            assert rgbic_light.effect_list == ["Preset 1", "Preset 2", "Preset 3", "Preset 4"]
            # Current preset is 0, so effect should be "Preset 1"
            assert rgbic_light.effect == "Preset 1"

            # Redundant same-value sends are no longer skipped (a stale-cache skip
            # made entities unreachable on units that stop reporting load keys), so
            # turn_on() re-sends atmon - a hardware-validated no-op on the device.
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                rgbic_light.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {ATMON_KEY: True})

            # Setting effect sends the (redundant) atmon plus the rgbpresetsel command
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                rgbic_light.turn_on(effect="Preset 3")
                assert mock_send_command.call_count == 2
                mock_send_command.assert_any_call(pydreo_fan, {RGBPRESETSEL_KEY: 2})

    def test_HCF003S(self):  # pylint: disable=invalid-name
        """Load HCF003S fan and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HCF003S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_fan = self.pydreo_manager.devices[0]
            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert ha_fan.is_on is True
            assert ha_fan.speed_count == 12
            assert ha_fan.unique_id is not None
            assert pydreo_fan.model == "DR-HCF003S"
            assert pydreo_fan.speed_range == (1, 12)
            assert pydreo_fan.preset_modes == ["normal", "natural", "sleep", "reverse"]

            # Test power commands
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: False})
            pydreo_fan.handle_server_update({REPORTED_KEY: {FANON_KEY: False}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: True})
            pydreo_fan.handle_server_update({REPORTED_KEY: {FANON_KEY: True}})

            # Test speed settings
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(25)  # Speed ~3
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 3})
            pydreo_fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 3}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(50)  # Speed ~6
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 6})
            pydreo_fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 6}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)  # Speed 12 (max)
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 12})
            pydreo_fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 12}})

            # Test preset modes
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("natural")
                mock_send_command.assert_called_once_with(pydreo_fan, {MODE_KEY: 2})
            pydreo_fan.handle_server_update({REPORTED_KEY: {MODE_KEY: 2}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("reverse")
                mock_send_command.assert_called_once_with(pydreo_fan, {MODE_KEY: 4})
            pydreo_fan.handle_server_update({REPORTED_KEY: {MODE_KEY: 4}})

            # Check to see what switches are added to ceiling fans
            switches = switch.get_entries([pydreo_fan])
            self.verify_expected_entities(switches, ["Panel Sound"])

            # Check to see what numbers are added to ceiling fans
            numbers = number.get_entries([pydreo_fan])
            self.verify_expected_entities(numbers, [])

            lights = light.get_entries([pydreo_fan])
            self.verify_expected_entities(lights, ["Light"])
            light_switch = self.get_entity_by_key(lights, "Light")

            # Test light control
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                light_switch.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: True})
            pydreo_fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: True}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                light_switch.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: False})
            pydreo_fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: False}})

            # Test brightness and color temperature
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                light_switch.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: True})
            pydreo_fan.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: True}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                # Brightness is converted from HA's 0-255 scale to device's 1-100 scale
                # 128/255 * 100 = ~50.2, which gets rounded to 50. lighton rides along:
                # skipping it on a cached "already on" strands the light on a stale cache.
                light_switch.turn_on(brightness=128)
                mock_send_command.assert_called_once_with(pydreo_fan, {BRIGHTNESS_KEY: 50, LIGHTON_KEY: True})
            pydreo_fan.handle_server_update({REPORTED_KEY: {BRIGHTNESS_KEY: 51}})

            # Test color temperature if supported
            if hasattr(light_switch, "color_temp") and light_switch.color_temp is not None:
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    # Color temp in mired, converted to 0-100 scale
                    light_switch.turn_on(color_temp=300)
                    # Should convert and send colortemp command
                    assert mock_send_command.called

    def test_HCF521S(self):  # pylint: disable=invalid-name
        """Load HCF521S fan and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HCF521S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_fan = self.pydreo_manager.devices[0]
            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert ha_fan.is_on is False
            assert ha_fan.speed_count == 12
            assert ha_fan.unique_id is not None
            assert pydreo_fan.model == "DR-HCF521S"
            assert pydreo_fan.speed_range == (1, 12)
            assert pydreo_fan.preset_modes == ["normal", "natural", "sleep", "reverse"]

            # Test power commands
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: True})
            pydreo_fan.handle_server_update({REPORTED_KEY: {FANON_KEY: True}})

            # Redundant same-value sends are no longer skipped: a skip decided on a
            # stale cache made entities permanently unreachable, and redundant
            # commands are hardware-validated no-ops.
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: True})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: False})
            pydreo_fan.handle_server_update({REPORTED_KEY: {FANON_KEY: False}})

            # Test speed settings - use 75% which maps to windlevel 9 (different from fixture's 6)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(75)  # Speed 9
                # set_percentage turns on the fan first (fanon: true), then sets speed
                assert mock_send_command.call_count == 2
                mock_send_command.assert_any_call(pydreo_fan, {FANON_KEY: True})
                mock_send_command.assert_any_call(pydreo_fan, {WINDLEVEL_KEY: 9})
            pydreo_fan.handle_server_update({REPORTED_KEY: {FANON_KEY: True}})
            pydreo_fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 9}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)  # Speed 12 (max)
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 12})
            pydreo_fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 12}})

            # Test preset modes
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("natural")
                mock_send_command.assert_called_once_with(pydreo_fan, {MODE_KEY: 2})
            pydreo_fan.handle_server_update({REPORTED_KEY: {MODE_KEY: 2}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("reverse")
                mock_send_command.assert_called_once_with(pydreo_fan, {MODE_KEY: 4})
            pydreo_fan.handle_server_update({REPORTED_KEY: {MODE_KEY: 4}})

            # Check switches, numbers, and lights
            switches = switch.get_entries([pydreo_fan])
            self.verify_expected_entities(switches, ["Panel Sound"])

            numbers = number.get_entries([pydreo_fan])
            self.verify_expected_entities(numbers, [])

            lights = light.get_entries([pydreo_fan])
            self.verify_expected_entities(lights, ["Light"])

    def test_HCF007S(self):  # pylint: disable=invalid-name
        """Load HCF007S fan and test fallback model mapping."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HCF007S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_fan = self.pydreo_manager.devices[0]
            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert pydreo_fan.model == "DR-HCF007S"
            assert pydreo_fan.speed_range == (1, 12)
            assert pydreo_fan.preset_modes == ["normal", "natural", "sleep", "reverse"]
            assert ha_fan.speed_count == 12
            assert ha_fan.preset_modes == ["normal", "natural", "sleep", "reverse"]

            # Fixture is gated off (poweron False): the implicit fan turn-on inside
            # set_preset_mode must be the atomic wake command.
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("reverse")
                assert mock_send_command.call_count == 2
                mock_send_command.assert_any_call(pydreo_fan, {FANON_KEY: True, POWERON_KEY: True, LIGHTON_KEY: False, ATMON_KEY: False})
                mock_send_command.assert_any_call(pydreo_fan, {MODE_KEY: 4})
            pydreo_fan.handle_server_update({REPORTED_KEY: {MODE_KEY: 4}})

            # Fan is now on (optimistic state from the wake above): only speed is sent.
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 12})
            pydreo_fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 12}})

            # ---- RGBIC atmosphere light (preset-based, with direct RGB colour write) ----
            lights = light.get_entries([pydreo_fan])
            self.verify_expected_entities(lights, ["Light", "RGBIC Light"])

            rgbic_light = self.get_entity_by_key(lights, "RGBIC Light")
            assert rgbic_light is not None
            # Device accepts ATMCOLOR_KEY commands (write-only) so RGB colour mode is enabled
            assert rgbic_light.color_mode == ColorMode.RGB

            # HCF007S has 4 presets (rgbpresetnum=4 in test data)
            assert rgbic_light.effect_list == ["Preset 1", "Preset 2", "Preset 3", "Preset 4"]

            # Initial rgbpresetsel=0 → "Preset 1"
            assert rgbic_light.effect == "Preset 1"

            # atmon was retained True in the fixture but the device was gated off,
            # and the fan wake above explicitly forced atmon off. The device then
            # reports it back on.
            assert rgbic_light.is_on is False
            pydreo_fan.handle_server_update({REPORTED_KEY: {ATMON_KEY: True}})
            assert rgbic_light.is_on is True

            # Selecting a preset must send RGBPRESETSEL_KEY (not RGBEFFECTID_KEY)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                rgbic_light.turn_on(effect="Preset 3")
                mock_send_command.assert_any_call(pydreo_fan, {RGBPRESETSEL_KEY: 2})

            # Verify rgbpresetsel server update changes the reported preset
            pydreo_fan.handle_server_update({REPORTED_KEY: {RGBPRESETSEL_KEY: 2}})
            assert rgbic_light.effect == "Preset 3"

            # Verify brightness slider works
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                rgbic_light.turn_on(brightness=128)
                mock_send_command.assert_any_call(pydreo_fan, {ATMBRI_KEY: 50})

            # Direct RGB colour control must send ATMCOLOR_KEY
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                rgbic_light.turn_on(**{ATTR_RGB_COLOR: (0, 255, 0)})
                mock_send_command.assert_any_call(pydreo_fan, {ATMCOLOR_KEY: 65280})

    def test_main_power_diagnostic_entity(self):
        """The whole-device gate is exposed as a diagnostic binary sensor.

        `light_on == False` collapses "light off" and "light retained on behind a
        closed gate"; only the gate distinguishes them, and until now that state
        existed nowhere in HA - it had to be probed live against Dreo's cloud REST.
        Recording it makes the failure mode visible after the fact.
        """
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HCF002S.json"
            self.pydreo_manager.load_devices()
            pydreo_fan = self.pydreo_manager.devices[0]

            sensors = binary_sensor.get_entries([pydreo_fan])
            assert len(sensors) == 1
            main_power = sensors[0]
            assert main_power.entity_description.key == "main_power"
            assert main_power.entity_category is EntityCategory.DIAGNOSTIC
            assert main_power.entity_registry_enabled_default is True
            assert main_power.unique_id.endswith("-main_power")
            # No state strings of our own: HA core supplies localized On/Off.
            assert main_power.device_class is None

            # Powered, light retained on, fan retained off.
            pydreo_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True, LIGHTON_KEY: True, ATMON_KEY: False, FANON_KEY: False}})
            assert main_power.is_on is True
            assert main_power.icon == "mdi:power"
            assert main_power.extra_state_attributes[LIGHTON_KEY] is True

            # Unpowered: the light entity reads off, but the attributes still show
            # lighton retained True. That difference is the whole point of the entity.
            pydreo_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
            assert main_power.is_on is False
            assert main_power.icon == "mdi:power-off"
            assert pydreo_fan.light_on is False
            assert main_power.extra_state_attributes[LIGHTON_KEY] is True
            assert main_power.extra_state_attributes["rest_readback_stale"] is False

    def test_no_main_power_entity_on_ungated_models(self):
        """DR-HCF001S and DR-HCF521S have no poweron key, so no gate and no entity."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            for devices_file in ("get_devices_HCF001S.json", "get_devices_HCF521S.json"):
                self.get_devices_file_name = devices_file
                self.pydreo_manager.load_devices()
                pydreo_fan = self.pydreo_manager.devices[0]
                assert pydreo_fan.poweron is None
                assert binary_sensor.get_entries([pydreo_fan]) == [], devices_file
