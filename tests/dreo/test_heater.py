"""Tests for the Dreo Ceiling heater HA class."""

from custom_components.dreo import climate
from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

from homeassistant.components.climate import (
    HVACMode
)

from custom_components.dreo.pydreo.constant import (
    HEAT_RANGE,
    ECOLEVEL_RANGE,
    PRESET_ECO,
    HeaterOscillationAngles,
    DreoHeaterMode
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
                                                                                        "mode": DreoHeaterMode.HOTAIR,  # Use string mode instead of HVACMode enum
                                                                            },
                                                                            modes = [
                                                                                DreoHeaterMode.COOLAIR,
                                                                                DreoHeaterMode.HOTAIR,
                                                                                DreoHeaterMode.ECO,
                                                                                DreoHeaterMode.OFF,
                                                                            ],
                                                                            swing_modes = [
                                                                                HeaterOscillationAngles.OSC,
                                                                                HeaterOscillationAngles.SIXTY,
                                                                                HeaterOscillationAngles.NINETY,
                                                                                HeaterOscillationAngles.ONE_TWENTY])
        
        test_heater = climate.DreoHeaterHA(mocked_pydreo_heater)
        assert test_heater.is_on is True
        assert test_heater.name == "Heater"  # DreoHeaterHA sets name to "Heater" not device name
        assert test_heater.unique_id is not None
        assert test_heater.current_temperature == 75
        assert test_heater.hvac_mode == HVACMode.HEAT
        
        # Test HVAC mode changes
        test_heater.set_hvac_mode(HVACMode.OFF)
        assert mocked_pydreo_heater.mode == DreoHeaterMode.OFF
        
        test_heater.set_hvac_mode(HVACMode.HEAT)
        assert mocked_pydreo_heater.mode == DreoHeaterMode.HOTAIR
        
        test_heater.set_preset_mode(PRESET_ECO)
        assert mocked_pydreo_heater.mode == DreoHeaterMode.ECO
        
        test_heater.set_hvac_mode(HVACMode.FAN_ONLY)
        assert mocked_pydreo_heater.mode == DreoHeaterMode.COOLAIR
        
        # Test heat level presets (H1, H2, H3)
        assert "H1" in test_heater.preset_modes
        assert "H2" in test_heater.preset_modes
        assert "H3" in test_heater.preset_modes
        
        # Test setting H1 preset
        test_heater.set_preset_mode("H1")
        assert mocked_pydreo_heater.htalevel == 1
        assert mocked_pydreo_heater.mode == DreoHeaterMode.HOTAIR
        
        # Test setting H2 preset
        test_heater.set_preset_mode("H2")
        assert mocked_pydreo_heater.htalevel == 2
        assert mocked_pydreo_heater.mode == DreoHeaterMode.HOTAIR
        
        # Test setting H3 preset
        test_heater.set_preset_mode("H3")
        assert mocked_pydreo_heater.htalevel == 3
        assert mocked_pydreo_heater.mode == DreoHeaterMode.HOTAIR
        
        # Test that preset mode reflects heat level when in HOTAIR mode
        mocked_pydreo_heater.htalevel = 1
        mocked_pydreo_heater.mode = DreoHeaterMode.HOTAIR
        assert test_heater.preset_mode == "H1"
        
        mocked_pydreo_heater.htalevel = 2
        assert test_heater.preset_mode == "H2"
        
        mocked_pydreo_heater.htalevel = 3
        assert test_heater.preset_mode == "H3"
