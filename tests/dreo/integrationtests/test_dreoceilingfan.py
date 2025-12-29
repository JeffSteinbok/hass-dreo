"""Integration Tests for Dreo Ceiling Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import fan
from custom_components.dreo import switch
from custom_components.dreo import number
from custom_components.dreo import light
from .imports import * # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase, PATCH_SEND_COMMAND

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_SCHEDULE_UPDATE_HA_STATE= f'{PATCH_BASE_PATH}.schedule_update_ha_state'

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
            pydreo_fan.handle_server_update({ REPORTED_KEY: {FANON_KEY: True} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: False})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {FANON_KEY: False} })

            # Turn fan back on for speed tests
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: True})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {FANON_KEY: True} })

            # Test speed settings
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(25)  # Speed ~3
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 3})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 3} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(50)  # Speed ~6
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 6})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 6} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)  # Speed 12 (max)
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 12})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 12} })

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
            pydreo_fan.handle_server_update({ REPORTED_KEY: {LIGHTON_KEY: True} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                light_switch.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: False})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {LIGHTON_KEY: False} })

            # Test brightness if supported
            if hasattr(light_switch, 'brightness') and light_switch.brightness is not None:
                # Turn light on first - light_switch.turn_on(brightness=X) turns light on if off
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    light_switch.turn_on()
                    mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: True})
                pydreo_fan.handle_server_update({ REPORTED_KEY: {LIGHTON_KEY: True} })
                
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    # Brightness is converted from HA's 0-255 scale to device's 1-100 scale
                    # 128/255 * 100 = ~50.2, which gets ceil'd to 51
                    light_switch.turn_on(brightness=128)
                    mock_send_command.assert_called_once_with(pydreo_fan, {BRIGHTNESS_KEY: 51})

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
            assert pydreo_fan.preset_modes == ['normal', 'natural', 'sleep', 'auto']
            
            # Test fan commands
            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: True})
            
            # Test preset modes (it will also turn on the fan if off)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode('auto')
                # Should call both fanon and mode since fan is currently off
                assert mock_send_command.call_count == 2
                # Check the last call was setting mode to 5 (auto)
                mock_send_command.assert_any_call(pydreo_fan, {MODE_KEY: 5})
            
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
            assert pydreo_fan.preset_modes == ['normal', 'natural', 'sleep', 'reverse']

            # Test power commands
            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: False})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {FANON_KEY: False} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: True})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {FANON_KEY: True} })

            # Test speed settings
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(25)  # Speed ~3
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 3})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 3} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(50)  # Speed ~6
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 6})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 6} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)  # Speed 12 (max)
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 12})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 12} })

            # Test preset modes
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode('natural')
                mock_send_command.assert_called_once_with(pydreo_fan, {MODE_KEY: 2})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {MODE_KEY: 2} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode('reverse')
                mock_send_command.assert_called_once_with(pydreo_fan, {MODE_KEY: 4})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {MODE_KEY: 4} })

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
            pydreo_fan.handle_server_update({ REPORTED_KEY: {LIGHTON_KEY: True} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                light_switch.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: False})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {LIGHTON_KEY: False} })

            # Test brightness and color temperature
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                light_switch.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: True})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {LIGHTON_KEY: True} })
            
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                # Brightness is converted from HA's 0-255 scale to device's 1-100 scale
                # 128/255 * 100 = ~50.2, which gets ceil'd to 51
                light_switch.turn_on(brightness=128)
                mock_send_command.assert_called_once_with(pydreo_fan, {BRIGHTNESS_KEY: 51})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {BRIGHTNESS_KEY: 51} })

            # Test color temperature if supported
            if hasattr(light_switch, 'color_temp') and light_switch.color_temp is not None:
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    # Color temp in mired, converted to 0-100 scale
                    light_switch.turn_on(color_temp=300)
                    # Should convert and send colortemp command
                    assert mock_send_command.called

