"""Tests for the Dreo Ceiling Fan HA class."""
from unittest.mock import MagicMock

from custom_components.dreo import fan
from custom_components.dreo import switch
from custom_components.dreo import number
from custom_components.dreo import light
from custom_components.dreo import sensor
from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

class TestDreoCeilingFanHA(TestDeviceBase):
    """Test the Dreo Ceiling Fan HA class."""

    def test_ceiling_fan_simple(self, mock_update_ha_state: MagicMock):
        """Test the Dreo Ceiling Fan HA class."""
        
        mocked_pydreo_ceilingfan : PyDreoDeviceMock = self.create_mock_device(name="Test Ceiling Fan", 
                                                                              serial_number="123456", 
                                                                              features= { "is_on" : True,
                                                                                          "preset_modes" : ['normal', 'natural', 'sleep', 'auto'],
                                                                                          "fan_speed" : 3,
                                                                                          "light_on" : True,
                                                                                          "brightness" : 50,
                                                                                          "color_temperature" : 25,
                                                                                          "speed_range" : (1, 5) })
        
        test_fan = fan.DreoFanHA(mocked_pydreo_ceilingfan)
        assert test_fan.is_on is True
        assert test_fan.percentage == 60
        assert test_fan.speed_count == 5
        assert test_fan.name == "Test Ceiling Fan"
        assert test_fan.unique_id is not None  # Unique ID format varies by implementation

        # Test percentage calculations
        test_fan.set_percentage(20)
        assert mocked_pydreo_ceilingfan.fan_speed == 1
        mock_update_ha_state.assert_called_once()
        mock_update_ha_state.reset_mock()

        test_fan.set_percentage(40)
        assert mocked_pydreo_ceilingfan.fan_speed == 2
        mock_update_ha_state.reset_mock()
        
        test_fan.set_percentage(80)
        assert mocked_pydreo_ceilingfan.fan_speed == 4
        mock_update_ha_state.reset_mock()
        
        test_fan.set_percentage(100)
        assert mocked_pydreo_ceilingfan.fan_speed == 5
        mock_update_ha_state.reset_mock()

        # Test turning off via percentage
        test_fan.set_percentage(0)
        assert mocked_pydreo_ceilingfan.is_on is False
        mock_update_ha_state.reset_mock()

        # Test turn_on and turn_off methods
        test_fan.turn_on()
        assert mocked_pydreo_ceilingfan.is_on is True
        
        test_fan.turn_off()
        assert mocked_pydreo_ceilingfan.is_on is False

        # Test all preset modes
        test_fan.set_preset_mode("normal")
        assert mocked_pydreo_ceilingfan.preset_mode is "normal"

        test_fan.set_preset_mode("natural")
        assert mocked_pydreo_ceilingfan.preset_mode is "natural"
        
        test_fan.set_preset_mode("sleep")
        assert mocked_pydreo_ceilingfan.preset_mode is "sleep"
        
        test_fan.set_preset_mode("auto")
        assert mocked_pydreo_ceilingfan.preset_mode is "auto"

        # Check to see what switches are added to ceiling fans
        self.verify_expected_entities(switch.get_entries([mocked_pydreo_ceilingfan]), [])

        # Check to see what lights are added to ceiling fans
        light_entities = light.get_entries([mocked_pydreo_ceilingfan])
        self.verify_expected_entities(light_entities, ["Light"])
        
        # Verify light entity exists and has basic properties
        assert len(light_entities) == 1
        light_entity = light_entities[0]
        assert light_entity is not None

        # Check to see what numbers are added to ceiling fans
        self.verify_expected_entities(number.get_entries([mocked_pydreo_ceilingfan]), [])

        # Check to see what sensors are added to ceiling fans
        self.verify_expected_entities(sensor.get_entries([mocked_pydreo_ceilingfan]), [])