"""Base class for all tests. Contains a mock for call_dreo_api() function and instantiated Dreo object."""
# pylint: disable=W0201
import logging
import os
from typing import Optional
from unittest.mock import patch
from homeassistant.helpers.entity import Entity
import pytest
from  .imports import * # pylint: disable=W0401,W0614
from . import defaults
from . import call_json

logger = logging.getLogger(__name__)

PATCH_BASE_PATH = 'custom_components.dreo.pydreo'
PATCH_SEND_COMMAND = f'{PATCH_BASE_PATH}.PyDreo.send_command'
PATCH_CALL_DREO_API = f'{PATCH_BASE_PATH}.PyDreo.call_dreo_api'

API_REPONSE_BASE_PATH = "tests/dreo/integrationtests/api_responses/"

Defaults = defaults.Defaults

class IntegrationTestBase:
    """Base class for all tests.

    Contains instantiated PyDreo object and mocked
    API call for call_api() function."""

    @property
    def get_devices_file_name(self):
        """Get the file name for the devices file."""
        return self._get_devices_file_name

    @get_devices_file_name.setter
    def get_devices_file_name(self, value: str):
        """Set the file name for the devices file."""
        self._get_devices_file_name = value

    @pytest.fixture(autouse=True, scope='function')
    def setup(self, caplog):
        """Fixture to instantiate Dreo object, start logging and start Mock.

        Attributes
        ----------
        self.mock_api : Mock
        self.pydreo_manager : PyDreo
        self.caplog : LogCaptureFixture

        Yields
        ------
        Class instance with mocked call_api() function and Dreo object
        """
        self._get_devices_file_name = None
        self.mock_api_call = patch(PATCH_CALL_DREO_API)
        self.caplog = caplog
        self.mock_api = self.mock_api_call.start()
        self.mock_api.side_effect = self.call_dreo_api
        self.mock_api.create_autospect()
        self.mock_api.return_value.ok = True
        self.pydreo_manager = PyDreo('EMAIL', 'PASSWORD', redact=True) # pylint: disable=E0601
        self.pydreo_manager.enabled = True
        self.pydreo_manager.token = Defaults.token
        self.pydreo_manager.account_id = Defaults.account_id
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()


    def call_dreo_api(self,
        api: str,
        json_object: Optional[dict] = None):
        """Call Dreo REST API"""
        print(f'API call: {api} {json_object}')
        logger.debug('API call: %s %s', api, json_object)

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
            return (call_json.get_response_from_file(self.get_devices_file_name), 200)
        if api == "devicestate":
            logger.debug("API call: %s %s", api, json_object)
            file_name = f"get_device_state_{json_object['deviceSn']}.json"
            if (os.path.exists(API_REPONSE_BASE_PATH + file_name)):
                logger.debug("Device state loaded from file: %s", API_REPONSE_BASE_PATH + file_name)
                return (call_json.get_response_from_file(file_name), 200)
            else:
                logger.debug("No file found: %s", API_REPONSE_BASE_PATH + file_name)
                return {}, 200
        if api == "setting_get":
            file_name = f"get_device_setting_{json_object['deviceSn']}_{json_object['dataKey']}.json"
            if (os.path.exists(API_REPONSE_BASE_PATH + file_name)):
                logger.debug("Device setting loaded from file: %s", API_REPONSE_BASE_PATH + file_name)
                return (call_json.get_response_from_file(file_name), 200)
            else:
                logger.debug("No file found: %s", API_REPONSE_BASE_PATH + file_name)
                return {}, 200

    def verify_expected_entities(self, ha_entities: list[Entity], expected_keys: list[str]) -> None:
        """Verify the expected entities are present."""
        found_entity_keys : list[str] = []
        for ha_entity in ha_entities:
            found_entity_keys.append(ha_entity.entity_description.key)
        found_entity_keys.sort()
        expected_keys.sort()
        logger.debug("Found entity keys: %s", found_entity_keys)
        logger.debug("Expected entity keys: %s", expected_keys)
        assert found_entity_keys == expected_keys, f"Found entity keys {found_entity_keys} do not match expected {expected_keys}"

    def get_entity_by_key(self, ha_entities: list, key: str) -> None:
        """Verify the expected entities are present."""
        for ha_entity in ha_entities:
            if (ha_entity.entity_description.key == key):
                return ha_entity
        return None


