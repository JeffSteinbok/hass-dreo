"""Tests for the Dreo Ceiling heater HA class."""

import pytest
from custom_components.dreo import climate
from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

from homeassistant.components.climate import (
    HVACMode,
    ClimateEntityFeature,
    SWING_OFF,
    SWING_ON,
    PRESET_NONE,
    ATTR_TEMPERATURE,
)

from custom_components.dreo.pydreo.constant import (
    HEAT_RANGE,
    ECOLEVEL_RANGE,
    PRESET_ECO,
    HeaterOscillationAngles,
    DreoHeaterMode,
    ANGLE_OSCANGLE_MAP,
    OSCANGLE_ANGLE_MAP,
)


class TestDreoHeaterHA(TestDeviceBase):
    """Test the Dreo Ceiling heater HA class."""

    def test_ceiling_heater_simple(self):
        """Test the Dreo Ceiling heater HA class."""

        mocked_pydreo_heater: PyDreoDeviceMock = self.create_mock_device(
            name="Test Heater",
            serial_number="123456",
            features={
                "poweron": True,
                "temperature": 75,
                "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
                "htalevel": 2,
                "ecolevel": 70,
                "mode": DreoHeaterMode.HOTAIR,  # Use string mode instead of HVACMode enum
            },
            modes=[
                DreoHeaterMode.COOLAIR,
                DreoHeaterMode.HOTAIR,
                DreoHeaterMode.ECO,
                DreoHeaterMode.OFF,
            ],
            swing_modes=[
                HeaterOscillationAngles.OSC,
                HeaterOscillationAngles.SIXTY,
                HeaterOscillationAngles.NINETY,
                HeaterOscillationAngles.ONE_TWENTY,
            ],
        )

        test_heater = climate.DreoHeaterHA(mocked_pydreo_heater)
        assert test_heater.is_on is True
        assert test_heater.name == "Heater"  # DreoHeaterHA sets name to "Heater" not device name
        assert test_heater.unique_id is not None
        assert test_heater.current_temperature == 75
        assert test_heater.hvac_mode == HVACMode.HEAT

        # Test HVAC mode changes: turning off must NOT change the mode to "off".
        # The last known active mode is preserved so that when the device powers
        # back on, hvac_mode can correctly reflect the active mode.
        test_heater.set_hvac_mode(HVACMode.OFF)
        assert mocked_pydreo_heater.poweron is False
        assert mocked_pydreo_heater.mode != DreoHeaterMode.OFF, (
            "set_hvac_mode(OFF) must not set mode to 'off'; "
            "the last known active mode must be preserved"
        )

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
        mocked_pydreo_heater: PyDreoDeviceMock = self.create_mock_device(
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
            swing_modes=None,
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
        assert supported_features & ClimateEntityFeature.TARGET_TEMPERATURE, (
            "TARGET_TEMPERATURE feature should be supported when device has ecolevel, even when OFF"
        )

        # Also verify that when we turn the device ON and set to ECO mode,
        # the target temperature is still available
        mocked_pydreo_heater.poweron = True
        mocked_pydreo_heater.mode = DreoHeaterMode.ECO
        test_heater.set_preset_mode(PRESET_ECO)

        assert test_heater.preset_mode == PRESET_ECO
        assert test_heater.target_temperature == 72
        supported_features_eco = test_heater.supported_features
        assert supported_features_eco & ClimateEntityFeature.TARGET_TEMPERATURE, "TARGET_TEMPERATURE feature should be supported in ECO mode"

    def test_set_temperature_in_eco_mode(self):
        """Test that target temperature can be set when device is in ECO mode."""
        # Create a heater device in ECO mode
        mocked_pydreo_heater: PyDreoDeviceMock = self.create_mock_device(
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
            swing_modes=None,
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
        mocked_pydreo_heater: PyDreoDeviceMock = self.create_mock_device(
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
            swing_modes=None,
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
        mocked_pydreo_heater: PyDreoDeviceMock = self.create_mock_device(
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
            swing_modes=None,
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
        mocked_pydreo_heater: PyDreoDeviceMock = self.create_mock_device(
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
            swing_modes=None,
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

    def _create_full_heater(self, **overrides):
        """Helper to create a heater with all modes and swing modes."""
        features = {
            "poweron": True,
            "temperature": 75,
            "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
            "htalevel": 2,
            "ecolevel": 70,
            "mode": DreoHeaterMode.HOTAIR,
            "oscon": None,
            "oscmode": None,
            "oscangle": None,
        }
        features.update(overrides.pop("features_override", {}))
        swing_modes = overrides.pop(
            "swing_modes",
            [
                HeaterOscillationAngles.OSC,
                HeaterOscillationAngles.SIXTY,
                HeaterOscillationAngles.NINETY,
                HeaterOscillationAngles.ONE_TWENTY,
            ],
        )
        kwargs = {
            "name": "Test Heater",
            "serial_number": "123456",
            "features": features,
            "modes": [
                DreoHeaterMode.COOLAIR,
                DreoHeaterMode.HOTAIR,
                DreoHeaterMode.ECO,
                DreoHeaterMode.OFF,
            ],
            "swing_modes": swing_modes,
        }
        kwargs.update(overrides)
        mock = self.create_mock_device(**kwargs)
        # Wire up device_definition to return real values
        device_ranges = features.get("device_ranges", {})
        mock.device_definition.device_ranges = device_ranges
        mock.device_definition.swing_modes = swing_modes
        mock.heat_range = device_ranges.get(HEAT_RANGE, (1, 3))
        return mock, climate.DreoHeaterHA(mock)

    def test_device_info(self):
        """Test device_info property returns expected DeviceInfo."""
        mock, heater = self._create_full_heater()
        info = heater.device_info
        assert info is not None

    def test_oscon_property(self):
        """Test oscon property returns device oscon value."""
        mock, heater = self._create_full_heater(features_override={"oscon": True})
        assert heater.oscon is True

    def test_oscangle_property_mapped(self):
        """Test oscangle property when value is in ANGLE_OSCANGLE_MAP."""
        mock, heater = self._create_full_heater(features_override={"oscangle": 60})
        assert heater.oscangle == ANGLE_OSCANGLE_MAP[60]

    def test_oscangle_property_unmapped(self):
        """Test oscangle property returns None for unmapped value."""
        mock, heater = self._create_full_heater(features_override={"oscangle": 999})
        assert heater.oscangle is None

    def test_htalevels_count(self):
        """Test htalevels_count returns correct count from heat_range."""
        mock, heater = self._create_full_heater()
        assert heater.htalevels_count == 3  # range (1,3) = 3 states

    def test_extra_state_attributes(self):
        """Test extra_state_attributes returns model."""
        mock, heater = self._create_full_heater()
        attrs = heater.extra_state_attributes
        assert "model" in attrs

    def test_preset_mode_when_off(self):
        """Test preset_mode returns PRESET_NONE when device is off."""
        mock, heater = self._create_full_heater(features_override={"poweron": False, "mode": DreoHeaterMode.OFF})
        assert heater.preset_mode == PRESET_NONE

    def test_set_preset_mode_invalid(self):
        """Test set_preset_mode with invalid preset logs warning."""
        mock, heater = self._create_full_heater()
        # Should not raise, just log a warning
        heater.set_preset_mode("INVALID_PRESET")
        # Mode should not have changed
        assert mock.mode == DreoHeaterMode.HOTAIR

    def test_set_preset_mode_none(self):
        """Test set_preset_mode with PRESET_NONE does nothing."""
        mock, heater = self._create_full_heater()
        original_mode = mock.mode
        heater.set_preset_mode(PRESET_NONE)
        # PRESET_NONE is not in HVAC_PRESET_TO_DREO_HEATER_MODE and is excluded from warning
        assert mock.mode == original_mode

    def test_turn_on_default(self):
        """Test turn_on sets HOTAIR mode by default."""
        mock, heater = self._create_full_heater(features_override={"poweron": False, "mode": DreoHeaterMode.OFF})
        heater.turn_on()
        assert mock.poweron is True
        assert mock.mode == DreoHeaterMode.HOTAIR

    def test_turn_on_preserves_eco_preset(self):
        """Test turn_on preserves ECO mode when preset is ECO."""
        mock, heater = self._create_full_heater(features_override={"mode": DreoHeaterMode.ECO})
        heater.turn_on()
        assert mock.poweron is True
        assert mock.mode == DreoHeaterMode.ECO

    def test_turn_on_restores_fan_only(self):
        """Test turn_on restores FAN_ONLY if last HVAC mode was FAN_ONLY."""
        mock, heater = self._create_full_heater(features_override={"mode": DreoHeaterMode.COOLAIR})
        # Turn off first to set _last_hvac_mode
        heater.turn_off()
        assert mock.poweron is False
        # Now turn on - should restore COOLAIR since last mode was FAN_ONLY
        heater.turn_on()
        assert mock.poweron is True
        assert mock.mode == DreoHeaterMode.COOLAIR

    def test_turn_on_restores_heat(self):
        """Test turn_on restores HEAT mode if last mode was HEAT."""
        mock, heater = self._create_full_heater(features_override={"mode": DreoHeaterMode.HOTAIR})
        heater.turn_off()
        heater.turn_on()
        assert mock.mode == DreoHeaterMode.HOTAIR

    def test_turn_off(self):
        """Test turn_off sets poweron to False."""
        mock, heater = self._create_full_heater()
        heater.turn_off()
        assert mock.poweron is False

    def test_oscon_setter(self):
        """Test oscon setter sets device oscon."""
        mock, heater = self._create_full_heater(features_override={"oscon": False})
        heater.oscon = True
        assert mock.oscon is True

    def test_oscangle_setter(self):
        """Test oscangle setter maps string to int angle."""
        mock, heater = self._create_full_heater(features_override={"oscangle": 0})
        heater.oscangle = "60°"
        assert mock.oscangle == OSCANGLE_ANGLE_MAP["60°"]

    def test_panel_sound(self):
        """Test panel_sound sets muteon to opposite."""
        mock, heater = self._create_full_heater()
        heater.panel_sound(True)
        assert mock.muteon is False
        heater.panel_sound(False)
        assert mock.muteon is True

    def test_muteon(self):
        """Test muteon sets device muteon."""
        mock, heater = self._create_full_heater()
        heater.muteon(True)
        assert mock.muteon is True
        heater.muteon(False)
        assert mock.muteon is False

    def test_min_temp(self):
        """Test min_temp returns first value of ECOLEVEL_RANGE."""
        mock, heater = self._create_full_heater()
        assert heater.min_temp == 41

    def test_max_temp(self):
        """Test max_temp returns second value of ECOLEVEL_RANGE."""
        mock, heater = self._create_full_heater()
        assert heater.max_temp == 95

    def test_target_temperature_step(self):
        """Test target_temperature_step returns 1."""
        mock, heater = self._create_full_heater()
        assert heater.target_temperature_step == 1

    def test_hvac_modes_property(self):
        """Test hvac_modes returns the list of available modes."""
        mock, heater = self._create_full_heater()
        modes = heater.hvac_modes
        assert isinstance(modes, list)
        assert HVACMode.HEAT in modes

    def test_set_hvac_mode_unsupported(self):
        """Test set_hvac_mode with unsupported mode does nothing."""
        mock, heater = self._create_full_heater()
        original_mode = mock.mode
        # HVACMode.COOL is not in the supported modes
        heater.set_hvac_mode(HVACMode.COOL)
        assert mock.mode == original_mode

    def test_set_hvac_mode_heat_already_eco(self):
        """Test set_hvac_mode HEAT when already in ECO doesn't change mode."""
        mock, heater = self._create_full_heater(features_override={"mode": DreoHeaterMode.ECO})
        heater.set_hvac_mode(HVACMode.HEAT)
        # ECO is already a HEAT-compatible mode, should not change
        assert mock.mode == DreoHeaterMode.ECO

    def test_set_hvac_mode_heat_from_coolair(self):
        """Test set_hvac_mode HEAT from COOLAIR changes to HOTAIR."""
        mock, heater = self._create_full_heater(features_override={"mode": DreoHeaterMode.COOLAIR})
        heater.set_hvac_mode(HVACMode.HEAT)
        assert mock.mode == DreoHeaterMode.HOTAIR

    def test_swing_modes_property(self):
        """Test swing_modes returns the configured swing modes."""
        mock, heater = self._create_full_heater()
        modes = heater.swing_modes
        assert modes is not None

    def test_swing_mode_with_oscmode(self):
        """Test swing_mode when oscmode is set (newer firmware)."""
        mock, heater = self._create_full_heater(features_override={"oscmode": 1})
        mode = heater.swing_mode
        assert mode == HeaterOscillationAngles.OSC

    def test_swing_mode_with_oscmode_off(self):
        """Test swing_mode when oscmode is 0."""
        mock, heater = self._create_full_heater(features_override={"oscmode": 0})
        mode = heater.swing_mode
        assert mode == SWING_OFF

    def test_swing_mode_with_oscon_true(self):
        """Test swing_mode when oscon is True."""
        mock, heater = self._create_full_heater(features_override={"oscon": True, "oscmode": None})
        mode = heater.swing_mode
        assert mode == SWING_ON

    def test_swing_mode_with_oscangle(self):
        """Test swing_mode when oscangle is set."""
        mock, heater = self._create_full_heater(features_override={"oscon": None, "oscmode": None, "oscangle": 60})
        mode = heater.swing_mode
        assert mode == ANGLE_OSCANGLE_MAP[60]

    def test_swing_mode_fallback_off(self):
        """Test swing_mode returns SWING_OFF when nothing is set."""
        mock, heater = self._create_full_heater(features_override={"oscon": None, "oscmode": None, "oscangle": None})
        mode = heater.swing_mode
        assert mode == SWING_OFF

    def test_set_swing_mode_oscmode(self):
        """Test set_swing_mode with oscmode-based device."""
        mock, heater = self._create_full_heater(features_override={"oscmode": 0})
        heater.set_swing_mode(HeaterOscillationAngles.SIXTY)
        assert mock.oscmode == 2  # HEATER_SWING_OSCMODE_MAP maps SIXTY to 2

    def test_set_swing_mode_oscon(self):
        """Test set_swing_mode with oscon-based device."""
        mock, heater = self._create_full_heater(features_override={"oscon": False, "oscmode": None})
        heater.set_swing_mode(SWING_ON)
        assert mock.oscon is True

    def test_set_swing_mode_oscon_off(self):
        """Test set_swing_mode to non-SWING_ON value via oscon."""
        mock, heater = self._create_full_heater(features_override={"oscon": True, "oscmode": None}, swing_modes=[SWING_ON, SWING_OFF])
        heater.set_swing_mode(SWING_OFF)
        assert mock.oscon is False

    def test_set_swing_mode_oscangle(self):
        """Test set_swing_mode with oscangle-based device."""
        mock, heater = self._create_full_heater(features_override={"oscon": None, "oscmode": None, "oscangle": 0})
        heater.set_swing_mode("60°")
        assert mock.oscangle == OSCANGLE_ANGLE_MAP["60°"]

    def test_set_fan_mode_raises(self):
        """Test set_fan_mode raises NotImplementedError."""
        mock, heater = self._create_full_heater()
        with pytest.raises(NotImplementedError):
            heater.set_fan_mode("auto")

    def test_set_humidity_raises(self):
        """Test set_humidity raises NotImplementedError."""
        mock, heater = self._create_full_heater()
        with pytest.raises(NotImplementedError):
            heater.set_humidity(50)

    def test_set_swing_horizontal_mode_raises(self):
        """Test set_swing_horizontal_mode raises NotImplementedError."""
        mock, heater = self._create_full_heater()
        with pytest.raises(NotImplementedError):
            heater.set_swing_horizontal_mode("auto")

    def test_toggle_on_to_off(self):
        """Test toggle turns off when on."""
        mock, heater = self._create_full_heater(features_override={"poweron": True})
        heater.toggle()
        assert mock.poweron is False

    def test_toggle_off_to_on(self):
        """Test toggle turns on when off."""
        mock, heater = self._create_full_heater(features_override={"poweron": False, "mode": DreoHeaterMode.OFF})
        heater.toggle()
        assert mock.poweron is True

    def test_turn_aux_heat_off_raises(self):
        """Test turn_aux_heat_off raises NotImplementedError."""
        mock, heater = self._create_full_heater()
        with pytest.raises(NotImplementedError):
            heater.turn_aux_heat_off()

    def test_turn_aux_heat_on_raises(self):
        """Test turn_aux_heat_on raises NotImplementedError."""
        mock, heater = self._create_full_heater()
        with pytest.raises(NotImplementedError):
            heater.turn_aux_heat_on()

    def test_supported_features_swing_mode(self):
        """Test supported_features includes SWING_MODE when oscon is set."""
        mock, heater = self._create_full_heater(features_override={"oscon": True})
        assert heater.supported_features & ClimateEntityFeature.SWING_MODE

    def test_supported_features_swing_mode_via_oscmode(self):
        """Test supported_features includes SWING_MODE when oscmode is set."""
        mock, heater = self._create_full_heater(features_override={"oscmode": 0})
        assert heater.supported_features & ClimateEntityFeature.SWING_MODE

    def test_set_temperature_no_temp_key(self):
        """Test set_temperature with no ATTR_TEMPERATURE key does nothing."""
        mock, heater = self._create_full_heater()
        original = mock.ecolevel
        heater.set_temperature(some_other_key=42)
        assert mock.ecolevel == original

    def test_target_temperature_none_when_no_ecolevel(self):
        """Test target_temperature returns None when ecolevel is None."""
        mock, heater = self._create_full_heater(features_override={"ecolevel": None})
        assert heater.target_temperature is None
