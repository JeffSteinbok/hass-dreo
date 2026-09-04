"""Support directional angle nudge buttons for some Dreo devices."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from .haimports import *  # pylint: disable=W0401,W0614
from .dreobasedevice import DreoBaseDeviceHA
from .pydreo import PyDreo, PyDreoBaseDevice
from .pydreo.constant import DreoDeviceType
from .const import DOMAIN, PYDREO_MANAGER

_LOGGER = logging.getLogger(__name__)


@dataclass
class DreoButtonEntityDescription(ButtonEntityDescription):
    """Describe Dreo Button entity."""

    press_method: str | None = None
    exists_fn: Callable[[PyDreoBaseDevice], bool] | None = None


BUTTONS: tuple[DreoButtonEntityDescription, ...] = (
    DreoButtonEntityDescription(
        key="Pan Left",
        icon="mdi:arrow-left-bold",
        press_method="nudge_horizontal_left",
        exists_fn=lambda device: device.type == DreoDeviceType.AIR_CIRCULATOR and device.is_feature_supported("horizontal_angle_nudge"),
    ),
    DreoButtonEntityDescription(
        key="Pan Right",
        icon="mdi:arrow-right-bold",
        press_method="nudge_horizontal_right",
        exists_fn=lambda device: device.type == DreoDeviceType.AIR_CIRCULATOR and device.is_feature_supported("horizontal_angle_nudge"),
    ),
    DreoButtonEntityDescription(
        key="Tilt Up",
        icon="mdi:arrow-up-bold",
        press_method="nudge_vertical_up",
        exists_fn=lambda device: device.type == DreoDeviceType.AIR_CIRCULATOR and device.is_feature_supported("vertical_angle_nudge"),
    ),
    DreoButtonEntityDescription(
        key="Tilt Down",
        icon="mdi:arrow-down-bold",
        press_method="nudge_vertical_down",
        exists_fn=lambda device: device.type == DreoDeviceType.AIR_CIRCULATOR and device.is_feature_supported("vertical_angle_nudge"),
    ),
)


def get_entries(pydreo_devices: list[PyDreoBaseDevice]) -> list["DreoButtonHA"]:
    """Create Button entities for supported devices."""
    entities: list[DreoButtonHA] = []

    for device in pydreo_devices:
        for button_description in BUTTONS:
            if button_description.exists_fn is None or not button_description.exists_fn(device):
                continue
            entities.append(DreoButtonHA(device, button_description))

    return entities


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Button platform."""
    _LOGGER.info("Starting Dreo Button Platform")

    pydreo_manager: PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]
    async_add_entities(get_entries(pydreo_manager.devices))


class DreoButtonHA(DreoBaseDeviceHA, ButtonEntity):
    """Representation of a stateless button action for a Dreo device."""

    def __init__(self, device: PyDreoBaseDevice, description: DreoButtonEntityDescription) -> None:
        super().__init__(device)
        self.device = device
        self.entity_description = description

        self._attr_has_entity_name = True
        self._attr_name = description.key
        self._attr_unique_id = f"{super().unique_id}-{description.key}"

    def press(self) -> None:
        """Press the button."""
        press_method = self.entity_description.press_method
        if press_method is None:
            return
        getattr(self.device, press_method)()
