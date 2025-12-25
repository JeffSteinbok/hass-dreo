"""Support additionl Numberes for some Dreo devices"""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613
from __future__ import annotations
from dataclasses import dataclass
import logging

from .haimports import * # pylint: disable=W0401,W0614
from .pydreo import PyDreo
from .pydreo.pydreobasedevice import PyDreoBaseDevice
from .dreobasedevice import DreoBaseDeviceHA

from .const import (
    LOGGER,
    DOMAIN,
    PYDREO_MANAGER
)

_LOGGER = logging.getLogger(LOGGER)

@dataclass
class DreoNumberEntityDescription(NumberEntityDescription):
    """Describe Dreo Number entity."""
    attr_name: str = None
    icon: str = None

    def __repr__(self):
        # Representation string of object.
        return f"<{self.__class__.__name__}:{self.attr_name}:{self.key}>"


NUMBERS: tuple[DreoNumberEntityDescription, ...] = (
    DreoNumberEntityDescription(
        key="Horizontal Angle",
        translation_key="horizontal_angle",
        attr_name="horizontal_angle",
        icon="mdi:angle-acute",
        min_value=-60,
        max_value=60,
    ),
    DreoNumberEntityDescription(
        key="Vertical Angle",
        translation_key="vertical_angle",
        attr_name="vertical_angle",
        icon="mdi:angle-acute",
        min_value=0,
        max_value=90
    ),
    DreoNumberEntityDescription(
        key="Horizontal Oscillation Angle Left",
        translation_key="horizontal_osc_angle_left",
        attr_name="horizontal_osc_angle_left",
        icon="mdi:vector-radius",
        min_value=-60,
        max_value=60,
    ),
    DreoNumberEntityDescription(
        key="Horizontal Oscillation Angle Right",
        translation_key="horizontal_osc_angle_right",
        attr_name="horizontal_osc_angle_right",
        icon="mdi:vector-radius",
        min_value=-60,
        max_value=60,
    ),
    DreoNumberEntityDescription(
        key="Vertical Oscillation Angle Top",
        translation_key="vertical_osc_angle_top",
        attr_name="vertical_osc_angle_top",
        icon="mdi:vector-radius",
        min_value=0,
        max_value=90
    ),
    DreoNumberEntityDescription(
        key="Vertical Oscillation Angle Bottom",
        translation_key="vertical_osc_angle_bottom",
        attr_name="vertical_osc_angle_bottom",
        icon="mdi:vector-radius",
        min_value=0,
        max_value=90
    ),
    DreoNumberEntityDescription(
        key="Oscillation Angle",
        translation_key="osc_angle",
        attr_name="shakehorizonangle",
        icon="mdi:angle-acute",
        min_value=30,
        max_value=120,
        step = 30
    ),
    DreoNumberEntityDescription(
        key="Horizontal Oscillation Angle",
        translation_key="horizontal_oscillation_angle",
        attr_name="horizontal_oscillation_angle",
        icon="mdi:angle-acute",
        min_value=-60,
        max_value=60,
    ),
    DreoNumberEntityDescription(
        key="Vertical Oscillation Angle",
        translation_key="vertical_oscillation_angle",
        attr_name="vertical_oscillation_angle",
        icon="mdi:angle-acute",
        min_value=0,
        max_value=90,
    ),
    DreoNumberEntityDescription(
        key="Heat Level",
        translation_key="htalevel",
        attr_name="htalevel",
        icon="mdi:heat-wave"
    ),
    DreoNumberEntityDescription(
        key="Target Humidity",
        translation_key="target_humidity",
        attr_name="target_humidity",
        icon="mdi:water-percent",
        min_value=40,
        max_value=90,
    )
)

def get_entries(pydreo_devices : list[PyDreoBaseDevice]) -> list[DreoNumberHA]:
    """Add Number entries for Dreo devices."""
    number_ha_collection : list[DreoNumberHA] = []
    
    for pydreo_device in pydreo_devices:
        _LOGGER.debug("Number:get_entries: Adding Numbers for %s", pydreo_device.name)
        number_keys : list[str] = []
        
        for number_definition in NUMBERS:
            _LOGGER.debug("Number:get_entries: checking attribute: %s on %s", number_definition.attr_name, pydreo_device.name)

            if pydreo_device.is_feature_supported(number_definition.attr_name):
                if (number_definition.key in number_keys):
                    _LOGGER.error("Number:get_entries: Duplicate number key %s", number_definition.key)
                    continue

                _LOGGER.debug("Number:get_entries: Adding Number %s for %s", number_definition.key, number_definition.attr_name)
                number_keys.append(number_definition.key)

                device_range = get_device_range(pydreo_device, number_definition)
                if device_range is not None and isinstance(device_range, tuple):
                    dned = DreoNumberEntityDescription(
                        key=number_definition.key,
                        translation_key=number_definition.translation_key,
                        attr_name=number_definition.attr_name,
                        icon=number_definition.icon,
                        min_value=device_range[0],
                        max_value=device_range[1],
                        device_class=number_definition.device_class,
                        native_unit_of_measurement=number_definition.native_unit_of_measurement,
                    )
                    number_ha_collection.append(DreoNumberHA(pydreo_device, dned))
                else:
                    number_ha_collection.append(DreoNumberHA(pydreo_device,number_definition))
    
    return number_ha_collection

def get_device_range(device: PyDreoBaseDevice, number_definition: DreoNumberEntityDescription) -> tuple | None:
    """Returns the device-specific range for a Number."""
    range_name = number_definition.attr_name + "_range"

    range_from_device = getattr(device, range_name, None)
    if range_from_device is not None:
        _LOGGER.debug("Number:get_device_range: range %s from device is %s", range_name, range_from_device)
        return range_from_device

    range_from_device_definition = getattr(device.device_definition.device_ranges, range_name, None)
    if range_from_device_definition is not None:
        _LOGGER.debug("Number:get_device_range: range %s from device definition is %s", range_name,
                      range_from_device_definition)
        return range_from_device_definition

    return None

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Number platform."""
    _LOGGER.info("Starting Dreo Number Platform")

    pydreo_manager : PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    async_add_entities(get_entries(pydreo_manager.devices))


class DreoNumberHA(DreoBaseDeviceHA, NumberEntity): # pylint: disable=abstract-method
    """Representation of a Number describing a read-only property of a Dreo device."""

    def __init__(self, 
                    pyDreoDevice: PyDreoBaseDevice,
                    description: DreoNumberEntityDescription) -> None:
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice

        # Note this is a "magic" HA property.  Don't rename
        self.entity_description = description

        self._attr_name = super().name + " " + description.key
        self._attr_unique_id = f"{super().unique_id}-{description.key}"

        self._attr_native_min_value = description.min_value
        self._attr_native_max_value = description.max_value
        self._attr_native_step = description.step
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._device_class_name = description.device_class

        _LOGGER.info(
            "new DreoSensorHA instance(%s), unique ID %s",
            self._attr_name,
            self._attr_unique_id)

    def __repr__(self):
        # Representation string of object.
        return f"<{self.__class__.__name__}:{self.entity_description}"
    
    @property
    def native_value(self) -> float:
        """Return the state of the number."""
        return getattr(self.device, self.entity_description.attr_name)

    def set_native_value(self, value: float) -> None:
        return setattr(self.device, self.entity_description.attr_name, value)
