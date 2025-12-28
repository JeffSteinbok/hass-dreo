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
    VERTICAL_OSCILLATION_ANGLE_KEY,
    HORIZONTAL_ANGLE_ADJ_KEY
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
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: False})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {POWERON_KEY: False} })

            # Test oscillation (HAF001S uses hoscon/voscon, not oscmode)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.oscillate(True)
                # HAF001S triggers hoscon=True and voscon=False (horizontal oscillation only)
                assert mock_send_command.call_count == 2
                calls = [call[0][1] for call in mock_send_command.call_args_list]
                assert {'hoscon': True} in calls
                assert {'voscon': False} in calls
            pydreo_fan.handle_server_update({ REPORTED_KEY: {'hoscon': True, 'voscon': False} })

            # Test speed settings  
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(25)  # Speed 1 (also turns on the fan since it's off)
                # This triggers both poweron and windlevel commands
                assert mock_send_command.call_count == 2
                calls = [call[0][1] for call in mock_send_command.call_args_list]
                assert {POWERON_KEY: True} in calls
                assert {WINDLEVEL_KEY: 1} in calls
            pydreo_fan.handle_server_update({ REPORTED_KEY: {POWERON_KEY: True, WINDLEVEL_KEY: 1} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)  # Speed 4 (max)
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 4})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 4} })

            # Check to see what switches are added to air circulator fans
            switches = switch.get_entries([pydreo_fan])
            self.verify_expected_entities(switches, ['Horizontally Oscillating', 'Panel Sound', 'Vertically Oscillating'])

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
            pydreo_fan.handle_server_update({ REPORTED_KEY: {POWERON_KEY: True} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: False})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {POWERON_KEY: False} })

            # Test oscillation (device starts with oscmode=2 which is VERTICAL oscillation)
            # Turn off oscillation first, then turn it back on
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.oscillate(False)
                mock_send_command.assert_called_once_with(pydreo_fan, {OSCMODE_KEY: 0})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {OSCMODE_KEY: 0} })
            
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.oscillate(True)
                mock_send_command.assert_called_once_with(pydreo_fan, {OSCMODE_KEY: 1})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {OSCMODE_KEY: 1} })

            # Turn fan back on for speed tests
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: True})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {POWERON_KEY: True} })

            # Test speed range (1-9)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(11)  # Speed 1
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 1})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 1} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(50)  # Mid-range (~speed 5)
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 5})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 5} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)  # Speed 9 (max)
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 9})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 9} })

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
            pydreo_fan.handle_server_update({ REPORTED_KEY: {FANON_KEY: False} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: True})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {FANON_KEY: True} })

            # Test speed settings across range
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(1)  # Minimum
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 1})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 1} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)  # Maximum
                mock_send_command.assert_called_once_with(pydreo_fan, {WINDLEVEL_KEY: 9})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WINDLEVEL_KEY: 9} })

            # Test preset mode commands
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("auto")
                mock_send_command.assert_called_once_with(pydreo_fan, {WIND_MODE_KEY: 2})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WIND_MODE_KEY: 2} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("sleep")
                mock_send_command.assert_called_once_with(pydreo_fan, {WIND_MODE_KEY: 3})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WIND_MODE_KEY: 3} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("natural")
                mock_send_command.assert_called_once_with(pydreo_fan, {WIND_MODE_KEY: 4})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WIND_MODE_KEY: 4} })

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("turbo")
                mock_send_command.assert_called_once_with(pydreo_fan, {WIND_MODE_KEY: 5})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {WIND_MODE_KEY: 5} })

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
            pydreo_fan.handle_server_update({ REPORTED_KEY: {HORIZONTAL_OSCILLATION_ANGLE_KEY: 30} })
            
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                pydreo_fan.vertical_oscillation_angle = 45
                mock_send_command.assert_called_once_with(pydreo_fan, {VERTICAL_OSCILLATION_ANGLE_KEY: 45})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {VERTICAL_OSCILLATION_ANGLE_KEY: 45} })

    def test_HPF005S(self):  # pylint: disable=invalid-name
        """Test HPF005S fan with hangleadj support."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE) as mock_update_ha_state:

            self.get_devices_file_name = "get_devices_HPF005S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_fan = self.pydreo_manager.devices[0]
            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert ha_fan.is_on is True
            assert ha_fan.speed_count == 10
            assert pydreo_fan.model == "DR-HPF005S"
            assert pydreo_fan.speed_range == (1, 10)
            assert pydreo_fan.horizontal_angle_range == (-60, 60)
            
            # Verify it has hangleadj
            assert pydreo_fan._horizontal_angle_adj is not None
            assert pydreo_fan._horizontal_angle_adj == -36
            
            # Verify it does NOT have cruise_conf or fixed_conf (uses hangleadj instead)
            assert pydreo_fan._cruise_conf is None
            assert pydreo_fan._fixed_conf is None
            
            # Check that the horizontal angle entity is available
            numbers = number.get_entries([pydreo_fan])
            number_names = [n.entity_description.key for n in numbers]
            assert 'Horizontal Angle' in number_names
            
            # Get the horizontal angle number entity
            horizontal_angle_number = next((n for n in numbers if n.entity_description.key == 'Horizontal Angle'), None)
            assert horizontal_angle_number is not None
            
            # Verify the range matches the device definition
            assert horizontal_angle_number._attr_native_min_value == -60
            assert horizontal_angle_number._attr_native_max_value == 60
            
            # Verify the current value
            assert horizontal_angle_number.native_value == -36
            
            # Test setting the horizontal angle
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                pydreo_fan.horizontal_angle = 45
                mock_send_command.assert_called_once_with(pydreo_fan, {HORIZONTAL_ANGLE_ADJ_KEY: 45})
            pydreo_fan.handle_server_update({ REPORTED_KEY: {HORIZONTAL_ANGLE_ADJ_KEY: 45} })
            
            # Should NOT have cruise mode entities (those require cruise_conf)
            assert 'Horizontal Oscillation Angle Left' not in number_names
            assert 'Horizontal Oscillation Angle Right' not in number_names
            assert 'Vertical Oscillation Angle Top' not in number_names
            assert 'Vertical Oscillation Angle Bottom' not in number_names
            
            # Should NOT have old firmware entities (those require hoscangle/voscangle values)
            assert 'Horizontal Oscillation Angle' not in number_names
            assert 'Vertical Oscillation Angle' not in number_names
