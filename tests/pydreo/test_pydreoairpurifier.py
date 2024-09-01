"""Tests for Dreo Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from . import call_json
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LOGIN_RESPONSE = call_json.LOGIN_RET_BODY


class TestPyDreoAirPurifier(TestBase):
    """Test TestPyDreoAirPurifier class."""

    def test_HAP003S(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HAP003S.json"
        self.manager.load_devices()
        assert len(self.manager.air_purifiers) == 1
        air_purifier = self.manager.air_purifiers[0]
        assert air_purifier.speed_range == (1, 18)
        assert air_purifier.preset_modes == ['auto', 'manual', 'sleep', 'turbo']
