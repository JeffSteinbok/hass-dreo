"""Integration Tests for Dreo Ceiling Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import number
from custom_components.dreo import humidifier

from  .imports import * # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_SCHEDULE_UPDATE_HA_STATE= f'{PATCH_BASE_PATH}.schedule_update_ha_state'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestDreoDeHumidifier(IntegrationTestBase):
    """Test Dreo Humidifers class and PyDreo together."""
    
    def test_HDH002S(self):  # pylint: disable=invalid-name
        """Load dehumidifier and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):

            self.get_devices_file_name = "get_devices_HDH002S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1
            
            pydreo_dehumidifier : PyDreoDehumidifier = self.pydreo_manager.devices[0]
            assert pydreo_dehumidifier.type == 'Dehumidifier'
            assert pydreo_dehumidifier.model == "DR-HDH002S"

            ha_humidifier = humidifier.DreoDehumidifierHA(pydreo_dehumidifier)
            assert ha_humidifier.is_on is False
            assert ha_humidifier.current_humidity == 66
            assert ha_humidifier.target_humidity == 50
            assert ha_humidifier.unique_id is not None
            assert ha_humidifier.name is not None

            # Test mode if available
            if ha_humidifier.available_modes:
                assert len(ha_humidifier.available_modes) > 0

            # Verify humidity range
            assert ha_humidifier.min_humidity is not None
            assert ha_humidifier.max_humidity is not None
            assert ha_humidifier.min_humidity <= ha_humidifier.target_humidity <= ha_humidifier.max_humidity

            # Check to see what numbers are added to chef makers
            numbers = number.get_entries([pydreo_dehumidifier])
            self.verify_expected_entities(numbers, [])

        
