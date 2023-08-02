"""
Fans & Air Circulators Device API Responses

FANS variable is a list of device types

DETAILS_RESPONSES variable is a dictionary of responses from the API
for get_details() methods.  The keys are the device types and the
values are the responses.  The responses are tuples of (response, status)

METHOD_RESPONSES variable is a defaultdict of responses from the API. This is
the FunctionResponse variable from the utils module in the tests dir.
The default response is a tuple with the value ({"code": 0, "msg": "success"}, 200).

The values of METHOD_RESPONSES can be a function that takes a single argument or
a static value. The value is checked if callable at runtime and if so, it is called
with the provided argument. If not callable, the value is returned as is.

METHOD_RESPONSES = {
    'DEV_TYPE': defaultdict(
        lambda: ({"code": 0, "msg": "success"}, 200))
    )
}

# For a function to handle the response
def status_response(request_body=None):
    # do work with request_body
    return request_body, 200

METHOD_RESPONSES['DEV_TYPE']['set_status'] = status_response

# To change the default value for a device type

METHOD_RESPONSES['DEVTYPE'].default_factory = lambda: ({"code": 0, "msg": "success"}, 200)
"""
from copy import deepcopy
from utils import Defaults, FunctionResponses

FANS = ['Core200S', 'Core300S', 'Core400S', 'Core600S', 'LV-PUR131S', 'LV600S',
        'Classic300S', 'Classic200S', 'Dual200S', 'LV600S']


def INNER_RESULT(inner: dict) -> dict:
    return {
        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "request success",
        "module": None,
        "stacktrace": None,
        "result": {
            "traceId": Defaults.trace_id,
            "code": 0,
            "result": inner
        }
    }


class FanDefaults:
    fan_level = 1
    filter_life = 80
    humidity = 50
    mist_level = 3
    warm_mist_level = 2
    air_quality = 3
    air_quality_value = 4


class FanDetails:
    details_air = (
        {
            'code': 0,
            'msg': None,
            'deviceStatus': 'on',
            'connectionStatus': 'online',
            'activeTime': Defaults.active_time,
            'deviceImg': None,
            'deviceName': 'LV-PUR131S-NAME',
            'filterLife': {
                'change': False,
                'useHour': None,
                'percent': FanDefaults.filter_life,
            },
            'airQuality': 'excellent',
            'screenStatus': 'on',
            'mode': 'manual',
            'level': FanDefaults.fan_level,
            'schedule': None,
            'timer': None,
            'scheduleCount': 0,
        },
        200,
    )

    details_core = ({
        "traceId": Defaults.trace_id,
        "code": 0,
        "msg": "request success",
        "result": {
            "traceId": Defaults.trace_id,
            "code": 0,
            "result": {
                "enabled": True,
                "filter_life": FanDefaults.filter_life,
                "mode": "manual",
                "level": FanDefaults.fan_level,
                "air_quality": FanDefaults.air_quality,
                "air_quality_value": FanDefaults.air_quality_value,
                "display": True,
                "child_lock": True,
                "configuration": {
                    "display": True,
                    "display_forever": True,
                    "auto_preference": {
                        "type": "default",
                        "room_size": 0
                    }
                },
                "extension": {
                    "schedule_count": 0,
                    "timer_remain": 0
                },
                "device_error_code": 0
            }
        }
    }, 200)

DETAILS_RESPONSES = {
    'LV-PUR131S': FanDetails.details_air,
}

FunctionResponses.default_factory = lambda: ({
    "traceId": Defaults.trace_id,
    "code": 0,
    "msg": "request success",
    "result": {
        "traceId": Defaults.trace_id,
        "code": 0
    }
}, 200)

METHOD_RESPONSES = {k: deepcopy(FunctionResponses) for k in FANS}

