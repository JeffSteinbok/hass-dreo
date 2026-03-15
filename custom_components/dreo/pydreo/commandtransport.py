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

_LOGGER = logging.getLogger(__name__)

WEBSOCKET_PING_INTERVAL = 15  # seconds between keepalive pings
WEBSOCKET_PING_MESSAGE = '2'  # Dreo WebSocket keepalive message
MAX_RETRY_COUNT = 3
RETRY_DELAY = 5  # seconds between send retries

class CommandTransport: 
    """Command transport class for Dreo API."""

    def __init__(self, 
                 recv_callback: Callable[[dict], None] ):

        self._event_thread = None
        self._ws = None
        self._ws_send_lock = None  # asyncio.Lock, created on the WS event loop
        self._transport_enabled = False
        self._signal_close = False
        self._testonly_signal_interrupt = False
        self._auto_reconnect = True
        self._loop = None

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
        _LOGGER.debug("auto_reconnect.setter: Setting auto_reconnect to %s", value)
        self._auto_reconnect = value


    def start_transport(self,
                        api_server_region: str,
                        token: str) -> None:
        """Initialize the websocket and start monitoring"""
        
        if self._event_thread is not None and self._event_thread.is_alive():
            _LOGGER.warning("start_transport: Transport already started")
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
        _LOGGER.info("stop_transport: Stopping Transport - May take up to 15s")
        self._signal_close = True
        self._transport_enabled = False

        # Close WebSocket from the WS thread's event loop if available
        if self._loop and self._ws and not self._ws.closed:
            try:
                asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.debug("stop_transport: Could not close WebSocket gracefully")

        # Wait for the thread to finish
        if self._event_thread and self._event_thread.is_alive():
            self._event_thread.join(timeout=20)
            if self._event_thread.is_alive():
                _LOGGER.warning("stop_transport: WebSocket thread did not stop within timeout")

    def update_token(self, token: str) -> None:
        """Update the authentication token for WebSocket reconnections."""
        _LOGGER.info("update_token: Updating WebSocket token")
        self._token = token

    def testonly_interrupt_transport(self) -> None:
        '''Close down the monitoring socket'''
        _LOGGER.info("testonly_interrupt_transport: Interrupting Transport - May take up to 15s")
        self._testonly_signal_interrupt = True

    async def _start_websocket(self) -> None:
        """Start the websocket connection to monitor for device changes and send commands.
        This function exits when monitoring is stopped."""
        _LOGGER.info("_start_websocket: Starting WebSocket for incoming changes and commands.")
        self._loop = asyncio.get_event_loop()
        self._ws_send_lock = asyncio.Lock()

        while not self._signal_close:
            # Build URL fresh each attempt so token updates are picked up
            url = f"wss://wsb-{self._api_server_region}.dreo-tech.com/websocket?accessToken={self._token}&timestamp={Helpers.api_timestamp()}"
            try:
                async for ws in websockets.connect(url):

                    if self._signal_close:
                        _LOGGER.info("_start_websocket: Transport has been stopped")
                        break

                    try:
                        self._ws = ws
                        _LOGGER.info("_start_websocket: WebSocket successfully opened")
                        await self._ws_handler(ws)
                    except websockets.exceptions.ConnectionClosed:
                        pass

                    if not self._auto_reconnect:
                        _LOGGER.error("_start_websocket: WebSocket appears closed.  Not Reconnecting.  Restart HA to reconnect.")
                        self._loop = None
                        _LOGGER.info("_start_websocket: Transport has been stopped and thread done")
                        return

                    # Break out of async for to rebuild URL with potentially refreshed token
                    _LOGGER.info("_start_websocket: Reconnecting with current token")
                    break

            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.error("_start_websocket: WebSocket connection failed: %s", ex)
                if not self._auto_reconnect or self._signal_close:
                    break
                await asyncio.sleep(RETRY_DELAY)

        self._loop = None
        _LOGGER.info("_start_websocket: Transport has been stopped and thread done")

    async def _ws_handler(self, ws):
        consumer_task = asyncio.create_task(self._ws_consumer_handler(ws))
        ping_task = asyncio.create_task(self._ws_ping_handler(ws))
        done, pending = await asyncio.wait(
            [consumer_task, ping_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        _LOGGER.debug("_ws_handler: WebSocket appears closed.")
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        for task in done:
            exc = task.exception()
            if exc:
                _LOGGER.error("_ws_handler: Task failed with exception: %s", exc)
        
    async def _ws_consumer_handler(self, ws):
        _LOGGER.debug("_ws_consumer_handler: Starting")
        try:
            async for message in ws:
                _LOGGER.debug("_ws_consumer_handler: got message")
                try:
                    self._ws_consume_message(json.loads(message))
                except (json.JSONDecodeError, Exception) as ex:  # pylint: disable=broad-except
                    _LOGGER.error("_ws_consumer_handler: Error processing message: %s", ex)
        except websockets.exceptions.ConnectionClosedError:
            _LOGGER.debug("_ws_consumer_handler: WebSocket appears closed.")
        
    async def _ws_ping_handler(self, ws):
        _LOGGER.debug("_ws_ping_handler: Starting")
        while True:
            try:
                # Were we told to kill the connection?
                if (self._signal_close):
                    _LOGGER.debug("_ws_ping_handler: Closing WebSocket")
                    await ws.close()

                if self._testonly_signal_interrupt:
                    _LOGGER.debug("_ws_ping_handler: Closing WebSocket (test interrupt)")
                    self._testonly_signal_interrupt = False
                    try:
                        await ws.close()
                    except CancelledError:
                        pass
                async with self._ws_send_lock:
                    await ws.send(WEBSOCKET_PING_MESSAGE)
                await asyncio.sleep(WEBSOCKET_PING_INTERVAL)
               
            except websockets.exceptions.ConnectionClosedError:
                _LOGGER.info('_ws_ping_handler: Dreo WebSocket Closed - Unless intended, will reconnect')
                break
            except CancelledError:
                _LOGGER.info('_ws_ping_handler: Dreo WebSocket Cancelled - Unless intended, will reconnect')
                break

    def _ws_consume_message(self, message):
        try:
            self._recv_callback(message)
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error("_ws_consume_message: Callback error: %s", ex)

    def send_message(self, content: dict):
        """Send a command to Dreo servers via the WebSocket."""
        if not self._transport_enabled:
            _LOGGER.error("send_message: Command transport disabled. Run start_transport first.")
            raise RuntimeError("Command transport disabled. Run start_transport first.")
        
        if self._loop is None or self._loop.is_closed():
            _LOGGER.error("send_message: WebSocket event loop not available.")
            raise RuntimeError("WebSocket event loop not available.")

        async def send_internal() -> None:
            retry_count = 0
            while retry_count < MAX_RETRY_COUNT:
                try:
                    if self._ws is None or self._ws.closed:
                        raise RuntimeError("WebSocket not connected")
                    async with self._ws_send_lock: 
                        await self._ws.send(content)
                    break
                except Exception:  # pylint: disable=broad-except
                    retry_count += 1
                    _LOGGER.error("send_message: Error sending command. Retrying in %s seconds. Retry count: %s", 
                                  RETRY_DELAY, 
                                  retry_count)
                    await asyncio.sleep(RETRY_DELAY)

        future = asyncio.run_coroutine_threadsafe(send_internal(), self._loop)
        future.result(timeout=MAX_RETRY_COUNT * RETRY_DELAY + 5)
        
