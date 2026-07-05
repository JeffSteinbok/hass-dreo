"""Tests for the Dreo Sensor entity."""

from unittest.mock import patch

from custom_components.dreo import sensor
from custom_components.dreo.sensor import DreoSensorHA, DreoSensorEntityDescription, SENSORS
from custom_components.dreo.pydreo.constant import DreoDeviceType

from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"


class TestDreoSensorHA(TestDeviceBase):
    """Test the Dreo Sensor entity."""

    def test_sensor_get_entries_temperature(self):
        """Test sensor creation for temperature-supporting devices."""
        device = self.create_mock_device(name="Test Humidifier", serial_number="HUM001", type="Humidifier", features={"temperature": 72})

        entities = sensor.get_entries([device])
        keys = [e.entity_description.key for e in entities]
        assert "Temperature" in keys

    def test_sensor_get_entries_humidity(self):
        """Test sensor creation for humidity-supporting devices."""
        device = self.create_mock_device(name="Test Humidifier", serial_number="HUM001", type="Humidifier", features={"humidity": 55})

        entities = sensor.get_entries([device])
        keys = [e.entity_description.key for e in entities]
        assert "Humidity" in keys

    def test_sensor_get_entries_heater_excluded_from_temp(self):
        """Test that heater devices are excluded from standalone temperature sensor."""
        device = self.create_mock_device(name="Test Heater", serial_number="HTR001", type="Heater", features={"temperature": 75})

        entities = sensor.get_entries([device])
        keys = [e.entity_description.key for e in entities]
        # Heaters should NOT get standalone temperature sensor (they use climate entity)
        assert "Temperature" not in keys

    def test_sensor_get_entries_ac_excluded_from_temp(self):
        """Test that air conditioner devices are excluded from standalone temperature sensor."""
        device = self.create_mock_device(name="Test AC", serial_number="AC001", type="Air Conditioner", features={"temperature": 72})

        entities = sensor.get_entries([device])
        keys = [e.entity_description.key for e in entities]
        assert "Temperature" not in keys

    def test_sensor_get_entries_no_features(self):
        """Test that devices without sensor features get no sensor entities."""
        device = self.create_mock_device(name="Simple Fan", serial_number="FAN001", features={"is_on": True, "fan_speed": 3})

        entities = sensor.get_entries([device])
        assert len(entities) == 0

    def test_sensor_entity_properties(self):
        """Test sensor entity basic properties."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Test Humidifier", serial_number="HUM001", type="Humidifier", features={"temperature": 72})

            entities = sensor.get_entries([device])
            temp_sensor = next(e for e in entities if e.entity_description.key == "Temperature")
            assert temp_sensor.name == "Test Humidifier Temperature"
            assert temp_sensor.unique_id == "HUM001-Temperature"

    def test_sensor_native_value(self):
        """Test the native_value property for temperature sensor."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Test Humidifier", serial_number="HUM001", type="Humidifier", features={"temperature": 72})

            entities = sensor.get_entries([device])
            temp_sensor = next(e for e in entities if e.entity_description.key == "Temperature")
            assert temp_sensor.native_value == 72

            # Simulate device update
            device.temperature = 75
            assert temp_sensor.native_value == 75

    def test_sensor_humidity_native_value(self):
        """Test the native_value property for humidity sensor."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Test Humidifier", serial_number="HUM001", type="Humidifier", features={"humidity": 55})

            entities = sensor.get_entries([device])
            hum_sensor = next(e for e in entities if e.entity_description.key == "Humidity")
            assert hum_sensor.native_value == 55

    def test_sensor_repr(self):
        """Test the repr method of DreoSensorHA."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Test Device", serial_number="DEV001", type="Humidifier", features={"temperature": 72})

            entities = sensor.get_entries([device])
            repr_str = repr(entities[0])
            assert "DreoSensorHA" in repr_str

    def test_sensor_work_time(self):
        """Test work_time sensor creation."""
        device = self.create_mock_device(name="Test Purifier", serial_number="PUR001", type="Air Purifier", features={"work_time": 120})

        entities = sensor.get_entries([device])
        keys = [e.entity_description.key for e in entities]
        assert "Use since cleaning" in keys

    def test_sensor_pm25(self):
        """Test PM2.5 sensor creation."""
        device = self.create_mock_device(name="Test Purifier", serial_number="PUR001", type="Air Purifier", features={"pm25": 15})

        entities = sensor.get_entries([device])
        keys = [e.entity_description.key for e in entities]
        assert "pm25" in keys

    def test_sensor_multiple_devices(self):
        """Test get_entries with multiple devices."""
        device1 = self.create_mock_device(name="Humidifier", serial_number="HUM001", type="Humidifier", features={"temperature": 72, "humidity": 55})
        device2 = self.create_mock_device(name="Fan", serial_number="FAN001", type="Tower Fan", features={"temperature": 68})

        entities = sensor.get_entries([device1, device2])
        # Humidifier gets temperature + humidity, fan gets temperature
        assert len(entities) == 3

    def test_sensor_unit_of_measurement(self):
        """Test that unit of measurement is set correctly from fn."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Test Humidifier", serial_number="HUM001", type="Humidifier", features={"humidity": 55})

            entities = sensor.get_entries([device])
            hum_sensor = next(e for e in entities if e.entity_description.key == "Humidity")
            assert hum_sensor._attr_native_unit_of_measurement == "%"

    def test_sensor_chefmaker_status(self):
        """Test ChefMaker status sensor creation."""
        device = self.create_mock_device(name="Chef Maker", serial_number="CM001", type="Chef Maker", features={"mode": "standby"})

        entities = sensor.get_entries([device])
        keys = [e.entity_description.key for e in entities]
        assert "Status" in keys

    def test_sensor_chefmaker_cook_time_remaining(self):
        """Test ChefMaker cook time remaining sensor creation."""
        device = self.create_mock_device(name="Chef Maker", serial_number="CM001", type="Chef Maker", features={"cook_time_remaining": 600})

        entities = sensor.get_entries([device])
        cook_time_sensor = next(e for e in entities if e.entity_description.key == "Cook time remaining")
        assert cook_time_sensor.native_value == 600
        assert cook_time_sensor._attr_native_unit_of_measurement == "s"
        
    def test_sensor_filter_life(self):
        """Test Filter Life sensor creation for humidifiers."""
        device = self.create_mock_device(name="Test Humidifier", serial_number="HUM001", type="Humidifier", features={"filtertime": 75})

        entities = sensor.get_entries([device])
        filter_life = next(e for e in entities if e.entity_description.key == "Filter Life")
        assert filter_life.native_value == 75
        assert filter_life._attr_native_unit_of_measurement == "%"


    def test_sensor_filter_active(self):
        """Test Filter Active sensor creation for humidifiers."""
        device = self.create_mock_device(name="Test Humidifier", serial_number="HUM001", type="Humidifier", features={"filteron": False})

        entities = sensor.get_entries([device])
        filter_active = next(e for e in entities if e.entity_description.key == "Filter Active")
        assert filter_active.native_value == "Inactive"
        assert filter_active.native_value in filter_active._attr_options

    def test_sensor_target_humidity_reached(self):
        """Test Target Humidity Reached sensor creation for humidifiers."""
        device = self.create_mock_device(name="Test Humidifier", serial_number="HUM001", type="Humidifier", features={"suspend": True})

        entities = sensor.get_entries([device])
        target_reached = next(e for e in entities if e.entity_description.key == "Target Humidity Reached")
        assert target_reached.native_value == "Yes"
        assert target_reached.native_value in target_reached._attr_options
