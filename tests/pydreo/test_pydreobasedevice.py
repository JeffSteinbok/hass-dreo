"""Tests for PyDreoBaseDevice callback safety."""
import logging
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from .imports import * # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_CALL_DREO_API

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestPyDreoBaseDevice(TestBase):
    """Test PyDreoBaseDevice class."""

    def test_do_callbacks_continues_after_exception(self):
        """Test that _do_callbacks continues executing remaining callbacks when one raises."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]

        cb1 = MagicMock()
        cb2 = MagicMock(side_effect=RuntimeError("callback error"))
        cb3 = MagicMock()

        device.add_attr_callback(cb1)
        device.add_attr_callback(cb2)
        device.add_attr_callback(cb3)

        device._do_callbacks()

        # All three should have been called, even though cb2 raised
        cb1.assert_called_once()
        cb2.assert_called_once()
        cb3.assert_called_once()

    def test_do_callbacks_no_callbacks(self):
        """Test _do_callbacks with no registered callbacks."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]

        # Should not raise
        device._do_callbacks()

    def test_refresh_state_calls_load_device_state(self):
        """Test refresh_state() triggers a REST API call when not throttled."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]

        # Reset last refresh so throttle won't block us
        device._last_state_refresh = None

        api_call_count_before = self.mock_api.call_count
        result = device.refresh_state()

        assert result is True
        # Exactly one additional API call (devicestate) should have been made
        assert self.mock_api.call_count == api_call_count_before + 1

    def test_refresh_state_throttled_within_window(self):
        """Test refresh_state() is throttled when called twice in quick succession."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]

        # First call – should go through
        device._last_state_refresh = None
        result1 = device.refresh_state()
        assert result1 is True

        # Second call immediately after – should be throttled
        api_call_count = self.mock_api.call_count
        result2 = device.refresh_state()
        assert result2 is False
        assert self.mock_api.call_count == api_call_count, "Throttled call should not make an API request"

    def test_refresh_state_allowed_after_throttle_expires(self):
        """Test refresh_state() makes an API call once the throttle window has passed."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]

        from custom_components.dreo.pydreo.pydreobasedevice import STATE_REFRESH_THROTTLE_SECONDS

        # Simulate that the last refresh happened just beyond the throttle window
        device._last_state_refresh = (
            datetime.now() - timedelta(seconds=STATE_REFRESH_THROTTLE_SECONDS + 1)
        )

        api_call_count_before = self.mock_api.call_count
        result = device.refresh_state()

        assert result is True
        assert self.mock_api.call_count == api_call_count_before + 1

    def test_refresh_state_updates_connected_status(self):
        """Test that refresh_state() updates the connected flag from the API response."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]

        # Confirm initial connected state is True (from test fixture)
        assert device.connected is True

        # Manually set connected to None to simulate unknown state
        device._connected = None
        device._last_state_refresh = None

        # refresh_state() should restore the connected flag from the API
        device.refresh_state()
        assert device.connected is True
