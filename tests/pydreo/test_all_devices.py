"""
This tests all requests made by the pydreo library with pytest.

All tests inherit from the TestBase class which contains the fixtures
and methods needed to run the tests.
"""
# import utils
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from  .imports import PyDreo
    from . import call_json
    from .testbase import TestBase
else:
    from imports import * # pylint: disable=W0401,W0614
    import call_json
    from testbase import TestBase


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestGeneralAPI(TestBase):
    """General API testing class for login() and get_devices()."""

    def test_login(self):
        """Test login() method request and API response."""
        print("Test Login")
        self.manager.enabled = False
        assert self.manager.login()

    def test_load_devices(self):
        """Test get_devices() method request and API response."""
        print("Test Device List")

        self.get_devices_file_name = "get_devices_HTF008S.json"
        self.manager.load_devices()
        assert len(self.manager.fans) == 1
        assert self.manager.fans[0].speed_range == (1, 5)
        assert self.manager.fans[0].preset_modes == ['normal', 'natural', 'sleep', 'auto']