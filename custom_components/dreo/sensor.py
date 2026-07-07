"""Support Sensors for some Dreo devices"""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.const import UnitOfTime

from .dreobasedevice import DreoBaseDeviceHA
from .pydreo import PyDreo
from .pydreo.pydreobasedevice import PyDreoBaseDevice
from .pydreo.constant import HUMIDITY_KEY, MODE_KEY, PM25_KEY, DreoDeviceType


from .haimports import *  # pylint: disable=W0401,W0614

from .const import (
    DOMAIN,
    PYDREO_MANAGER,
)

from .pydreo.pydreochefmaker import (
    MODE_OFF,
    MODE_COOKING,
    MODE_STANDBY,
    MODE_PAUSED,
    MODE_COMPLETE,
)

from .pydreo.pydreohumidifier import (
    WORKTIME_KEY,
    FILTERTIME_KEY,
    FILTERON_KEY,
    SUSPEND_KEY,
    MODE_NORMAL,
    MODE_AUTO,
    MODE_SLEEP,
    WATER_LEVEL_OK,
    WATER_LEVEL_EMPTY,
    WATER_LEVEL_STATUS_KEY,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class DreoSensorEntityDescription(SensorEntityDescription):
    """Describe Dreo sensor entity."""

    value_fn: Callable[[DreoBaseDeviceHA], StateType] = None
    exists_fn: Callable[[DreoBaseDeviceHA], bool] = None
    native_unit_of_measurement_fn: Callable[[DreoBaseDeviceHA], str] = None


SENSORS: tuple[DreoSensorEntityDescription, ...] = (
    DreoSensorEntityDescription(
        key="Temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        value_fn=lambda device: device.temperature,
        exists_fn=lambda device: (
            (device.type not in {DreoDeviceType.HEATER, DreoDeviceType.AIR_CONDITIONER}) and device.is_feature_supported("temperature")
        ),
    ),
    DreoSensorEntityDescription(
        key="Humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement_fn=lambda device: "%",
        value_fn=lambda device: device.humidity,
        exists_fn=lambda device: device.is_feature_supported("humidity"),
    ),
    DreoSensorEntityDescription(
        key="Use since cleaning",
        translation_key="use_hours",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement_fn=lambda device: "h",
        value_fn=lambda device: device.work_time,
        exists_fn=lambda device: device.is_feature_supported("work_time"),
    ),
    DreoSensorEntityDescription(
        key="Target temp reached",
        translation_key="reach_target_temp",
        device_class=SensorDeviceClass.ENUM,
        options=["Yes", "No"],
        value_fn=lambda device: device.temp_target_reached,
        exists_fn=lambda device: device.is_feature_supported("temp_target_reached"),
    ),
    DreoSensorEntityDescription(
        key="Status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=[MODE_STANDBY, MODE_COOKING, MODE_OFF, MODE_PAUSED, MODE_COMPLETE],
        value_fn=lambda device: device.mode,
        exists_fn=lambda device: (device.type in {DreoDeviceType.CHEF_MAKER}) and device.is_feature_supported(MODE_KEY),
    ),
    DreoSensorEntityDescription(
        key="Cook time remaining",
        translation_key="cook_time_remaining",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda device: device.cook_time_remaining,
        exists_fn=lambda device: (device.type in {DreoDeviceType.CHEF_MAKER}) and device.is_feature_supported("cook_time_remaining"),
    ),
    DreoSensorEntityDescription(
        key="pm25",
        translation_key="pm25",
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        value_fn=lambda device: device.pm25,
        exists_fn=lambda device: device.is_feature_supported(PM25_KEY),
    ),
    DreoSensorEntityDescription(
        key="Water Level",
        translation_key="water",
        device_class=SensorDeviceClass.ENUM,
        options=[WATER_LEVEL_OK, WATER_LEVEL_EMPTY],
        value_fn=lambda device: device.water_level,
        exists_fn=lambda device: (device.type != DreoDeviceType.HUMIDIFIER) and device.is_feature_supported(WATER_LEVEL_STATUS_KEY),
    ),
    DreoSensorEntityDescription(
        key="Use since cleaning HM",
        translation_key="use_hours_hm",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement_fn=lambda device: "h",
        value_fn=lambda device: device.worktime,
        exists_fn=lambda device: (device.type in {DreoDeviceType.HUMIDIFIER}) and device.is_feature_supported(WORKTIME_KEY),
    ),
    DreoSensorEntityDescription(
        key="Filter Life",
        translation_key="filter_life",
        icon="mdi:air-filter",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement_fn=lambda device: "%",
        value_fn=lambda device: device.filtertime,
        exists_fn=lambda device: (device.type in {DreoDeviceType.HUMIDIFIER}) and device.is_feature_supported(FILTERTIME_KEY),
    ),
    DreoSensorEntityDescription(
        key="Filter Active",
        translation_key="filter_active",
        icon="mdi:filter-check",
        device_class=SensorDeviceClass.ENUM,
        options=["Active", "Inactive"],
        value_fn=lambda device: None if device.filteron is None else ("Active" if device.filteron else "Inactive"),
        exists_fn=lambda device: (device.type in {DreoDeviceType.HUMIDIFIER}) and device.is_feature_supported(FILTERON_KEY),
    ),
    DreoSensorEntityDescription(
        key="Target Humidity Reached",
        translation_key="target_humidity_reached",
        icon="mdi:water-check",
        device_class=SensorDeviceClass.ENUM,
        options=["Yes", "No"],
        value_fn=lambda device: None if device.suspend is None else ("Yes" if device.suspend else "No"),
        exists_fn=lambda device: (device.type in {DreoDeviceType.HUMIDIFIER, DreoDeviceType.EVAPORATIVE_COOLER}) and device.is_feature_supported(SUSPEND_KEY),
    ),
)


def get_entries(pydreo_devices: list[PyDreoBaseDevice]) -> list[DreoSensorHA]:
    """Add Sensor entries for Dreo devices."""
    sensor_ha_collection: list[DreoSensorHA] = []

    for pydreo_device in pydreo_devices:
        _LOGGER.debug("get_entries: Adding Sensors for %s", pydreo_device.name)
        sensor_keys: list[str] = []

        for sensor_definition in SENSORS:
            _LOGGER.debug("get_entries: checking exists fn: %s on %s", sensor_definition.key, pydreo_device.name)

            if sensor_definition.exists_fn(pydreo_device):
                if sensor_definition.key in sensor_keys:
                    _LOGGER.error("get_entries: Duplicate sensor key %s", sensor_definition.key)
                    continue

                _LOGGER.debug("get_entries: Adding Sensor %s", sensor_definition.key)
                sensor_keys.append(sensor_definition.key)

                sensor_ha_collection.append(DreoSensorHA(pydreo_device, sensor_definition))

    return sensor_ha_collection


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Sensor platform."""
    _LOGGER.info("get_entries: Starting Dreo Sensor Platform")

    pydreo_manager: PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    async_add_entities(get_entries(pydreo_manager.devices))


class DreoSensorHA(DreoBaseDeviceHA, SensorEntity):
    """Representation of a sensor describing a read-only property of a Dreo device."""

    def __init__(self, pyDreoDevice: PyDreoBaseDevice, description: DreoSensorEntityDescription) -> None:
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice

        # Note this is a "magic" HA property.  Don't rename
        self.entity_description = description
        # Use has_entity_name + translation_key so the entity name (and, where
        # provided, state values) are localized from the translations/*.json files.
        # The base class sets _attr_name to the device name; delete it so the
        # translation_key on the entity description is used instead.
        self._attr_has_entity_name = True
        del self._attr_name
        self._attr_unique_id = f"{super().unique_id}-{description.key}"
        if description.native_unit_of_measurement_fn is not None:
            self._attr_native_unit_of_measurement = description.native_unit_of_measurement_fn(self.device)
        if description.options is not None:
            self._attr_options = description.options

        _LOGGER.info("new DreoSensorHA instance(%s), unique ID %s", description.translation_key, self._attr_unique_id)

    def __repr__(self):
        # Representation string of object.
        return f"<{self.__class__.__name__}:{self.entity_description}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.device)
