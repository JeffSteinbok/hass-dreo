"""Dreo Transport Library."""

# flake8: noqa
# from .pydreo import PyDreo
import logging
import threading

import asyncio
import json
from asyncio.exceptions import CancelledError
from collections.abc import Callable

import websockets

from .constant import * # pylint: disable=W0401,W0614
from .helpers import Helpers
from .models import * # pylint: disable=W0401,W0614

_LOGGER = logging.getLogger(LOGGER_NAME)

class CommandTransport: 
    """Command transport class for Dreo API."""

    def __init__(self, 
                 recv_callback: Callable[[dict], None] ):

        self._event_thread = None
        self._ws = None
        self._ws_send_lock = threading.Lock()
        self._transport_enabled = False
        self._signal_close = False
        self._testonly_signal_interrupt = False
        self._auto_reconnect = True

        self._api_server_region = None
        self._token = None
        self._recv_callback = recv_callback
   
    @property
    def auto_reconnect(self) -> bool:
        """Return auto_reconnect option."""
        return self._auto_reconnect

    @auto_reconnect.setter
    def auto_reconnect(self, value: bool) -> None:
        """Set auto_reconnect option."""
        _LOGGER.debug("CommandTransport::Setting auto_reconnect to %s", value)
        self._auto_reconnect = value


    def start_transport(self,
                        api_server_region: str,
                        token: str) -> None:
        """Initialize the websocket and start monitoring"""
        
        if self._event_thread is not None and self._event_thread.is_alive():
            _LOGGER.warning("Transport already started")
            return

        self._api_server_region = api_server_region
        self._token = token
        self._transport_enabled = True
        self._signal_close = False

        def start_ws_wrapper():
            asyncio.run(self._start_websocket())

        self._event_thread = threading.Thread(
            name="DreoWebSocketStream", target=start_ws_wrapper, args=()
        )
        self._event_thread.daemon = True
        self._event_thread.start()

    def stop_transport(self) -> None:
        '''Close down the monitoring socket'''
        _LOGGER.info("Stopping Transport - May take up to 15s")
        self._signal_close = True
        self._transport_enabled = False

    def testonly_interrupt_transport(self) -> None:
        '''Close down the monitoring socket'''
        _LOGGER.info("Interrupting Transport - May take up to 15s")
        self._testonly_signal_interrupt = True

    async def _start_websocket(self) -> None:
        """Start the websocket connection to monitor for device changes and send commands.
        This function exits when monitoring is stopped."""
        _LOGGER.info("Starting WebSocket for incoming changes and commands.")
        # open websocket
        url = f"wss://wsb-{self._api_server_region}.dreo-cloud.com/websocket?accessToken={self._token}&timestamp={Helpers.api_timestamp()}"
        async for ws in websockets.connect(url):
            
            if self._signal_close:
                _LOGGER.info("Transport has been stopped")
                break # This break causes us not to connect
            
            try:
                self._ws = ws
                _LOGGER.info("WebSocket successfully opened")
                await self._ws_handler(ws)
            except websockets.exceptions.ConnectionClosed:
                pass

            if not self._auto_reconnect:
                _LOGGER.error("WebSocket appears closed.  Not Reconnecting.  Restart HA to reconnect.")
                break # This break causes us not to connect
            else:
                continue

        _LOGGER.info("Transport has been stopped and thread done")  

    async def _ws_handler(self, ws):
        consumer_task = asyncio.create_task(self._ws_consumer_handler(ws))
        ping_task = asyncio.create_task(self._ws_ping_handler(ws))
        done, pending = await asyncio.wait(
            [consumer_task, ping_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        _LOGGER.debug("CommandTransport::_ws_handler - WebSocket appears closed.")
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        for task in done:
            task.exception()
        
    async def _ws_consumer_handler(self, ws):
        _LOGGER.debug("CommandTransport::_ws_consumer_handler")
        try:
            async for message in ws:
                _LOGGER.debug("CommandTransport::_ws_consumer_handler - got message")
                self._ws_consume_message(json.loads(message))
        except websockets.exceptions.ConnectionClosedError:
            _LOGGER.debug("CommandTransport::_ws_consumer_handler - WebSocket appears closed.")
        
    async def _ws_ping_handler(self, ws):
        _LOGGER.debug("_ws_ping_handler")
        while True:
            try:
                # Were we told to kill the connection?
                if (self._signal_close):
                    _LOGGER.debug("CommandTransport::_ws_ping_handler - Closing WebSocket")
                    await ws.close()

                if self._testonly_signal_interrupt:
                    _LOGGER.debug("CommandTransport::_ws_ping_handler - Closing WebSocket")
                    self._testonly_signal_interrupt = False
                    try:
                        await ws.close()
                    except CancelledError:
                        pass
                with self._ws_send_lock:
                    await ws.send('2')
                await asyncio.sleep(15)
               
            except websockets.exceptions.ConnectionClosedError:
                _LOGGER.info('Dreo WebSocket Closed - Unless intended, will reconnect')
                break
            except CancelledError:
                _LOGGER.info('Dreo WebSocket Cancelled - Unless intended, will reconnect')
                break

    def _ws_consume_message(self, message):
        self._recv_callback(message)

    def send_message(self, content: dict):
        """Send a command to Dreo servers via the WebSocket."""
        if not self._transport_enabled:
            _LOGGER.error("Command transport disabled. Run start_transport first.")
            raise RuntimeError("Command transport disabled. Run start_transport first.")
        
        async def send_internal() -> None:
            MAX_RETRY_COUNT = 3
            RETRY_DELAY = 5
            retry_count = 0
            while retry_count < MAX_RETRY_COUNT:
                try:
                    with self._ws_send_lock: 
                        await self._ws.send(content)
                    break
                except: # pylint: disable=bare-except
                    retry_count += 1
                    _LOGGER.error("Error sending command. Retrying in %s seconds. Retry count: %s", 
                                  RETRY_DELAY, 
                                  retry_count)
                    await asyncio.sleep(RETRY_DELAY)

        asyncio.run(send_internal())
        