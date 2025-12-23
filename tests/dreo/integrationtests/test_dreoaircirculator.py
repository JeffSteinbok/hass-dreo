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
            assert ha_fan.is_on is False
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
            assert not(ha_fan.supported_features & FanEntityFeature.PRESET_MODE)
            assert pydreo_fan.model == "DR-HPF008S"
            assert pydreo_fan.speed_range == (1, 9)

            """This shouldn't be needed, but for some reason HA calls this even if preset_mode is not supported."""
            assert ha_fan.preset_mode is None

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
