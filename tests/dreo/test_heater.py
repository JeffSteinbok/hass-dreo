"""Tests for the Dreo Ceiling heater HA class."""

from custom_components.dreo import climate
from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

from homeassistant.components.climate import (
    HVACMode,
    ClimateEntityFeature
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

    def test_target_temperature_available_when_off(self):
        """Test that target temperature is available even when device is OFF.
        
        This is a regression test for issue where target temperature showed as 
        unavailable when the device was OFF, even though the device stores the
        target temperature (ecolevel) and it should remain visible to users.
        """
        # Create a heater device that supports ECO mode (and thus has ecolevel/target temp)
        mocked_pydreo_heater : PyDreoDeviceMock = self.create_mock_device(
            name="WH517S Test Heater", 
            serial_number="123456", 
            features={
                "poweron": False,  # Device is OFF
                "temperature": 67,  # Current temperature
                "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
                "htalevel": 3,
                "ecolevel": 72,  # Target temperature stored in device
                "mode": DreoHeaterMode.OFF,  # Mode is OFF
            },
            modes=[
                DreoHeaterMode.COOLAIR,
                DreoHeaterMode.HOTAIR,
                DreoHeaterMode.ECO,
                DreoHeaterMode.OFF,
            ],
            swing_modes=None
        )
        
        test_heater = climate.DreoHeaterHA(mocked_pydreo_heater)
        
        # Verify device is OFF
        assert test_heater.is_on is False
        assert test_heater.hvac_mode == HVACMode.OFF
        
        # Verify target temperature is available (ecolevel is set)
        assert test_heater.target_temperature == 72
        assert mocked_pydreo_heater.ecolevel == 72
        
        # The key assertion: TARGET_TEMPERATURE feature should be supported
        # even when the device is OFF, as long as the device has ecolevel capability
        supported_features = test_heater.supported_features
        assert supported_features & ClimateEntityFeature.TARGET_TEMPERATURE, \
            "TARGET_TEMPERATURE feature should be supported when device has ecolevel, even when OFF"
        
        # Also verify that when we turn the device ON and set to ECO mode,
        # the target temperature is still available
        mocked_pydreo_heater.poweron = True
        mocked_pydreo_heater.mode = DreoHeaterMode.ECO
        test_heater.set_preset_mode(PRESET_ECO)
        
        assert test_heater.preset_mode == PRESET_ECO
        assert test_heater.target_temperature == 72
        supported_features_eco = test_heater.supported_features
        assert supported_features_eco & ClimateEntityFeature.TARGET_TEMPERATURE, \
            "TARGET_TEMPERATURE feature should be supported in ECO mode"

    def test_set_temperature_in_eco_mode(self):
        """Test that target temperature can be set when device is in ECO mode."""
        # Create a heater device in ECO mode
        mocked_pydreo_heater : PyDreoDeviceMock = self.create_mock_device(
            name="WH517S Test Heater ECO", 
            serial_number="123456", 
            features={
                "poweron": True,  # Device is ON
                "temperature": 67,  # Current temperature
                "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
                "htalevel": 3,
                "ecolevel": 72,  # Initial target temperature
                "mode": DreoHeaterMode.ECO,  # Mode is ECO
            },
            modes=[
                DreoHeaterMode.COOLAIR,
                DreoHeaterMode.HOTAIR,
                DreoHeaterMode.ECO,
                DreoHeaterMode.OFF,
            ],
            swing_modes=None
        )
        
        test_heater = climate.DreoHeaterHA(mocked_pydreo_heater)
        
        # Verify device is in ECO mode
        assert test_heater.is_on is True
        assert test_heater.hvac_mode == HVACMode.HEAT  # ECO maps to HEAT
        assert test_heater.preset_mode == PRESET_ECO
        
        # Verify target temperature is initially 72
        assert test_heater.target_temperature == 72
        
        # Set a new target temperature
        from homeassistant.components.climate import ATTR_TEMPERATURE
        test_heater.set_temperature(**{ATTR_TEMPERATURE: 80})
        
        # Verify the target temperature was updated
        assert mocked_pydreo_heater.ecolevel == 80
        assert test_heater.target_temperature == 80

    def test_set_temperature_in_off_mode(self):
        """Test that set_temperature sends a command to the device even when in OFF mode.

        Regression test: previously the else branch hardcoded _attr_target_temperature=4
        and never called self.device.ecolevel, so no command reached the device.
        """
        mocked_pydreo_heater : PyDreoDeviceMock = self.create_mock_device(
            name="WH517S Test Heater OFF",
            serial_number="123456",
            features={
                "poweron": False,
                "temperature": 67,
                "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
                "htalevel": 3,
                "ecolevel": 72,
                "mode": DreoHeaterMode.OFF,
            },
            modes=[
                DreoHeaterMode.COOLAIR,
                DreoHeaterMode.HOTAIR,
                DreoHeaterMode.ECO,
                DreoHeaterMode.OFF,
            ],
            swing_modes=None
        )

        test_heater = climate.DreoHeaterHA(mocked_pydreo_heater)

        assert test_heater.hvac_mode == HVACMode.OFF

        from homeassistant.components.climate import ATTR_TEMPERATURE
        test_heater.set_temperature(**{ATTR_TEMPERATURE: 80})

        # The command must reach the device (ecolevel updated), not silently dropped
        assert mocked_pydreo_heater.ecolevel == 80
        assert test_heater.target_temperature == 80

    def test_set_temperature_in_fan_only_mode(self):
        """Test that set_temperature sends a command to the device when in FAN_ONLY mode.

        Regression test: previously the else branch hardcoded _attr_target_temperature=4
        and never called self.device.ecolevel, so no command reached the device.
        """
        mocked_pydreo_heater : PyDreoDeviceMock = self.create_mock_device(
            name="WH517S Test Heater FAN_ONLY",
            serial_number="123456",
            features={
                "poweron": True,
                "temperature": 67,
                "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
                "htalevel": None,
                "ecolevel": 72,
                "mode": DreoHeaterMode.COOLAIR,
            },
            modes=[
                DreoHeaterMode.COOLAIR,
                DreoHeaterMode.HOTAIR,
                DreoHeaterMode.ECO,
                DreoHeaterMode.OFF,
            ],
            swing_modes=None
        )

        test_heater = climate.DreoHeaterHA(mocked_pydreo_heater)

        assert test_heater.hvac_mode == HVACMode.FAN_ONLY

        from homeassistant.components.climate import ATTR_TEMPERATURE
        test_heater.set_temperature(**{ATTR_TEMPERATURE: 78})

        # The command must reach the device (ecolevel updated), not silently dropped
        assert mocked_pydreo_heater.ecolevel == 78
        assert test_heater.target_temperature == 78

    def test_set_temperature_rounds_instead_of_truncating(self):
        """Test that set_temperature rounds fractional Fahrenheit values instead of truncating.

        When HA is configured in Celsius and the entity uses Fahrenheit,
        HA converts the user's Celsius input to Fahrenheit before calling set_temperature.
        For example, 21°C = 69.8°F. Using int() would truncate to 69°F (≈20.6°C),
        but round() correctly gives 70°F (≈21.1°C).
        """
        mocked_pydreo_heater : PyDreoDeviceMock = self.create_mock_device(
            name="HSH003S Test Heater",
            serial_number="123456",
            features={
                "poweron": True,
                "temperature": 67,
                "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
                "htalevel": 3,
                "ecolevel": 72,
                "mode": DreoHeaterMode.ECO,
            },
            modes=[
                DreoHeaterMode.COOLAIR,
                DreoHeaterMode.HOTAIR,
                DreoHeaterMode.ECO,
                DreoHeaterMode.OFF,
            ],
            swing_modes=None
        )

        test_heater = climate.DreoHeaterHA(mocked_pydreo_heater)

        from homeassistant.components.climate import ATTR_TEMPERATURE

        # 21°C = 69.8°F - should round to 70, not truncate to 69
        test_heater.set_temperature(**{ATTR_TEMPERATURE: 69.8})
        assert mocked_pydreo_heater.ecolevel == 70
        assert test_heater.target_temperature == 70

        # 25°C = 77°F - exact conversion, no rounding needed
        test_heater.set_temperature(**{ATTR_TEMPERATURE: 77.0})
        assert mocked_pydreo_heater.ecolevel == 77
        assert test_heater.target_temperature == 77

        # 18°C = 64.4°F - should round to 64, not truncate to 64 (same result here)
        test_heater.set_temperature(**{ATTR_TEMPERATURE: 64.4})
        assert mocked_pydreo_heater.ecolevel == 64
        assert test_heater.target_temperature == 64

        # 22°C = 71.6°F - should round to 72, not truncate to 71
        test_heater.set_temperature(**{ATTR_TEMPERATURE: 71.6})
        assert mocked_pydreo_heater.ecolevel == 72
        assert test_heater.target_temperature == 72
