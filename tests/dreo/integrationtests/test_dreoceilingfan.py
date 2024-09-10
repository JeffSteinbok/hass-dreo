"""Integration Tests for Dreo Ceiling Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import fan
from custom_components.dreo import switch
from custom_components.dreo import number
from .imports import * # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase, PATCH_SEND_COMMAND

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_SCHEDULE_UPDATE_HA_STATE= f'{PATCH_BASE_PATH}.schedule_update_ha_state'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestDreoCeilingFan(IntegrationTestBase):
    """Test Dreo Ceiling Fan class and PyDreo together."""
    
    def test_HCF001S(self):  # pylint: disable=invalid-name
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE) as mock_update_ha_state:

            self.get_devices_file_name = "get_devices_HCF001S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1
            
            pydreo_fan = self.pydreo_manager.devices[0]
            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert ha_fan.is_on is False
            assert ha_fan.speed_count == 12

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_fan.turn_on()
                # TODO: Possible bug; need to test at home.  Why does this not cause an update?
                #mock_update_ha_state.assert_called_once()
                #mock_update_ha_state.reset_mock()
                mock_send_command.assert_called_once_with(pydreo_fan, {FANON_KEY: True})

            # Check to see what switches are added to ceiling fans
            switches = switch.get_entries([pydreo_fan])
            self.verify_expected_entities(switches, ["Light", "Panel Sound"])
            light_switch = self.get_entity_by_key(switches, "Light")

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                light_switch.turn_on()
                # TODO: Possible bug; need to test at home.  Why does this not cause an update?
                #mock_update_ha_state.assert_called_once()
                #mock_update_ha_state.reset_mock()
                mock_send_command.assert_called_once_with(pydreo_fan, {LIGHTON_KEY: True})            

            # Check to see what numbers are added to ceiling fans
            numbers = number.get_entries([pydreo_fan])
            self.verify_expected_entities(numbers, [])

        
