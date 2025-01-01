"""Tests for Dreo Fans"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import diagnostics

import pytest
from .imports import *  # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestDiagnostics(IntegrationTestBase):
    """Test Diagnostics functionality{"""

    def test_diagnostics_simple(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HTF005S.json"
        self.pydreo_manager.load_devices()
        diag = diagnostics._get_diagnostics(self.pydreo_manager)  # pylint: disable=protected-access
        dreo = diag.get("dreo")
        assert dreo.get("device_count") == 1
        raw_device_list = dreo.get("raw_devicelist").get("data")
        assert raw_device_list.get("totalNum") == 1
        assert raw_device_list.get("list")[0].get("deviceName") == "Pilot Pro S"
        assert raw_device_list.get("list")[0].get("sn") == "**REDACTED**"
        assert raw_device_list.get("list")[0].get("productId") == "**REDACTED**"
