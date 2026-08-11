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
    WATER_LEVEL_KEY as EVAP_WATER_LEVEL_KEY,
    WATER_LEVEL_EMPTY as EVAP_WATER_LEVEL_EMPTY,
)
from .pydreo.pydreodehumidifier import (
    ERROR_CODE_KEY as DEHUMIDIFIER_ERROR_CODE_KEY,
    ERROR_CODE_WATER_EMPTY as DEHUMIDIFIER_WATER_EMPTY,
)
from .haimports import *  # pylint: disable=W0401,W0614
from .const import DOMAIN, PYDREO_MANAGER

_LOGGER = logging.getLogger(__name__)


@dataclass
class DreoBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describe Dreo binary sensor entity."""

    value_fn: Callable[[PyDreoBaseDevice], bool | None] = None
    exists_fn: Callable[[PyDreoBaseDevice], bool] = None
    icon_fn: Callable[[PyDreoBaseDevice], str] = None
    attrs_fn: Callable[[PyDreoBaseDevice], dict] = None
    # Suffix appended to the device serial to form the entity's unique_id.
    # Defaults to `key`; water_empty pins its historical "water-empty" spelling
    # because changing a unique_id orphans the entity in users' registries.
    unique_id_suffix: str = None


def _water_empty_value(device: PyDreoBaseDevice) -> bool | None:
    if device.type == DreoDeviceType.HUMIDIFIER:
        return device.water_level == WATER_LEVEL_EMPTY
    if device.type == DreoDeviceType.EVAPORATIVE_COOLER:
        return device.water_level == EVAP_WATER_LEVEL_EMPTY
    if device.type == DreoDeviceType.DEHUMIDIFIER:
        return device.water_level == DEHUMIDIFIER_WATER_EMPTY
    return None


def _water_empty_exists(device: PyDreoBaseDevice) -> bool:
    if device.type == DreoDeviceType.HUMIDIFIER:
        return device.is_feature_supported(WATER_LEVEL_STATUS_KEY)
    if device.type == DreoDeviceType.EVAPORATIVE_COOLER:
        return device.is_feature_supported(EVAP_WATER_LEVEL_KEY)
    if device.type == DreoDeviceType.DEHUMIDIFIER:
        return device.is_feature_supported(DEHUMIDIFIER_ERROR_CODE_KEY)
    return False


def _fixed_conf_settle_pending(device: PyDreoBaseDevice) -> bool:
    return bool(getattr(device, "fixed_conf_settle_pending", False))


def _fixed_conf_attrs(device: PyDreoBaseDevice) -> dict:
    debug = getattr(device, "fixed_conf_debug_state", None)
    if isinstance(debug, dict):
        return debug
    return {
        "reported": getattr(device, "fixed_conf_reported", None),
        "commanded": getattr(device, "fixed_conf_commanded", None),
        "pending_target": getattr(device, "fixed_conf_pending_target", None),
        "settle_seconds": getattr(device, "fixed_conf_settle_seconds", None),
    }


BINARY_SENSORS: tuple[DreoBinarySensorEntityDescription, ...] = (
    DreoBinarySensorEntityDescription(
        key="water_empty",
        translation_key="water_empty",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_registry_enabled_default=True,
        value_fn=_water_empty_value,
        exists_fn=_water_empty_exists,
        icon_fn=lambda device: "mdi:water-remove" if _water_empty_value(device) else "mdi:water-check",
        attrs_fn=lambda device: {"water_level": getattr(device, "water_level", None)},
        unique_id_suffix="water-empty",  # pre-dates the key-derived default; do not change
    ),
    DreoBinarySensorEntityDescription(
        key="main_power",
        translation_key="main_power",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=True,
        # No device_class, and no state strings of our own: plain On/Off reads
        # clearest here and HA core localizes it for free. The obvious classes
        # render worse - POWER as "Detected"/"Clear", RUNNING as "Running"/
        # "Not running".
        value_fn=lambda device: device.poweron,
        exists_fn=lambda device: device.type == DreoDeviceType.CEILING_FAN and device.poweron is not None,
        icon_fn=lambda device: "mdi:power" if device.poweron else "mdi:power-off",
        attrs_fn=lambda device: device.gate_diagnostics(),
    ),
    # Diagnostic: models with fixedconf settle (e.g. DR-HPF017S) queue axis
    # updates while the head is moving; enable this entity to observe the queue.
    DreoBinarySensorEntityDescription(
        key="fixed_conf_settle_pending",
        translation_key="fixed_conf_settle_pending",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_fixed_conf_settle_pending,
        exists_fn=lambda device: device.is_feature_supported("fixed_conf_settle_pending"),
        icon_fn=lambda device: "mdi:timer-sand" if _fixed_conf_settle_pending(device) else "mdi:timer-sand-complete",
        attrs_fn=_fixed_conf_attrs,
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
        # Use has_entity_name + translation_key so the entity name and its
        # on/off state text are localized from the translations/*.json files.
        self._attr_has_entity_name = True
        del self._attr_name
        self._attr_unique_id = f"{super().unique_id}-{description.unique_id_suffix or description.key}"
        if description.entity_category is not None:
            self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = description.entity_registry_enabled_default

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.device)

    @property
    def icon(self) -> str:
        if self.entity_description.icon_fn is None:
            return None
        return self.entity_description.icon_fn(self.device)

    @property
    def extra_state_attributes(self) -> dict:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.device)
