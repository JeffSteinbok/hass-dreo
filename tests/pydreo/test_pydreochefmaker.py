"""Tests for Dreo Chef Makers"""

# pylint: disable=used-before-assignment
import logging
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestPyDreoChefMaker(TestBase):
    """Test PyDreoChefMaker class."""

    def test_KCM001S(self):  # pylint: disable=invalid-name
        """Load ChefMaker and test sending commands."""

        self.get_devices_file_name = "get_devices_KCM001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        chef_maker = self.pydreo_manager.devices[0]
        assert chef_maker.is_feature_supported("is_on") is True
