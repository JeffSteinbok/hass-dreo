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

            # Check to see what sensors are added - should include Target Humidity
            sensors = sensor.get_entries([pydreo_humidifier])
            
            # Find the Target Humidity sensor
            target_humidity_sensor = None
            for s in sensors:
                if s.entity_description.key == "Target Humidity":
                    target_humidity_sensor = s
                    break
            
            assert target_humidity_sensor is not None, "Target Humidity sensor should exist"
            assert target_humidity_sensor.native_value == 60, "Target Humidity sensor value should be 60"
            
            self.verify_expected_entities(sensors, ["Humidity", "Target Humidity", "Status", "Water Level", "Ambient Light Humidifier", "Use since cleaning"])


    def test_HHM014S(self):  # pylint: disable=invalid-name
        """Load HHM014S humidifier and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):

            self.get_devices_file_name = "get_devices_HHM014S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1
            
            pydreo_humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
            assert pydreo_humidifier.type == 'Humidifier'
            assert pydreo_humidifier.humidity == 52
            assert pydreo_humidifier.model == "DR-HHM014S"
            assert pydreo_humidifier.series_name == "HM774S"

            ha_humidifier = humidifier.DreoHumidifierHA(pydreo_humidifier)
            assert ha_humidifier.is_on is True
            assert ha_humidifier.current_humidity == 52
            assert ha_humidifier.target_humidity == 55
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

            # Check to see what sensors are added - should include Target Humidity
            sensors = sensor.get_entries([pydreo_humidifier])
            
            # Find the Target Humidity sensor
            target_humidity_sensor = None
            for s in sensors:
                if s.entity_description.key == "Target Humidity":
                    target_humidity_sensor = s
                    break
            
            assert target_humidity_sensor is not None, "Target Humidity sensor should exist for HHM014S"
            assert target_humidity_sensor.native_value == 55, "Target Humidity sensor value should be 55 for HHM014S"
            self.verify_expected_entities(sensors, ["Humidity", "Status", "Water Level", "Ambient Light Humidifier", "Use since cleaning", "Target Humidity"])

    def test_HHM003S(self):  # pylint: disable=invalid-name
        """Load HHM003S (HM713S/813S) humidifier and test all features including humidity sensors."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):

            self.get_devices_file_name = "get_devices_HHM003S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1
            
            pydreo_humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
            assert pydreo_humidifier.type == 'Humidifier'
            assert pydreo_humidifier.humidity == 40
            assert pydreo_humidifier.model == "DR-HHM003S"
            assert pydreo_humidifier.series_name == "HM713S/813S"

            ha_humidifier = humidifier.DreoHumidifierHA(pydreo_humidifier)
            assert ha_humidifier.is_on is False  # Device is off in test data
            assert ha_humidifier.current_humidity == 40
            assert ha_humidifier.target_humidity == 50
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

            # Check to see what sensors are added - should include Humidity, Target Humidity, and worktime
            sensors = sensor.get_entries([pydreo_humidifier])
            
            # Find the Humidity sensor
            humidity_sensor = None
            for s in sensors:
                if s.entity_description.key == "Humidity":
                    humidity_sensor = s
                    break
            
            assert humidity_sensor is not None, "Humidity sensor should exist for HHM003S"
            assert humidity_sensor.native_value == 40, "Humidity sensor value should be 40 for HHM003S"
            
            # Find the Target Humidity sensor
            target_humidity_sensor = None
            for s in sensors:
                if s.entity_description.key == "Target Humidity":
                    target_humidity_sensor = s
                    break
            
            assert target_humidity_sensor is not None, "Target Humidity sensor should exist for HHM003S"
            assert target_humidity_sensor.native_value == 50, "Target Humidity sensor value should be 50 for HHM003S"
            
            # Find the Use since cleaning sensor
            worktime_sensor = None
            for s in sensors:
                if s.entity_description.key == "Use since cleaning" and s.entity_description.translation_key == "use_hours_HM":
                    worktime_sensor = s
                    break
            
            assert worktime_sensor is not None, "Use since cleaning sensor should exist for HHM003S"
            assert worktime_sensor.native_value == 10, "Use since cleaning sensor value should be 10 for HHM003S"
            
            self.verify_expected_entities(sensors, ["Humidity", "Status", "Water Level", "Ambient Light Humidifier", "Use since cleaning", "Target Humidity"])

        
