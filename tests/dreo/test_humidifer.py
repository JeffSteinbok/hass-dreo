"""Tests for the Dreo Humidifier entity."""
from unittest.mock import patch
from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

from custom_components.dreo import humidifier
from custom_components.dreo import switch
from custom_components.dreo import number

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_UPDATE_HA_STATE = f'{PATCH_BASE_PATH}.schedule_update_ha_state'

class Test_DreoHumidifierHA(TestDeviceBase):

    def test_humidifier_entries(self, mocker):
        mocked_pydreo_devices : list[PyDreoDeviceMock] = [ self.create_mock_device( name="Test Tower Fan", type="Tower Fan"),
                                                        self.create_mock_device( name="Test Ceiling Fan", type="Ceiling Fan"),
                                                        self.create_mock_device( name="Test Air Circulator", type="Air Circulator"),
                                                        self.create_mock_device( name="Test Air Purifier", type="Air Purifier"),
                                                        self.create_mock_device( name="Test Heater", type="Heater"),
                                                        self.create_mock_device( name="Test Humidifier", type="Humidifier"),
                                                        self.create_mock_device( name="Test Dehumidifier", type="Dehumidifier"),
                                                        self.create_mock_device( name="Test Air Conditioner", type="Air Conditioner")]

        entity_list = humidifier.get_entries(mocked_pydreo_devices)
        assert len(entity_list) == 1

    def test_humidifier_simple(self, mocker):
        with patch(PATCH_UPDATE_HA_STATE) as mock_update_ha_state:

            mocked_pydreo_humidifier : PyDreoDeviceMock = self.create_mock_device( name="Test Humidifier", 
                                                                                   serial_number="123456",
                                                                                   features= { "is_on" : True,
                                                                                               "mode" : "sleep",
                                                                                               "modes" : ['manual', 'auto', 'sleep']})
            
            test_humidifier = humidifier.DreoHumidifierHA(mocked_pydreo_humidifier)
            assert test_humidifier.is_on is True
            assert test_humidifier.available_modes == [ "manual", "auto", "sleep" ]
            
            test_humidifier.set_mode("auto")
            assert mocked_pydreo_humidifier.mode == "auto"

            # Check to see what switches are added to ceiling Humidifiers
            self.verify_expected_entities(switch.get_entries([mocked_pydreo_humidifier]), [])

            # Check to see what numbers are added to ceiling Humidifiers
            self.verify_expected_entities(number.get_entries([mocked_pydreo_humidifier]), [])

