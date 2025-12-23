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

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_on()
                # TODO: Possible bug; need to test at home.  Why does this not cause an update?
                #mock_update_ha_state.assert_called_once()
                #mock_update_ha_state.reset_mock()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: True})

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

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_on()
                # TODO: Possible bug; need to test at home.  Why does this not cause an update?
                #mock_update_ha_state.assert_called_once()
                #mock_update_ha_state.reset_mock()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: True})

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

            """This shouldn't be needed, but for some reason HA calls this even if preset_mode is not supported."""
            assert ha_fan.preset_mode is None
