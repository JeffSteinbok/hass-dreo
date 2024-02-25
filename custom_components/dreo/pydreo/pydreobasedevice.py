import threading
import logging
from typing import Dict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydreo import PyDreo

from .constant import (
    LOGGER_NAME,
    REPORTED_KEY,
    POWERON_KEY,
    STATE_KEY
)

from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(LOGGER_NAME)

class UnknownModelError(Exception):
    """Exception thrown when we don't recognize a model of a device."""

class PyDreoBaseDevice(object):
    """Base class for all Dreo devices.

    Has code to handle providing common attributes and comment event handling.
    """

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        self._device_definition = device_definition
        self._name = details.get("deviceName", None)
        self._device_id = details.get("deviceId", None)
        self._sn = details.get("sn", None)
        self._brand = details.get("brand", None)
        self._model = details.get("model", None)
        self._productId = details.get("productId", None)
        self._productName = details.get("productName", None)
        self._deviceName = details.get("deviceName", None)
        self._shared = details.get("shared", None)
        self._series = details.get("series", None)
        self._seriesName = details.get("seriesName", None)
        self._color = details.get("color", None)
        #self._temperatureUnit = details['controlsConf']['preference']

        self._dreo = dreo
        self._is_on = False

        self._feature_key_names : Dict[str, str] = {}

        self.raw_state = None
        self._attr_cbs = []
        self._lock = threading.Lock()

    def __repr__(self):
        # Representation string of object.
        return "<{0}:{1}:{2}>".format(
            self.__class__.__name__, self._device_id, self._name
        )

    def get_server_update_key_value(self, message: dict, key: str):
        """Helper method to get values from a WebSocket update in a safe way."""
        if (message is not None) and (isinstance(message, dict)) and (REPORTED_KEY in message) and (isinstance(message[REPORTED_KEY], dict)):
            reported: dict = message[REPORTED_KEY]

            if (reported is not None) and (key in reported):
                value = reported[key]
                _LOGGER.info("%s reported: %s", key, value)
                return value

        return None

    def handle_server_update_base(self, message):
        """Initial method called when we get a WebSocket message."""
        _LOGGER.debug("{%s}: got {%s} message **", self.name, message)

        # This method exists so that we can run the polymorphic function to process updates, and then
        # run a _do_callbacks() command safely afterwards.
        self.handle_server_update(message)
        self._do_callbacks()

    def handle_server_update(self, message: dict):
        """Method to process WebSocket message"""

    def _send_command(self, commandKey: str, value):
        """Send a command to the Dreo servers via WebSocket."""
        params: dict = {commandKey: value}
        self._dreo.send_command(self, params)

    def get_state_update_value(self, state: dict, key: str):
        """Get a value from the state update in a safe manner."""
        if key in state:
            key_val_object: dict = state[key]
            if key_val_object is not None:
                return key_val_object[STATE_KEY]

        _LOGGER.debug("State value (%s) not present.  Device: %s", key, self.name)
        return None

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("pyDreoBaseDevice:update_state: %s", state)

        # TODO: Inconsistent placement of POWERON between BaseDevice and Fan for State/WebSocket
        self._is_on = self.get_state_update_value(state, POWERON_KEY)

    def add_attr_callback(self, cb):
        """Add a callback to be called by _do_callbacks. """
        self._attr_cbs.append(cb)

    def _do_callbacks(self):
        """Run all registered callback"""
        cbs = []
        with self._lock:
            for cb in self._attr_cbs:
                cbs.append(cb)
        for cb in cbs:
            cb()

    @property
    def device_definition(self):
        """Returns the device definition."""
        return self._device_definition
        
    @property
    def name(self):
        """Returns the device name."""
        return self._name

    @property
    def deviceId(self):
        """Returns the device ID"""
        return self._device_id

    @property
    def device_id(self):
        """Returns the device's id."""
        return self._device_id

    @property
    def sn(self):
        """Returns the device's serial number."""
        return self._sn

    @property
    def serialNumber(self):
        """Returns the device's serial number."""
        return self._sn

    @property
    def brand(self):
        """Returns the device's manufacturer."""

    @property
    def model(self):
        """Returns the device's model number."""
        return self._model

    @property
    def productId(self):
        """Returns the device's product ID."""
        return self._productId

    @property
    def productName(self):
        """Return's the device's product name."""
        return self._productName

    @property
    def deviceName(self):
        """Returns the device's name"""
        return self._deviceName

    @property
    def shared(self):
        """Returns true if the device is shared"""
        return self._shared

    @property
    def series(self):
        """Returns the series of the model of the device"""
        return self._series

    @property
    def seriesName(self):
        """Returns the series name of the device model"""
        return self._seriesName

    @property
    def color(self):
        """Returns the color of the device. Maybe use for an image at some point"""
        return self._color

    
    def is_feature_supported(self, feature: str) -> bool:
        """Does this device support a given feature"""
        _LOGGER.debug("Checking if %s supports feature %s", self, feature)
        for att in dir(self):
            _LOGGER.debug(att, getattr(self,att))
        property_name = feature
        if (hasattr(self, property_name)):
            val = getattr(self, property_name)
            if (val is not None):
                _LOGGER.debug("found attribute for %s --> %s", property_name, val)
                return True
        
        return False

