"""Tests for Dreo Fans"""
# pylint: disable=used-before-assignment
import logging
from  .imports import * # pylint: disable=W0401,W0614
from .testbase import TestBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestPyDreoAirPurifier(TestBase):
    """Test TestPyDreoAirPurifier class."""

    def test_HAP002S(self):  # pylint: disable=invalid-name
        """Test DR-HAP002S Air Purifier (Macro Pro S)."""

        self.get_devices_file_name = "get_devices_HAP002S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP002S"
        assert air_purifier.series_name == "Macro Pro S"
        assert air_purifier.speed_range == (1, 18)
        assert air_purifier.preset_modes == ['manual']

    def test_HAP003S(self):  # pylint: disable=invalid-name
        """Test DR-HAP003S Air Purifier (Macro Max S)."""

        self.get_devices_file_name = "get_devices_HAP003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP003S"
        assert air_purifier.series_name == "Macro Max S"
        assert air_purifier.speed_range == (1, 18)
        assert air_purifier.preset_modes == ['auto', 'manual', 'sleep', 'turbo']

    def test_HAP005S(self):  # pylint: disable=invalid-name
        """Test DR-HAP005S Air Purifier (Macro AP505S)."""

        self.get_devices_file_name = "get_devices_HAP005S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP005S"
        assert air_purifier.series_name == "Macro AP505S"
        assert air_purifier.speed_range == (1, 4)
        assert air_purifier.preset_modes == ['manual']
