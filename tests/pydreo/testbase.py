"""Base class for all tests. Contains a mock for call_dreo_api() function and instantiated Dreo object."""

# pylint: disable=W0201
import logging
import os
import time
from typing import Optional
from unittest.mock import patch
import pytest
from custom_components.dreo.pydreo.commandoutbox import OutboxTiming
from custom_components.dreo.pydreo.pydreobasedevice import PyDreoBaseDevice
from .imports import *  # pylint: disable=W0401,W0614
from . import defaults
from . import call_json

logger = logging.getLogger(__name__)

API_REPONSE_BASE_PATH = "tests/pydreo/api_responses/"

PATCH_BASE_PATH = "custom_components.dreo.pydreo"
PATCH_SEND_COMMAND = f"{PATCH_BASE_PATH}.PyDreo.send_command"
PATCH_CALL_DREO_API = f"{PATCH_BASE_PATH}.PyDreo.call_dreo_api"

Defaults = defaults.Defaults


def wait_for(predicate, timeout: float = 2.0) -> bool:
    """Poll until predicate() is true (scheduler tests must not rely on fixed sleeps)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return False


class TestBase:
    """Base class for all tests.

    Contains instantiated PyDreo object and mocked
    API call for call_api() function."""

    @property
    def get_devices_file_name(self):
        """Get the file name for the devices file."""
        return self._get_devices_file_name

    @get_devices_file_name.setter
    def get_devices_file_name(self, value: str):
        """Set the file name for the devices file."""
        self._get_devices_file_name = value

    @pytest.fixture(autouse=True, scope="function")
    def setup(self, caplog):
        """Fixture to instantiate Dreo object, start logging and start Mock.

        Attributes
        ----------
        self.mock_api : Mock
        self.pydreo_manager : PyDreo
        self.caplog : LogCaptureFixture

        Yields
        ------
        Class instance with mocked call_api() function and Dreo object
        """
        self._get_devices_file_name = None
        self.mock_api_call = patch(PATCH_CALL_DREO_API)
        self.caplog = caplog
        self.mock_api = self.mock_api_call.start()
        self.mock_api.side_effect = self.call_dreo_api
        self.mock_api.create_autospect()
        self.mock_api.return_value.ok = True
        self.pydreo_manager = PyDreo("EMAIL", "PASSWORD", redact=True)  # pylint: disable=E0601
        self.pydreo_manager.enabled = True
        self.pydreo_manager.token = Defaults.token
        self.pydreo_manager.account_id = Defaults.account_id
        caplog.set_level(logging.DEBUG)
        # Send commands synchronously and unpaced in tests (batching and
        # pacing protect real hardware, not mocks).
        self._orig_command_timing = PyDreoBaseDevice._COMMAND_TIMING
        PyDreoBaseDevice._COMMAND_TIMING = OutboxTiming.IMMEDIATE
        yield
        PyDreoBaseDevice._COMMAND_TIMING = self._orig_command_timing
        # Cancel deferred work (outbox flushes, verification timers) before
        # the API mock goes away, or a late timer would attempt a real call.
        for device in self.pydreo_manager.devices:
            device.dispose()
        self.mock_api_call.stop()

    wait_for = staticmethod(wait_for)

    def install_manual_scheduler(self) -> list[dict]:
        """Install a test scheduler that records delayed work for manual firing.

        Delayed work goes through ``PyDreo.schedule_call_later``; replacing it
        makes anything time-based (command-outbox flushes, ceiling-fan state
        verification) deterministic instead of slept-on.

        Returns a list of dicts with keys: delay, callback, cancelled.
        """
        scheduled: list[dict] = []

        def schedule_call_later(delay: float, callback) -> callable:
            entry = {"delay": delay, "callback": callback, "cancelled": False}
            scheduled.append(entry)

            def cancel() -> None:
                entry["cancelled"] = True

            return cancel

        self.pydreo_manager.set_schedule_call_later(schedule_call_later)
        return scheduled

    @staticmethod
    def fire_last_scheduled(scheduled: list[dict]) -> None:
        """Fire the most recent non-cancelled scheduled callback."""
        for entry in reversed(scheduled):
            if not entry["cancelled"]:
                entry["callback"]()
                return
        raise AssertionError("No non-cancelled scheduled callback to fire")

    @staticmethod
    def pending_scheduled(scheduled: list[dict]) -> list[dict]:
        """The scheduled entries that have not been cancelled."""
        return [entry for entry in scheduled if not entry["cancelled"]]

    def call_dreo_api(self, api: str, json_object: Optional[dict] = None):
        """Call Dreo REST API"""
        print(f"API call: {api} {json_object}")
        logger.debug("API call: %s %s", api, json_object)

        if api == "login":
            return (
                {
                    "traceId": Defaults.trace_id,
                    "msg": "",
                    "data": {
                        "region": "NA",
                        "access_token": Defaults.token,
                    },
                    "code": 0,
                },
                200,
            )
        if api == "devicelist":
            return (call_json.get_response_from_file(self.get_devices_file_name), 200)
        if api == "devicestate":
            logger.debug("API call: %s %s", api, json_object)
            file_name = f"get_device_state_{json_object['deviceSn']}.json"
            if os.path.exists(API_REPONSE_BASE_PATH + file_name):
                logger.debug("Device state loaded from file: %s", API_REPONSE_BASE_PATH + file_name)
                return (call_json.get_response_from_file(file_name), 200)
            else:
                logger.debug("No file found: %s", API_REPONSE_BASE_PATH + file_name)
                return {}, 200
        if api == "setting_get":
            file_name = f"get_device_setting_{json_object['deviceSn']}_{json_object['dataKey']}.json"
            if os.path.exists(API_REPONSE_BASE_PATH + file_name):
                logger.debug("Device setting loaded from file: %s", API_REPONSE_BASE_PATH + file_name)
                return (call_json.get_response_from_file(file_name), 200)
            else:
                logger.debug("No file found: %s", API_REPONSE_BASE_PATH + file_name)
                return {}, 200
