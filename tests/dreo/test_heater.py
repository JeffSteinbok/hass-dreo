"""Tests for the Dreo Ceiling heater HA class."""

from custom_components.dreo import climate
from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

from homeassistant.components.climate import (
    HVACMode
)

from custom_components.dreo.pydreo.constant import (
    HEATER_MODE_COOLAIR,
    HEATER_MODE_HOTAIR,
    HEATER_MODE_ECO,
    HEATER_MODE_OFF,
    HEAT_RANGE,
    ECOLEVEL_RANGE,
    HeaterOscillationAngles
)

class TestDreoHeaterHA(TestDeviceBase):
    """Test the Dreo Ceiling heater HA class."""

    def test_ceiling_heater_simple(self):
        """Test the Dreo Ceiling heater HA class."""
        
        mocked_pydreo_heater : PyDreoDeviceMock = self.create_mock_device(name="Test Heater", 
                                                                            serial_number="123456", 
                                                                            features= { "poweron" : True,
                                                                                        "temperature" : 75,
                                                                                        "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
                                                                                        "htalevel": 2,
                                                                                        "ecolevel": 70,
                                                                                        "hvac_mode": HVACMode.HEAT,
                                                                                        "hvac_modes" : [
                                                                                            HEATER_MODE_COOLAIR,
                                                                                            HEATER_MODE_HOTAIR,
                                                                                            HEATER_MODE_ECO,
                                                                                            HEATER_MODE_OFF,
                                                                                        ],
                                                                                        "swing_modes" : [
                                                                                            HeaterOscillationAngles.OSC,
                                                                                            HeaterOscillationAngles.SIXTY,
                                                                                            HeaterOscillationAngles.NINETY,
                                                                                            HeaterOscillationAngles.ONE_TWENTY]})
        
        test_heater = climate.DreoHeaterHA(mocked_pydreo_heater)
        assert test_heater.is_on is True
        assert test_heater.name == "Test Heater"
        assert test_heater.unique_id == "123456-climate"
        assert test_heater.current_temperature == 75
        assert test_heater.hvac_mode == HVACMode.HEAT
        
        # Test HVAC mode changes
        test_heater.set_hvac_mode(HVACMode.OFF)
        assert mocked_pydreo_heater.hvac_mode == HVACMode.OFF
        
        test_heater.set_hvac_mode(HVACMode.HEAT)
        assert mocked_pydreo_heater.hvac_mode == HVACMode.HEAT
        
        test_heater.set_hvac_mode(HVACMode.AUTO)
        assert mocked_pydreo_heater.hvac_mode == HVACMode.AUTO
        
        test_heater.set_hvac_mode(HVACMode.FAN_ONLY)
        assert mocked_pydreo_heater.hvac_mode == HVACMode.FAN_ONLY
        
        # Test available modes
        assert HEATER_MODE_COOLAIR in test_heater.hvac_modes
        assert HEATER_MODE_HOTAIR in test_heater.hvac_modes
        assert HEATER_MODE_ECO in test_heater.hvac_modes
        assert HEATER_MODE_OFF in test_heater.hvac_modes
        
        # Test swing modes
        assert test_heater.swing_modes is not None
        assert len(test_heater.swing_modes) == 4
        
        test_heater.set_swing_mode(HeaterOscillationAngles.SIXTY)
        assert mocked_pydreo_heater.swing_mode == HeaterOscillationAngles.SIXTY
        
        # Test temperature settings (eco level)
        test_heater.set_temperature(temperature=80)
        assert mocked_pydreo_heater.ecolevel == 80
        
        # Test heat level
        assert test_heater.target_temperature is not None or test_heater.target_temperature_high is not None
