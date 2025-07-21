"""Tests for the Dreo Fan entity."""
from unittest.mock import patch

from custom_components.dreo import fan
from custom_components.dreo import switch
from custom_components.dreo import number

from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_UPDATE_HA_STATE = f'{PATCH_BASE_PATH}.schedule_update_ha_state'

class TestDreoFanHA(TestDeviceBase):
    """Test the Dreo Fan entity."""

    def test_fan_entries(self):
        """Test the creation of the fan entries."""

        with patch(PATCH_UPDATE_HA_STATE):

            mocked_pydreo_fans : list[PyDreoDeviceMock] = [ self.create_mock_device( name="Test Tower Fan", type="Tower Fan"),
                                                            self.create_mock_device( name="Test Ceiling Fan", type="Ceiling Fan"),
                                                            self.create_mock_device( name="Test Air Circulator", type="Air Circulator"),
                                                            self.create_mock_device( name="Test Air Purifier", type="Air Purifier"),
                                                            self.create_mock_device( name="Test Heater", type="Heater"),
                                                            self.create_mock_device( name="Test Humidifier", type="Humidifier"),
                                                            self.create_mock_device( name="Test Dehumidifier", type="Dehumidifier"),
                                                            self.create_mock_device( name="Test Air Conditioner", type="Air Conditioner")]

            entity_list = fan.get_entries(mocked_pydreo_fans)
            assert len(entity_list) == 4

    def test_fan_simple(self):
        """Test the creation of the fan entity."""
        with patch(PATCH_UPDATE_HA_STATE) as mock_update_ha_state:

            mocked_pydreo_fan : PyDreoDeviceMock = self.create_mock_device( name="Test Ceiling Fan", 
                                                                            serial_number="123456", 
                                                                            features= { "is_on" : True,
                                                                                        "preset_modes" : ['normal', 'natural', 'sleep', 'auto'],
                                                                                        "fan_speed" : 3,
                                                                                        "speed_range" : (1, 5) })

            test_fan = fan.DreoFanHA(mocked_pydreo_fan)
            assert test_fan.is_on is True
            assert test_fan.percentage == 60
            assert test_fan.speed_count == 5

            test_fan.set_percentage(20)
            assert mocked_pydreo_fan.fan_speed == 1
            mock_update_ha_state.assert_called_once()
            mock_update_ha_state.reset_mock()

            test_fan.set_percentage(0)
            assert mocked_pydreo_fan.is_on is False

            test_fan.set_preset_mode("normal")
            assert mocked_pydreo_fan.preset_mode is "normal"
            mock_update_ha_state.assert_called_once()
            mock_update_ha_state.reset_mock()

            # Check to see what switches are added to ceiling fans
            self.verify_expected_entities(switch.get_entries([mocked_pydreo_fan]), [])

            # Check to see what numbers are added to ceiling fans
            self.verify_expected_entities(number.get_entries([mocked_pydreo_fan]), [])
