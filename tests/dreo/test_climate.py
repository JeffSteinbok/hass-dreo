"""Tests for the Dreo Climate platform (climate.py get_entries)."""
from unittest.mock import patch

from custom_components.dreo import climate

from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

from custom_components.dreo.pydreo.constant import (
    HEAT_RANGE,
    ECOLEVEL_RANGE,
    DreoHeaterMode
)

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_UPDATE_HA_STATE = f'{PATCH_BASE_PATH}.schedule_update_ha_state'


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
