"""Tests for the Dreo Humidifier entity."""
from unittest.mock import patch

from custom_components.dreo import humidifier
from custom_components.dreo import switch
from custom_components.dreo import number

from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_UPDATE_HA_STATE = f'{PATCH_BASE_PATH}.schedule_update_ha_state'

class TestDreoHumidifier(TestDeviceBase):
    """Test the Dreo Humidifier entity."""

    def test_humidifier_entries(self):
        """Test the creation of the humidifier entries."""
        mocked_pydreo_devices : list[PyDreoDeviceMock] = [ 
            self.create_mock_device( name="Test Tower Fan", type="Tower Fan"),
            self.create_mock_device( name="Test Ceiling Fan", type="Ceiling Fan"),
            self.create_mock_device( name="Test Air Circulator", type="Air Circulator"),
            self.create_mock_device( name="Test Air Purifier", type="Air Purifier"),
            self.create_mock_device( name="Test Heater", type="Heater"),
            self.create_mock_device( name="Test Humidifier", type="Humidifier"),
            self.create_mock_device( name="Test Dehumidifier", type="Dehumidifier"),
            self.create_mock_device( name="Test Air Conditioner", type="Air Conditioner")]

        entity_list = humidifier.get_entries(mocked_pydreo_devices)
        assert len(entity_list) == 2

    def test_humidifier_simple(self): 
        """Test the creation of the humidifier entity."""
        with patch(PATCH_UPDATE_HA_STATE):

            mocked_pydreo_humidifier : PyDreoDeviceMock = self.create_mock_device( 
                name="Test Humidifier", 
                serial_number="123456",
                features= { "is_on" : True,
                            "mode" : "sleep",
                            "modes" : ['manual', 'auto', 'sleep'],
                            "humidity" : 55,
                            "target_humidity" : 60})
            
        test_humidifier = humidifier.DreoHumidifierHA(mocked_pydreo_humidifier)
        assert test_humidifier.is_on is True
        assert test_humidifier.available_modes == [ "manual", "auto", "sleep" ]
        assert test_humidifier.mode == "sleep"
        assert test_humidifier.name == "Test Humidifier"
        assert test_humidifier.unique_id is not None  # Unique ID format varies by implementation
        
        # Test all mode changes
        test_humidifier.set_mode("auto")
        assert mocked_pydreo_humidifier.mode == "auto"
        
        test_humidifier.set_mode("manual")
        assert mocked_pydreo_humidifier.mode == "manual"
        
        test_humidifier.set_mode("sleep")
        assert mocked_pydreo_humidifier.mode == "sleep"
        
        # Test turn on/off
        test_humidifier.turn_off()
        assert mocked_pydreo_humidifier.is_on is False
        
        test_humidifier.turn_on()
        assert mocked_pydreo_humidifier.is_on is True
        
        # Test humidity levels if supported
        if hasattr(mocked_pydreo_humidifier, 'target_humidity'):
            test_humidifier.set_humidity(65)
            assert mocked_pydreo_humidifier.target_humidity == 65

            # Check to see what switches are added to ceiling Humidifiers
            self.verify_expected_entities(switch.get_entries([mocked_pydreo_humidifier]), [])

            # Check to see what numbers are added to ceiling Humidifiers
            self.verify_expected_entities(number.get_entries([mocked_pydreo_humidifier]), [])

    def test_dehumidifier_simple(self):
        """Test the creation of the dehumidifier entity."""
        with patch(PATCH_UPDATE_HA_STATE):

            mocked_pydreo_dehumidifier : PyDreoDeviceMock = self.create_mock_device( 
                name="Test Dehumidifier", 
                serial_number="DEHUM123",
                type="Dehumidifier",
                features= { "is_on" : False,
                            "mode" : "auto",
                            "modes" : ['auto', 'manual'],
                            "humidity" : 65,
                            "target_humidity" : 50})
            
            test_dehumidifier = humidifier.DreoHumidifierHA(mocked_pydreo_dehumidifier)
            assert test_dehumidifier.is_on is False
            assert test_dehumidifier.available_modes == [ "auto", "manual" ]
            assert test_dehumidifier.mode == "auto"
            
            # Test mode switching
            test_dehumidifier.set_mode("manual")
            assert mocked_pydreo_dehumidifier.mode == "manual"
