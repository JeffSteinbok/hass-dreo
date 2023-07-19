import threading
import logging
from typing import Dict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydreo import PyDreo

from .constant import *

_LOGGER = logging.getLogger(LOGGER_NAME)


class UnknownModelError(Exception):
    pass


class PyDreoBaseDevice(object):
    """Base class for all Dreo devices.

    Has code to handle providing common attributes and comment event handling.
    """

    def __init__(self, details: Dict[str, list], dreo: "PyDreo"):
        self._name = details.get("deviceName", None)
        self._device_id = details.get("deviceId", None)
        self._sn = details.get("sn", None)
        self._model = details.get("model", None)
        self._dreo = dreo
        self._is_on = False

        self.raw_state = None
        self._attr_cbs = []
        self._lock = threading.Lock()

    def __repr__(self):
        # Representation string of object.
        return "<{0}:{1}:{2}>".format(
            self.__class__.__name__, self._device_id, self._name
        )

    def get_server_update_key_value(self, message: dict, key: str):
        if (message is not None) and (isinstance(message[REPORTED_KEY], dict)):
            reported: dict = message[REPORTED_KEY]

            if (reported is not None) and (key in reported):
                value = reported[key]
                _LOGGER.info("%s reported: %s", key, value)
                return value

        return None

    def handle_server_update_base(self, message):
        _LOGGER.debug("{}: got {} message **".format(self.name, message))
        self.handle_server_update(message)
        self._do_callbacks()

    def handle_server_update(self):
        pass

    def _send_command(self, commandKey: str, value):
        params: dict = {commandKey: value}
        self._dreo.send_command(self, params)

    def get_state_update_value(self, state: dict, key: str):
        keyValObject: dict = state[key]
        if (keyValObject is not None):
            return keyValObject[STATE_KEY]
        else:
            _LOGGER.debug("Expected state value {0} not present.  Device: {1}".format(key, self.name))
            return None

    def update_state(self, state: dict):
        _LOGGER.debug("pyDreoBaseDevice:update_state: {0}".format(state))
        self._is_on = self.get_state_update_value(state, POWERON_KEY)

    def add_attr_callback(self, cb):
        self._attr_cbs.append(cb)

    def _do_callbacks(self):
        cbs = []
        with self._lock:
            for cb in self._attr_cbs:
                cbs.append(cb)
        for cb in cbs:
            cb()

    @property
    def name(self):
        """Returns the device name."""
        return self._name

    @property
    def device_id(self):
        """Returns the device's id."""
        return self._device_id

    @property
    def sn(self):
        """Returns the device's serial number."""
        return self._sn

    @property
    def model(self):
        """Returns the device's model number."""
        return self._model
