"""Integration Tests for Dreo Ceiling Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import dreoheater
from custom_components.dreo import sensor
from custom_components.dreo import number

from homeassistant.components.climate import (
    HVACMode
)

from  .imports import * # pylint: disable=W0401,W0614
from .integrationtestbase import PATCH_SEND_COMMAND, IntegrationTestBase

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_SCHEDULE_UPDATE_HA_STATE= f'{PATCH_BASE_PATH}.schedule_update_ha_state'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestDreoHeater(IntegrationTestBase):
    """Test Dreo Heaters and PyDreo together."""

    def test_HSH009S(self):  # pylint: disable=invalid-name
        """Load heater and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):

            self.get_devices_file_name = "get_devices_HSH009S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater : PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == 'Heater'

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.hvac_mode is HVACMode.HEAT

            numbers = number.get_entries([pydreo_heater])
            self.verify_expected_entities(numbers, ["Heat Level"])

            sensors = sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(sensors, [])

            with patch(PATCH_SEND_COMMAND) as mock_send_command:  
                heater_ha.set_hvac_mode(HVACMode.AUTO)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})
                mock_send_command.assert_any_call(pydreo_heater, {MODE_KEY: "eco"})

            pydreo_heater.handle_server_update({ REPORTED_KEY: {MODE_KEY: "eco"} })
            assert heater_ha.hvac_mode == HVACMode.AUTO



