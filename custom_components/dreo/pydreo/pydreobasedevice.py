"""Base class for all Dreo devices."""
import threading
import logging
from typing import Dict
from typing import TYPE_CHECKING

from .constant import LOGGER_NAME, REPORTED_KEY
from .dreoapiresponseparser import DreoApiKeys
from .models import DreoDeviceDetails

if TYPE_CHECKING:
    from pydreo import PyDreo

_LOGGER = logging.getLogger(LOGGER_NAME)

class UnknownProductError(Exception):
    """Exception thrown when we don't recognize a product of a device."""

class UnknownModelError(Exception):
    """Exception thrown when we don't recognize a model of a device."""

class PyDreoBaseDevice(object):
    """Base class for all Dreo devices.

    Has code to handle providing common attributes and comment event handling.
    """

    def __init__(
        self,
        device_definition: DreoDeviceDetails,
        details: Dict[str, list],
        dreo: "PyDreo",
    ):
        self._device_definition = device_definition
        self._name = details.get("deviceName", None)
        self._device_id = details.get("deviceId", None)
        # Support both old API ("sn") and new API ("deviceSn") field names
        self._sn = details.get("deviceSn", details.get("sn", None))
        self._brand = details.get("brand", None)
        self._model = details.get("model", None)
        self._product_id = details.get("productId", None)
        self._product_name = details.get("productName", None)
        self._device_name = details.get("deviceName", None)
        self._shared = details.get("shared", None)
        self._series = details.get("series", None)
        self._series_name = details.get("seriesName", None)
        self._color = details.get("color", None)
        # self._temperatureUnit = details['controlsConf']['preference']

        self._dreo = dreo
        self._is_on = False

        self._feature_key_names: Dict[str, str] = {}

        self.raw_state = None
        self._attr_cbs = []
        self._lock = threading.Lock()

    def __repr__(self):
        # Representation string of object.
        return f"<{self.__class__.__name__}:{self._sn}:{self._name}>"

    def get_server_update_key_value(self, message: dict, key: str):
        """Helper method to get values from a WebSocket update in a safe way."""
        if (
            (message is not None)
            and (isinstance(message, dict))
            and (REPORTED_KEY in message)
            and (isinstance(message[REPORTED_KEY], dict))
        ):
            reported: dict = message[REPORTED_KEY]

            if (reported is not None) and (key in reported):
                value = reported[key]
                _LOGGER.info("%s reported: %s", key, value)
                return value

        return None


    def is_preference_supported(self, preference_type: str, details: dict) -> bool:
        """Check if a preference type is supported."""
        _LOGGER.debug("PyDreoBaseDevice:Checking for preference type %s", preference_type)
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            preferences = controls_conf.get("preference", None)
            if (preferences is not None):
                for preference in preferences:
                    if preference.get("type", None) == preference_type:
                        _LOGGER.debug("PyDreoFanBase:Found preference type %s", preference_type)
                        return True
                    
        _LOGGER.debug("PyDreoBaseDevice:Preference type %s not found", preference_type)
        return False
    
    def get_setting(self, dreo : "PyDreo", setting_name: str, default_value : any) -> any:
        """Get the value of a preference."""
        _LOGGER.debug("PyDreoBaseDevice:get_setting: %s", setting_name)
        setting_val = dreo.get_device_setting(self, setting_name)
        if setting_val is None:
            _LOGGER.debug("PyDreoBaseDevice:get_setting: %s not found.  Using default value.", setting_name)
            setting_val = default_value

        _LOGGER.debug("PyDreoBaseDevice:get_setting: %s -> %s", setting_name, setting_val)
        return setting_val
    
    def handle_server_update_base(self, message):
        """Initial method called when we get a WebSocket message."""
        _LOGGER.debug("{%s}: got {%s} message **", self.name, message)

        # This method exists so that we can run the polymorphic function to process updates, and then
        # run a _do_callbacks() command safely afterwards.
        self.handle_server_update(message)
        self._do_callbacks()

    def handle_server_update(self, message: dict):
        """Method to process WebSocket message"""

    def _send_command(self, command_key: str, value):
        """Send a command to the Dreo servers via WebSocket."""
        _LOGGER.debug(
            "pyDreoBaseDevice(%s):send_command: %s-> %s", self, command_key, value
        )

        params: dict = {command_key: value}
        self._dreo.send_command(self, params)

    def _set_setting(self, setting_key: str, value):
        """Set a setting on the device."""
        _LOGGER.debug(
            "pyDreoBaseDevice(%s):set_setting: %s-> %s", self, setting_key, value
        )
        self._dreo.set_device_setting(self, setting_key, value)

    def get_state_update_value(self, state: dict, key: str):
        """Get a value from the state update in a safe manner.

        Handles both old API format (nested with timestamps) and new API format (flat).
        Also checks alternate field names for backward compatibility.
        """
       
        # Try the requested key first
        if key in state:
            key_val_object = state[key]
            if key_val_object is not None:
                # New API format: {"key": value}
                _LOGGER.debug(
                    "pyDreoBaseDevice(%s):get_state_update_value: %s-> %s",
                    self,
                    key,
                    key_val_object,
                )
                return key_val_object

        _LOGGER.debug("State value (%s) not present.  Device: %s", key, self.name)
        return None
    
    def get_state_update_value_mapped(self, state: dict, key: str, mapping: dict):
        """Get a value from the state update in a safe manner, and map it to something."""
        raw_value = self.get_state_update_value(state, key)

        if raw_value is not None:
            if raw_value in mapping:
                return mapping[raw_value]
            else:
                _LOGGER.error("Value (%s) not in mapping for key %s.  Device: %s", raw_value, key, self.name)
        else:
            _LOGGER.debug("State value (%s) not present.  Device: %s", key, self.name)

        return None    

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("pyDreoBaseDevice:update_state: %s", state)

        # TODO: Inconsistent placement of POWERON between BaseDevice and Fan for State/WebSocket
        self._is_on = self.get_state_update_value(state, DreoApiKeys.POWER_SWITCH)

    def add_attr_callback(self, cb):
        """Add a callback to be called by _do_callbacks."""
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
    def device_definition(self) -> DreoDeviceDetails:
        """Returns the device definition."""
        return self._device_definition

    @property
    def name(self):
        """Returns the device name."""
        return self._name

    @property
    def device_id(self):
        """Returns the device's id."""
        return self._device_id

    @property
    def serial_number(self):
        """Returns the device's serial number."""
        return self._sn

    @property
    def brand(self):
        """Returns the device's manufacturer."""
        return "Dreo"

    @property
    def type(self):
        """Returns the device's type."""
        return self._device_definition.device_type

    @property
    def model(self):
        """Returns the device's model number."""
        return self._model

    @property
    def product_id(self):
        """Returns the device's product ID."""
        return self._product_id

    @property
    def product_name(self):
        """Return's the device's product name."""
        return self._product_name

    @property
    def device_name(self):
        """Returns the device's name"""
        return self._device_name

    @property
    def shared(self):
        """Returns true if the device is shared"""
        return self._shared

    @property
    def series(self):
        """Returns the series of the model of the device"""
        return self._series

    @property
    def series_name(self):
        """Returns the series name of the device model"""
        return self._series_name

    @property
    def color(self):
        """Returns the color of the device. Maybe use for an image at some point"""
        return self._color

    def is_feature_supported(self, feature: str) -> bool:
        """Does this device support a given feature"""
        _LOGGER.debug("Checking if %s supports feature %s", self, feature)
        property_name = feature
        if hasattr(self, property_name):
            val = getattr(self, property_name)
            if val is not None:
                _LOGGER.debug(
                    "%s found attribute for %s --> %s", self, property_name, val
                )
                return True

        return False
