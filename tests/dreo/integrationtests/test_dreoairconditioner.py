"""Integration Tests for Dreo Ceiling Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import number, sensor
from  .imports import * # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_SCHEDULE_UPDATE_HA_STATE= f'{PATCH_BASE_PATH}.schedule_update_ha_state'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestDreoAirConditioner(IntegrationTestBase):
    """Test Dreo Ceiling Fan class and PyDreo together."""

    def test_HAC001S(self):  # pylint: disable=invalid-name
        """Load air conditioner and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):

            self.get_devices_file_name = "get_devices_HAC001S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_ac = self.pydreo_manager.devices[0]
            assert pydreo_ac.type == 'Air Conditioner'

            numbers = number.get_entries([pydreo_ac])
            self.verify_expected_entities(numbers, [])

            sensors = sensor.get_entries([pydreo_ac])
            self.verify_expected_entities(sensors, [])

