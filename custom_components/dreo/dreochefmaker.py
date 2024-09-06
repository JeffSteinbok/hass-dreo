"""Support for Dreo ChefMaker cookers."""
from __future__ import annotations

import logging
from typing import Any

from .haimports import * # pylint: disable=W0401,W0614

from .dreobasedevice import DreoBaseDeviceHA
from .const import (
    LOGGER
)

from .pydreo.pydreochefmaker import PyDreoChefMaker

_LOGGER = logging.getLogger(LOGGER)

class DreoChefMakerHA(DreoBaseDeviceHA, SwitchEntity):
    """Representation of a Dreo chefmaker."""
    # Note that these are implemented as Switches, as there is no 
    # platform in HA that matches this device.

    def __init__(self, pyDreoChefMaker: PyDreoChefMaker):
        """Initialize the Dreo ChefMaker device."""
        super().__init__(pyDreoChefMaker)
        self.device = pyDreoChefMaker
        self._icon = "mdi:power"

    @property
    def is_on(self) -> bool:
        """Return True if device is on."""
        return self.device.is_on

    def turn_on(
        self,
        **kwargs: Any,
    ) -> None:
        """Turn the device on."""
        _LOGGER.debug("DreoChefMakerHA:turn_on")
        self.device.is_on = True

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        _LOGGER.debug("DreoChefMakerHA:turn_off")
        self.device.is_on = False
