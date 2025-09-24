"""Support temperature for some Dreo fans"""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from .dreobasedevice import DreoBaseDeviceHA
from .pydreo import PyDreo
from .pydreo.pydreobasedevice import PyDreoBaseDevice
from .pydreo.constant import (
    HUMIDITY_KEY,
    MODE_KEY,
    PM25_KEY,
    DreoDeviceType
)

from .pydreo.pydreoevaporativecooler import (
    WATER_LEVEL_EMPTY, 
    WATER_LEVEL_OK, 
    WATER_LEVEL_STATUS_KEY
)

from .haimports import *  # pylint: disable=W0401,W0614

from .const import (
    LOGGER,
    DOMAIN,
    PYDREO_MANAGER,
)

from .pydreo.pydreoairconditioner import (
    WORK_TIME,
    TEMP_TARGET_REACHED,
)

from .pydreo.pydreochefmaker import (
    MODE_OFF,
    MODE_COOKING,
    MODE_STANDBY,
    MODE_PAUSED,
)

_LOGGER = logging.getLogger(LOGGER)


@dataclass
class DreoSensorEntityDescription(SensorEntityDescription):
    """Describe Dreo sensor entity."""

    value_fn: Callable[[DreoBaseDeviceHA], StateType] = None
    exists_fn: Callable[[DreoBaseDeviceHA], bool] = None
    native_unit_of_measurement_fn: Callable[[DreoBaseDeviceHA], str] = None


SENSORS: tuple[DreoSensorEntityDescription, ...] = (
    DreoSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        value_fn=lambda device: device.temperature,
        exists_fn=lambda device: (not device.type in { DreoDeviceType.HEATER, DreoDeviceType.AIR_CONDITIONER }) and device.is_feature_supported("temperature"),
    ),
    DreoSensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement_fn=lambda device: "%",
        value_fn=lambda device: device.humidity,
        exists_fn=lambda device: device.is_feature_supported(HUMIDITY_KEY),
    ),
    DreoSensorEntityDescription(
        key="Use since cleaning",
        translation_key="use_hours",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement_fn=lambda device: "h",
        value_fn=lambda device: device.work_time,
        exists_fn=lambda device: device.is_feature_supported(WORK_TIME),
    ),
    DreoSensorEntityDescription(
        key="Target temp reached",
        translation_key="reach_target_temp",
        device_class=SensorDeviceClass.ENUM,
        options=["Yes", "No"],
        value_fn=lambda device: device.temp_target_reached,
        exists_fn=lambda device: device.is_feature_supported(TEMP_TARGET_REACHED),
    ),
    DreoSensorEntityDescription(
        key="Status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=[MODE_STANDBY, MODE_COOKING, MODE_OFF, MODE_PAUSED],
        value_fn=lambda device: device.mode,
        exists_fn=lambda device: device.is_feature_supported(MODE_KEY),
    ),
    DreoSensorEntityDescription(
        key="pm25",
        translation_key="pm25",
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement_fn=lambda device: "%",
        value_fn=lambda device: device.pm25,
        exists_fn=lambda device: device.is_feature_supported(PM25_KEY),
    ),
    DreoSensorEntityDescription(
        key="Water Level",
        translation_key="water",
        device_class=SensorDeviceClass.ENUM,
        options=[WATER_LEVEL_OK, WATER_LEVEL_EMPTY],
        value_fn=lambda device: device.water_level,
        exists_fn=lambda device: device.is_feature_supported(WATER_LEVEL_STATUS_KEY),
    )
)

def get_entries(pydreo_devices : list[PyDreoBaseDevice]) -> list[DreoSensorHA]:
    """Add Sensor entries for Dreo devices."""
    sensor_ha_collection : list[DreoSensorHA] = []

    for pydreo_device in pydreo_devices:
        _LOGGER.debug("Sensor:get_entries: Adding Sensors for %s", pydreo_device.name)
        sensor_keys : list[str] = []
        
        for sensor_definition in SENSORS:
            _LOGGER.debug("Sensor:get_entries: checking exists fn: %s on %s", sensor_definition.key, pydreo_device.name)

            if sensor_definition.exists_fn(pydreo_device):
                if (sensor_definition.key in sensor_keys):
                    _LOGGER.error("Sensor:get_entries: Duplicate sensor key %s", sensor_definition.key)
                    continue

                _LOGGER.debug("Sensor:get_entries: Adding Sensor %s", sensor_definition.key)
                sensor_keys.append(sensor_definition.key)

                sensor_ha_collection.append(DreoSensorHA(pydreo_device, sensor_definition))

    return sensor_ha_collection


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Sensor platform."""
    _LOGGER.info("Starting Dreo Sensor Platform")

    pydreo_manager : PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    async_add_entities(get_entries(pydreo_manager.devices))


class DreoSensorHA(DreoBaseDeviceHA, SensorEntity):
    """Representation of a sensor describing a read-only property of a Dreo device."""

    def __init__(
        self, pyDreoDevice: PyDreoBaseDevice, description: DreoSensorEntityDescription
    ) -> None:
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice

        # Note this is a "magic" HA property.  Don't rename
        self.entity_description = description
        self._attr_name = super().name + " " + description.key
        self._attr_unique_id = f"{super().unique_id}-{description.key}"
        if description.native_unit_of_measurement_fn is not None:
            self._attr_native_unit_of_measurement = (
                description.native_unit_of_measurement_fn(self.device)
            )
        if description.options is not None:
            self._attr_options = description.options

        _LOGGER.info(
            "new DreoSensorHA instance(%s), unique ID %s",
            self._attr_name,
            self._attr_unique_id)

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.device)
