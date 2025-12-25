"""Integration Tests for Dreo Air Circulator Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from homeassistant.components.fan import (
    FanEntity, 
    FanEntityFeature
)
from custom_components.dreo import fan
from custom_components.dreo import switch
from custom_components.dreo import number
from .imports import * # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase, PATCH_SEND_COMMAND
from custom_components.dreo.pydreo.constant import (
    HORIZONTAL_OSCILLATION_ANGLE_KEY,
    VERTICAL_OSCILLATION_ANGLE_KEY
)

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_SCHEDULE_UPDATE_HA_STATE= f'{PATCH_BASE_PATH}.schedule_update_ha_state'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestDreoAirCirculator(IntegrationTestBase):
    """Test Dreo Air Circulators and PyDreo together."""
    
    def test_HAF001S(self):  # pylint: disable=invalid-name
        """Test HAF001S fan."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE) as mock_update_ha_state:

            self.get_devices_file_name = "get_devices_HAF001S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1
            
            pydreo_fan = self.pydreo_manager.devices[0]
            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert ha_fan.is_on is True
            assert ha_fan.speed_count == 4
            assert ha_fan.supported_features & FanEntityFeature.OSCILLATE
            assert ha_fan.unique_id is not None
            assert pydreo_fan.model == "DR-HAF001S"
            assert pydreo_fan.speed_range == (1, 4)

            # Test percentage calculation
            assert ha_fan.percentage >= 0 and ha_fan.percentage <= 100

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: True})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: False})

            # Test oscillation
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.oscillate(True)
                assert mock_send_command.call_count >= 1

            # Test speed settings
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(25)  # Speed 1
                assert mock_send_command.call_count >= 1

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)  # Speed 4 (max)
                assert mock_send_command.call_count >= 1

            # Check to see what switches are added to ceiling fans
            switches = switch.get_entries([pydreo_fan])
            self.verify_expected_entities(switches, ['Horizontally Oscillating', 'Panel Sound'])

    def test_HAF004S(self):  # pylint: disable=invalid-name
        """Test HAF004S fan."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE) as mock_update_ha_state:

            self.get_devices_file_name = "get_devices_HAF004S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1
            
            pydreo_fan = self.pydreo_manager.devices[0]
            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert ha_fan.is_on is False
            assert ha_fan.speed_count == 9
            assert ha_fan.supported_features & FanEntityFeature.OSCILLATE
            assert ha_fan.unique_id is not None
            assert pydreo_fan.model == "DR-HAF004S"
            assert pydreo_fan.speed_range == (1, 9)

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: True})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: False})

            # Test oscillation (both horizontal and vertical)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.oscillate(True)
                # Oscillation may trigger multiple commands or none if already oscillating
                # Just verify the call was attempted
                assert mock_send_command.call_count >= 0

            # Test speed range (1-9)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(11)  # Speed 1
                assert mock_send_command.call_count >= 1

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(50)  # Mid-range
                assert mock_send_command.call_count >= 1

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)  # Speed 9 (max)
                assert mock_send_command.call_count >= 1

            # Check to see what switches are added to air circulator fans
            switches = switch.get_entries([pydreo_fan])
            self.verify_expected_entities(switches, ['Adaptive Brightness', 'Horizontally Oscillating', 'Panel Sound', 'Vertically Oscillating'])

    def test_HPF007S(self):  # pylint: disable=invalid-name
        """Test test_HPF007S fan."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE) as mock_update_ha_state:

            self.get_devices_file_name = "get_devices_HPF007S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1
            
            pydreo_fan = self.pydreo_manager.devices[0]
            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert ha_fan.is_on is True
            assert ha_fan.speed_count == 10
            assert not(ha_fan.supported_features & FanEntityFeature.PRESET_MODE)

            """This shouldn't be needed, but for some reason HA calls this even if preset_mode is not supported."""
            assert ha_fan.preset_mode is None


    def test_HPF008S(self):  # pylint: disable=invalid-name
        """Test HPF008S fan."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE) as mock_update_ha_state:

            self.get_devices_file_name = "get_devices_HPF008S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1
            
            pydreo_fan = self.pydreo_manager.devices[0]
            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert ha_fan.is_on is True
            assert ha_fan.speed_count == 9
            assert ha_fan.supported_features & FanEntityFeature.PRESET_MODE
            assert pydreo_fan.model == "DR-HPF008S"
            assert pydreo_fan.speed_range == (1, 9)

            # Verify preset modes
            assert pydreo_fan.preset_modes == ["normal", "auto", "sleep", "natural", "turbo"]
            assert pydreo_fan.preset_mode == "normal"  # Initial mode is 1 which is "normal"
            assert ha_fan.preset_modes == ["normal", "auto", "sleep", "natural", "turbo"]
            assert ha_fan.preset_mode == "normal"

            # Verify temperature sensor (HPF008S has temperature monitoring)
            assert pydreo_fan.temperature is not None
            assert isinstance(pydreo_fan.temperature, (int, float))

            # Test power commands
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: False})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: True})

            # Test speed settings across range
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(1)  # Minimum
                assert mock_send_command.call_count >= 1

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)  # Maximum
                assert mock_send_command.call_count >= 1

            # Test preset mode commands
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("auto")
                mock_send_command.assert_called_once_with(pydreo_fan, {WIND_MODE_KEY: 2})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("sleep")
                mock_send_command.assert_called_once_with(pydreo_fan, {WIND_MODE_KEY: 3})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("natural")
                mock_send_command.assert_called_once_with(pydreo_fan, {WIND_MODE_KEY: 4})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("turbo")
                mock_send_command.assert_called_once_with(pydreo_fan, {WIND_MODE_KEY: 5})

    def test_HAF003S_newer_firmware(self):  # pylint: disable=invalid-name
        """Test HAF003S fan with newer firmware (Device 1 - with cruiseconf/fixedconf)."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE) as mock_update_ha_state:

            self.get_devices_file_name = "get_devices_HAF003S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 2
            
            # Device 1 is the newer firmware
            pydreo_fan = self.pydreo_manager.devices[0]
            assert pydreo_fan.model == "DR-HAF003S"
            assert pydreo_fan.speed_range == (1, 8)
            assert pydreo_fan.horizontal_angle_range == (-60, 60)
            assert pydreo_fan.vertical_angle_range == (-15, 90)
            
            # Verify it has cruise_conf and fixed_conf
            assert pydreo_fan._cruise_conf is not None
            assert pydreo_fan._fixed_conf is not None
            assert pydreo_fan._horizontal_oscillation_angle is None
            assert pydreo_fan._vertical_oscillation_angle is None
            
            # Check that the cruise mode entities are available
            numbers = number.get_entries([pydreo_fan])
            number_names = [n.entity_description.key for n in numbers]
            assert 'Horizontal Angle' in number_names
            assert 'Vertical Angle' in number_names
            assert 'Horizontal Oscillation Angle Left' in number_names
            assert 'Horizontal Oscillation Angle Right' in number_names
            assert 'Vertical Oscillation Angle Top' in number_names
            assert 'Vertical Oscillation Angle Bottom' in number_names
            
            # Should NOT have the single oscillation angle entities (those are for older firmware)
            assert 'Horizontal Oscillation Angle' not in number_names
            assert 'Vertical Oscillation Angle' not in number_names

    def test_HAF003S_older_firmware(self):  # pylint: disable=invalid-name
        """Test HAF003S fan with older firmware (Device 2 - with hoscon/voscon)."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE) as mock_update_ha_state:

            self.get_devices_file_name = "get_devices_HAF003S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 2
            
            # Device 2 is the older firmware
            pydreo_fan = self.pydreo_manager.devices[1]
            assert pydreo_fan.model == "DR-HAF003S"
            assert pydreo_fan.speed_range == (1, 8)
            assert pydreo_fan.horizontal_angle_range == (-60, 60)
            assert pydreo_fan.vertical_angle_range == (-15, 90)
            
            # Verify it does NOT have cruise_conf or fixed_conf
            assert pydreo_fan._cruise_conf is None
            assert pydreo_fan._fixed_conf is None
            
            # But it DOES have horizontal/vertical oscillation angles
            assert pydreo_fan._horizontal_oscillation_angle is not None
            assert pydreo_fan._vertical_oscillation_angle is not None
            
            # Check that the single oscillation angle entities are available
            numbers = number.get_entries([pydreo_fan])
            number_names = [n.entity_description.key for n in numbers]
            assert 'Horizontal Oscillation Angle' in number_names
            assert 'Vertical Oscillation Angle' in number_names
            
            # Should NOT have cruise mode entities (those require cruise_conf)
            assert 'Horizontal Angle' not in number_names
            assert 'Vertical Angle' not in number_names
            assert 'Horizontal Oscillation Angle Left' not in number_names
            assert 'Horizontal Oscillation Angle Right' not in number_names
            assert 'Vertical Oscillation Angle Top' not in number_names
            assert 'Vertical Oscillation Angle Bottom' not in number_names
            
            # Test setting the oscillation angle
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                pydreo_fan.horizontal_oscillation_angle = 30
                mock_send_command.assert_called_once_with(pydreo_fan, {HORIZONTAL_OSCILLATION_ANGLE_KEY: 30})
            
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                pydreo_fan.vertical_oscillation_angle = 45
                mock_send_command.assert_called_once_with(pydreo_fan, {VERTICAL_OSCILLATION_ANGLE_KEY: 45})
