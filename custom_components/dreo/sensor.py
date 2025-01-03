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
    TemperatureUnit,
    HUMIDITY_KEY,
    MODE_KEY,
    DreoDeviceType
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
        exists_fn=lambda device: device.is_feature_supported("temperature"),
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
    )
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo sensor platform."""
    _LOGGER.info("Starting Dreo Sensor Platform")

    pydreo_manager : PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    sensor_has : list[SensorEntity] = []
    for pydreo_device in pydreo_manager.devices:

        if (pydreo_device.type == DreoDeviceType.TOWER_FAN or
            pydreo_device.type == DreoDeviceType.AIR_CIRCULATOR or
            pydreo_device.type == DreoDeviceType.AIR_PURIFIER):
            # Really ugly hack since there is just one sensor for now...
            sensor_has.append(DreoSensorHA(pydreo_device, SENSORS[0]))

        if pydreo_device.type == DreoDeviceType.HEATER:
            # Really ugly hack since there is just one sensor for now...
            sensor_has.append(DreoSensorHA(pydreo_device, SENSORS[0]))

        if pydreo_device.type == DreoDeviceType.AIR_CONDITIONER:
            # Really ugly hack...
            sensor_has.append(DreoSensorHA(pydreo_device, SENSORS[0]))
            sensor_has.append(DreoSensorHA(pydreo_device, SENSORS[1]))
            sensor_has.append(DreoSensorHA(pydreo_device, SENSORS[2]))
            sensor_has.append(DreoSensorHA(pydreo_device, SENSORS[3]))

        if pydreo_device.type == DreoDeviceType.CHEF_MAKER:
            # Really ugly hack...
            sensor_has.append(DreoSensorHA(pydreo_device, SENSORS[4]))

    async_add_entities(sensor_has)


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

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.device)
