"""Integration Tests for Dreo Ceiling Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import number
from custom_components.dreo import humidifier
from custom_components.dreo import sensor

from  .imports import * # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_SCHEDULE_UPDATE_HA_STATE= f'{PATCH_BASE_PATH}.schedule_update_ha_state'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestDreoHumidifier(IntegrationTestBase):
    """Test Dreo Humidifers class and PyDreo together."""
    
    def test_HHM001S(self):  # pylint: disable=invalid-name
        """Load air conditioner and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):

            self.get_devices_file_name = "get_devices_HHM001S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1
            
            pydreo_humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
            assert pydreo_humidifier.type == 'Humidifier'
            assert pydreo_humidifier.humidity == 47
            assert pydreo_humidifier.model == "DR-HHM001S"

            ha_humidifier = humidifier.DreoHumidifierHA(pydreo_humidifier)
            assert ha_humidifier.is_on is True
            assert ha_humidifier.current_humidity == 47
            assert ha_humidifier.target_humidity == 60
            assert ha_humidifier.unique_id is not None
            assert ha_humidifier.name is not None

            # Test mode if available
            if ha_humidifier.available_modes:
                assert len(ha_humidifier.available_modes) > 0
                current_mode = ha_humidifier.mode
                assert current_mode is not None or current_mode in ha_humidifier.available_modes

            # Check to see what numbers are added to humidifiers
            numbers = number.get_entries([pydreo_humidifier])
            self.verify_expected_entities(numbers, [])

            # Check to see what sensors are added to humidifiers
            sensors = sensor.get_entries([pydreo_humidifier])
            self.verify_expected_entities(sensors, ["Humidity", "Status", "Water Level", "Ambient Light Humidifier", "Use since cleaning"])

        
