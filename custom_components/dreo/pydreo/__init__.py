"""Dreo API Library."""

# flake8: noqa
# from .pydreo import PyDreo
import logging
import threading
import sys

import json
from itertools import chain
from typing import Optional, Tuple
from asyncio.exceptions import CancelledError

from .constant import *
from .helpers import Helpers
from .models import *
from .commandtransport import CommandTransport
from .pydreobasedevice import PyDreoBaseDevice, UnknownModelError, UnknownProductError
from .pydreounknowndevice import PyDreoUnknownDevice
from .pydreotowerfan import PyDreoTowerFan
from .pydreoaircirculator import PyDreoAirCirculator
from .pydreoceilingfan import PyDreoCeilingFan
from .pydreoairpurifier import PyDreoAirPurifier
from .pydreoheater import PyDreoHeater
from .pydreoairconditioner import PyDreoAC
from .pydreochefmaker import PyDreoChefMaker
from .pydreohumidifier import PyDreoHumidifier
from .pydreodehumidifier import PyDreoDehumidifier
from .pydreoevaporativecooler import PyDreoEvaporativeCooler

_LOGGER = logging.getLogger(LOGGER_NAME)

_DREO_DEVICE_TYPE_TO_CLASS = {
    DreoDeviceType.TOWER_FAN: PyDreoTowerFan,
    DreoDeviceType.AIR_CIRCULATOR: PyDreoAirCirculator,
    DreoDeviceType.AIR_PURIFIER: PyDreoAirPurifier,
    DreoDeviceType.CEILING_FAN: PyDreoCeilingFan,
    DreoDeviceType.HEATER: PyDreoHeater,
    DreoDeviceType.AIR_CONDITIONER: PyDreoAC,
    DreoDeviceType.CHEF_MAKER: PyDreoChefMaker,
    DreoDeviceType.HUMIDIFIER: PyDreoHumidifier,
    DreoDeviceType.DEHUMIDIFIER: PyDreoDehumidifier,
    DreoDeviceType.EVAPORATIVE_COOLER: PyDreoEvaporativeCooler
}

class PyDreo:  # pylint: disable=function-redefined
    """Dreo API functions."""

    def __init__(self, 
                 username, 
                 password, 
                 redact=True, 
                 debug_test_mode=False,
                 debug_test_mode_payload=None) -> None:
        self._transport = CommandTransport(self._transport_consume_message)

        """Initialize Dreo class with username, password and time zone."""
        self.auth_region = DREO_AUTH_REGION_NA  # Will get the region from the auth call

        self._redact = redact
        if redact:
            self.redact = redact
        self.raw_response = None
        self.username : str = username
        self.password : str  = password
        self.token = None
        self.account_id = None
        self.devices = None
        self.enabled = False
        self.in_process = False
        self._dev_list = {}
        self._device_list_by_sn = {}
        self.devices: list[PyDreoBaseDevice] = []
        
        self.debug_test_mode : bool = debug_test_mode
        self.debug_test_mode_payload : dict = debug_test_mode_payload

        if self.debug_test_mode:
            _LOGGER.error("Debug Test Mode is enabled!")
            if self.debug_test_mode_payload is None:
                _LOGGER.error("Debug Test Mode payload is None!")

    @property
    def api_server_region(self) -> str:
        """Return region."""
        if self.auth_region == DREO_AUTH_REGION_NA:
            return DREO_API_REGION_US
        elif self.auth_region == DREO_AUTH_REGION_EU:
            return DREO_API_REGION_EU
        else:
            _LOGGER.error("Invalid Auth Region: %s", self.auth_region)

    @property
    def auto_reconnect(self) -> bool:
        """Return auto_reconnect option."""
        return self._transport.auto_reconnect

    @auto_reconnect.setter
    def auto_reconnect(self, value: bool) -> None:
        """Set auto_reconnect option."""
        _LOGGER.debug("Setting auto_reconnect to %s", value)
        self._transport.auto_reconnect = value

    @property
    def redact(self) -> bool:
        """Return debug flag."""
        return self._redact

    @redact.setter
    def redact(self, new_flag: bool) -> None:
        """Set debug flag."""
        if new_flag:
            Helpers.shouldredact = True
        elif new_flag is False:
            Helpers.shouldredact = False
        self._redact = new_flag

    def add_dev_test(self, new_dev: dict) -> bool:
        """Test if new device should be added - True = Add."""
        if "cid" in new_dev:
            for _, v in self._dev_list.items():
                for dev in v:
                    if dev.deviceId == new_dev.get(DEVICEID_KEY):
                        return False
        return True

    @staticmethod
    def set_dev_id(devices: list) -> list:
        """Correct devices without cid or uuid."""
        dev_num = 0
        dev_rem = []
        for dev in devices:
            if dev.get(DEVICEID_KEY) is not None:
                dev[DEVICEID_KEY] = dev[DEVICEID_KEY]
            dev_num += 1
            if dev_rem:
                devices = [i for j, i in enumerate(devices) if j not in dev_rem]
        return devices

    def _process_devices(self, dev_list: list) -> bool:
        """Instantiate Device Objects."""
        devices = self.set_dev_id(dev_list)
        _LOGGER.debug("pydreo._process_devices")
        num_devices = 0
        for _, v in self._dev_list.items():
            if isinstance(v, list):
                num_devices += len(v)
            else:
                num_devices += 1

        if not devices:
            _LOGGER.warning("No devices found in api return")
            return False
        if num_devices == 0:
            _LOGGER.debug("New device list initialized")
        # else:
        #    self.remove_old_devices(devices)

        # devices[:] = [x for x in devices if self.add_dev_test(x)]

        # detail_keys = ['deviceType', 'deviceName', 'deviceStatus']
        for dev in devices:
            # Get the state of the device...separate API call...boo
            try:
                model = dev.get("model", None)
                
                _LOGGER.debug("Found device with model %s", model)

                if model is not None: 
                    # Get the prefix of the model number to match against the supported devices.
                    # Not all models will have known prefixes.
                    model_prefix = None
                    for prefix in SUPPORTED_MODEL_PREFIXES:
                        if model[:len(prefix):] == prefix:
                            model_prefix = prefix
                            _LOGGER.debug("Prefix %s assigned from model %s", model_prefix, model)
                            break
                    
                    device_details = None
                    if model in SUPPORTED_DEVICES:
                        _LOGGER.debug("Device %s found!", model)
                        device_details = SUPPORTED_DEVICES[model]
                    elif model_prefix is not None and model_prefix in SUPPORTED_DEVICES:
                        _LOGGER.debug("Device %s found! via prefix %s", model, model_prefix)
                        device_details = SUPPORTED_DEVICES[model_prefix]

                # If device_details is None at this point, we have an unknown device model.
                # Unsupported/Unknown Device.  Load the state, but store it in an "unsupported objects"
                # list for later use in diagnostics.
                device_class = None
                
                if device_details is not None:
                    device_class = _DREO_DEVICE_TYPE_TO_CLASS.get(device_details.device_type, None)
                else:
                    device_details = DreoDeviceDetails(device_type = DreoDeviceType.UNKNOWN)

                if device_class is None:
                    device_class = PyDreoUnknownDevice
                
                device : PyDreoBaseDevice = device_class(device_details, dev, self)

                self.load_device_state(device)

                self.devices.append(device)

                self._device_list_by_sn[device.serial_number] = device
            except UnknownModelError as ume:
                _LOGGER.warning("Unknown device model: %s", ume)
                _LOGGER.debug(dev)

        return True

    def load_devices(self) -> bool:
        """Load devices from API. This is called once upon initialization."""
        if not self.enabled:
            return False

        self.in_process = True
        proc_return = False

        response = None

        if self.debug_test_mode:
            _LOGGER.debug("Debug Test Mode is enabled.  Using test payload.")
            response = self.debug_test_mode_payload.get("get_devices", None)    
        else:
            response, _ = self.call_dreo_api(DREO_API_DEVICELIST)

        # Stash the raw response for use by the diagnostics system, so we don't have to pull
        # logs
        self.raw_response = response

        if response and Helpers.code_check(response):
            if DATA_KEY in response and LIST_KEY in response[DATA_KEY]:
                device_list = response[DATA_KEY][LIST_KEY]
                proc_return = self._process_devices(device_list)
            else:
                _LOGGER.error("Device list in response not found")
        else:
            _LOGGER.warning("Error retrieving device list")

        self.in_process = False

        return proc_return

    def load_device_state(self, device: PyDreoBaseDevice) -> bool:
        """Load device state from API. This is called once upon initialization for each supported device."""
        _LOGGER.debug("load_device_state: %s, enabled: %s", device.name, self.enabled)
        if not self.enabled:
            return False

        self.in_process = True
        proc_return = False

        response = None

        if self.debug_test_mode:
            _LOGGER.debug("Debug Test Mode is enabled.  Using test payload.")
            response = self.debug_test_mode_payload.get(device.serial_number, None)    
        else:
            response, _ = self.call_dreo_api(
                DREO_API_DEVICESTATE, {DEVICESN_KEY: device.serial_number}
            )

        # stash the raw return value from the devicestate api call
        device.raw_state = response

        if response and Helpers.code_check(response):
            if DATA_KEY in response and MIXED_KEY in response[DATA_KEY]:
                device_state = response[DATA_KEY][MIXED_KEY]
                device.update_state(device_state)
                proc_return = True
            else:
                _LOGGER.error("Mixed state in response not found")
        else:
            _LOGGER.error("Error retrieving device state")

        self.in_process = False

        return proc_return

    def login(self) -> bool:
        """Return True if log in request succeeds."""

        if self.debug_test_mode:
            self.enabled = True
            _LOGGER.debug("Debug Test Mode is enabled.  Skipping login.")  
            return True

        user_check = isinstance(self.username, str) and len(self.username) > 0
        pass_check = isinstance(self.password, str) and len(self.password) > 0
        if user_check is False:
            _LOGGER.error("Username invalid")
            return False
        if pass_check is False:
            _LOGGER.error("Password invalid")
            return False
        response, _ = self.call_dreo_api(DREO_API_LOGIN)

        if Helpers.code_check(response) and DATA_KEY in response:
            # get the region code from auth
            auth_region = response[DATA_KEY][REGION_KEY]
            _LOGGER.info("Dreo Auth reports user region as: %s", auth_region)
            if auth_region != self.auth_region:
                _LOGGER.info(
                    "Dreo Auth reports different region than current; retrying."
                )
                self.auth_region = auth_region
                return self.login()
            else:
                self.token = response[DATA_KEY][ACCESS_TOKEN_KEY]
                self.enabled = True
                _LOGGER.debug("Login successful")
                return True
        _LOGGER.error("Error logging in with username and password")
        return False

    def get_device_setting(self, device: PyDreoBaseDevice, setting : DreoDeviceSetting) -> bool | int:
        """Get a device setting from the API."""
        _LOGGER.debug("get_device_setting: %s(%s), enabled: %s", 
                    device.name, 
                    setting,
                    self.enabled)
        if not self.enabled:
            return None

        self.in_process = True
        setting_value = None
        response, _ = self.call_dreo_api(
            DREO_API_SETTING_GET, 
            {   DEVICESN_KEY: device.serial_number,
                DREO_API_SETTING_DATA_KEY: setting
            }
        )

        if response and Helpers.code_check(response):
            if DATA_KEY in response:
                data_node = response[DATA_KEY]
                if DREO_API_SETTING_DATA_VALUE in data_node:
                    setting_value = data_node[DREO_API_SETTING_DATA_VALUE]
                else:
                    _LOGGER.error("%s key not found in returned data. %s",
                                DREO_API_SETTING_DATA_VALUE,
                                data_node)
        else:
            _LOGGER.error("Error retrieving device setting.")

        self.in_process = False

        return setting_value
    
    def set_device_setting(self, device: PyDreoBaseDevice, setting : DreoDeviceSetting, value : bool | int) -> None:
        """Get a device setting from the API."""
        _LOGGER.debug("set_device_setting: %s(%s=%s), enabled: %s", 
                    device.name, 
                    setting,
                    value,
                    self.enabled)
        if not self.enabled:
            return None

        self.in_process = True
        proc_return = False
        response, _ = self.call_dreo_api(
            DREO_API_SETTING_PUT, 
            {   DEVICESN_KEY: device.serial_number,
                DREO_API_SETTING_DATA_KEY: setting,
                DREO_API_SETTING_DATA_VALUE: value
            }
        )        

        # stash the raw return value from the devicestate api call
        device.raw_state = response

        if response and Helpers.code_check(response):
            if DATA_KEY in response and MIXED_KEY in response[DATA_KEY]:
                device_state = response[DATA_KEY][MIXED_KEY]
                device.update_state(device_state)
                proc_return = True
            else:
                _LOGGER.error("Mixed state in response not found")
        else:
            _LOGGER.error("Error retrieving device state")

        self.in_process = False

        return proc_return
    
    def call_dreo_api(self, api: str, json_object: Optional[dict] = None) -> tuple:
        """Call the Dreo API. This is used for login and the initial device list and states as well
           as device settings."""
        _LOGGER.debug("Calling Dreo API: {%s}", api)
        api_url = DREO_API_URL_FORMAT.format(self.api_server_region)

        if json_object is None:
            json_object = {}

        json_object_full = {**Helpers.req_body(self, api), **json_object}

        return Helpers.call_api(
            api_url,
            DREO_APIS[api][DREO_API_PATH],
            DREO_APIS[api][DREO_API_METHOD],
            json_object_full,
            Helpers.req_headers(self),
        )

    def start_transport(self) -> None:
        """Initialize the websocket and start transport"""
        if not self.debug_test_mode:
            self._transport.start_transport(self.api_server_region, self.token)

    def stop_transport(self) -> None:
        """Close down the transport socket"""
        if not self.debug_test_mode:
            self._transport.stop_transport()

    def testonly_interrupt_transport(self) -> None:
        """Close down the transport socket"""
        self._transport.testonly_interrupt_transport()

    def _transport_consume_message(self, message):
        _LOGGER.debug("pydreo._transport_consume_message: %s", message)

        message_device_sn = message["devicesn"]

        if message_device_sn in self._device_list_by_sn:
            device = self._device_list_by_sn[message_device_sn]
            device.handle_server_update_base(message)
        else:
            # Message is to an unknown device, log it out just in case...
            _LOGGER.debug(
                "Received message for unknown or unsupported device. SN: %s",
                message_device_sn,
            )
            _LOGGER.debug("Message: %s", message)

    def send_command(self, device: PyDreoBaseDevice, params) -> None:
        """Send a command to Dreo servers via the WebSocket."""
        full_params = {
            "devicesn": device.serial_number,
            "method": "control",
            "params": params,
            "timestamp": Helpers.api_timestamp(),
        }
        content = json.dumps(full_params)
        _LOGGER.debug(content)

        if self.debug_test_mode:
            _LOGGER.debug("Debug Test Mode is enabled.  Pretending we received the message...")
            self._transport_consume_message({"devicesn": device.serial_number, 
                                             "method": "report", 
                                             "reported": params})
        else:
            # Send the message to the transport, which will then send it to the Dreo servers
            self._transport.send_message(content)
