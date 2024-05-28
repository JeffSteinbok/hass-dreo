"""Support temperature for some Dreo fans"""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from .basedevice import DreoBaseDeviceHA
from .fan import DreoFanHA
from .pydreo.pydreobasedevice import PyDreoBaseDevice
from .pydreo.constant import (
    TemperatureUnit,
    HUMIDITY_KEY,
)

from .haimports import * # pylint: disable=W0401,W0614

from .const import (
    LOGGER,
    DOMAIN,
    DREO_MANAGER,
)

from .pydreo.pydreoac import (
    WORK_TIME,
    TEMP_TARGET_REACHED,
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
        native_unit_of_measurement_fn=lambda device: UnitOfTemperature.CELSIUS if (device.temperature_units == TemperatureUnit.CELCIUS) else UnitOfTemperature.FAHRENHEIT,
        value_fn=lambda device: device.temperature,
        exists_fn=lambda device: device.is_feature_supported("temperature")
    ),
    DreoSensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement_fn=lambda device: "%",
        value_fn=lambda device: device.humidity,
        exists_fn=lambda device: device.is_feature_supported(HUMIDITY_KEY)
    ),
    DreoSensorEntityDescription(
        key="Use since cleaning",
        translation_key="use_hours",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement_fn=lambda device: "h",
        value_fn=lambda device: device.work_time,
        exists_fn=lambda device: device.is_feature_supported(WORK_TIME)
    ),
    DreoSensorEntityDescription(
        key="Target temp reached",
        translation_key="reach_target_temp",
        device_class=SensorDeviceClass.ENUM,
        options=["Yes", "No"],
        value_fn=lambda device: device.temp_target_reached,
        exists_fn=lambda device: device.is_feature_supported(TEMP_TARGET_REACHED)
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo sensor platform."""
    _LOGGER.info("Starting Dreo Sensor Platform")

    manager = hass.data[DOMAIN][DREO_MANAGER]

    sensorsHAs = []
    for fanEntity in manager.fans:
        # Really ugly hack since there is just one sensor for now...
        sensorsHAs.append(DreoSensorHA(fanEntity, SENSORS[0]))

    for heaterEntity in manager.heaters:
        # Really ugly hack since there is just one sensor for now...
        sensorsHAs.append(DreoSensorHA(heaterEntity, SENSORS[0]))

    for acEntity in manager.acs:
        # Really ugly hack...
        sensorsHAs.append(DreoSensorHA(acEntity, SENSORS[0]))
        sensorsHAs.append(DreoSensorHA(acEntity, SENSORS[1]))
        sensorsHAs.append(DreoSensorHA(acEntity, SENSORS[2]))
        sensorsHAs.append(DreoSensorHA(acEntity, SENSORS[3]))

    async_add_entities(sensorsHAs)


class DreoSensorHA(DreoBaseDeviceHA, SensorEntity):
    """Representation of a sensor describing a read-only property of a Dreo device."""

    def __init__(self, 
                    pyDreoDevice: PyDreoBaseDevice,
                    description: DreoSensorEntityDescription) -> None:
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice
        
        # Note this is a "magic" HA property.  Don't rename
        self.entity_description = description
        self._attr_name = super().name + " " + description.key
        self._attr_unique_id = f"{super().unique_id}-{description.key}"
        if description.native_unit_of_measurement_fn is not None:
            self._attr_native_unit_of_measurement = description.native_unit_of_measurement_fn(self.device)
        if description.options is not None:
            self._attr_options = description.options
        
    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.device)