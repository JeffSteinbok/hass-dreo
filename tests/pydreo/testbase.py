"""Base class for all tests. Contains a mock for call_dreo_api() function and instantiated Dreo object."""
import logging
from typing import Optional, TYPE_CHECKING
from unittest.mock import patch
import pytest

if TYPE_CHECKING:
    from  .imports import * # pylint: disable=W0401,W0614
    from . import defaults
    from . import call_json
else:
    from imports import * # pylint: disable=W0401,W0614
    import defaults
    import call_json

logger = logging.getLogger(__name__)


Defaults = defaults.Defaults

class TestBase:
    """Base class for all tests.

    Contains instantiated PyDreo object and mocked
    API call for call_api() function.

    Attributes
    ----------
    self.mock_api : Mock
        Mock for call_api() function
    self.manager : Dreo
        Instantiated Dreo object that is logged in
    self.caplog : LogCaptureFixture
        Pytest fixture for capturing logs
    """
    _getDevicesFileName = None
    

    @property
    def getDevicesFileName(self):
        return self._getDevicesFileName

    @getDevicesFileName.setter
    def getDevicesFileName(self, value: str):
        self._getDevicesFileName = value

    @pytest.fixture(autouse=True, scope='function')
    def setup(self, caplog):
        """Fixture to instantiate Dreo object, start logging and start Mock.

        Attributes
        ----------
        self.mock_api : Mock
        self.manager : Dreo
        self.caplog : LogCaptureFixture

        Yields
        ------
        Class instance with mocked call_api() function and Dreo object
        """
        self.mock_api_call = patch('pydreo.PyDreo.call_dreo_api')
        self.caplog = caplog
        self.mock_api = self.mock_api_call.start()
        self.mock_api.side_effect = self.call_dreo_api
        self.mock_api.create_autospect()
        self.mock_api.return_value.ok = True
        self.manager = PyDreo('EMAIL', 'PASSWORD', redact=True) # pylint: disable=E0601
        self.manager.enabled = True
        self.manager.token = Defaults.token
        self.manager.account_id = Defaults.account_id
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()


    def call_dreo_api(self,
        api: str,
        json_object: Optional[dict] = None):
        """Call Dreo REST API"""
        print(f'API call: {api} {json_object}')
        logger.debug(f'API call: {api} {json_object}')

        if api == "login":
            return (
                {
                    'traceId': Defaults.trace_id,
                    'msg': '',
                    'data': {
                        'region': 'NA',
                        'access_token': Defaults.token,
                    },
                    'code': 0,
                },
                200)
        if api == "devicelist":
            return (call_json.get_response_from_file(self.getDevicesFileName), 200)
        if api == "devicestate":
            logger.debug("API call: %s %s", api, json_object)
            return (call_json.get_response_from_file(f"get_device_state_{json_object['deviceSn']}.json"), 200)