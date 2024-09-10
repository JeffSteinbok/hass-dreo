"""Tests for Dreo Ceiling Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestPyDreoHumidifier(TestBase):
    """Test PyDreoFan class."""
  
    def test_HHM001S(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier : PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.modes == ['manual', 'auto', 'sleep']
        assert humidifier.is_feature_supported('is_on') is True
