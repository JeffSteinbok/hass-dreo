"""Helper file for calling JSON APIs from the tests."""
from typing import TYPE_CHECKING
import json

from .defaults import Defaults

# DEFAULT_BODY = Standard body for new device calls
# DEFAULT_HEADER = standard header for most calls
# DEFAULT_HEADER_BYPASS = standard header for most calls api V2
# ENERGY_HISTORY = standard outlet energy history response
#-------------------------------------------------------
# login_call_body(email, pass) = body of login call
# LOGIN_RET_BODY = return of login call
#-------------------------------------------------------
# get_devices_body() = body of call to get device list
# LIST_CONF_AIR = device list entry for air purifier

DEFAULT_HEADER = {
    'accept-language': 'en',
    'accountId': Defaults.account_id,
}

DEFAULT_HEADER_BYPASS = {
    'Content-Type': 'application/json; charset=UTF-8',
    'User-Agent': 'okhttp/3.12.1'
}

DEFAULT_BODY = {
    'acceptLanguage': 'en',
    'accountID': Defaults.account_id,
    'token': Defaults.token,
    'traceId': Defaults.trace_id,
}

LOGIN_RET_BODY = (
    {
        'traceId': Defaults.trace_id,
        'msg': '',
        'data': {
            'region': 'NA',
            'access_token': Defaults.token,
        },
        'code': 0,
    },
    200,
)

def get_response_from_file(filename: str) -> json:
    with open("tests/pydreo/api_responses/" + filename, 'r') as file:
        return json.load(file)

def login_call_body(email, password):
    json_object = {
        'acceptLanguage': 'en',
        'devToken': '',
        'email': email,
        'method': 'login',
        'password': password,
        'traceId': Defaults.trace_id,
        'userType': '1',
    }
    return json_object
