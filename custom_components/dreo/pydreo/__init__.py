"""Dreo API Library."""

# flake8: noqa
# from .pydreo import PyDreo
import logging
import threading

import asyncio
import json
import sys
import time
from itertools import chain
from typing import Optional, Tuple

import websockets

from .constant import *
from .helpers import Helpers
from .models import *
from .pydreotowerfan import PyDreoTowerFan
from .pydreoaircirculatorfan import PyDreoAirCirculatorFan
from .pydreobasedevice import PyDreoBaseDevice, UnknownModelError
from .pydreofan import PyDreoFan

__version__ = "0.2.0"

_LOGGER = logging.getLogger(LOGGER_NAME)

API_RATE_LIMIT: int = 30


class PyDreo:  # pylint: disable=function-redefined
    """Dreo API functions."""

    def __init__(self, username, password, redact=True):
        """Initialize Dreo class with username, password and time zone."""
        self.auth_region = DREO_AUTH_REGION_NA  # Will get the region from the auth call

        self._redact = redact
        if redact:
            self.redact = redact
        self.username = username
        self.password = password
        self.token = None
        self.account_id = None
        self.devices = None
        self.enabled = False
        self.update_interval = API_RATE_LIMIT
        self.last_update_ts = None
        self.in_process = False
        self._dev_list = {}
        self._deviceListBySn = {}
        self.fans : list[PyDreoFan] = []
        self._signal_close = False
        self._testonly_signal_interrupt = False

        self._dev_list = {
            "fans": self.fans,
        }

    @property
    def apiServerRegion(self) -> str:
        """Return region."""
        if self.auth_region == DREO_AUTH_REGION_NA:
            return DREO_API_REGION_US
        elif self.auth_region == DREO_AUTH_REGION_EU:
            return DREO_API_REGION_EU
        else:
            _LOGGER.error("Invalid Auth Region: {0}".format(self.auth_region))

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
            # For now, let's keep this simple and just support fans...
            # Get the state of the device...seperate API call...boo
            try:
                model = dev.get("model", None)
                _LOGGER.debug(f"found device with model {model}")
                deviceFan = None

                if model is None:
                    raise UnknownModelError(model)
                elif model in SUPPORTED_TOWER_FANS:
                    _LOGGER.debug(f"{model} is a tower fan")
                    deviceFan = PyDreoTowerFan(SUPPORTED_TOWER_FANS[model], dev, self)
                elif model in SUPPORTED_AIR_CIRCULATOR_FANS:
                    _LOGGER.debug(f"{model} is an air circulator")
                    deviceFan = PyDreoAirCirculatorFan(SUPPORTED_AIR_CIRCULATOR_FANS[model], dev, self)
                else:
                    raise UnknownModelError(model)

                self.load_device_state(deviceFan)
                self.fans.append(deviceFan)
                self._deviceListBySn[deviceFan.sn] = deviceFan
            except UnknownModelError as ume:
                _LOGGER.warning("Unknown fan model: %s", ume)
                _LOGGER.debug(dev)

        return True

    def load_devices(self) -> bool:
        if not self.enabled:
            return False

        self.in_process = True
        proc_return = False
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
        _LOGGER.debug("load_device_state")
        if not self.enabled:
            return False

        self.in_process = True
        proc_return = False
        response, _ = self.call_dreo_api(
            DREO_API_DEVICESTATE, {DEVICESN_KEY: device.sn}
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
            authRegion = response[DATA_KEY][REGION_KEY]
            _LOGGER.info("Dreo Auth reports user region as: {0}".format(authRegion))
            if authRegion != self.auth_region:
                _LOGGER.info(
                    "Dreo Auth reports different region than current; retrying."
                )
                self.auth_region = authRegion
                return self.login()
            else:
                self.token = response[DATA_KEY][ACCESS_TOKEN_KEY]
                self.enabled = True
                _LOGGER.debug("Login successful")
                return True
        _LOGGER.error("Error logging in with username and password")
        return False

    def device_time_check(self) -> bool:
        """Test if update interval has been exceeded."""
        if (
            self.last_update_ts is None
            or (time.time() - self.last_update_ts) > self.update_interval
        ):
            return True
        return False

    def call_dreo_api(
        self,
        api: str,
        json_object: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> tuple:
        _LOGGER.debug("Calling Dreo API: {%s}",
                      api)
        api_url = DREO_API_URL_FORMAT.format(self.apiServerRegion)

        if json_object is None:
            json_object = {}

        json_object_full = {**Helpers.req_body(self, api), **json_object}

        return Helpers.call_api(
            api_url,
            DREO_APIS[api][DREO_API_LIST_PATH],
            DREO_APIS[api][DREO_API_LIST_METHOD],
            json_object_full,
            Helpers.req_headers(self),
        )

    def start_monitoring(self):
        """Initialize the websocket and start monitoring"""

        def start_ws_wrapper():
            asyncio.run(self._start_websocket())

        self._event_thread = threading.Thread(
            name="DreoWebSocketStream", target=start_ws_wrapper, args=()
        )
        self._event_thread.setDaemon(True)
        self._event_thread.start()
        return True

    def stop_monitoring(self):
        '''Close down the monitoring socket'''
        _LOGGER.info("Stopping Monitoring - May take up to 15s")
        self._signal_close = True

    def testonly_interrupt_monitoring(self):
        '''Close down the monitoring socket'''
        _LOGGER.info("Interrupting Monitoring - May take up to 15s")
        self._testonly_signal_interrupt = True

    async def _start_websocket(self):
        _LOGGER.info("Starting WebSocket for incoming changes.")
        # open websocket
        url = f"wss://wsb-{self.apiServerRegion}.dreo-cloud.com/websocket?accessToken={self.token}&timestamp={Helpers.api_timestamp()}"
        async with websockets.connect(url) as ws:
            self.ws = ws
            _LOGGER.info("WebSocket successfully opened")
            await self._ws_handler(ws)

    async def _ws_handler(self, ws):
        consumer_task = asyncio.create_task(self._ws_consumer_handler(ws))
        ping_task = asyncio.create_task(self._ws_ping_handler(ws))
        done, pending = await asyncio.wait(
            [consumer_task, ping_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        _LOGGER.debug("_ws_handler - WebSocket appears closed.")
        for task in pending:
            task.cancel()
        # Reconnect the WebSocket
        _LOGGER.debug("_ws_handler - Reconnecting WebSocket")
        await self._start_websocket()

    async def _ws_consumer_handler(self, ws):
        _LOGGER.debug("_ws_consumer_handler")
        async for message in ws:
            _LOGGER.debug("_ws_consumer_handler - got message")
            self._ws_consume_message(json.loads(message))
        _LOGGER.debug("_ws_consumer_handler - WebSocket appears closed.")            
        return True

    async def _ws_ping_handler(self, ws):
        _LOGGER.debug("_ws_ping_handler")
        while True:
            try:
                await ws.send('2')
                await asyncio.sleep(15)
            except websockets.exceptions.ConnectionClosed:
                _LOGGER.info('Dreo WebSocket Closed - Unless intended, will reconnect')
                break

    def _ws_consume_message(self, message):
        messageDeviceSn = message["devicesn"]

        if (messageDeviceSn in self._deviceListBySn):
            device = self._deviceListBySn[messageDeviceSn]
            device.handle_server_update_base(message)
        else:
            # Message is to an unknown device, log it out just in case...
            _LOGGER.debug("Received message for unknown or unsupported device. SN: {0}".format(messageDeviceSn))
            _LOGGER.debug("Message: {0}".format(message))

    def send_command(self, device: PyDreoBaseDevice, params):
        fullParams = {
            "devicesn": device.sn,
            "method": "control",
            "params": params,
            "timestamp": Helpers.api_timestamp(),
        }
        content = json.dumps(fullParams)
        _LOGGER.debug(content)
        asyncio.run(self.ws.send(content))
