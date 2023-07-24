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

SENSORS: tuple[DreoSensorEntityDescription, ...] = (
    DreoSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
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
                 definition: DreoSensorEntityDescription) -> None:
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice
        self.entity_definition = definition
        self._attr_name = super().name + " " + definition.key
        self._attr_unique_id = f"{super().unique_id}-{definition.key}"
        self._attr_device_class = definition.device_class
        self._attr_state_class = definition.state_class

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_definition.value_fn(self.device)