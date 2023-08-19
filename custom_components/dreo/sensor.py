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
from .pydreo.constant import TemperatureUnit

from .haimports import * # pylint: disable=W0401,W0614

from .const import (
    LOGGER,
    DOMAIN,
    DREO_MANAGER
)

_LOGGER = logging.getLogger(LOGGER)

@dataclass
class DreoSensorEntityDescription(SensorEntityDescription):
    """Describe Dreo sensor entity."""
    value_fn: Callable[[DreoFanHA], StateType] = None
    exists_fn: Callable[[DreoFanHA], bool] = None
    native_unit_of_measurement_fn: Callable[[DreoFanHA], str] = None

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
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo sensor platform."""
    _LOGGER.info("Starting Dreo Sensor Platform")
    _LOGGER.debug("Dreo Sensor:async_setup_platform")

    manager = hass.data[DOMAIN][DREO_MANAGER]

    sensorsHAs = []
    for fanEntity in manager.fans:
        # Really ugly hack since there is just one sensor for now...
        sensorsHAs.append(DreoSensorHA(fanEntity, SENSORS[0]))

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
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement_fn(self.device)
        
    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.device)