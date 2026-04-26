"""Support Binary Sensors for Dreo devices."""
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
from .pydreo.constant import DreoDeviceType
from .pydreo.pydreohumidifier import WATER_LEVEL_STATUS_KEY, WATER_LEVEL_EMPTY
from .pydreo.pydreoevaporativecooler import (
    WATER_LEVEL_STATUS_KEY as EVAP_WATER_LEVEL_STATUS_KEY,
    WATER_LEVEL_EMPTY as EVAP_WATER_LEVEL_EMPTY,
)
from .haimports import *  # pylint: disable=W0401,W0614
from .const import DOMAIN, PYDREO_MANAGER

_LOGGER = logging.getLogger(__name__)


@dataclass
class DreoBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describe Dreo binary sensor entity."""

    value_fn: Callable[[PyDreoBaseDevice], bool | None] = None
    exists_fn: Callable[[PyDreoBaseDevice], bool] = None


def _water_empty_value(device: PyDreoBaseDevice) -> bool | None:
    if device.type == DreoDeviceType.HUMIDIFIER:
        return device.water_level == WATER_LEVEL_EMPTY
    if device.type == DreoDeviceType.EVAPORATIVE_COOLER:
        return device.water_level == EVAP_WATER_LEVEL_EMPTY
    return None


def _water_empty_exists(device: PyDreoBaseDevice) -> bool:
    if device.type == DreoDeviceType.HUMIDIFIER:
        return device.is_feature_supported(WATER_LEVEL_STATUS_KEY)
    if device.type == DreoDeviceType.EVAPORATIVE_COOLER:
        return device.is_feature_supported(EVAP_WATER_LEVEL_STATUS_KEY)
    return False


BINARY_SENSORS: tuple[DreoBinarySensorEntityDescription, ...] = (
    DreoBinarySensorEntityDescription(
        key="water_empty",
        translation_key="water_empty",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_registry_enabled_default=True,
        value_fn=_water_empty_value,
        exists_fn=_water_empty_exists,
    ),
)


def get_entries(pydreo_devices: list[PyDreoBaseDevice]) -> list["DreoBinarySensorHA"]:
    """Create BinarySensor entities for supported devices."""
    entities: list[DreoBinarySensorHA] = []
    for device in pydreo_devices:
        for desc in BINARY_SENSORS:
            if desc.exists_fn(device):
                entities.append(DreoBinarySensorHA(device, desc))
    return entities


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,  # pylint: disable=unused-argument
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Binary Sensor platform."""
    _LOGGER.info("Starting Dreo Binary Sensor Platform")
    pydreo_manager: PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]
    async_add_entities(get_entries(pydreo_manager.devices))


class DreoBinarySensorHA(DreoBaseDeviceHA, BinarySensorEntity):
    """Representation of a Dreo binary sensor."""

    def __init__(
        self,
        device: PyDreoBaseDevice,
        description: DreoBinarySensorEntityDescription,
    ) -> None:
        super().__init__(device)
        self.device = device
        self.entity_description = description
        self._attr_name = super().name + " Water Empty"
        self._attr_unique_id = f"{super().unique_id}-water-empty"

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.device)

    @property
    def icon(self) -> str:
        return "mdi:water-remove" if self.is_on else "mdi:water-check"

    @property
    def extra_state_attributes(self) -> dict:
        return {"water_level": getattr(self.device, "water_level", None)}
