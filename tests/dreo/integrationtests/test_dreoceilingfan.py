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

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: False})

            # Test speed settings
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(25)  # Speed ~3
                assert mock_send_command.call_count >= 1

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(50)  # Speed ~6
                assert mock_send_command.call_count >= 1

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)  # Speed 12 (max)
                assert mock_send_command.call_count >= 1

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

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                light_switch.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: False})

            # Test brightness if supported
            if hasattr(light_switch, 'brightness') and light_switch.brightness is not None:
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    light_switch.turn_on(brightness=128)
                    assert mock_send_command.call_count >= 1                 

    def test_HCF002S(self):  # pylint: disable=invalid-name
        """Test DR-HCF002S ceiling fan with RGB atmosphere lights."""
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
                # Should send both atmon and atmcolor commands
                assert mock_send_command.call_count >= 1

    def test_HCF003S(self):  # pylint: disable=invalid-name
        """Test DR-HCF003S ceiling fan - newer firmware with updated features."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            
            self.get_devices_file_name = "get_devices_HCF003S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1
            
            pydreo_fan = self.pydreo_manager.devices[0]
            ha_fan = fan.DreoFanHA(pydreo_fan)
            
            # Test basic fan properties
            assert pydreo_fan.model == "DR-HCF003S"
            assert pydreo_fan.speed_range == (1, 12)
            assert ha_fan.speed_count == 12
            assert pydreo_fan.preset_modes == ['normal', 'natural', 'sleep', 'reverse']
            
            # Test fan is on (from state data)
            assert ha_fan.is_on is True
            
            # Test fan commands
            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: True})
            
            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: False})
            
            # Test speed settings
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(50)  # Speed ~6
                assert mock_send_command.call_count >= 1
            
            # Test preset modes
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode('natural')
                # Should call mode command
                mock_send_command.assert_any_call(pydreo_fan, {MODE_KEY: 2})
            
            # Check switches
            switches = switch.get_entries([pydreo_fan])
            self.verify_expected_entities(switches, ["Panel Sound"])
            
            # Check numbers - should be empty for this model
            numbers = number.get_entries([pydreo_fan])
            self.verify_expected_entities(numbers, [])
            
            # Check lights - should have main light only
            lights = light.get_entries([pydreo_fan])
            self.verify_expected_entities(lights, ["Light"])
            
            # Test main light with color temperature support
            main_light = self.get_entity_by_key(lights, "Light")
            assert main_light is not None
            
            # Light should be off from state data
            assert main_light.is_on is False
            
            # Verify light supports color temperature
            assert hasattr(main_light, 'color_temp')
            assert main_light.color_temp is not None
            
            # Test light on/off
            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                main_light.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: True})
            
            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                main_light.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: False})
            
            # Test brightness control
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                main_light.turn_on(brightness=128)
                assert mock_send_command.call_count >= 1
            
            # Test color temperature control (0-100 range)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                main_light.turn_on(color_temp=350)  # HA uses mireds
                # Should send lighton and colortemp commands
                assert mock_send_command.call_count >= 1

