"""Support additional switches for some Dreo devices"""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613
from __future__ import annotations

from typing import Any
from dataclasses import dataclass
import logging

from .haimports import *  # pylint: disable=W0401,W0614
from .dreobasedevice import DreoBaseDeviceHA
from .dreochefmaker import DreoChefMakerHA
from .pydreo import PyDreo, PyDreoBaseDevice
from .pydreo.constant import DreoDeviceType

from .const import DOMAIN, PYDREO_MANAGER

_LOGGER = logging.getLogger(__name__)


@dataclass
class DreoSwitchEntityDescription(SwitchEntityDescription):
    """Describe Dreo Switch entity.
    
    Extends Home Assistant's SwitchEntityDescription to add Dreo-specific fields:
    - attr_name: The PyDreo device attribute name to control
    - icon: Material Design Icon to display in the UI
    """

    attr_name: str = None  # Name of the device attribute (e.g., "childlockon")
    icon: str = None       # MDI icon identifier (e.g., "mdi:lock")


# Master list of all possible switch types supported by Dreo devices
# Not all devices support all switches - get_entries() checks device capabilities
SWITCHES: tuple[DreoSwitchEntityDescription, ...] = (
    DreoSwitchEntityDescription(
        key="Horizontally Oscillating",
        translation_key="horizontally_oscillating",
        attr_name="horizontally_oscillating",
        icon="mdi:rotate-360",
    ),
    DreoSwitchEntityDescription(
        key="Vertically Oscillating",
        translation_key="vertically_oscillating",
        attr_name="vertically_oscillating",
        icon="mdi:rotate-360",
    ),
    DreoSwitchEntityDescription(
        key="Display Auto Off",
        translation_key="display_auto_off",
        attr_name="display_auto_off",
        icon="mdi:monitor",
    ),
    DreoSwitchEntityDescription(
        key="Panel Sound",
        translation_key="panel_sound",
        attr_name="panel_sound",
        icon="mdi:volume-high",
    ),
    DreoSwitchEntityDescription(
        key="Adaptive Brightness",
        translation_key="adaptive_brightness",
        attr_name="adaptive_brightness",
        icon="mdi:monitor",
    ),
    DreoSwitchEntityDescription(
        key="Panel Mute",
        translation_key="mute_on",
        attr_name="mute_on",
        icon="mdi:volume-high",
    ),  
    DreoSwitchEntityDescription(
        key="Oscillating",
        translation_key="oscon",
        attr_name="oscon",
        icon="mdi:rotate-360",
    ),
    DreoSwitchEntityDescription(
        key="PTC", 
        translation_key="ptcon", 
        attr_name="ptcon", 
        icon="mdi:help"
    ),
    DreoSwitchEntityDescription(
        key="Child Lock",
        translation_key="childlockon",
        attr_name="childlockon",
        icon="mdi:lock",
    ),
    DreoSwitchEntityDescription(    
        key="Light",
        translation_key="light",
        attr_name="ledpotkepton",
        icon="mdi:led-on",
    ),
    DreoSwitchEntityDescription(    
        key="Humidify",
        translation_key="humidify",
        attr_name="humidify",
        icon="mdi:air-humidifier",
    ),
    DreoSwitchEntityDescription(    
        key="Display Light",
        translation_key="display_light",
        attr_name="display_light",
        icon="mdi:led-on",
    ),
    DreoSwitchEntityDescription(    
        key="Auto Turn On",
        translation_key="auto_mode",
        attr_name="auto_mode",
        icon="mdi:autorenew",
    ),
    DreoSwitchEntityDescription(
        key="Schedule",
        translation_key="scheon",
        attr_name="scheon",
        icon="mdi:calendar",
    )  
)

def get_entries(pydreo_devices : list[PyDreoBaseDevice]) -> list[DreoSwitchHA]:
    """Get the Dreo Switches for the devices.
    
    Iterates through all Dreo devices and creates switch entities for each supported
    feature. Each switch controls a specific device capability (oscillation, mute, etc.).
    A single device typically has multiple switches.
    
    Args:
        pydreo_devices: List of PyDreo device objects from the device manager
        
    Returns:
        List of DreoSwitchHA entities to be registered with Home Assistant
    """
    switch_ha_collection : DreoSwitchHA = []

    for pydreo_device in pydreo_devices:
        _LOGGER.debug("Switch:get_entries: Adding switches for %s", pydreo_device.name)
        switch_keys : list[str] = []  # Track keys to prevent duplicates

        # Check each switch definition to see if this device supports it
        for switch_definition in SWITCHES:
            _LOGGER.debug("Switch:get_entries: checking attribute: %s on %s", switch_definition.attr_name, pydreo_device.name)

            # Only create switch if device supports this feature
            if pydreo_device.is_feature_supported(switch_definition.attr_name):
                # Prevent duplicate switches (shouldn't happen, but defensive coding)
                if (switch_definition.key in switch_keys):
                    _LOGGER.error("Switch:get_entries: Duplicate switch key %s", switch_definition.key)
                    continue
                
                _LOGGER.debug("Switch:get_entries: Adding switch %s", switch_definition.key)
                switch_keys.append(switch_definition.key)
                switch_ha_collection.append(DreoSwitchHA(pydreo_device, switch_definition))

    return switch_ha_collection


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Dreo Switch platform.
    
    Called by Home Assistant when the integration is loaded. Creates switch entities
    for each supported device feature, plus special handling for ChefMaker devices.
    """
    _LOGGER.info("Starting Dreo Switch Platform")

    # Get the PyDreo manager from Home Assistant's data storage
    pydreo_manager: PyDreo = hass.data[DOMAIN][PYDREO_MANAGER]

    switch_entities_ha : list[SwitchEntity] = []
    
    # Special case: ChefMaker devices get their own switch class
    # (ChefMaker has complex cooking modes that need custom handling)
    for pydreo_device in pydreo_manager.devices:
        if pydreo_device.type == DreoDeviceType.CHEF_MAKER:
            switch_entities_ha.append(DreoChefMakerHA(pydreo_device))
    
    # Add standard feature switches for all devices
    switch_entities_to_add = get_entries(pydreo_manager.devices)
    switch_entities_ha.extend(switch_entities_to_add)

    # Register all switch entities with Home Assistant
    async_add_entities(switch_entities_ha)

class DreoSwitchHA(DreoBaseDeviceHA, SwitchEntity):
    """Representation of a Switch describing a read-write property of a Dreo device."""

    def __init__(
        self, 
        pydreo_base_device: PyDreoBaseDevice, 
        description: DreoSwitchEntityDescription
    ) -> None:
        super().__init__(pydreo_base_device)
        self.pydreo_device = pydreo_base_device

        # Note this is a "magic" HA property.  Don't rename
        self.entity_description = description

        self._attr_name = super().name + " " + description.key
        self._attr_unique_id = f"{super().unique_id}-{description.key}"

        _LOGGER.info(
            "New DreoSwitchHA instance(%s), unique ID %s",
            self._attr_name,
            self._attr_unique_id)

    def __repr__(self):
        # Representation string of object.
        return f"<{self.__class__.__name__}:{self.entity_description}"
    
    @property
    def is_on(self) -> bool:
        """Return True if the switch feature is enabled.
        
        Reads the current state from the PyDreo device object. The device object
        is updated automatically via WebSocket messages from Dreo's servers.
        """
        _LOGGER.debug(
            "DreoSwitchHA:is_on for %s %s is %s",
            self.pydreo_device.name,
            self.entity_description.key,
            getattr(self.pydreo_device, self.entity_description.attr_name),
        )
        # Get the boolean value from the device's attribute (e.g., device.childlockon)
        return getattr(self.pydreo_device, self.entity_description.attr_name)

    def turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Enable the switch feature.
        
        Sets the device attribute to True, which triggers the PyDreo library to send
        a command to the device via Dreo's API/WebSocket.
        
        Note: percentage and preset_mode parameters are not used for switches but are
        part of the Home Assistant API signature.
        """
        _LOGGER.debug("Turning on switch %s %s", self.pydreo_device.name, self.entity_description.key)
        # Setting this attribute triggers PyDreo to send a command to the device
        setattr(self.pydreo_device, self.entity_description.attr_name, True)

    def turn_off(self, **kwargs: Any) -> None:
        """Disable the switch feature.
        
        Sets the device attribute to False, which triggers the PyDreo library to send
        a command to the device via Dreo's API/WebSocket.
        """
        _LOGGER.debug(
            "Turning off %s %s", self.pydreo_device.name, self.entity_description.key
        )
        # Setting this attribute triggers PyDreo to send a command to the device
        setattr(self.pydreo_device, self.entity_description.attr_name, False)
