"""Tests for the Dreo Air Conditioner HA class."""

from unittest.mock import patch, MagicMock

from custom_components.dreo.dreoairconditioner import (
    DreoAirConditionerHA,
    DREO_MODE_TO_HVAC_MODE,
    DREO_MODE_TO_PRESET,
    HVAC_PRESET_TO_DREO_MODE,
    DREO_FAN_MODE_TO_HA,
    HA_FAN_MODE_TO_DREO,
)
from custom_components.dreo.pydreo.constant import (
    DreoACMode,
    DreoACFanMode,
    TEMP_RANGE,
    TARGET_TEMP_RANGE,
    TARGET_TEMP_RANGE_ECO,
    HUMIDITY_RANGE,
)

from homeassistant.components.climate import (
    HVACMode,
    ClimateEntityFeature,
    ATTR_TEMPERATURE,
    SWING_ON,
    SWING_OFF,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    PRESET_ECO,
    PRESET_NONE,
    PRESET_SLEEP,
)

from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"


class TestDreoAirConditionerHA(TestDeviceBase):
    """Test the Dreo Air Conditioner HA class."""

    def _create_ac_device(self, **overrides):
        """Helper to create a mocked AC device with realistic defaults."""
        device_ranges_obj = MagicMock()
        device_ranges_obj.temp_range = (60, 86)
        device_ranges_obj.__getitem__ = lambda self, key: {
            TEMP_RANGE: (60, 86),
            TARGET_TEMP_RANGE: (64, 86),
            TARGET_TEMP_RANGE_ECO: (75, 86),
            HUMIDITY_RANGE: (30, 80),
        }[key]

        device_definition = MagicMock()
        device_definition.device_ranges = device_ranges_obj
        device_definition.swing_modes = [SWING_ON, SWING_OFF]
        device_definition.fan_modes = [FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO]

        defaults = {
            "name": "Test AC",
            "serial_number": "AC001",
            "type": "Air Conditioner",
            "features": {
                "poweron": True,
                "temperature": 72,
                "target_temperature": 70,
                "mode": DreoACMode.COOL,
                "modes": [DreoACMode.COOL, DreoACMode.DRY, DreoACMode.FAN, DreoACMode.SLEEP, DreoACMode.ECO],
                "oscon": False,
                "oscangle": None,
                "fan_mode": DreoACFanMode.AUTO,
                "device_id": "ac_device_1",
                "device_definition": device_definition,
                "brand": "Dreo",
                "series_name": "DR-HAC",
                "model": "DR-HAC001S",
                "product_name": "Air Conditioner",
                "device_name": "Test AC",
                "humidity": 55,
                "target_humidity": 50,
                "preset_mode": None,
            },
        }
        defaults.update(overrides)
        return self.create_mock_device(**defaults)

    def test_ac_basic_properties(self):
        """Test AC basic properties after initialization."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            assert ac.name == "Air Conditioner"
            assert ac.unique_id is not None
            assert ac.is_on is True
            assert ac.current_temperature == 72

    def test_ac_hvac_mode_when_on(self):
        """Test hvac_mode reflects device mode when powered on."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            # Device is in COOL mode
            assert ac.hvac_mode == HVACMode.COOL

    def test_ac_hvac_mode_when_off(self):
        """Test hvac_mode is OFF when device is powered off."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device(
                features={
                    "poweron": False,
                    "temperature": 72,
                    "target_temperature": 70,
                    "mode": DreoACMode.COOL,
                    "modes": [DreoACMode.COOL, DreoACMode.DRY, DreoACMode.FAN],
                    "oscon": False,
                    "oscangle": None,
                    "fan_mode": DreoACFanMode.AUTO,
                    "device_id": "ac_device_1",
                    "device_definition": self._create_ac_device()._mock_children[0] if False else MagicMock(),
                    "brand": "Dreo",
                    "series_name": "DR-HAC",
                    "model": "DR-HAC001S",
                    "product_name": "Air Conditioner",
                    "device_name": "Test AC",
                    "humidity": 55,
                    "target_humidity": 50,
                    "preset_mode": None,
                }
            )
            # Need to properly set up device_definition
            device_definition = MagicMock()
            device_definition.device_ranges = {
                TEMP_RANGE: (60, 86),
                TARGET_TEMP_RANGE: (64, 86),
                TARGET_TEMP_RANGE_ECO: (75, 86),
                HUMIDITY_RANGE: (30, 80),
            }
            device_definition.swing_modes = [SWING_ON, SWING_OFF]
            device_definition.fan_modes = [FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO]
            device.device_definition = device_definition

            ac = DreoAirConditionerHA(device)
            assert ac.hvac_mode == HVACMode.OFF

    def test_ac_set_hvac_mode_off(self):
        """Test setting HVAC mode to OFF."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            ac.set_hvac_mode(HVACMode.OFF)
            assert device.poweron is False

    def test_ac_set_hvac_mode_cool(self):
        """Test setting HVAC mode to COOL."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            ac.set_hvac_mode(HVACMode.COOL)
            assert device.poweron is True
            assert device.mode == DreoACMode.COOL

    def test_ac_set_hvac_mode_dry(self):
        """Test setting HVAC mode to DRY."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            ac.set_hvac_mode(HVACMode.DRY)
            assert device.poweron is True

    def test_ac_set_hvac_mode_fan_only(self):
        """Test setting HVAC mode to FAN_ONLY."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            ac.set_hvac_mode(HVACMode.FAN_ONLY)
            assert device.poweron is True

    def test_ac_turn_on(self):
        """Test turning AC on."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            device.poweron = False
            ac = DreoAirConditionerHA(device)

            ac.turn_on()
            assert device.poweron is True

    def test_ac_turn_off(self):
        """Test turning AC off."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            ac.turn_off()
            assert device.poweron is False

    def test_ac_fan_modes_are_strings(self):
        """Test that fan_modes list contains strings, not DreoACFanMode enums.

        Regression test for: TypeError: sequence item 0: expected str instance,
        DreoACFanMode found - caused by assigning raw enum values to _attr_fan_modes.
        """
        with patch(PATCH_UPDATE_HA_STATE):
            # Create device definition with DreoACFanMode enum values exactly as
            # models.py stores them, to reproduce the original regression scenario.
            device_ranges_obj = MagicMock()
            device_ranges_obj.__getitem__ = lambda self, key: {
                TEMP_RANGE: (60, 86),
                TARGET_TEMP_RANGE: (64, 86),
                TARGET_TEMP_RANGE_ECO: (75, 86),
                HUMIDITY_RANGE: (30, 80),
            }[key]
            device_definition = MagicMock()
            device_definition.device_ranges = device_ranges_obj
            device_definition.swing_modes = [SWING_ON, SWING_OFF]
            device_definition.fan_modes = [DreoACFanMode.AUTO, DreoACFanMode.LOW, DreoACFanMode.MEDIUM, DreoACFanMode.HIGH]

            device = self.create_mock_device(
                name="Test AC",
                serial_number="AC001",
                type="Air Conditioner",
                features={
                    "poweron": True,
                    "temperature": 72,
                    "target_temperature": 70,
                    "mode": DreoACMode.COOL,
                    "modes": [DreoACMode.COOL, DreoACMode.DRY, DreoACMode.FAN, DreoACMode.SLEEP, DreoACMode.ECO],
                    "oscon": False,
                    "oscangle": None,
                    "fan_mode": DreoACFanMode.AUTO,
                    "device_id": "ac_device_1",
                    "device_definition": device_definition,
                    "brand": "Dreo",
                    "series_name": "DR-HAC",
                    "model": "DR-HAC005S",
                    "product_name": "Air Conditioner",
                    "device_name": "Test AC",
                    "humidity": 55,
                    "target_humidity": 50,
                    "preset_mode": None,
                },
            )

            ac = DreoAirConditionerHA(device)
            assert ac.fan_modes is not None
            for mode in ac.fan_modes:
                assert isinstance(mode, str), f"fan_modes must contain strings, got {type(mode)}: {mode!r}"
            assert FAN_AUTO in ac.fan_modes
            assert FAN_LOW in ac.fan_modes
            assert FAN_MEDIUM in ac.fan_modes
            assert FAN_HIGH in ac.fan_modes

    def test_ac_fan_mode_property(self):
        """Test fan_mode property."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            # Device has AUTO fan mode
            assert ac.fan_mode == FAN_AUTO

    def test_ac_set_fan_mode(self):
        """Test setting fan mode."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            ac.set_fan_mode(FAN_LOW)
            assert device.fan_mode == DreoACFanMode.LOW

            ac.set_fan_mode(FAN_MEDIUM)
            assert device.fan_mode == DreoACFanMode.MEDIUM

            ac.set_fan_mode(FAN_HIGH)
            assert device.fan_mode == DreoACFanMode.HIGH

            ac.set_fan_mode(FAN_AUTO)
            assert device.fan_mode == DreoACFanMode.AUTO

    def test_ac_set_invalid_fan_mode(self):
        """Test setting invalid fan mode doesn't crash."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            # Should not raise
            ac.set_fan_mode("turbo")

    def test_ac_temperature_control(self):
        """Test temperature control."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            assert ac.current_temperature == 72
            assert ac.target_temperature == 70

            ac.set_temperature(**{ATTR_TEMPERATURE: 75})
            assert device.target_temperature == 75

    def test_ac_min_max_temp(self):
        """Test min/max temperature properties."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            assert ac.min_temp == 60
            assert ac.max_temp == 86
            assert ac.target_temperature_step == 1

    def test_ac_humidity_control(self):
        """Test humidity control."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            assert ac.current_humidity == 55
            assert ac.target_humidity == 50

            ac.set_humidity(60)
            assert device.target_humidity == 60

    def test_ac_swing_mode(self):
        """Test swing mode."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            # oscon is False, so swing should be OFF
            assert ac.swing_mode == SWING_OFF

            # Set oscon to True
            device.oscon = True
            assert ac.swing_mode == SWING_ON

    def test_ac_set_swing_mode(self):
        """Test setting swing mode."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            ac.set_swing_mode(SWING_ON)
            assert device.oscon is True

    def test_ac_preset_modes(self):
        """Test preset mode list."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            preset_modes = ac.preset_modes
            assert PRESET_NONE in preset_modes

    def test_ac_preset_mode_property(self):
        """Test current preset mode."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            # Device in COOL mode - preset should be NONE
            assert ac.preset_mode == PRESET_NONE

    def test_ac_set_preset_mode_eco(self):
        """Test setting ECO preset mode."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            ac.set_preset_mode(PRESET_ECO)
            assert device.mode == DreoACMode.ECO

    def test_ac_set_preset_mode_none(self):
        """Test setting NONE preset mode (clears preset)."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            ac.set_preset_mode(PRESET_NONE)
            assert device.mode == DreoACMode.COOL

    def test_ac_supported_features(self):
        """Test supported features."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            features = ac.supported_features
            assert features & ClimateEntityFeature.TARGET_TEMPERATURE
            assert features & ClimateEntityFeature.FAN_MODE
            assert features & ClimateEntityFeature.SWING_MODE
            assert features & ClimateEntityFeature.TURN_ON
            assert features & ClimateEntityFeature.TURN_OFF

    def test_ac_extra_state_attributes(self):
        """Test extra state attributes."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            attrs = ac.extra_state_attributes
            assert "model" in attrs

    def test_ac_device_info(self):
        """Test device info."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            device_info = ac.device_info
            assert device_info is not None

    def test_ac_oscon_property(self):
        """Test oscon property."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            assert ac.oscon is False
            device.oscon = True
            assert ac.oscon is True

    def test_ac_min_max_humidity(self):
        """Test min/max humidity properties."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._create_ac_device()
            ac = DreoAirConditionerHA(device)

            assert ac.min_humidity == 30
            assert ac.max_humidity == 80


class TestDreoACModeMapping:
    """Test the mode mapping dictionaries."""

    def test_dreo_mode_to_hvac_mode(self):
        """Test DREO_MODE_TO_HVAC_MODE mapping."""
        assert DREO_MODE_TO_HVAC_MODE[DreoACMode.COOL] == HVACMode.COOL
        assert DREO_MODE_TO_HVAC_MODE[DreoACMode.DRY] == HVACMode.DRY
        assert DREO_MODE_TO_HVAC_MODE[DreoACMode.FAN] == HVACMode.FAN_ONLY
        assert DREO_MODE_TO_HVAC_MODE[DreoACMode.SLEEP] == HVACMode.COOL
        assert DREO_MODE_TO_HVAC_MODE[DreoACMode.ECO] == HVACMode.COOL

    def test_dreo_mode_to_preset(self):
        """Test DREO_MODE_TO_PRESET mapping."""
        assert DREO_MODE_TO_PRESET[DreoACMode.SLEEP] == PRESET_SLEEP
        assert DREO_MODE_TO_PRESET[DreoACMode.ECO] == PRESET_ECO
        assert DreoACMode.COOL not in DREO_MODE_TO_PRESET

    def test_hvac_preset_to_dreo_mode(self):
        """Test HVAC_PRESET_TO_DREO_MODE mapping."""
        assert HVAC_PRESET_TO_DREO_MODE[(HVACMode.COOL, PRESET_NONE)] == DreoACMode.COOL
        assert HVAC_PRESET_TO_DREO_MODE[(HVACMode.COOL, PRESET_ECO)] == DreoACMode.ECO
        assert HVAC_PRESET_TO_DREO_MODE[(HVACMode.COOL, PRESET_SLEEP)] == DreoACMode.SLEEP
        assert HVAC_PRESET_TO_DREO_MODE[(HVACMode.DRY, PRESET_NONE)] == DreoACMode.DRY
        assert HVAC_PRESET_TO_DREO_MODE[(HVACMode.FAN_ONLY, PRESET_NONE)] == DreoACMode.FAN

    def test_dreo_fan_mode_to_ha(self):
        """Test DREO_FAN_MODE_TO_HA mapping."""
        assert DREO_FAN_MODE_TO_HA[DreoACFanMode.LOW] == FAN_LOW
        assert DREO_FAN_MODE_TO_HA[DreoACFanMode.MEDIUM] == FAN_MEDIUM
        assert DREO_FAN_MODE_TO_HA[DreoACFanMode.HIGH] == FAN_HIGH
        assert DREO_FAN_MODE_TO_HA[DreoACFanMode.AUTO] == FAN_AUTO

    def test_ha_fan_mode_to_dreo(self):
        """Test HA_FAN_MODE_TO_DREO mapping."""
        assert HA_FAN_MODE_TO_DREO[FAN_LOW] == DreoACFanMode.LOW
        assert HA_FAN_MODE_TO_DREO[FAN_MEDIUM] == DreoACFanMode.MEDIUM
        assert HA_FAN_MODE_TO_DREO[FAN_HIGH] == DreoACFanMode.HIGH
        assert HA_FAN_MODE_TO_DREO[FAN_AUTO] == DreoACFanMode.AUTO
