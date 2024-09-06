"""Integration Tests for Dreo Ceiling Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from  .imports import * # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase, PATCH_SEND_COMMAND
from custom_components.dreo import fan
from custom_components.dreo import switch
from custom_components.dreo import number

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_SCHEDULE_UPDATE_HA_STATE= f'{PATCH_BASE_PATH}.schedule_update_ha_state'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestDreoChefMaker(IntegrationTestBase):
    """Test Dreo Ceiling Fan class and PyDreo together."""
    
    def test_KCM001S(self):  # pylint: disable=invalid-name
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE) as mock_update_ha_state:

            self.get_devices_file_name = "get_devices_KCM001S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1
            
            pydreo_chef_maker = self.pydreo_manager.devices[0]
            ha_chef_maker = fan.DreoFanHA(pydreo_chef_maker)
            assert ha_chef_maker.is_on is False

            with patch(PATCH_SEND_COMMAND) as mock_send_command:    
                ha_chef_maker.turn_on()
                # TODO: Possible bug; need to test at home.  Why does this not cause an update?
                #mock_update_ha_state.assert_called_once()
                #mock_update_ha_state.reset_mock()
                mock_send_command.assert_called_once_with(pydreo_chef_maker, {POWERON_KEY: True})

            # Check to see what switches are added to ceiling fans
            switches = switch.get_entries([pydreo_chef_maker])
            self.verify_expected_entities(switches, ["Light"])
            light_switch = self.get_entity_by_key(switches, "Light")

            # Check to see what numbers are added to chef makers
            numbers = number.get_entries([pydreo_chef_maker])
            self.verify_expected_entities(numbers, [])

        
