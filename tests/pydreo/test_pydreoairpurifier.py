"""Tests for Dreo Fans"""
# pylint: disable=used-before-assignment
import logging
from  .imports import * # pylint: disable=W0401,W0614
from . import call_json
from .testbase import TestBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestPyDreoAirPurifier(TestBase):
    """Test TestPyDreoAirPurifier class."""

    def test_HAP003S(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HAP003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.speed_range == (1, 18)
        assert air_purifier.preset_modes == ['auto', 'manual', 'sleep', 'turbo']
