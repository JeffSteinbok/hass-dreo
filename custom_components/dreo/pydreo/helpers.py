"""Helper functions for PyDreo library."""

import hashlib
import logging
import time
import json
from typing import Optional, Union
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
            "ua": "dreo/2.8.2",
            "lang": "en",
            "content-type": "application/json; charset=UTF-8",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/4.9.1",
        }
        if manager.token is not None:
            headers["authorization"] = f"Bearer {manager.token}"
        return headers

    @staticmethod
    def req_body_base() -> dict:
        """Return universal keys for body of api requests."""
        return {"acceptLanguage": "en"}

    @classmethod
    def req_body(cls, manager, type_) -> dict:
        """Builder for body of api requests."""
        body = {}

        # These magic headers are needed to make the Dreo API do what we want it to do
        if type_ == "login":
            body = {**cls.req_body_base()}
            body["client_id"] = "7de37c362ee54dcf9c4561812309347a"
            body["client_secret"] = "32dfa0764f25451d99f94e1693498791"
            body["email"] = manager.username
            body["encrypt"] = "ciphertext"
            body["grant_type"] = "email-password"
            body["himei"] = "faede31549d649f58864093158787ec9"
            body["password"] = cls.hash_password(manager.password)
            body["scope"] = "all"
            print(body)

        elif type_ == "devicelist":
            body = {**cls.req_body_base()}
            body["method"] = "devices"
            body["pageNo"] = "1"
            body["pageSize"] = "100"

        return body

    @staticmethod
    def calculate_hex(hex_string) -> float:
        """Credit for conversion to itsnotlupus/vesync_wsproxy."""
        hex_conv = hex_string.split(":")
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
            stringvalue = re.sub(
                r"".join(
                    (
                        "(?i)",
                        '((?<=token": ")|',
                        '(?<=password": ")|',
                        '(?<=email": ")|',
                        '(?<=tk": ")|',
                        '(?<=accountId": ")|',
                        '(?<=authKey": ")|',
                        '(?<=uuid": ")|',
                        '(?<=cid": ")|',
                        '(?<=authorization": "))',
                        '[^"]+',
                    )
                ),
                "##_REDACTED_##",
                stringvalue,
            )
        return stringvalue

    @staticmethod
    def call_api(
        url: str,
        api: str,
        method: str,
        json_object: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> tuple:
        """Make API calls by passing endpoint, header and body."""
        response = None
        status_code = None
        try:
            _LOGGER.debug("=======call_api=============================")
            _LOGGER.debug("[%s] calling '%s' api", method, api)
            _LOGGER.debug("API call URL: \n  %s%s", url, api)
            _LOGGER.debug(
                "API call headers: \n  %s", Helpers.redactor(
                    json.dumps(headers))
            )
            _LOGGER.debug(
                "API call json: \n  %s", Helpers.redactor(
                    json.dumps(json_object))
            )
            if method.lower() == "get":
                r = requests.get(
                    url + api,
                    headers=headers,
                    params={**json_object, "timestamp": Helpers.api_timestamp()},
                    timeout=API_TIMEOUT,
                )
            elif method.lower() == "post":
                r = requests.post(
                    url + api,
                    json=json_object,
                    headers=headers,
                    params={"timestamp": Helpers.api_timestamp()},
                    timeout=API_TIMEOUT,
                )
            elif method.lower() == "put":
                r = requests.put(
                    url + api, json=json_object, headers=headers, timeout=API_TIMEOUT
                )
        except requests.exceptions.RequestException as exception:
            _LOGGER.debug(exception)
        else:
            if r.status_code == 200: # pylint: disable=E0606
                status_code = 200
                if r.content:
                    response = r.json()
                    _LOGGER.debug(
                        "API response: \n\n  %s \n ",
                        Helpers.redactor(json.dumps(response)),
                    )
            else:
                _LOGGER.debug("Unable to fetch %s%s", url, api)
        return response, status_code

    @staticmethod
    def code_check(reponse_dict: dict) -> bool:
        """Test if code == 0 for successful API call."""
        if reponse_dict is None:
            _LOGGER.error("No response from API")
            return False
        if isinstance(reponse_dict, dict) and reponse_dict.get("code") == 0:
            return True
        return False

    @staticmethod
    def api_timestamp() -> str:
        """Timestamp in correct format for API calls"""
        return str(int(time.time() * 1000))

    @staticmethod
    def name_from_value(name_value_list : list[tuple], value) -> str:
        """Return name from list of tuples."""
        for name, val in name_value_list:
            if val == value:
                return name
        return None

    @staticmethod
    def value_from_name(name_value_list : list[tuple], name) -> any:
        """Return value from list of tuples."""
        for n, val in name_value_list:
            if n == name:
                return val
        return None

    @staticmethod
    def get_name_list(name_value_list : list[tuple]) -> list[str]:
        """Return list of names from list of tuples."""
        return [name for name, _ in name_value_list]
