"""Integration Tests for Dreo Ceiling Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import number
from custom_components.dreo import humidifier
from custom_components.dreo import sensor
from homeassistant.components.humidifier import HumidifierEntityFeature

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

            # Check to see what sensors are added
            sensors = sensor.get_entries([pydreo_humidifier])
            self.verify_expected_entities(sensors, ["Humidity", "Water Level", "Ambient Light Humidifier", "Use since cleaning HM"])


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

            # Check to see what sensors are added
            sensors = sensor.get_entries([pydreo_humidifier])
            self.verify_expected_entities(sensors, ["Humidity", "Water Level", "Ambient Light Humidifier", "Use since cleaning HM"])

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

            # Check to see what sensors are added - should include Humidity, and worktime
            sensors = sensor.get_entries([pydreo_humidifier])
            
            # Find the Humidity sensor
            humidity_sensor = None
            for s in sensors:
                if s.entity_description.key == "Humidity":
                    humidity_sensor = s
                    break
            
            assert humidity_sensor is not None, "Humidity sensor should exist for HHM003S"
            assert humidity_sensor.native_value == 40, "Humidity sensor value should be 40 for HHM003S"
            
            # Find the Use since cleaning sensor
            worktime_sensor = None
            for s in sensors:
                if s.entity_description.key == "Use since cleaning HM" and s.entity_description.translation_key == "use_hours_HM":
                    worktime_sensor = s
                    break
            
            assert worktime_sensor is not None, "Use since cleaning sensor should exist for HHM003S"
            assert worktime_sensor.native_value == 10, "Use since cleaning sensor value should be 10 for HHM003S"
            
            self.verify_expected_entities(sensors, ["Humidity", "Water Level", "Ambient Light Humidifier", "Use since cleaning HM"])

    def test_HHM015S(self):  # pylint: disable=invalid-name
        """Load HHM015S (HM755S) humidifier and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):

            self.get_devices_file_name = "get_devices_HHM015S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
            assert pydreo_humidifier.type == 'Humidifier'
            assert pydreo_humidifier.humidity == 31
            assert pydreo_humidifier.model == "DR-HHM015S"
            assert pydreo_humidifier.series_name == "HM755S"

            ha_humidifier = humidifier.DreoHumidifierHA(pydreo_humidifier)
            assert ha_humidifier.is_on is False
            assert ha_humidifier.current_humidity == 31
            assert ha_humidifier.target_humidity == 60
            assert ha_humidifier.unique_id is not None
            assert ha_humidifier.name is not None

            # HHM015S has no modes — available_modes should be None (not empty list)
            # and supported_features should not include MODES
            assert ha_humidifier.available_modes is None
            assert not (ha_humidifier.supported_features & HumidifierEntityFeature.MODES)

            # Check to see what numbers are added to humidifiers
            numbers = number.get_entries([pydreo_humidifier])
            self.verify_expected_entities(numbers, [])

            # Check to see what sensors are added
            sensors = sensor.get_entries([pydreo_humidifier])
            self.verify_expected_entities(sensors, ["Humidity", "Water Level", "Ambient Light Humidifier", "Use since cleaning HM"])

    def test_HHM006S(self):  # pylint: disable=invalid-name
        """Load HHM006S (HM306S) humidifier and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):

            self.get_devices_file_name = "get_devices_HHM006S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
            assert pydreo_humidifier.type == 'Humidifier'
            assert pydreo_humidifier.humidity == 65
            assert pydreo_humidifier.model == "DR-HHM006S"
            assert pydreo_humidifier.series_name == "HM306S"

            ha_humidifier = humidifier.DreoHumidifierHA(pydreo_humidifier)
            assert ha_humidifier.is_on is False  # Device is off in test data
            assert ha_humidifier.current_humidity == 65
            assert ha_humidifier.target_humidity == 55
            assert ha_humidifier.unique_id is not None
            assert ha_humidifier.name is not None

            # Test modes - HHM006S supports manual/auto/sleep
            assert ha_humidifier.available_modes is not None
            assert len(ha_humidifier.available_modes) == 3
            assert "manual" in ha_humidifier.available_modes
            assert "auto" in ha_humidifier.available_modes
            assert "sleep" in ha_humidifier.available_modes
            assert ha_humidifier.mode == "auto"  # mode=1 in test data

            # Check to see what numbers are added to humidifiers
            numbers = number.get_entries([pydreo_humidifier])
            self.verify_expected_entities(numbers, [])

            # Check to see what sensors are added
            sensors = sensor.get_entries([pydreo_humidifier])
            self.verify_expected_entities(sensors, ["Humidity", "Water Level", "Ambient Light Humidifier", "Use since cleaning HM"])

    def test_HHM003S_mode_changes(self):  # pylint: disable=invalid-name
        """Test that HHM003S (HM713S/813S) mode changes call schedule_update_ha_state."""
        
        self.get_devices_file_name = "get_devices_HHM003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        
        pydreo_humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
        ha_humidifier = humidifier.DreoHumidifierHA(pydreo_humidifier)
        
        # Mock _send_command to avoid transport errors
        with patch.object(pydreo_humidifier, '_send_command'):
            # Mock schedule_update_ha_state to verify it's called
            with patch.object(ha_humidifier, 'schedule_update_ha_state') as mock_schedule:
                # Test turn_on
                ha_humidifier.turn_on()
                mock_schedule.assert_called()
                mock_schedule.reset_mock()
                
                # Test turn_off
                ha_humidifier.turn_off()
                mock_schedule.assert_called()
                mock_schedule.reset_mock()
                
                # Test set_mode
                ha_humidifier.set_mode('sleep')
                mock_schedule.assert_called()
                mock_schedule.reset_mock()
                
                # Test set_humidity
                ha_humidifier.set_humidity(60)
                mock_schedule.assert_called()

        
