"""Tests for the native_* climate temperature compatibility mixin."""

import importlib
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_MAX_TEMP,
    ATTR_MIN_TEMP,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ATTR_TEMPERATURE,
    ClimateEntityFeature,
)
from homeassistant.const import UnitOfTemperature

from custom_components.dreo import climatecompat
from custom_components.dreo.climatecompat import (
    HAS_NATIVE_CLIMATE_TEMPERATURES,
    NativeClimateTemperatureCompat,
)
from custom_components.dreo.dreoairconditioner import DreoAirConditionerHA
from custom_components.dreo.dreoheater import DreoHeaterHA
from custom_components.dreo.pydreo.constant import (
    ECOLEVEL_RANGE,
    HEAT_RANGE,
    HUMIDITY_RANGE,
    TARGET_TEMP_RANGE,
    TARGET_TEMP_RANGE_ECO,
    TEMP_RANGE,
    DreoACFanMode,
    DreoACMode,
    DreoHeaterMode,
)

from .testdevicebase import TestDeviceBase

LEGACY_MEMBERS = {
    "temperature_unit",
    "current_temperature",
    "target_temperature",
    "target_temperature_high",
    "target_temperature_low",
}
NATIVE_MEMBERS = {
    "native_temperature_unit",
    "native_current_temperature",
    "native_target_temperature",
    "native_target_temperature_high",
    "native_target_temperature_low",
}


def _hass(unit: str) -> MagicMock:
    hass = MagicMock()
    hass.config.units.temperature_unit = unit
    return hass


def _own_members(cls: type) -> set[str]:
    return {name for name in vars(cls) if not name.startswith("__")}


class TestNativeClimateTemperatureCompat(TestDeviceBase):
    """The climate entities report their temperatures to Home Assistant on every supported version."""

    def _heater(self, unit: str) -> DreoHeaterHA:
        device = self.create_mock_device(
            name="Test Heater",
            serial_number="H1",
            features={
                "poweron": True,
                "temperature": 70,
                "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
                "htalevel": 2,
                "ecolevel": 68,
                "mode": DreoHeaterMode.ECO,
            },
            modes=[DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF],
            swing_modes=None,
        )
        device.device_definition.device_ranges = {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)}
        heater = DreoHeaterHA(device)
        heater.hass = _hass(unit)
        return heater

    def _ac(self, unit: str) -> DreoAirConditionerHA:
        device_ranges = {TEMP_RANGE: (60, 86), TARGET_TEMP_RANGE: (64, 86), TARGET_TEMP_RANGE_ECO: (75, 86), HUMIDITY_RANGE: (30, 80)}
        device_definition = MagicMock()
        device_definition.device_ranges = device_ranges
        device_definition.swing_modes = None
        device = self.create_mock_device(
            name="Test AC",
            serial_number="AC1",
            features={
                "poweron": True,
                "temperature": 72,
                "target_temperature": 70,
                "mode": DreoACMode.COOL,
                "modes": [DreoACMode.COOL, DreoACMode.ECO],
                "preset_mode": None,
                "fan_mode": DreoACFanMode.AUTO,
                "oscon": False,
                "oscangle": None,
                "humidity": 55,
                "target_humidity": 50,
                "device_definition": device_definition,
            },
        )
        ac = DreoAirConditionerHA(device)
        ac.hass = _hass(unit)
        return ac

    def test_heater_state_in_fahrenheit(self):
        heater = self._heater(UnitOfTemperature.FAHRENHEIT)

        assert heater.state_attributes[ATTR_CURRENT_TEMPERATURE] == 70
        assert heater.state_attributes[ATTR_TEMPERATURE] == 68
        assert heater.capability_attributes[ATTR_MIN_TEMP] == 41
        assert heater.capability_attributes[ATTR_MAX_TEMP] == 95

    def test_heater_state_in_celsius(self):
        """The native unit is °F, so Home Assistant converts to °C (20 °C targets ecolevel 68)."""
        heater = self._heater(UnitOfTemperature.CELSIUS)

        assert heater.state_attributes[ATTR_CURRENT_TEMPERATURE] == 21
        assert heater.state_attributes[ATTR_TEMPERATURE] == 20
        assert heater.capability_attributes[ATTR_MIN_TEMP] == 5
        assert heater.capability_attributes[ATTR_MAX_TEMP] == 35

    def test_ac_state_in_fahrenheit(self):
        ac = self._ac(UnitOfTemperature.FAHRENHEIT)
        features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE

        with patch.object(DreoAirConditionerHA, "supported_features", new_callable=PropertyMock, return_value=features):
            attributes = ac.state_attributes

        assert attributes[ATTR_CURRENT_TEMPERATURE] == 72
        assert attributes[ATTR_TEMPERATURE] == 70
        assert attributes[ATTR_TARGET_TEMP_LOW] == 64
        assert attributes[ATTR_TARGET_TEMP_HIGH] == 86
        assert ac.capability_attributes[ATTR_MIN_TEMP] == 60
        assert ac.capability_attributes[ATTR_MAX_TEMP] == 86

    def test_ac_state_in_celsius(self):
        ac = self._ac(UnitOfTemperature.CELSIUS)
        features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE

        with patch.object(DreoAirConditionerHA, "supported_features", new_callable=PropertyMock, return_value=features):
            attributes = ac.state_attributes

        assert attributes[ATTR_CURRENT_TEMPERATURE] == 22
        assert attributes[ATTR_TEMPERATURE] == 21
        assert attributes[ATTR_TARGET_TEMP_LOW] == 18
        assert attributes[ATTR_TARGET_TEMP_HIGH] == 30

    @pytest.mark.parametrize("entity", ["_heater", "_ac"])
    def test_unit_is_fahrenheit(self, entity):
        climate_entity = getattr(self, entity)(UnitOfTemperature.CELSIUS)

        assert climate_entity.native_temperature_unit == UnitOfTemperature.FAHRENHEIT
        if not HAS_NATIVE_CLIMATE_TEMPERATURES:
            assert climate_entity.temperature_unit == climate_entity.native_temperature_unit

    @pytest.mark.skipif(not HAS_NATIVE_CLIMATE_TEMPERATURES, reason="Home Assistant lacks the native_* climate API")
    def test_mixin_is_empty_with_native_api(self):
        """Providing no member keeps Home Assistant 2026.11+ from reporting deprecated ones."""
        assert _own_members(NativeClimateTemperatureCompat) == set()

    @pytest.mark.skipif(HAS_NATIVE_CLIMATE_TEMPERATURES, reason="Home Assistant has the native_* climate API")
    def test_mixin_serves_legacy_names_without_native_api(self):
        assert LEGACY_MEMBERS | NATIVE_MEMBERS <= _own_members(NativeClimateTemperatureCompat)


class TestCompatBranches:
    """Both branches of the mixin, whichever Home Assistant version is installed."""

    @staticmethod
    def _reload_with(climate_entity: type):
        try:
            with patch("homeassistant.components.climate.ClimateEntity", climate_entity):
                module = importlib.reload(climatecompat)
                return module.HAS_NATIVE_CLIMATE_TEMPERATURES, module.NativeClimateTemperatureCompat
        finally:
            importlib.reload(climatecompat)

    def test_without_native_api(self):
        has_native, mixin = self._reload_with(type("OldClimateEntity", (), {}))

        assert not has_native

        class Entity(mixin):
            _attr_native_temperature_unit = UnitOfTemperature.FAHRENHEIT
            _attr_native_current_temperature = 70
            _attr_native_target_temperature = 68
            _attr_native_target_temperature_low = 64
            _attr_native_target_temperature_high = 86

        entity = Entity()
        assert entity.temperature_unit == entity.native_temperature_unit == UnitOfTemperature.FAHRENHEIT
        assert entity.current_temperature == entity.native_current_temperature == 70
        assert entity.target_temperature == entity.native_target_temperature == 68
        assert entity.target_temperature_low == entity.native_target_temperature_low == 64
        assert entity.target_temperature_high == entity.native_target_temperature_high == 86

    def test_with_native_api(self):
        has_native, mixin = self._reload_with(type("NewClimateEntity", (), {"native_temperature_unit": None}))

        assert has_native
        assert _own_members(mixin) == set()
