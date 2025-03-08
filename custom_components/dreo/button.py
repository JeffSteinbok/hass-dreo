"""Support buttons for some Dreo devices"""
from __future__ import annotations
from dataclasses import dataclass
import logging

from .haimports import * # pylint: disable=W0401,W0614
from .pydreo import PyDreo, PyDreoBaseDevice
from .pydreo.constant import DreoDeviceType
from .dreobasedevice import DreoBaseDeviceHA

from .const import (
    LOGGER,
    DOMAIN,
    PYDREO_MANAGER
)

_LOGGER = logging.getLogger(LOGGER)

@dataclass
class DreoButtonEntityDescription(ButtonEntityDescription):
    """Describe Dreo Button entity."""
    attr_name: str = None
    icon: str = None

    def __repr__(self):
        return f"<{self.__class__.__name__}:{self.attr_name}:{self.key}>"

BUTTONS: tuple[DreoButtonEntityDescription, ...] = (
    DreoButtonEntityDescription(
        key="Reset Filter Life",
        translation_key="reset_filter",
        attr_name="reset_filter",
        icon="mdi:filter-sync",
    ),
    DreoButtonEntityDescription(
        key="Reset Cleaning Reminder",
        translation_key="reset_work_time",
        attr_name="reset_work_time",
        icon="mdi:timer-sync",
    ),
)

def get_entries(pydreo_devices: list[PyDreoBaseDevice]) -> list[DreoButtonHA]:
    """Get the Dreo Buttons for the devices."""
    button_ha_collection: list[DreoButtonHA] = []

    for pydreo_device in pydreo_devices:
        _LOGGER.debug("Button:get_entries: Adding buttons for %s", pydreo_device.name)
        button_keys: list[str] = []

        for button_definition in BUTTONS:
            _LOGGER.debug("Button:get_entries: checking attribute: %s on %s", 
                         button_definition.attr_name, pydreo_device.name)

            if pydreo_device.is_feature_supported(button_definition.attr_name):
                if (button_definition.key in button_keys):
                    _LOGGER.error("Button:get_entries: Duplicate button key %s", 
                                button_definition.key)
                    continue

                _LOGGER.debug("Button:get_entries: Adding button %s", button_definition.key)
                button_keys.append(button_definition.key)
                button_ha_collection.append(DreoButtonHA(pydreo_device, button_definition))

    return button_ha_collection

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Button platform."""
    _LOGGER.info("Starting Dreo Button Platform")

    pydreo_manager: PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]
    button_entities_ha = get_entries(pydreo_manager.devices)
    async_add_entities(button_entities_ha)

class DreoButtonHA(DreoBaseDeviceHA, ButtonEntity):
    """Representation of a Button for a Dreo device."""

    def __init__(
        self,
        pydreo_base_device: PyDreoBaseDevice,
        description: DreoButtonEntityDescription
    ) -> None:
        super().__init__(pydreo_base_device)
        self.pydreo_device = pydreo_base_device

        # Note this is a "magic" HA property. Don't rename
        self.entity_description = description

        self._attr_name = super().name + " " + description.key
        self._attr_unique_id = f"{super().unique_id}-{description.key}"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug(
            "DreoButtonHA:async_press for %s %s",
            self.pydreo_device.name,
            self.entity_description.key,
        )
        
        # Call the corresponding method on the device
        method = getattr(self.pydreo_device, self.entity_description.attr_name)
        await self.hass.async_add_executor_job(method)