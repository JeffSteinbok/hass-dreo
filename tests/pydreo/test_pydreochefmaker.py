"""Tests for Dreo Chef Makers"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch, call
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from . import call_json
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LOGIN_RESPONSE = call_json.LOGIN_RET_BODY

class TestPyDreoChefMaker(TestBase):
    """Test PyDreoChefMaker class."""
    def test_KCM001S(self):
        """Load ChefMaker and test sending commands."""

        self.get_devices_file_name = "get_devices_KCM001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        chefMaker = self.pydreo_manager.devices[0]


