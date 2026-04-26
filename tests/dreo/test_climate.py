"""Tests for the Dreo Climate platform (climate.py get_entries)."""

import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from custom_components.dreo import climate
from custom_components.dreo.const import DOMAIN, PYDREO_MANAGER

from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

from custom_components.dreo.pydreo.constant import (
    HEAT_RANGE,
    ECOLEVEL_RANGE,
    DreoHeaterMode,
    DreoDeviceType,
    DreoACMode,
    DreoACFanMode,
)

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"


class TestDreoClimatePlatform(TestDeviceBase):
    """Test the Dreo Climate platform get_entries."""

    def test_climate_get_entries_heater(self):
        """Test that get_entries creates a heater entity for heater devices."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Test Heater",
                serial_number="HTR001",
                type="Heater",
                features={
                    "poweron": True,
                    "temperature": 72,
                    "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
                    "htalevel": 2,
                    "ecolevel": 70,
                    "mode": DreoHeaterMode.HOTAIR,
                },
                modes=[
                    DreoHeaterMode.COOLAIR,
                    DreoHeaterMode.HOTAIR,
                    DreoHeaterMode.ECO,
                    DreoHeaterMode.OFF,
                ],
                swing_modes=None,
            )

            entities = climate.get_entries([device])
            assert len(entities) == 1
            assert type(entities[0]).__name__ == "DreoHeaterHA"

    def test_climate_get_entries_filters_non_climate(self):
        """Test that get_entries filters out non-climate device types."""
        devices = [
            self.create_mock_device(name="Fan", serial_number="FAN001", type="Tower Fan"),
            self.create_mock_device(name="Humidifier", serial_number="HUM001", type="Humidifier"),
            self.create_mock_device(name="Purifier", serial_number="PUR001", type="Air Purifier"),
        ]

        entities = climate.get_entries(devices)
        assert len(entities) == 0

    def test_climate_get_entries_mixed_devices(self):
        """Test get_entries with a mix of climate and non-climate devices."""
        with patch(PATCH_UPDATE_HA_STATE):
            heater = self.create_mock_device(
                name="Test Heater",
                serial_number="HTR001",
                type="Heater",
                features={
                    "poweron": True,
                    "temperature": 72,
                    "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
                    "htalevel": 2,
                    "ecolevel": 70,
                    "mode": DreoHeaterMode.HOTAIR,
                },
                modes=[
                    DreoHeaterMode.COOLAIR,
                    DreoHeaterMode.HOTAIR,
                    DreoHeaterMode.ECO,
                    DreoHeaterMode.OFF,
                ],
                swing_modes=None,
            )
            fan = self.create_mock_device(
                name="Fan",
                serial_number="FAN001",
                type="Tower Fan",
            )

            entities = climate.get_entries([heater, fan])
            assert len(entities) == 1

    def test_climate_get_entries_empty(self):
        """Test get_entries with empty device list."""
        entities = climate.get_entries([])
        assert len(entities) == 0

    def test_climate_get_entries_air_conditioner(self):
        """Test that get_entries creates an AC entity for air conditioner devices."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Test AC",
                serial_number="AC001",
                type=DreoDeviceType.AIR_CONDITIONER,
                features={
                    "poweron": True,
                    "temperature": 72,
                    "target_temperature": 70,
                    "mode": DreoACMode.COOL,
                    "oscon": False,
                    "fan_mode": DreoACFanMode.LOW,
                },
                modes=[DreoACMode.COOL, DreoACMode.DRY, DreoACMode.FAN],
                swing_modes=None,
            )

            entities = climate.get_entries([device])
            assert len(entities) == 1
            assert type(entities[0]).__name__ == "DreoAirConditionerHA"

    def test_climate_get_entries_heater_and_ac(self):
        """Test get_entries with both heater and AC devices."""
        with patch(PATCH_UPDATE_HA_STATE):
            heater = self.create_mock_device(
                name="Test Heater",
                serial_number="HTR001",
                type=DreoDeviceType.HEATER,
                features={
                    "poweron": True,
                    "temperature": 72,
                    "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
                    "htalevel": 2,
                    "ecolevel": 70,
                    "mode": DreoHeaterMode.HOTAIR,
                },
                modes=[
                    DreoHeaterMode.COOLAIR,
                    DreoHeaterMode.HOTAIR,
                    DreoHeaterMode.ECO,
                    DreoHeaterMode.OFF,
                ],
                swing_modes=None,
            )
            ac = self.create_mock_device(
                name="Test AC",
                serial_number="AC001",
                type=DreoDeviceType.AIR_CONDITIONER,
                features={
                    "poweron": True,
                    "temperature": 72,
                    "target_temperature": 70,
                    "mode": DreoACMode.COOL,
                    "oscon": False,
                    "fan_mode": DreoACFanMode.LOW,
                },
                modes=[DreoACMode.COOL, DreoACMode.DRY, DreoACMode.FAN],
                swing_modes=None,
            )

            entities = climate.get_entries([heater, ac])
            assert len(entities) == 2
            type_names = [type(e).__name__ for e in entities]
            assert "DreoHeaterHA" in type_names
            assert "DreoAirConditionerHA" in type_names

    def test_async_setup_entry(self):
        """Test async_setup_entry sets up climate entities from hass.data."""
        with patch(PATCH_UPDATE_HA_STATE):
            heater = self.create_mock_device(
                name="Test Heater",
                serial_number="HTR001",
                type=DreoDeviceType.HEATER,
                features={
                    "poweron": True,
                    "temperature": 72,
                    "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
                    "htalevel": 2,
                    "ecolevel": 70,
                    "mode": DreoHeaterMode.HOTAIR,
                },
                modes=[
                    DreoHeaterMode.COOLAIR,
                    DreoHeaterMode.HOTAIR,
                    DreoHeaterMode.ECO,
                    DreoHeaterMode.OFF,
                ],
                swing_modes=None,
            )

            mock_pydreo = MagicMock()
            mock_pydreo.devices = [heater]

            mock_hass = MagicMock()
            mock_hass.data = {DOMAIN: {PYDREO_MANAGER: mock_pydreo}}

            mock_config_entry = MagicMock()
            mock_add_entities = MagicMock()

            asyncio.run(climate.async_setup_entry(mock_hass, mock_config_entry, mock_add_entities))

            mock_add_entities.assert_called_once()
            entities = mock_add_entities.call_args[0][0]
            assert len(entities) == 1
            assert type(entities[0]).__name__ == "DreoHeaterHA"
