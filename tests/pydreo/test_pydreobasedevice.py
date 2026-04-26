"""Tests for PyDreoBaseDevice callback safety."""

import logging
from unittest.mock import MagicMock, patch
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase

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
