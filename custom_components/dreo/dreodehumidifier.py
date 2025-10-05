"""Support climate control for some Dreo devices"""
# Suppress warnings about DataClass constructors
# pylint: disable=E1123

# Suppress warnings about unused function arguments
# pylint: disable=W0613

from typing import Any
import logging

from .haimports import *  # pylint: disable=W0401,W0614
from .dreobasedevice import DreoBaseDeviceHA
from .pydreo import PyDreoDehumidifier

from .const import (
    LOGGER,
    DOMAIN
)

_LOGGER = logging.getLogger(LOGGER)

# Implementation of the Dehumidifier
class DreoDehumidifierHA(DreoBaseDeviceHA, HumidifierEntity):
    """Representation of a Dreo Dehumidifier entity."""

    def __init__(self, pyDreoDevice: PyDreoDehumidifier) -> None:
        super().__init__(pyDreoDevice)
        self.device = pyDreoDevice
        _LOGGER.info(
            "DreoDehumidifierHA:__init__(%s)",
            pyDreoDevice.name
        )

        _LOGGER.info(
            "new DreoDehumidifierHA instance(%s), mode %s, available_modes [%s]",
            self.name,
            self.mode,
            self.available_modes,
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this dehumidifier."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device.serial_number)},
            manufacturer=self.device.brand,
            model=f"{self.device.series_name} ({self.device.model}) {self.device.product_name}",
            name=self.device.device_name,
        )

    @property
    def device_class(self) -> HumidifierDeviceClass:
        """Return the device class for this dehumidifier."""
        return HumidifierDeviceClass.DEHUMIDIFIER

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        supported_features = 0
        if self.device.modes is not None:
            supported_features |= HumidifierEntityFeature.MODES
        
        return supported_features
    
    @property
    def is_on(self) -> bool:
        """Return True if device is on."""
        return self.device.is_on

    @property
    def mode(self) -> str | None:
        """Get the current mode."""
        return self.device.mode

    @property
    def available_modes(self) -> list[str]:
        """Return the list of supported modes."""
        return self.device.modes

    @property
    def current_humidity(self) -> float:
        """Return the current humidity."""
        return self.device.humidity
    
    @property
    def target_humidity(self) -> float:
        """Return the humidity level we try to reach."""
        return self.device.target_humidity

    @property
    def min_humidity(self) -> int:
        """Return the minimum humidity."""
        return 30

    @property
    def max_humidity(self) -> int:
        """Return the maximum humidity."""
        return 85
    
    def turn_on(self, **kwargs: any) -> None:
        """Turn the device on."""
        _LOGGER.debug("DreoDehumidifierHA:turn_on(%s)", self.device.name)
        self.device.is_on = True

    def turn_off(self, **kwargs: any) -> None:
        """Turn the device off."""
        _LOGGER.debug("DreoDehumidifierHA:turn_off(%s)", self.device.name)
        self.device.is_on = False

    def set_mode(self, mode: str) -> None:
        """Set the mode of the device."""
        _LOGGER.debug(
            "DreoDehumidifierHA:set_mode(%s) --> %s", self.device.name, mode
        )
        
        if not self.device.is_on:
            self.device.is_on = True

        if mode not in self.available_modes:
            raise ValueError(
                f"{mode} is not one of the valid preset modes: {self.available_modes}"
            )

        self.device.mode = mode

    def set_humidity(self, humidity: float) -> None:
        """Set the target humidity level."""
        _LOGGER.debug(
            "DreoDehumidifierHA:set_humidity(%s) --> %s", self.device.name, humidity
        )
        self.device.target_humidity = int(humidity)


    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        attributes = {}
        
        if hasattr(self.device, 'display_light'):
            attributes["display_light"] = self.device.display_light
        
        if hasattr(self.device, 'childlockon'):
            attributes["childlockon"] = self.device.childlockon
            
        if hasattr(self.device, 'auto_mode'):
            attributes["auto_mode"] = self.device.auto_mode
            
        if hasattr(self.device, 'panel_sound'):
            attributes["panel_sound"] = self.device.panel_sound
            
        if hasattr(self.device, 'temperature'):
            attributes["temperature"] = f"{getattr(self.device, 'temperature', 'N/A')}°F"
            
        return attributes
