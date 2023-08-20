"""
This tests all requests made by the pydreo library with pytest.

All tests inherit from the TestBase class which contains the fixtures
and methods needed to run the tests.

The `helpers.call_api` method is patched to return a mock response.
The method, endpoint, headers and json arguments are recorded
in YAML files in the api directory, catagorized in folders by
module and files by the class name.

The default is to record requests that do not exist and compare requests
that already exist. If the API changes, set the overwrite argument to True
in order to overwrite the existing YAML file with the new request.
"""
# import utils
import logging

import call_json
from imports import * # pylint: disable=W0401,W0614
from utils import assert_test, parse_args
from testbase import TestBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LOGIN_RESPONSE = call_json.LOGIN_RET_BODY


def test_device_tests():
    """Test to ensure all devices have are defined for testing.

    All devices should have an entry in the DETAILS_RESPONSES dict
    with response for get_details() method. This test ensures that
    all devices have been configured for testing. The details response
    should be located in `{device_type}Details` class of the respective
    call_json_{device_type} module and the DETAILS_RESPONSE module variable.
    The class variable with the details response does not matter, the dictionary
    key of DETAILS_RESPONSES should match the device type.

    Examples
    ---------
    class FanDetails:
        "Core200SResponse": {'speed': 1, 'device_status': 'on'}

    DETAILS_RESPONSES = {
        'Core200S': FanDetails.Core200SResponse
    }

    Asserts
    -------
    Number of devices for each type has a response defined in the
        respective `call_json` module.

    See Also
    --------
    src/tests/README.md - README located in the tests directory
    """
    # assert call_json_fans.FANS_NUM == len(call_json_fans.DETAILS_RESPONSES)

class TestGeneralAPI(TestBase):
    """General API testing class for login() and get_devices()."""

    def test_login(self):
        """Test login() method request and API response."""
        print("Test Login")
        self.write_api = True
        self.overwrite = True
        #self.mock_api.return_value = LOGIN_RESPONSE
        self.manager.enabled = False
        assert self.manager.login()
        all_kwargs = parse_args(self.mock_api)
        assert assert_test(self.manager.login, all_kwargs, None,
                           self.write_api, self.overwrite)

    def test_load_devices(self):
        """Test get_devices() method request and API response."""
        print("Test Device List")
        
        self.write_api = True
        self.overwrite = True

        #self.mock_api.return_value = call_json.LOAD_DEVICES_RESPONSE, 200 #call_json.DeviceList.device_list_response()
        self.manager.load_devices()
        all_kwargs = parse_args(self.mock_api)
        assert assert_test(self.manager.load_devices, all_kwargs, None,
                           self.write_api, self.overwrite)
        assert len(self.manager.fans) == 1