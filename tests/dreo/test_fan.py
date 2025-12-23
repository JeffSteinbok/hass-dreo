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
            assert len(entity_list) == 5

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
            assert test_fan.name == "Test Ceiling Fan"
            assert test_fan.unique_id == "123456-fan"

            # Test percentage to speed conversion
            test_fan.set_percentage(20)
            assert mocked_pydreo_fan.fan_speed == 1
            mock_update_ha_state.assert_called_once()
            mock_update_ha_state.reset_mock()

            test_fan.set_percentage(40)
            assert mocked_pydreo_fan.fan_speed == 2
            mock_update_ha_state.assert_called_once()
            mock_update_ha_state.reset_mock()

            test_fan.set_percentage(60)
            assert mocked_pydreo_fan.fan_speed == 3
            mock_update_ha_state.assert_called_once()
            mock_update_ha_state.reset_mock()

            test_fan.set_percentage(100)
            assert mocked_pydreo_fan.fan_speed == 5
            mock_update_ha_state.assert_called_once()
            mock_update_ha_state.reset_mock()

            # Test turning off via percentage
            test_fan.set_percentage(0)
            assert mocked_pydreo_fan.is_on is False

            # Test turn_on and turn_off
            test_fan.turn_on()
            assert mocked_pydreo_fan.is_on is True

            test_fan.turn_off()
            assert mocked_pydreo_fan.is_on is False

            # Test preset modes
            test_fan.set_preset_mode("normal")
            assert mocked_pydreo_fan.preset_mode is "normal"
            mock_update_ha_state.assert_called_once()
            mock_update_ha_state.reset_mock()

            test_fan.set_preset_mode("natural")
            assert mocked_pydreo_fan.preset_mode is "natural"
            
            test_fan.set_preset_mode("sleep")
            assert mocked_pydreo_fan.preset_mode is "sleep"
            
            test_fan.set_preset_mode("auto")
            assert mocked_pydreo_fan.preset_mode is "auto"

            # Verify preset mode list
            assert test_fan.preset_modes == ['normal', 'natural', 'sleep', 'auto']

            # Check to see what switches are added to ceiling fans
            self.verify_expected_entities(switch.get_entries([mocked_pydreo_fan]), [])

            # Check to see what numbers are added to ceiling fans
            self.verify_expected_entities(number.get_entries([mocked_pydreo_fan]), [])

    def test_fan_with_oscillation(self):
        """Test fan with oscillation feature."""
        with patch(PATCH_UPDATE_HA_STATE) as mock_update_ha_state:

            mocked_pydreo_fan : PyDreoDeviceMock = self.create_mock_device( 
                name="Test Tower Fan", 
                serial_number="987654", 
                features= { "is_on" : True,
                            "oscillating" : False,
                            "fan_speed" : 6,
                            "speed_range" : (1, 12) })

            test_fan = fan.DreoFanHA(mocked_pydreo_fan)
            assert test_fan.is_on is True
            assert test_fan.oscillating is False
            assert test_fan.percentage == 50  # 6 out of 12 = 50%
            assert test_fan.speed_count == 12

            # Test oscillation toggle
            test_fan.oscillate(True)
            assert mocked_pydreo_fan.oscillating is True
            mock_update_ha_state.assert_called_once()
            mock_update_ha_state.reset_mock()

            test_fan.oscillate(False)
            assert mocked_pydreo_fan.oscillating is False
            mock_update_ha_state.assert_called_once()

    def test_fan_speed_boundaries(self):
        """Test fan speed boundary conditions."""
        with patch(PATCH_UPDATE_HA_STATE) as mock_update_ha_state:

            mocked_pydreo_fan : PyDreoDeviceMock = self.create_mock_device( 
                name="Test Fan", 
                serial_number="BOUNDARY123", 
                features= { "is_on" : True,
                            "fan_speed" : 1,
                            "speed_range" : (1, 10) })

            test_fan = fan.DreoFanHA(mocked_pydreo_fan)
            
            # Test minimum speed (1% should map to speed 1)
            test_fan.set_percentage(1)
            assert mocked_pydreo_fan.fan_speed == 1
            
            # Test maximum speed (100% should map to speed 10)
            test_fan.set_percentage(100)
            assert mocked_pydreo_fan.fan_speed == 10
            
            # Test mid-range
            test_fan.set_percentage(50)
            assert mocked_pydreo_fan.fan_speed == 5
