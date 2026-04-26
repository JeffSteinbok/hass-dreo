"""Tests for the Dreo Number entity."""

# pylint: disable=E1123
from unittest.mock import patch, MagicMock

from custom_components.dreo import number
from custom_components.dreo.number import DreoNumberHA, DreoNumberEntityDescription, NUMBERS, get_device_range

from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"


class TestDreoNumberHA(TestDeviceBase):
    """Test the Dreo Number entity."""

    def test_number_get_entries_target_humidity(self):
        """Test number entity creation for target_humidity."""
        device = self.create_mock_device(name="Test Dehumidifier", serial_number="DH001", type="Dehumidifier", features={"target_humidity": 50})

        entities = number.get_entries([device])
        keys = [e.entity_description.key for e in entities]
        assert "Target Humidity" in keys

    def test_number_get_entries_humidifier_excluded(self):
        """Test that Humidifier type devices are excluded from target_humidity number."""
        device = self.create_mock_device(name="Test Humidifier", serial_number="HUM001", type="Humidifier", features={"target_humidity": 60})

        entities = number.get_entries([device])
        keys = [e.entity_description.key for e in entities]
        # Humidifier uses the humidifier platform, not number entity
        assert "Target Humidity" not in keys

    def test_number_get_entries_horizontal_angle(self):
        """Test number entity creation for horizontal_angle."""
        device = self.create_mock_device(name="Test Circulator", serial_number="AC001", features={"horizontal_angle": 30})

        entities = number.get_entries([device])
        keys = [e.entity_description.key for e in entities]
        assert "Horizontal Angle" in keys

    def test_number_get_entries_vertical_angle(self):
        """Test number entity creation for vertical_angle."""
        device = self.create_mock_device(name="Test Circulator", serial_number="AC001", features={"vertical_angle": 45})

        entities = number.get_entries([device])
        keys = [e.entity_description.key for e in entities]
        assert "Vertical Angle" in keys

    def test_number_get_entries_empty(self):
        """Test that devices without number features get no number entities."""
        device = self.create_mock_device(name="Simple Fan", serial_number="FAN001", features={"is_on": True, "fan_speed": 3})

        entities = number.get_entries([device])
        assert len(entities) == 0

    def test_number_entity_properties(self):
        """Test number entity basic properties."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Test Circulator", serial_number="AC001", features={"horizontal_angle": 30})

            entities = number.get_entries([device])
            angle_number = next(e for e in entities if e.entity_description.key == "Horizontal Angle")
            assert angle_number._attr_has_entity_name is True
            assert angle_number._attr_translation_key == "horizontal_angle"
            assert angle_number.unique_id == "AC001-Horizontal Angle"
            assert angle_number._attr_native_min_value == -60
            assert angle_number._attr_native_max_value == 60

    def test_number_native_value(self):
        """Test the native_value property."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Test Circulator", serial_number="AC001", features={"horizontal_angle": 30})

            entities = number.get_entries([device])
            angle_number = next(e for e in entities if e.entity_description.key == "Horizontal Angle")
            assert angle_number.native_value == 30

    def test_number_set_native_value(self):
        """Test the set_native_value method."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Test Circulator", serial_number="AC001", features={"horizontal_angle": 30})

            entities = number.get_entries([device])
            angle_number = next(e for e in entities if e.entity_description.key == "Horizontal Angle")

            angle_number.set_native_value(45)
            assert device.horizontal_angle == 45

    def test_number_repr(self):
        """Test the repr method of DreoNumberHA."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Test Device", serial_number="DEV001", features={"horizontal_angle": 0})

            entities = number.get_entries([device])
            repr_str = repr(entities[0])
            assert "DreoNumberHA" in repr_str

    def test_number_oscillation_angles(self):
        """Test oscillation angle number entities."""
        device = self.create_mock_device(
            name="Air Circulator",
            serial_number="AC001",
            features={
                "horizontal_osc_angle_left": -30,
                "horizontal_osc_angle_right": 30,
                "vertical_osc_angle_top": 60,
                "vertical_osc_angle_bottom": 10,
            },
        )

        entities = number.get_entries([device])
        keys = [e.entity_description.key for e in entities]
        assert "Horizontal Oscillation Angle Left" in keys
        assert "Horizontal Oscillation Angle Right" in keys
        assert "Vertical Oscillation Angle Top" in keys
        assert "Vertical Oscillation Angle Bottom" in keys
        assert len(entities) == 4

    def test_number_shakehorizonangle(self):
        """Test shakehorizonangle number entity."""
        device = self.create_mock_device(name="Tower Fan", serial_number="TF001", features={"shakehorizonangle": 60})

        entities = number.get_entries([device])
        keys = [e.entity_description.key for e in entities]
        assert "Oscillation Angle" in keys

    def test_number_multiple_devices(self):
        """Test get_entries with multiple devices."""
        device1 = self.create_mock_device(name="Circulator", serial_number="AC001", features={"horizontal_angle": 0, "vertical_angle": 45})
        device2 = self.create_mock_device(name="Fan", serial_number="FAN001", features={"shakehorizonangle": 90})

        entities = number.get_entries([device1, device2])
        assert len(entities) == 3

    def test_get_device_range_from_device_attr(self):
        """Test get_device_range when range is available directly on device."""
        device = MagicMock()
        device.horizontal_angle_range = (-45, 45)
        device.device_definition = MagicMock()
        device.device_definition.device_ranges = MagicMock()
        device.device_definition.device_ranges.horizontal_angle_range = None

        desc = DreoNumberEntityDescription(
            key="Horizontal Angle",
            attr_name="horizontal_angle",
            min_value=-60,
            max_value=60,
        )

        result = get_device_range(device, desc)
        assert result == (-45, 45)

    def test_get_device_range_from_device_definition(self):
        """Test get_device_range when range is available from device definition."""
        device = MagicMock()
        device.horizontal_angle_range = None
        device.device_definition = MagicMock()
        device.device_definition.device_ranges = {"horizontal_angle_range": (-50, 50)}

        desc = DreoNumberEntityDescription(
            key="Horizontal Angle",
            attr_name="horizontal_angle",
            min_value=-60,
            max_value=60,
        )

        result = get_device_range(device, desc)
        assert result == (-50, 50)

    def test_get_device_range_none(self):
        """Test get_device_range when no range is available."""
        device = MagicMock()
        device.horizontal_angle_range = None
        device.device_definition = MagicMock()
        device.device_definition.device_ranges = {}

        desc = DreoNumberEntityDescription(
            key="Horizontal Angle",
            attr_name="horizontal_angle",
            min_value=-60,
            max_value=60,
        )

        result = get_device_range(device, desc)
        assert result is None
