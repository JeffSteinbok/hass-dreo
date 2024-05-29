import logging
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from pydreo import PyDreo

from .constant import (
    LOGGER_NAME,
    REPORTED_KEY,
    POWERON_KEY,
    STATE_KEY,
)

from .models import DreoDeviceDetails
from .pydreobasedevice import PyDreoBaseDevice, UnknownModelError

_LOGGER = logging.getLogger(LOGGER_NAME)


class PyDreoChefMaker(PyDreoBaseDevice):
    """Representation of a Dreo ChefMaker device."""

    def __init__(
        self,
        device_definition: DreoDeviceDetails,
        details: Dict[str, list],
        dreo: "PyDreo",
    ):
        """Initialize the ChefMaker device."""
        super().__init__(device_definition, details, dreo)
        self._is_on = False

    @property
    def is_on(self) -> bool:
        """Return True if device is on."""
        return self._is_on

    @is_on.setter
    def is_on(self, value: bool) -> None:
        """Set the power state of the device."""
        self._is_on = value
        self._send_command(POWERON_KEY, value)

    def update_state(self, state: dict) -> None:
        """Process the state dictionary from the REST API."""
        super().update_state(state)  # handles _is_on

        _LOGGER.debug("PyDreoChefMaker(%s):update_state: %s", self, state)

        self._is_on = self.get_state_update_value(state, POWERON_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug(
            "PyDreoChefMaker:handle_server_update(%s): %s", self.name, message
        )

        val_poweron = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_poweron, bool):
            _LOGGER.debug(
                "PyDreoChefMaker:handle_server_update - poweron: %s --> %s",
                self._is_on,
                val_poweron,
            )
            self._is_on = val_poweron  # Ensure poweron state is updated
