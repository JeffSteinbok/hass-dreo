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
            self.verify_expected_entities(sensors, ["Status"])

            with patch(PATCH_SEND_COMMAND) as mock_send_command:  
                heater_ha.set_hvac_mode(HVACMode.AUTO)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})
                mock_send_command.assert_any_call(pydreo_heater, {MODE_KEY: "eco"})

            pydreo_heater.handle_server_update({ REPORTED_KEY: {MODE_KEY: "eco"} })
            assert heater_ha.hvac_mode == HVACMode.AUTO

    def test_HSH003S(self):  # pylint: disable=invalid-name
        """Load heater and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):

            self.get_devices_file_name = "get_devices_HSH003S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater : PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == 'Heater'

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.hvac_mode is HVACMode.AUTO

            numbers = number.get_entries([pydreo_heater])
            self.verify_expected_entities(numbers, ["Heat Level"])

            sensors = sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(sensors, ["Status"])

            with patch(PATCH_SEND_COMMAND) as mock_send_command:  
                heater_ha.set_hvac_mode(HVACMode.AUTO)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})
                mock_send_command.assert_any_call(pydreo_heater, {MODE_KEY: "eco"})

            pydreo_heater.handle_server_update({ REPORTED_KEY: {POWERON_KEY: True} })
            pydreo_heater.handle_server_update({ REPORTED_KEY: {MODE_KEY: "eco"} })
            assert heater_ha.hvac_mode == HVACMode.AUTO            


    def test_HSH034S(self):  # pylint: disable=invalid-name
        """Load heater and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):

            self.get_devices_file_name = "get_devices_HSH034S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater : PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == 'Heater'

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.hvac_mode is HVACMode.OFF

            numbers = number.get_entries([pydreo_heater])
            self.verify_expected_entities(numbers, ["Heat Level"])

            sensors = sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(sensors, ["Status"])

            with patch(PATCH_SEND_COMMAND) as mock_send_command:  
                heater_ha.set_hvac_mode(HVACMode.AUTO)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})
                mock_send_command.assert_any_call(pydreo_heater, {MODE_KEY: "eco"})

            pydreo_heater.handle_server_update({ REPORTED_KEY: {POWERON_KEY: True} })
            pydreo_heater.handle_server_update({ REPORTED_KEY: {MODE_KEY: "eco"} })
            assert heater_ha.hvac_mode == HVACMode.AUTO            




    def test_heater_status_sensor_eco_mode(self):  # pylint: disable=invalid-name
        """Test that the Status sensor correctly handles eco mode."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):

            self.get_devices_file_name = "get_devices_HSH009S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater : PyDreoHeater = self.pydreo_manager.devices[0]
            
            # Get sensors and find the Status sensor
            sensors = sensor.get_entries([pydreo_heater])
            status_sensor = next((s for s in sensors if s.entity_description.key == "Status"), None)
            assert status_sensor is not None, "Status sensor should exist"
            
            # Verify that eco is in the options
            assert "eco" in status_sensor.entity_description.options, "eco should be in Status sensor options"
            
            # Verify all heater modes are in the options
            expected_modes = ["coolair", "hotair", "eco", "off"]
            for mode in expected_modes:
                assert mode in status_sensor.entity_description.options, f"{mode} should be in Status sensor options"
            
            # Test that the sensor correctly reports eco mode
            pydreo_heater.handle_server_update({ REPORTED_KEY: {MODE_KEY: "eco"} })
            assert status_sensor.native_value == "eco", "Status sensor should report eco mode"
