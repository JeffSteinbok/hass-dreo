"""Helper file for calling JSON APIs from the tests."""
from typing import TYPE_CHECKING
import json

if TYPE_CHECKING:
    from .defaults import Defaults
else:
    from defaults import Defaults

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

GET_DEVICE_RESPONSE = {
    "code": 0,
    "msg": "OK",
    "data": {
        "mixed": {
            "mcu_hardware_model": {
                "state": "SC95F8613B",
                "timestamp": 1686788164
            },
            "wifi_ssid": {
                "state": "steinbok-iot",
                "timestamp": 1686788164
            },
            "windlevel": {
                "state": 2,
                "timestamp": 1687064489
            },
            "wifi_rssi": {
                "state": -37,
                "timestamp": 1686788164
            },
            "poweron": {
                "state": "True",
                "timestamp": 1687057235
            },
            "windtype": {
                "state": 1,
                "timestamp": 1686789795
            },
            "timeron": {
                "state": {
                    "du": 0,
                    "ts": 7
                },
                "timestamp": None
            },
            "voiceon": {
                "state": False,
                "timestamp": 1686788993
            },
            "wrong": {
                "state": 0,
                "timestamp": 1686788164
            },
            "module_firmware_version": {
                "state": "2.3.15",
                "timestamp": 1686788164
            },
            "connected": {
                "state": True,
                "timestamp": 1686788164
            },
            "mcuon": {
                "state": True,
                "timestamp": 1686788164
            },
            "timeroff": {
                "state": {
                    "du": 0,
                    "ts": 7
                },
                "timestamp": None
            },
            "shakehorizon": {
                "state": False,
                "timestamp": 1686811203
            },
            "network_latency": {
                "state": 102,
                "timestamp": 1686788164
            },
            "_ota": {
                "state": 0,
                "timestamp": 1686788164
            },
            "module_hardware_model": {
                "state": "HeFi",
                "timestamp": 1686788164
            },
            "mcu_firmware_version": {
                "state": "1.0.17",
                "timestamp": 1686788164
            },
            "temperature": {
                "state": 71,
                "timestamp": 1687062055
            },
            "module_hardware_mac": {
                "state": "001cc263494b",
                "timestamp": 1686788164
            },
            "ledalwayson": {
                "state": False,
                "timestamp": 1686788164
            }
        },
        "sn": "1582290393341964289-77f2977b24191a4a: 001: 0000000000b",
        "productId": "1582290393341964289",
        "region": "us-east-2"
    }
}
