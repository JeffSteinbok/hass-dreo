"""Tests for Dreo Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import diagnostics

import pytest
from  .imports import * # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestDiagnostics(IntegrationTestBase):
    """Test Diagnostics functionality{"""

    def test_diagnostics_simple(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""

        self.get_devices_file_name = "get_devices_multiple_1.json"
        self.pydreo_manager.load_devices()
        diag = diagnostics._get_diagnostics(self.pydreo_manager) # pylint: disable=protected-access
        dreo = diag.get("dreo")
        assert(dreo.get("device_count") == 2)
        raw_device_list = dreo.get("raw_devicelist")
        assert len(raw_device_list) == 2
        assert raw_device_list[0].get("deviceName") == "Main Bedroom Fan"
        assert raw_device_list[0].get("deviceSn") == "**REDACTED**"

