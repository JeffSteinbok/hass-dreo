"""Helper functions for Dreo API."""

import hashlib
import logging
import time
import json
import colorsys
from dataclasses import dataclass, field, InitVar
from typing import NamedTuple, Optional, Union
import re
import requests

from .constant import LOGGER_NAME
_LOGGER = logging.getLogger(LOGGER_NAME)

API_TIMEOUT = 30

NUMERIC = Optional[Union[int, float, str]]


class Helpers:
    """Dreo Helper Functions."""

    @staticmethod
    def req_headers(manager) -> dict:
        """Build header for api requests."""
        headers = {
            'ua': 'dreo/2.0.7 (sdk_gphone64_x86_64;android 13;Scale/2.625)',
            'lang': 'en',
            'content-type': 'application/json; charset=UTF-8',
            'accept-encoding': 'gzip',
            'user-agent': 'okhttp/4.9.1',
        }
        if (manager.token != None):
            headers["authorization"] = f"Bearer {manager.token}"
        return headers

    @staticmethod
    def req_body_base(manager) -> dict:
        """Return universal keys for body of api requests."""
        return {'acceptLanguage': 'en'}

    @classmethod
    def req_body(cls, manager, type_) -> dict:
        """Builder for body of api requests."""
        body = {}

        # These magic headers are needed to make the Dreo API do what we want it to do
        if type_ == "login":
            body = {**cls.req_body_base(manager)}
            body["client_id"] =  "7de37c362ee54dcf9c4561812309347a"
            body["client_secret"] = "32dfa0764f25451d99f94e1693498791"
            body['email'] = manager.username
            body['encrypt'] =  "ciphertext"
            body['grant_type'] =  "email-password"
            body['himei'] =  "faede31549d649f58864093158787ec9"
            body['password'] = cls.hash_password(manager.password)
            body['scope'] =  "all"
            print("HI THERE")
            print(body)

        elif type_ == 'devicelist':
            body = {
                **cls.req_body_base(manager)
            }
            body['method'] = 'devices'
            body['pageNo'] = '1'
            body['pageSize'] = '100'
 

        return body

    @staticmethod
    def calculate_hex(hex_string) -> float:
        """Credit for conversion to itsnotlupus/vesync_wsproxy."""
        hex_conv = hex_string.split(':')
        converted_hex = (int(hex_conv[0], 16) + int(hex_conv[1], 16)) / 8192

        return converted_hex

    @staticmethod
    def hash_password(string) -> str:
        """Encode password."""
        return hashlib.md5(string.encode()).hexdigest()

    shouldredact = False

    @classmethod
    def redactor(cls, stringvalue: str) -> str:
        """Redact sensitive strings from debug output."""
        if cls.shouldredact:
            stringvalue = re.sub(r''.join((
                                          '(?i)',
                                          '((?<=token": ")|',
                                          '(?<=password": ")|',
                                          '(?<=email": ")|',
                                          '(?<=tk": ")|',
                                          '(?<=accountId": ")|',
                                          '(?<=authKey": ")|',
                                          '(?<=uuid": ")|',
                                          '(?<=cid": "))',
                                          '[^"]+')
                                          ),
                                 '##_REDACTED_##', stringvalue)
        return stringvalue

    @staticmethod
    def call_api(url: str, api: str, method: str, json_object:  Optional[dict] = None,
                 headers: Optional[dict] = None) -> tuple:
        """Make API calls by passing endpoint, header and body."""
        response = None
        status_code = None
        try:
            _LOGGER.debug("=======call_api=============================")
            _LOGGER.debug("[%s] calling '%s' api", method, api)
            _LOGGER.debug("API call URL: \n  %s%s", url, api)
            _LOGGER.debug("API call headers: \n  %s",
                         Helpers.redactor(json.dumps(headers)))
            _LOGGER.debug("API call json: \n  %s",
                         Helpers.redactor(json.dumps(json_object)))
            if method.lower() == 'get':
                r = requests.get(
                    url + api, headers=headers, params={**json_object, "timestamp": str(int(time.time() * 1000))},
                    timeout=API_TIMEOUT
                )
            elif method.lower() == 'post':
                r = requests.post(
                    url + api, json=json_object, headers=headers,  params={"timestamp": str(int(time.time() * 1000))},
                    timeout=API_TIMEOUT
                )
            elif method.lower() == 'put':
                r = requests.put(
                    url + api, json=json_object, headers=headers,
                    timeout=API_TIMEOUT
                )
        except requests.exceptions.RequestException as e:
            _LOGGER.debug(e)
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.debug(e)
        else:
            if r.status_code == 200:
                status_code = 200
                if r.content:
                    response = r.json()
                    _LOGGER.debug("API response: \n\n  %s \n ",
                                 Helpers.redactor(json.dumps(response)))
            else:
                _LOGGER.debug('Unable to fetch %s%s', url, api)
        return response, status_code

    @staticmethod
    def code_check(r: dict) -> bool:
        """Test if code == 0 for successful API call."""
        if r is None:
            _LOGGER.error('No response from API')
            return False
        if isinstance(r, dict) and r.get('code') == 0:
            return True
        return False

    @staticmethod
    def build_details_dict(r: dict) -> dict:
        """Build details dictionary from API response."""
        return {
            'active_time': r.get('activeTime', 0),
            'energy': r.get('energy', 0),
            'night_light_status': r.get('nightLightStatus', None),
            'night_light_brightness': r.get('nightLightBrightness', None),
            'night_light_automode': r.get('nightLightAutomode', None),
            'power': r.get('power', 0),
            'voltage': r.get('voltage', 0),
        }

    @staticmethod
    def build_config_dict(r: dict) -> dict:
        """Build configuration dictionary from API response."""
        if r.get('threshold') is not None:
            threshold = r.get('threshold')
        else:
            threshold = r.get('threshHold')
        return {
            'current_firmware_version': r.get('currentFirmVersion'),
            'latest_firmware_version': r.get('latestFirmVersion'),
            'maxPower': r.get('maxPower'),
            'threshold': threshold,
            'power_protection': r.get('powerProtectionStatus'),
            'energy_saving_status': r.get('energySavingStatus'),
        }

    @staticmethod
    def named_tuple_to_str(named_tuple: NamedTuple) -> str:
        """Convert named tuple to string."""
        tuple_str = ''
        for key, val in named_tuple._asdict().items():
            tuple_str += f'{key}: {val}, '
        return tuple_str

