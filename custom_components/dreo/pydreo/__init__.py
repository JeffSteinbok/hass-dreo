"""Dreo API Library."""

# pylint: skip-file
# flake8: noqa
# from .pydreo import PyDreo
import logging
import threading

"""Dreo API Device Libary."""

import logging
import time
import json
import logging
import time
from itertools import chain
from typing import Tuple

from .pydreobasedevice import PyDreoBaseDevice
from .pydreofan import PyDreoFan
from .helpers import Helpers

import asyncio
import websockets

from .constant import LOGGER_NAME

__version__ = "0.0.1"

_LOGGER = logging.getLogger(LOGGER_NAME)

API_RATE_LIMIT: int = 30

DEFAULT_ENER_UP_INT: int = 21600


def object_factory(dev_type, config, dreo : "PyDreo") -> Tuple[str, PyDreoBaseDevice]:
    """Get device type and instantiate class."""
    def fans(dev_type, config, manager):
        fan_cls = fan_mods.fan_modules[dev_type]  # noqa: F405
        fan_obj = getattr(fan_mods, fan_cls)
        return 'fans', fan_obj(config, manager)

    if dev_type in fan_mods.fan_modules:  # type: ignore  # noqa: F405
        type_str, dev_obj = fans(dev_type, config, dreo)
    else:
        _LOGGER.debug('Unknown device named %s model %s',
                     config.get('deviceName', ''),
                     config.get('deviceType', '')
                     )
        type_str = 'unknown'
        dev_obj = None
    return type_str, dev_obj


class PyDreo:  # pylint: disable=function-redefined
    """Dreo API functions."""

    def __init__(self, username, password, region, redact=True):
        """Initialize Dreo class with username, password and time zone."""

        self._redact = redact
        if redact:
            self.redact = redact
        self.username = username
        self.password = password
        self.region = region
        self.api_url = f"https://app-api-{region}.dreo-cloud.com"
        self.token = None
        self.account_id = None
        self.devices = None
        self.enabled = False
        self.update_interval = API_RATE_LIMIT
        self.last_update_ts = None
        self.in_process = False
        self._dev_list = {}
        self._deviceListBySn = {}
        self.fans = []

        self._dev_list = {
            'fans': self.fans,
        }

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
        if 'cid' in new_dev:
            for _, v in self._dev_list.items():
                for dev in v:
                    if (
                        dev.deviceId == new_dev.get('deviceId')
                    ):
                        return False
        return True
    
    @staticmethod
    def set_dev_id(devices: list) -> list:
        """Correct devices without cid or uuid."""
        dev_num = 0
        dev_rem = []
        for dev in devices:
            if dev.get('deviceId') is not None:
                dev['deviceId'] = dev['deviceId']
            dev_num += 1
            if dev_rem:
                devices = [i for j, i in enumerate(
                            devices) if j not in dev_rem]
        return devices

    def process_devices(self, dev_list: list) -> bool:
        """Instantiate Device Objects."""
        devices = self.set_dev_id(dev_list)
        _LOGGER.debug('pydreo.process_devices')
        num_devices = 0
        for _, v in self._dev_list.items():
            if isinstance(v, list):
                num_devices += len(v)
            else:
                num_devices += 1

        if not devices:
            _LOGGER.warning('No devices found in api return')
            return False
        if num_devices == 0:
            _LOGGER.debug('New device list initialized')
        #else:
        #    self.remove_old_devices(devices)

        #devices[:] = [x for x in devices if self.add_dev_test(x)]

        #detail_keys = ['deviceType', 'deviceName', 'deviceStatus']
        for dev in devices:
            try:
                #device_str, device_obj = object_factory(dev_type, dev, self)
                #device_list = getattr(self, device_str)
                #device_list.append(device_obj)
                print(dev)
                # For now, let's keep this simple and just support fans...

                # Get the state of the device...seperate API call...boo
                

                deviceFan = PyDreoFan(dev, self)
                self.load_device_state(deviceFan)
                self.fans.append(deviceFan)
                self._deviceListBySn[deviceFan.sn] = deviceFan
            except AttributeError as err:
                _LOGGER.debug('Error - %s', err)
                _LOGGER.debug('%s device not added', dev_type)
                continue

        return True

    def load_devices(self) -> bool:
        """Return tuple listing outlets, switches, and fans of devices."""
        if not self.enabled:
            return False

        self.in_process = True
        proc_return = False
        response, _ = Helpers.call_api(
            self.api_url,
            '/api/v2/user-device/device/list',
            'get',
            headers=Helpers.req_headers(self),
            json_object=Helpers.req_body(self, 'devicelist'),
        )

        if response and Helpers.code_check(response):
            if 'data' in response and 'list' in response['data']:
                device_list = response['data']['list']
                proc_return = self.process_devices(device_list)
            else:
                _LOGGER.error('Device list in response not found')
        else:
            _LOGGER.warning('Error retrieving device list')

        self.in_process = False

        return proc_return
    
    def load_device_state(self, device: PyDreoBaseDevice) -> bool:
        _LOGGER.debug("load_device_state")
        if not self.enabled:
            return False

        self.in_process = True
        proc_return = False
        response, _ = Helpers.call_api(
            self.api_url,
            '/api/user-device/device/state',
            'get',
            headers=Helpers.req_headers(self),
            json_object={ **Helpers.req_body(self, 'devicestate'),
                          'deviceSn': device.sn },
        )
        
        if response and Helpers.code_check(response):
            if 'data' in response and 'mixed' in response['data']:
                device_state = response['data']['mixed']
                device.update_state(device_state)
            else:
                _LOGGER.error('Mixed state in response not found')
        else:
            _LOGGER.warning('Error retrieving device state')

        self.in_process = False

        return proc_return    

    def login(self) -> bool:
        """Return True if log in request succeeds."""
        
        user_check = isinstance(self.username, str) and len(self.username) > 0
        pass_check = isinstance(self.password, str) and len(self.password) > 0
        if user_check is False:
            _LOGGER.error('Username invalid')
            return False
        if pass_check is False:
            _LOGGER.error('Password invalid')
            return False
        response, _ = Helpers.call_api(
            self.api_url,
            '/api/oauth/login', 'post',
            headers=Helpers.req_headers(self),
            json_object=Helpers.req_body(self, 'login')
        )
        print (response)
        if Helpers.code_check(response) and 'data' in response:
            self.token = response["data"]["access_token"]
            print("TOKEN")
            print(self.token)
            self.enabled = True
            _LOGGER.debug('Login successful')
            _LOGGER.debug('token %s', self.token)

            return True
        _LOGGER.error('Error logging in with username and password')
        return False

    def device_time_check(self) -> bool:
        """Test if update interval has been exceeded."""
        if (
            self.last_update_ts is None
            or (time.time() - self.last_update_ts) > self.update_interval
        ):
            return True
        return False

    def start_monitoring(self):
        self._event_thread = threading.Thread(
            name="DreoWebSocketStream", target=self.start_test, args=()
        )
        self._event_thread.setDaemon(True)
        self._event_thread.start()
        return True


    def start_test(self):
        asyncio.run(self.start_websocket())

    async def start_websocket(self):
        _LOGGER.info("Starting WebSocket for incoming changes.")
        # open websocket
        url = f"wss://wsb-{self.region}.dreo-cloud.com/websocket?accessToken={self.token}&timestamp={str(int(time.time() * 1000))}"
        async with websockets.connect(url) as ws:
            self.ws = ws
            _LOGGER.info('WebSocket successfully opened')
            await self._ws_handler(ws)

    async def _ws_handler(self, ws) :
        consumer_task = asyncio.create_task(self._ws_consumer_handler(ws))
        ping_task = asyncio.create_task(self._ws_ping_handler(ws))
        done, pending = await asyncio.wait(
            [consumer_task, ping_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

    async def _ws_consumer_handler(self, ws):
        _LOGGER.debug("_ws_consumer_handler")
        async for message in ws:
            _LOGGER.debug("_ws_consumer_handler - got message")
            self._ws_consume_message(json.loads(message))
        return True

    async def _ws_ping_handler(self, ws) :
        _LOGGER.debug("_ws_ping_handler")
        while True:
            try:
                await ws.send('2')
                await asyncio.sleep(15)
            except websockets.exceptions.ConnectionClosed:
                _LOGGER.error('Dreo WebSocket Closed')
                break
        

    def _ws_consume_message(self, message) :
        messageDeviceSn = message["devicesn"]
        device : PyDreoBaseDevice = self._deviceListBySn[messageDeviceSn] 
        device.handle_server_update_base(message)

    def send_command(self, device : PyDreoBaseDevice, params):
        fullParams = {
            'devicesn': device.sn,
            'method': "control",
            'params': params,
            'timestamp': str(int(time.time() * 1000))
        }
        content = json.dumps(fullParams)
        print(content)
        asyncio.run(self.ws.send(content))