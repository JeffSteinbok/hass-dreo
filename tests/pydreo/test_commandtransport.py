"""Test CommandTransport for PyDreo."""
import asyncio
import json
import threading
from unittest.mock import MagicMock, AsyncMock, patch, call
import pytest
from .imports import CommandTransport


class TestCommandTransport:
    """Test CommandTransport class."""

    def test_init_defaults(self):
        """Test that __init__ sets all default attributes correctly."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        assert transport._event_thread is None
        assert transport._ws is None
        assert transport._ws_send_lock is None  # created lazily on WS event loop
        assert transport._transport_enabled is False
        assert transport._signal_close is False
        assert transport._testonly_signal_interrupt is False
        assert transport._auto_reconnect is True
        assert transport._api_server_region is None
        assert transport._token is None
        assert transport._recv_callback is callback

    def test_auto_reconnect_property_get(self):
        """Test auto_reconnect property getter."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        # Test default value
        assert transport.auto_reconnect is True
        
        # Test after modification
        transport._auto_reconnect = False
        assert transport.auto_reconnect is False

    def test_auto_reconnect_property_set(self):
        """Test auto_reconnect property setter."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        # Set to False
        transport.auto_reconnect = False
        assert transport._auto_reconnect is False
        assert transport.auto_reconnect is False
        
        # Set back to True
        transport.auto_reconnect = True
        assert transport._auto_reconnect is True
        assert transport.auto_reconnect is True

    def test_start_transport_creates_thread(self):
        """Test that start_transport creates and starts a thread."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        with patch.object(threading.Thread, 'start') as mock_start:
            with patch.object(threading, 'Thread') as mock_thread:
                mock_thread_instance = MagicMock()
                mock_thread_instance.is_alive.return_value = False
                mock_thread.return_value = mock_thread_instance
                
                transport.start_transport("us", "test_token_123")
                
                # Verify Thread was created with correct parameters
                mock_thread.assert_called_once()
                args, kwargs = mock_thread.call_args
                assert kwargs['name'] == "DreoWebSocketStream"
                assert kwargs['args'] == ()
                assert 'target' in kwargs
                
                # Verify daemon was set to True
                assert mock_thread_instance.daemon is True
                
                # Verify thread was started
                mock_thread_instance.start.assert_called_once()

    def test_start_transport_already_running(self):
        """Test that start_transport does nothing when thread is already alive."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        # Create a mock thread that is already alive
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        transport._event_thread = mock_thread
        
        with patch.object(threading, 'Thread') as mock_thread_constructor:
            transport.start_transport("us", "test_token_123")
            
            # Thread constructor should not be called
            mock_thread_constructor.assert_not_called()
            
            # Properties should not be updated
            assert transport._api_server_region != "us"
            assert transport._token != "test_token_123"

    def test_start_transport_stores_credentials(self):
        """Test that start_transport stores region and token."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        with patch.object(threading.Thread, 'start'):
            with patch.object(threading, 'Thread') as mock_thread:
                mock_thread_instance = MagicMock()
                mock_thread_instance.is_alive.return_value = False
                mock_thread.return_value = mock_thread_instance
                
                transport.start_transport("eu", "token_abc_123")
                
                assert transport._api_server_region == "eu"
                assert transport._token == "token_abc_123"
                assert transport._transport_enabled is True
                assert transport._signal_close is False

    def test_stop_transport_sets_flags(self):
        """Test that stop_transport sets the correct flags."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        # Set initial state
        transport._transport_enabled = True
        transport._signal_close = False
        
        transport.stop_transport()
        
        assert transport._signal_close is True
        assert transport._transport_enabled is False

    def test_testonly_interrupt_transport(self):
        """Test that testonly_interrupt_transport sets the interrupt flag."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        assert transport._testonly_signal_interrupt is False
        
        transport.testonly_interrupt_transport()
        
        assert transport._testonly_signal_interrupt is True

    def test_send_message_disabled_raises(self):
        """Test that send_message raises RuntimeError when transport is disabled."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        # Transport is disabled by default
        assert transport._transport_enabled is False
        
        with pytest.raises(RuntimeError) as exc_info:
            transport.send_message({"command": "test"})
        
        assert "Command transport disabled" in str(exc_info.value)
        assert "Run start_transport first" in str(exc_info.value)

    def test_send_message_no_event_loop_raises(self):
        """Test that send_message raises when event loop is not available."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        transport._transport_enabled = True
        transport._loop = None

        with pytest.raises(RuntimeError) as exc_info:
            transport.send_message({"command": "test"})
        assert "event loop not available" in str(exc_info.value)

    def test_send_message_enabled(self):
        """Test that send_message calls ws.send when transport is enabled."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        # Enable transport and set up mock event loop
        transport._transport_enabled = True
        
        # Create a mock websocket
        mock_ws = AsyncMock()
        mock_ws.closed = False
        transport._ws = mock_ws
        
        test_message = {"command": "power", "value": "on"}
        
        # Use a real event loop running in a thread to test send_message
        loop = asyncio.new_event_loop()
        transport._loop = loop
        transport._ws_send_lock = asyncio.Lock()
        
        def run_loop():
            loop.run_forever()
        
        t = threading.Thread(target=run_loop, daemon=True)
        t.start()
        try:
            transport.send_message(test_message)
            # Verify ws.send was called with the correct content
            mock_ws.send.assert_called_once_with(test_message)
        finally:
            loop.call_soon_threadsafe(loop.stop)
            t.join(timeout=5)

    def test_send_message_retry_on_failure(self):
        """Test that send_message retries on failure."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        transport._transport_enabled = True
        
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.send.side_effect = [
            Exception("Connection error"),
            Exception("Connection error"),
            None  # Success on third attempt
        ]
        transport._ws = mock_ws
        
        test_message = {"command": "power", "value": "on"}
        
        loop = asyncio.new_event_loop()
        transport._loop = loop
        transport._ws_send_lock = asyncio.Lock()
        
        def run_loop():
            loop.run_forever()
        
        t = threading.Thread(target=run_loop, daemon=True)
        t.start()
        try:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                transport.send_message(test_message)
            assert mock_ws.send.call_count == 3
            mock_ws.send.assert_called_with(test_message)
        finally:
            loop.call_soon_threadsafe(loop.stop)
            t.join(timeout=5)

    def test_send_message_max_retries(self):
        """Test that send_message stops after MAX_RETRY_COUNT failures."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        transport._transport_enabled = True
        
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.send.side_effect = Exception("Connection error")
        transport._ws = mock_ws
        
        test_message = {"command": "power", "value": "on"}
        
        loop = asyncio.new_event_loop()
        transport._loop = loop
        transport._ws_send_lock = asyncio.Lock()
        
        def run_loop():
            loop.run_forever()
        
        t = threading.Thread(target=run_loop, daemon=True)
        t.start()
        try:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                transport.send_message(test_message)
            assert mock_ws.send.call_count == 3
        finally:
            loop.call_soon_threadsafe(loop.stop)
            t.join(timeout=5)

    def test_ws_consume_message_calls_callback(self):
        """Test that _ws_consume_message calls the recv_callback."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        test_message = {"type": "status", "data": {"power": "on"}}
        
        transport._ws_consume_message(test_message)
        
        callback.assert_called_once_with(test_message)

    def test_ws_consume_message_with_various_messages(self):
        """Test _ws_consume_message with different message types."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        messages = [
            {"type": "status"},
            {"type": "update", "device": "fan1", "state": {"power": True}},
            {},
            {"complex": {"nested": {"data": [1, 2, 3]}}},
        ]
        
        for msg in messages:
            transport._ws_consume_message(msg)
        
        assert callback.call_count == len(messages)
        callback.assert_has_calls([call(msg) for msg in messages])

    def test_ws_consumer_handler(self):
        """Test _ws_consumer_handler receives and processes messages."""
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            
            # Create mock websocket with async iteration
            mock_ws = AsyncMock()
            test_messages = [
                '{"type": "status", "power": "on"}',
                '{"type": "update", "value": 123}',
            ]
            
            # Make the websocket async iterable
            mock_ws.__aiter__.return_value = iter(test_messages)
            
            # Run the consumer handler
            await transport._ws_consumer_handler(mock_ws)
            
            # Verify callback was called for each message
            assert callback.call_count == 2
            callback.assert_any_call({"type": "status", "power": "on"})
            callback.assert_any_call({"type": "update", "value": 123})
        
        asyncio.run(_test())

    def test_ws_consumer_handler_connection_closed(self):
        """Test _ws_consumer_handler handles ConnectionClosedError gracefully."""
        # Import the actual exception for testing
        import websockets.exceptions
        
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            
            # Create mock websocket that raises ConnectionClosedError
            mock_ws = AsyncMock()
            
            # Create an async generator that raises the exception
            async def async_iter():
                raise websockets.exceptions.ConnectionClosedError(None, None)
                yield  # pragma: no cover - never reached
            
            # Set up the mock to use our async generator
            mock_ws.__aiter__ = lambda self: async_iter()
            
            # Should not raise an exception
            await transport._ws_consumer_handler(mock_ws)
        
        asyncio.run(_test())

    def test_ws_ping_handler_signal_close(self):
        """Test _ws_ping_handler closes WS when signal_close is set."""
        import websockets.exceptions
        
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            transport._ws_send_lock = asyncio.Lock()
            
            # Set signal_close immediately
            transport._signal_close = True
            
            mock_ws = AsyncMock()
            
            # Mock asyncio.sleep to avoid delays and break the loop
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                mock_sleep.side_effect = websockets.exceptions.ConnectionClosedError(None, None)
                
                await transport._ws_ping_handler(mock_ws)
            
            # Verify close was called
            mock_ws.close.assert_called()
        
        asyncio.run(_test())

    def test_ws_ping_handler_test_interrupt(self):
        """Test _ws_ping_handler closes WS when testonly_signal_interrupt is set."""
        import websockets.exceptions
        
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            transport._ws_send_lock = asyncio.Lock()
            
            # Set test interrupt flag
            transport._testonly_signal_interrupt = True
            
            mock_ws = AsyncMock()
            
            # Mock asyncio.sleep to break after first iteration
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                mock_sleep.side_effect = websockets.exceptions.ConnectionClosedError(None, None)
                
                await transport._ws_ping_handler(mock_ws)
            
            # Verify close was called
            mock_ws.close.assert_called()
            # Verify flag was reset
            assert transport._testonly_signal_interrupt is False
        
        asyncio.run(_test())

    def test_ws_ping_handler_sends_ping(self):
        """Test _ws_ping_handler sends ping messages."""
        import websockets.exceptions
        
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            transport._ws_send_lock = asyncio.Lock()
            
            mock_ws = AsyncMock()
            
            # Create a counter to limit iterations
            iteration_count = [0]
            
            async def limited_sleep(duration):
                iteration_count[0] += 1
                if iteration_count[0] >= 2:
                    raise websockets.exceptions.ConnectionClosedError(None, None)
            
            with patch('asyncio.sleep', side_effect=limited_sleep):
                await transport._ws_ping_handler(mock_ws)
            
            # Verify ping was sent (at least once)
            assert mock_ws.send.call_count >= 1
            mock_ws.send.assert_called_with('2')
        
        asyncio.run(_test())

    def test_ws_ping_handler_connection_closed(self):
        """Test _ws_ping_handler breaks on ConnectionClosedError."""
        import websockets.exceptions
        
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            transport._ws_send_lock = asyncio.Lock()
            
            mock_ws = AsyncMock()
            mock_ws.send.side_effect = websockets.exceptions.ConnectionClosedError(None, None)
            
            # Should exit gracefully
            await transport._ws_ping_handler(mock_ws)
            
            # Verify send was called before breaking
            mock_ws.send.assert_called_once_with('2')
        
        asyncio.run(_test())

    def test_ws_ping_handler_cancelled(self):
        """Test _ws_ping_handler handles CancelledError."""
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            transport._ws_send_lock = asyncio.Lock()
            
            mock_ws = AsyncMock()
            mock_ws.send.side_effect = asyncio.CancelledError()
            
            # Should exit gracefully
            await transport._ws_ping_handler(mock_ws)
            
            # Verify send was called before breaking
            mock_ws.send.assert_called_once_with('2')
        
        asyncio.run(_test())

    def test_ws_handler_cancels_pending_tasks(self):
        """Test _ws_handler cancels pending tasks when one completes."""
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            
            mock_ws = AsyncMock()
            
            # Make consumer complete quickly
            mock_ws.__aiter__.return_value = iter([])
            
            # Track if ping task gets cancelled
            ping_cancelled = [False]
            
            async def mock_ping_handler(ws):
                try:
                    await asyncio.sleep(10)
                except asyncio.CancelledError:
                    ping_cancelled[0] = True
                    raise
            
            # Patch the handlers
            with patch.object(transport, '_ws_consumer_handler', return_value=asyncio.sleep(0)):
                with patch.object(transport, '_ws_ping_handler', side_effect=mock_ping_handler):
                    await transport._ws_handler(mock_ws)
            
            # Verify the pending task was cancelled
            assert ping_cancelled[0] is True
        
        asyncio.run(_test())

    def test_ws_handler_both_tasks_complete(self):
        """Test _ws_handler handles both tasks completing."""
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            
            mock_ws = AsyncMock()
            
            # Both tasks complete quickly
            async def quick_consumer(ws):
                pass
            
            async def quick_ping(ws):
                pass
            
            with patch.object(transport, '_ws_consumer_handler', side_effect=quick_consumer):
                with patch.object(transport, '_ws_ping_handler', side_effect=quick_ping):
                    await transport._ws_handler(mock_ws)
            
            # Should complete without errors
        
        asyncio.run(_test())

    def test_start_websocket_signal_close_before_connect(self):
        """Test _start_websocket exits if signal_close is set before connection."""
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            transport._api_server_region = "us"
            transport._token = "test_token"
            transport._signal_close = True
            
            # Mock websockets.connect to yield once
            mock_ws = AsyncMock()
            
            async def mock_connect(url):
                yield mock_ws
            
            with patch('custom_components.dreo.pydreo.commandtransport.websockets.connect', side_effect=mock_connect):
                await transport._start_websocket()
            
            # Handler should not be called since we break immediately
            assert transport._ws is None  # ws is not assigned when signal_close is True
        
        asyncio.run(_test())

    def test_start_websocket_auto_reconnect_false(self):
        """Test _start_websocket exits after disconnect when auto_reconnect is False."""
        import websockets.exceptions
        
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            transport._api_server_region = "us"
            transport._token = "test_token"
            transport._auto_reconnect = False
            
            # Mock websockets.connect to yield once then raise ConnectionClosed
            mock_ws = AsyncMock()
            
            iteration_count = [0]
            
            async def mock_connect(url):
                iteration_count[0] += 1
                if iteration_count[0] == 1:
                    yield mock_ws
            
            with patch('custom_components.dreo.pydreo.commandtransport.websockets.connect', side_effect=mock_connect):
                with patch.object(transport, '_ws_handler', side_effect=websockets.exceptions.ConnectionClosed(None, None)):
                    await transport._start_websocket()
            
            # Should only connect once
            assert iteration_count[0] == 1
        
        asyncio.run(_test())

    def test_start_websocket_auto_reconnect_true(self):
        """Test _start_websocket reconnects when auto_reconnect is True."""
        import websockets.exceptions
        
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            transport._api_server_region = "us"
            transport._token = "test_token"
            transport._auto_reconnect = True
            
            mock_ws = AsyncMock()
            
            connect_count = [0]
            
            # Create an async context manager mock that yields a websocket each time
            class MockWebSocketConnect:
                def __init__(self, url):
                    self.url = url
                    
                async def __aenter__(self):
                    connect_count[0] += 1
                    return mock_ws
                
                async def __aexit__(self, *args):
                    pass
                
                def __aiter__(self):
                    return self
                
                async def __anext__(self):
                    # Yield websocket once, then stop iteration
                    if connect_count[0] < 3:  # Allow up to 3 connections
                        connect_count[0] += 1
                        return mock_ws
                    raise StopAsyncIteration
            
            def mock_connect_factory(url):
                return MockWebSocketConnect(url)
            
            with patch('custom_components.dreo.pydreo.commandtransport.websockets.connect', side_effect=mock_connect_factory):
                # Handler raises exception first time to trigger reconnect
                call_count = [0]
                async def mock_handler(ws):
                    call_count[0] += 1
                    if call_count[0] == 1:
                        # First call raises exception to trigger reconnect
                        raise websockets.exceptions.ConnectionClosed(None, None)
                    else:
                        # Second call sets signal_close to stop reconnecting
                        transport._signal_close = True
                
                with patch.object(transport, '_ws_handler', side_effect=mock_handler):
                    await transport._start_websocket()
            
            # Handler should be called twice (once on first connection, once on reconnect)
            assert call_count[0] == 2
        
        asyncio.run(_test())

    def test_start_websocket_url_format(self):
        """Test _start_websocket constructs the correct WebSocket URL."""
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            transport._api_server_region = "eu"
            transport._token = "my_token_123"
            
            captured_url = [None]
            
            async def mock_connect(url):
                captured_url[0] = url
                # Signal close after capturing URL so the loop exits
                transport._signal_close = True
                # Yield nothing — the async for won't iterate
                return
                yield  # Make this an async generator  # pylint: disable=unreachable
            
            with patch('custom_components.dreo.pydreo.commandtransport.websockets.connect', side_effect=mock_connect):
                with patch.object(transport._recv_callback, '__call__'):
                    await transport._start_websocket()
            
            # Verify URL format
            assert captured_url[0] is not None
            url = str(captured_url[0])
            assert url.startswith("wss://wsb-eu.dreo-tech.com/websocket")
            assert "accessToken=my_token_123" in url
            assert "timestamp=" in url
        
        asyncio.run(_test())

    def test_send_message_with_lock(self):
        """Test that send_message uses the lock correctly."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        transport._transport_enabled = True
        
        mock_ws = AsyncMock()
        mock_ws.closed = False
        transport._ws = mock_ws
        
        loop = asyncio.new_event_loop()
        transport._loop = loop
        transport._ws_send_lock = asyncio.Lock()
        
        def run_loop():
            loop.run_forever()
        
        t = threading.Thread(target=run_loop, daemon=True)
        t.start()
        try:
            transport.send_message({"test": "data"})
            mock_ws.send.assert_called_once_with({"test": "data"})
        finally:
            loop.call_soon_threadsafe(loop.stop)
            t.join(timeout=5)

    def test_multiple_messages_sequential(self):
        """Test sending multiple messages sequentially."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        transport._transport_enabled = True
        
        mock_ws = AsyncMock()
        mock_ws.closed = False
        transport._ws = mock_ws
        
        loop = asyncio.new_event_loop()
        transport._loop = loop
        transport._ws_send_lock = asyncio.Lock()
        
        def run_loop():
            loop.run_forever()
        
        t = threading.Thread(target=run_loop, daemon=True)
        t.start()
        try:
            messages = [
                {"command": "power", "value": "on"},
                {"command": "speed", "value": 5},
                {"command": "oscillate", "value": True},
            ]
            
            for msg in messages:
                transport.send_message(msg)
            
            assert mock_ws.send.call_count == 3
            for i, msg in enumerate(messages):
                assert mock_ws.send.call_args_list[i] == call(msg)
        finally:
            loop.call_soon_threadsafe(loop.stop)
            t.join(timeout=5)

    def test_recv_callback_not_called_without_messages(self):
        """Test that recv_callback is not called when no messages are received."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        # Just creating the transport shouldn't call the callback
        callback.assert_not_called()
        
        # Other operations shouldn't call it either
        transport.auto_reconnect = False
        transport.stop_transport()
        
        callback.assert_not_called()

    def test_thread_name(self):
        """Test that the WebSocket thread has the correct name."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        
        with patch.object(threading, 'Thread') as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread_instance.is_alive.return_value = False
            mock_thread.return_value = mock_thread_instance
            
            transport.start_transport("us", "token")
            
            # Verify thread was created with correct name
            args, kwargs = mock_thread.call_args
            assert kwargs['name'] == "DreoWebSocketStream"

    def test_send_message_different_data_types(self):
        """Test send_message with different data types in the dict."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        transport._transport_enabled = True
        
        mock_ws = AsyncMock()
        mock_ws.closed = False
        transport._ws = mock_ws
        
        loop = asyncio.new_event_loop()
        transport._loop = loop
        transport._ws_send_lock = asyncio.Lock()
        
        def run_loop():
            loop.run_forever()
        
        t = threading.Thread(target=run_loop, daemon=True)
        t.start()
        try:
            messages = [
                {"string": "value", "int": 42, "float": 3.14},
                {"bool": True, "none": None},
                {"list": [1, 2, 3], "nested": {"a": {"b": "c"}}},
            ]
            
            for msg in messages:
                transport.send_message(msg)
            
            assert mock_ws.send.call_count == len(messages)
        finally:
            loop.call_soon_threadsafe(loop.stop)
            t.join(timeout=5)

    def test_update_token(self):
        """Test that update_token updates the stored token."""
        callback = MagicMock()
        transport = CommandTransport(callback)
        transport._token = "old_token"

        transport.update_token("new_token")
        assert transport._token == "new_token"

    def test_reconnect_uses_fresh_token(self):
        """Test that WebSocket reconnect picks up a new token."""
        async def _test():
            callback = MagicMock()
            transport = CommandTransport(callback)
            transport._api_server_region = "us"
            transport._token = "token_v1"

            captured_urls = []
            call_count = [0]

            async def mock_connect(url):
                captured_urls.append(url)
                call_count[0] += 1
                if call_count[0] == 1:
                    # After first connection, update token and yield a mock WS
                    transport._token = "token_v2"
                    mock_ws = AsyncMock()
                    mock_ws.__aiter__ = MagicMock(return_value=iter([]))
                    yield mock_ws
                elif call_count[0] == 2:
                    # Second connection should use new token; signal close
                    transport._signal_close = True
                    return
                    yield  # pylint: disable=unreachable

            with patch('custom_components.dreo.pydreo.commandtransport.websockets.connect', side_effect=mock_connect):
                transport._auto_reconnect = True
                await transport._start_websocket()

            assert len(captured_urls) == 2
            assert "accessToken=token_v1" in captured_urls[0]
            assert "accessToken=token_v2" in captured_urls[1]

        asyncio.run(_test())
