"""Tests for PyDreo send_command retry logic, ACK handling, and command slot management."""

import logging
import threading
from unittest.mock import patch, MagicMock
import pytest
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND, PATCH_BASE_PATH

from custom_components.dreo.pydreo import PyDreo
from custom_components.dreo.pydreo.pydreobasedevice import PyDreoBaseDevice

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

PATCH_TRANSPORT_SEND = f"{PATCH_BASE_PATH}.CommandTransport.send_message"


class TestSendCommand(TestBase):
    """Tests for send_command, retry logic, and ACK handling."""

    def _load_fan(self):
        """Load a test fan device."""
        self.get_devices_file_name = "get_devices_HAF004S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        return self.pydreo_manager.devices[0]

    def test_send_command_success_with_ack(self):
        """Test that send_command succeeds when ACK is received."""
        fan = self._load_fan()

        def simulate_ack(content):
            """Simulate server sending back a control-report ACK."""
            self.pydreo_manager._transport_consume_message(
                {"devicesn": fan.serial_number, "method": "control-report", "reported": {POWERON_KEY: True}}
            )

        with patch(PATCH_TRANSPORT_SEND, side_effect=simulate_ack):
            fan.is_on = True

    def test_send_command_retries_on_timeout(self):
        """Test that send_command retries when no ACK is received."""
        fan = self._load_fan()

        with patch(PATCH_TRANSPORT_SEND) as mock_transport, patch(f"{PATCH_BASE_PATH}._COMMAND_ACK_TIMEOUT", 0.1):
            fan.is_on = True
            # Should have been called 1 (initial) + 2 (retries) = 3 times
            assert mock_transport.call_count == 3

    def test_send_command_stops_retrying_on_ack(self):
        """Test that send_command stops retrying once ACK is received."""
        fan = self._load_fan()
        call_count = 0

        def ack_on_second_attempt(content):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                self.pydreo_manager._transport_consume_message(
                    {"devicesn": fan.serial_number, "method": "control-report", "reported": {POWERON_KEY: True}}
                )

        with patch(PATCH_TRANSPORT_SEND, side_effect=ack_on_second_attempt), patch(f"{PATCH_BASE_PATH}._COMMAND_ACK_TIMEOUT", 0.1):
            fan.is_on = True
            # Should stop after 2nd attempt (got ACK), not retry a 3rd time
            assert call_count == 2

    def test_send_command_releases_slot_on_exception(self):
        """Test that command slot is released when transport raises an exception."""
        fan = self._load_fan()

        with patch(PATCH_TRANSPORT_SEND, side_effect=RuntimeError("Connection lost")):
            with pytest.raises(RuntimeError):
                fan.is_on = True

        # Slot should be released - another command should not deadlock
        assert self.pydreo_manager._pending_command_device is None

    def test_ack_ignores_wrong_device(self):
        """Test that ACK from a different device is ignored."""
        fan = self._load_fan()

        def ack_wrong_device(content):
            self.pydreo_manager._transport_consume_message(
                {"devicesn": "WRONG_DEVICE_SN", "method": "control-report", "reported": {POWERON_KEY: True}}
            )

        with patch(PATCH_TRANSPORT_SEND, side_effect=ack_wrong_device), patch(f"{PATCH_BASE_PATH}._COMMAND_ACK_TIMEOUT", 0.1):
            fan.is_on = True
            # No valid ACK received - should have exhausted all retries

    def test_ack_ignores_wrong_method(self):
        """Test that messages with non-ACK method are ignored."""
        fan = self._load_fan()

        def ack_wrong_method(content):
            self.pydreo_manager._transport_consume_message({"devicesn": fan.serial_number, "method": "report", "reported": {POWERON_KEY: True}})

        with patch(PATCH_TRANSPORT_SEND, side_effect=ack_wrong_method), patch(f"{PATCH_BASE_PATH}._COMMAND_ACK_TIMEOUT", 0.1):
            fan.is_on = True
            # No valid ACK (wrong method) - should have exhausted all retries

    def test_command_slot_serializes_commands(self):
        """Test that only one command can be in-flight at a time."""
        fan = self._load_fan()
        slot_was_busy = threading.Event()
        first_command_started = threading.Event()

        def slow_send(content):
            first_command_started.set()

        with (
            patch(PATCH_TRANSPORT_SEND, side_effect=slow_send),
            patch(f"{PATCH_BASE_PATH}._COMMAND_ACK_TIMEOUT", 0.2),
            patch(f"{PATCH_BASE_PATH}._MAX_COMMAND_RETRIES", 0),
        ):

            def send_second_command():
                first_command_started.wait(timeout=2)
                if self.pydreo_manager._pending_command_device is not None:
                    slot_was_busy.set()
                fan.is_on = False

            t = threading.Thread(target=send_second_command)
            t.start()
            fan.is_on = True
            t.join(timeout=5)

            assert slot_was_busy.is_set(), "Second command should have found slot busy"


class TestAuthRegion(TestBase):
    """Tests for auth region validation."""

    def test_invalid_region_raises_value_error(self):
        """Test that an invalid auth region raises ValueError."""
        self.pydreo_manager.auth_region = "invalid_region"
        with pytest.raises(ValueError, match="Invalid Auth Region"):
            _ = self.pydreo_manager.api_server_region

    def test_na_region(self):
        """Test NA region returns US API server."""
        self.pydreo_manager.auth_region = "NA"
        assert self.pydreo_manager.api_server_region == "us"

    def test_eu_region(self):
        """Test EU region returns EU API server."""
        self.pydreo_manager.auth_region = "EU"
        assert self.pydreo_manager.api_server_region == "eu"
