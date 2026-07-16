"""Support Select entities for some Dreo devices."""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import logging

from .haimports import *  # pylint: disable=W0401,W0614
from .dreobasedevice import DreoBaseDeviceHA
from .pydreo import PyDreo
from .pydreo.pydreobasedevice import PyDreoBaseDevice
from .pydreo.constant import DreoDeviceType

from .const import DOMAIN, PYDREO_MANAGER

_LOGGER = logging.getLogger(__name__)


@dataclass
class DreoSelectEntityDescription(SelectEntityDescription):
    """Describe Dreo Select entity."""

    attr_name: str | None = None
    options_list: list[str] = field(default_factory=list)
    raw_values: list[int] = field(default_factory=list)
    exists_fn: Callable[[PyDreoBaseDevice], bool] | None = None


SELECTS: tuple[DreoSelectEntityDescription, ...] = (
    DreoSelectEntityDescription(
        key="Mist Level",
        translation_key="mist_level",
        attr_name="mist_level",
        icon="mdi:weather-windy",
        options_list=["low", "medium", "high"],
        raw_values=[1, 2, 3],
        exists_fn=lambda device: device.type in {DreoDeviceType.HUMIDIFIER, DreoDeviceType.EVAPORATIVE_COOLER} 
        and device.is_feature_supported("mist_level"),
    ),
    DreoSelectEntityDescription(
        key="Ambient Light Mode",
        translation_key="ambient_light_mode",
        attr_name="rgbmode",
        icon="mdi:lightbulb-cog",
        options_list=["humidity", "color"],
        raw_values=[0, 1, 2, 3],
        exists_fn=lambda device: device.type in {DreoDeviceType.HUMIDIFIER, DreoDeviceType.EVAPORATIVE_COOLER}
        and device.is_feature_supported("rgbmode"),
    ),
    DreoSelectEntityDescription(
        key="3D Angle Preset",
        translation_key="three_d_angle_preset",
        attr_name="angle_preset",
        icon="mdi:axis-arrow",
        exists_fn=lambda device: device.type == DreoDeviceType.AIR_CIRCULATOR and device.is_feature_supported("angle_preset"),
    ),
)


def get_entries(pydreo_devices: list[PyDreoBaseDevice]) -> list["DreoSelectHA"]:
    """Create Select entities for supported devices."""
    entities: list[DreoSelectHA] = []

    for device in pydreo_devices:
        for sel in SELECTS:
            if sel.exists_fn is not None and not sel.exists_fn(device):
                continue
            if not device.is_feature_supported(sel.attr_name):
                continue
            entities.append(DreoSelectHA(device, sel))

    return entities


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Select platform."""
    _LOGGER.info("Starting Dreo Select Platform")

    pydreo_manager: PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]
    async_add_entities(get_entries(pydreo_manager.devices))


class DreoSelectHA(DreoBaseDeviceHA, SelectEntity):
    """Representation of a Select describing a read-write property of a Dreo device."""

    def __init__(self, device: PyDreoBaseDevice, description: DreoSelectEntityDescription) -> None:
        super().__init__(device)
        self.device = device
        self.entity_description = description

        self._attr_has_entity_name = True
        del self._attr_name
        self._attr_translation_key = description.translation_key
        self._attr_unique_id = f"{super().unique_id}-{description.key}"
        self._attr_options = self._get_device_options()

    def _get_device_options(self) -> list[str]:
        """Return current options list for this select."""
        options_attr_name = f"{self.entity_description.attr_name}_options"
        options = getattr(self.device, options_attr_name, None)
        if isinstance(options, list) and len(options) > 0:
            return options
        return self.entity_description.options_list

    @property
    def options(self) -> list[str]:
        """Return the list of selectable options."""
        self._attr_options = self._get_device_options()
        return self._attr_options

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        raw = getattr(self.device, self.entity_description.attr_name)
        if raw is None:
            return None
        if len(self.entity_description.raw_values) == 0:
            return str(raw)
        try:
            idx = self.entity_description.raw_values.index(int(raw))
            return self.entity_description.options_list[idx]
        except (ValueError, IndexError):
            return None

    def select_option(self, option: str) -> None:
        """Set a new option."""
        if len(self.entity_description.raw_values) == 0:
            setattr(self.device, self.entity_description.attr_name, option)
            return
        try:
            idx = self.entity_description.options_list.index(option)
        except ValueError:
            return
        setattr(self.device, self.entity_description.attr_name, self.entity_description.raw_values[idx])
