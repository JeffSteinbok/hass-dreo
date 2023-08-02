"""Common base class for tests and Default values.

Routine Listings
----------------

FunctionResponses : defaultdict
    Defaultdict of the standard response tuple for device methods
Defaults: class
    Default values and methods for generating default values
TestBase: class
    Base class for tests to start mock & instantiat VS object
"""
import logging
from pathlib import Path
from typing import Any
import pytest
import yaml
from collections import defaultdict, namedtuple
from unittest.mock import patch
from requests.structures import CaseInsensitiveDict
from imports import * # pylint: disable=W0401,W0614

logger = logging.getLogger(__name__)

FunctionResponses: defaultdict = defaultdict(lambda: ({"code": 0, "msg": None}, 200))

CALL_API_ARGS = ['url', 'method', 'data', 'headers']

ID_KEYS = ['CID', 'UUID', 'MACID']

class Defaults:
    """General defaults for API responses and requests.

    Attributes
    ----------
    token : str
        Default token for API requests
    active_time : str
        Default active time for API responses
    account_id : str
        Default account ID for API responses
    active_time : str
        Default active time for API responses
    color: Color (dataclass)
        Red=50, Green=100, Blue=225, Hue=223, Saturation=77.78, value=88.24
        Default Color dataclass
        contains red, green, blue, hue, saturation and value attributes

    Methods
    --------
    name(dev_type='NA')
        Default device name created from "dev_type-NAME"
    cid(dev_type='NA')
        Default device cid created from "dev_type-CID"
    uuid(dev_type='NA')
        Default device uuid created from "dev_type-UUID"
    macid(dev_type='NA')
        Default device macid created from "dev_type-MACID"
    """

    token = 'sample_tk'
    account_id = 'sample_id'
    trace_id = "TRACE_ID"
    active_time = 1
    brightness = 100
    color_temp = 100
    bool_toggle = True
    str_toggle = 'on'
    bin_toggle = 1

    @staticmethod
    def name(dev_type: str = 'NA'):
        """Name of device with format f"{dev_type}-NAME".

        Parameters
        ----------
        dev_type : str
            Device type use to create default name

        Returns
        -------
        str
            Default name for device f"dev_type-NAME"
        """
        return f'{dev_type}-NAME'

    @staticmethod
    def cid(dev_type='NA'):
        """CID for a device with format f"{dev_type}-CID".

        Parameters
        ----------
        dev_type : str
            Device type use to create default cid

        Returns
        -------
        str
            Default cid for device f"dev_type-CID"
        """
        return f'{dev_type}-CID'

    @staticmethod
    def uuid(dev_type='NA'):
        """UUID for a device with format f"{dev_type}-UUID".

        Parameters
        ----------
        dev_type : str
            Device type use to create default UUID

        Returns
        -------
        str
            Default uuid for device f"{dev_type}-UUID"
        """
        return f'{dev_type}-UUID'

    @staticmethod
    def macid(dev_type='NA'):
        """MACID for a device with format f"{dev_type}-MACID".

        Parameters
        ----------
        dev_type : str
            Device type use to create default macid

        Returns
        -------
        str
            Default macID for device f"{dev_type}-MACID"
        """
        return f'{dev_type}-MACID'


def parse_args(mock_api):
    """Parse arguments from mock API call.

    Arguments
    ----------
    mock_api : mock
        Mock object used to path call_api() method

    Returns
    -------
    dict
        dictionary of all call_api() arguments
    """
    call_args = mock_api.call_args.args
    call_kwargs = mock_api.call_args.kwargs
    all_kwargs = dict(zip(CALL_API_ARGS, call_args))
    all_kwargs.update(call_kwargs)
    return all_kwargs


API_DEFAULTS = CaseInsensitiveDict({
    'accountID': Defaults.account_id,
    'token': Defaults.token,
    "tk": Defaults.token,
    "traceId": "TRACE_ID",
    'verifyEmail': 'EMAIL',
    'nickName': 'NICKNAME',
    'password': 'PASSWORD',
    'username': 'EMAIL',
    'email': 'EMAIL',
    'deviceName': 'NAME'

})


class YAMLWriter:
    """Read and Write API request data to YAML files.

    Arguments
    ---------
    module : str
        name of module that is being tested
    dev_type : str
        device type being tested

    Attributes
    ----------
    self.file_path : Path
        Path to YAML directory, default to API dir in tests folder
    self.file : Path
        Path to YAML file based on device type and module
    self.existings_yaml : dict
        Existing YAML data read to dict object
    self._existing_api : dict, optional
        Existing data dict of a specific API call

    Methods
    -------
    self.existing_api()
        Return existing data dict of a specific API call or None
    self.write_api(api, data, overwrite=False)
        Writes data to YAML file for a specific API call,
        set overwrite=True to overwrite existing data

    """

    def __init__(self, module, dev_type):
        """Init the YAMLWriter class.

        Arguments
        ----------
        module : str
            name of module that is being tested
        dev_type : str
            device type being tested
        """
        self.file_path = self._get_path(module)
        self.file = Path.joinpath(self.file_path, dev_type + '.yaml')
        self.new_file = self._new_file()
        self.existing_yaml = self._get_existing_yaml()
        self._existing_api = None

    @staticmethod
    def _get_path(module) -> Path:
        yaml_dir = Path.joinpath(Path(__file__).parent, 'api', module)
        if not yaml_dir.exists():
            yaml_dir.mkdir(parents=True)
        return yaml_dir

    def _new_file(self) -> bool:
        if not self.file.exists():
            logger.debug(f'Creating new file {self.file}')
            self.file.touch()
            return True
        return False

    def _get_existing_yaml(self) -> Any:
        if self.new_file:
            return None
        with open(self.file, 'rb') as f:
            data = yaml.full_load(f)
        return data

    def existing_api(self, method) -> bool:
        """Check YAML file for existing data for API call.

        Arguments
        ----------
        method : str
            Name of method being tested

        Returns
        -------
        dict or None
            Existing data for API call or None
        """
        if self.existing_yaml is not None:
            current_dict = self.existing_yaml.get(method)
            self._existing_api = current_dict
            if current_dict is not None:
                logger.debug(f'API call {method} already exists in {self.file}')
                return True
        return False

    def write_api(self, method, yaml_dict, overwrite=False):
        """Write API data to YAML file.

        Arguments
        ----------
        method : str
            Name of method being tested
        yaml_dict : dict
            Data to write to YAML file
        overwrite : bool, optional
            Overwrite existing data, default to False
        """
        if self.existing_yaml is not None:
            current_dict = self.existing_yaml.get(method)
            if current_dict is not None and overwrite is False:
                logger.debug(f'API call {method} already exists in {self.file}')
                return
            self.existing_yaml[method] = yaml_dict
        else:
            self.existing_yaml = {method: yaml_dict}
        with open(self.file, 'w', encoding='utf-8') as f:
            yaml.dump(self.existing_yaml, f, encoding='utf-8')


def api_scrub(api_dict, device_type=None):
    """Recursive function to scrub all sensitive data from API call.

    Arguments
    ----------
    api_dict : dict
        API call data to scrub
    device_type : str, optional
        Device type to use for default values

    Returns
    -------
    dict
        Scrubbed API call data
    """
    def id_cleaner(key, value):
        if key.upper() in ID_KEYS:
            return f"{device_type or 'UNKNOWN'}-{key.upper()}"
        if key in API_DEFAULTS:
            return API_DEFAULTS[key]
        return value

    def nested_dict_iter(nested, mapper, last_key=None):
        if isinstance(nested, dict):
            if nested.get('deviceType') is not None:
                nonlocal device_type
                device_type = nested['deviceType']
            out = {}
            for key, value in nested.items():
                out[key] = nested_dict_iter(value, mapper, key)
            return out

        if isinstance(nested, list):
            return [nested_dict_iter(el, mapper, last_key) for el in nested]
        if not last_key:
            return nested
        return mapper(last_key, nested)
    return nested_dict_iter(api_dict, id_cleaner)


class TestBase:
    """Base class for all tests.

    Contains instantiated Dreo object and mocked
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
    overwrite = False
    write_api = False

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
        self.mock_api_call = patch('pydreo.helpers.Helpers.call_api')
        self.caplog = caplog
        self.mock_api = self.mock_api_call.start()
        self.mock_api.create_autospect()
        self.mock_api.return_value.ok = True
        self.manager = PyDreo('EMAIL', 'PASSWORD', redact=True)
        self.manager.enabled = True
        self.manager.token = Defaults.token
        self.manager.account_id = Defaults.account_id
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()


def assert_test(test_func, all_kwargs, dev_type=None,
                 write_api=False, overwrite=False):
    """Test pyDreo API calls against existing API.

    Set `write_api=True` to True to write API call data to YAML file. 
    This will not overwrite existing data unless overwrite is True.
    The overwrite argument is only used when API changes, defaults
    to false for development testing. `overwrite=True` and `write_api=True`
    need to both be set to overwrite existing data.

    Arguments
    ----------
    test_func : method
        Method that is being tested
    all_kwargs : dict
        Dictionary of call_api() arguments
    dev_type : str, optional
        Device type being tested
    write_api : bool, optional
        Write API call data to YAML file, default to False
    overwrite : bool, optional
        Overwrite existing data ONLY USE FOR CHANGING API,
          default to False. Must be set with `write_api=True`

    Returns
    -------
    bool
        True if test passes, False if test fails

    Asserts
    -------
        Asserts that the API call data matches the expected data
    """
    if all_kwargs.get('json_object') is not None:
        all_kwargs['json_object'] = api_scrub(all_kwargs['json_object'], dev_type)
    if all_kwargs.get('headers') is not None:
        all_kwargs['headers'] = api_scrub(all_kwargs['headers'], dev_type)
    mod = test_func.__module__.split(".")[-1]
    if dev_type is None:
        cls_name = test_func.__self__.__class__.__name__
    else:
        cls_name = dev_type
    method_name = test_func.__name__
    writer = YAMLWriter(mod, cls_name)
    if overwrite is True and write_api is True:
        writer.write_api(method_name, all_kwargs, overwrite)
        return True
    if writer.existing_api(method_name) is False:
        logger.debug("No existing, API data for %s %s %s", mod, cls_name, method_name)
        if write_api is True:
            logger.debug("Writing API data for %s %s %s", mod, cls_name, method_name)
            writer.write_api(method_name, all_kwargs, overwrite)
        else:
            logger.debug("Not writing API data for %s %s %s", mod, cls_name, method_name)
    assert writer._existing_api == all_kwargs
    return True
