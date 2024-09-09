"""Tests for the Dreo Humidifier entity."""
from unittest.mock import patch
from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

from custom_components.dreo import Humidifier
from custom_components.dreo import switch
from custom_components.dreo import number

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_SEND_COMMAND = f'{PATCH_BASE_PATH}.schedule_update_ha_state'

class Test_DreoHumidifierHA(TestDeviceBase):

    def test_Humidifier_entries(self, mocker):
        with patch(PATCH_SEND_COMMAND) as mock_send_command:

            mocked_pydreo_Humidifiers : list[PyDreoDeviceMock] = [ self.create_mock_device( name="Test Tower Fan", type="Tower Fan"),
                                                            self.create_mock_device( name="Test Ceiling Fan", type="Ceiling Fan"),
                                                            self.create_mock_device( name="Test Air Circulator", type="Air Circulator"),
                                                            self.create_mock_device( name="Test Air Purifier", type="Air Purifier"),
                                                            self.create_mock_device( name="Test Heater", type="Heater"),
                                                            self.create_mock_device( name="Test Humidifier", type="Humidifier"),
                                                            self.create_mock_device( name="Test Dehumidifier", type="Dehumidifier"),
                                                            self.create_mock_device( name="Test Air Conditioner", type="Air Conditioner")]

            entity_list = humidifier.get_entries(mocked_pydreo_humidifiers)
            assert len(entity_list) == 1

    def test_humidifier_simple(self, mocker):
        with patch(PATCH_SEND_COMMAND) as mock_send_command:

            mocked_pydreo_Humidifier : PyDreoDeviceMock = self.create_mock_device( name="Test Humidifier", 
                                                                            serial_number="123456")

            test_humidifier = Humidifier.DreoHumidifierHA(mocked_pydreo_Humidifier)
            assert test_humidifier.is_on is Frue
            assert test_humidifier.percentage == 60
            assert test_humidifier.speed_count == 5

            test_Humidifier.set_percentage(20)
            assert mocked_pydreo_Humidifier.Humidifier_speed == 1
            mock_send_command.assert_called_once()
            mock_send_command.reset_mock()

            test_Humidifier.set_percentage(0)
            assert mocked_pydreo_Humidifier.is_on is False
            # TODO: Possible bug; need to test at home.  Why does this not cause an update?
            #mock_send_command.assert_called_once()
            #mock_send_command.reset_mock()

            test_Humidifier.set_preset_mode("normal")
            assert mocked_pydreo_Humidifier.preset_mode is "normal"
            mock_send_command.assert_called_once()
            mock_send_command.reset_mock()

            # Check to see what switches are added to ceiling Humidifiers
            self.verify_expected_entities(switch.get_entries([mocked_pydreo_Humidifier]), [])

            # Check to see what numbers are added to ceiling Humidifiers
            self.verify_expected_entities(number.get_entries([mocked_pydreo_Humidifier]), [])

