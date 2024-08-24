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
from typing import TYPE_CHECKING
from collections import defaultdict
import yaml

if TYPE_CHECKING:
    from . import defaults
    from .imports import * # pylint: disable=W0401,W0614
else:
    import defaults
    from imports import * # pylint: disable=W0401,W0614


API_DEFAULTS = defaults.API_DEFAULTS

logger = logging.getLogger(__name__)

FunctionResponses: defaultdict = defaultdict(lambda: ({"code": 0, "msg": None}, 200))

CALL_API_ARGS = ['url', 'method', 'data', 'headers']

ID_KEYS = ['CID', 'UUID', 'MACID']

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
