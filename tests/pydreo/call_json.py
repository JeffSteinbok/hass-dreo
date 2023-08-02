import copy
import call_json_fans
from utils import Defaults

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


def BYPASS_V1_BODY(cid: str, config_module: str, json_cmd: dict):
    return {
        "traceId": Defaults.trace_id,
        "method": "bypass",
        "token": Defaults.token,
        "cid": cid,
        "configModule": config_module,
        "jsonCmd": json_cmd
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


class DeviceList:
    list_response_base = {
        'code': 0,
        'msg': 'Success',
        'result': {
            'pageNo': 1,
            'pageSize': 100,
            'total': 0,
            'list': [],
        }
    }
    device_list_base = {
        'extension': None,
        'isOwner': True,
        'authKey': None,
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'connectionType': 'wifi',
        'mode': None,
        'speed': None,
        'deviceProps': None,
        'configModule': 'ConfigModule',
    }

    fans = dict.fromkeys(call_json_fans.FANS, "wifi-air")

    @classmethod
    def device_list_item(cls, model, sub_device_no=0):
        model_types = {**cls.fans}

        device_dict = cls.device_list_base
        model_dict = device_dict.copy()
        model_dict['deviceType'] = model
        model_dict['deviceName'] = Defaults.name(model)
        model_dict['type'] = model_types.get(model)
        model_dict['cid'] = Defaults.cid(model)
        model_dict['uuid'] = Defaults.uuid(model)
        model_dict['macID'] = Defaults.macid(model)
        if model == 'ESO15-TB':
            model_dict['subDeviceNo'] = 1
        return model_dict

    @classmethod
    def device_list_response(cls, device_types=None, _types=None):
        """Class method that returns the api get_devices response

        Args:
            _types (list, str, optional): Can be one or list of types of devices.
                Defaults to None. can be bulb, fans, switches, outlets in list or string
            device_types (list, str optional): List or string of device_type(s)
                to return. Defaults to None.

        """

        response_base = copy.deepcopy(cls.list_response_base)
        if _types is not None:
            if isinstance(_types, list):
                full_model_list = {}
                for _type in _types:
                    device_types = full_model_list.update(cls.__dict__[_type])
            else:
                full_model_list = cls.__dict__[_types]
        else:
            full_model_list = {**cls.fans}
        if device_types is not None:
            if isinstance(device_types, list):
                full_model_list = {k: v for k, v in full_model_list.items()
                                   if k in device_types}
            else:
                full_model_list = {k: v for k, v in full_model_list.items()
                                   if k == device_types}
        for model in full_model_list:
            response_base['result']['list'].append(cls.device_list_item(model))
            response_base['result']['total'] += 1
        return response_base, 200
  
    LIST_CONF_AIR = {
        'deviceName': 'Name Air Purifier',
        'cid': 'AIRPUR-CID',
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'connectionType': 'wifi',
        'deviceType': 'LV-PUR131S',
        'type': 'wifi-air',
        'uuid': 'UUID',
        'configModule': 'AirPurifier131',
        'macID': None,
        'mode': 'manual',
        'speed': 'low',
        'extension': None,
        'currentFirmVersion': None,
    }

    LIST_CONF_LV131S = {
        'deviceName': 'LV131S NAME',
        'cid': 'CID-LV131S',
        'deviceStatus': 'on',
        'connectionStatus': 'online',
        'connectionType': 'wifi',
        'deviceType': 'LV-PUR131S',
        'type': 'wifi-air',
        'uuid': 'UUID-LV131S',
        'configModule': 'AirPurifier131',
        'macID': None,
        'mode': 'auto',
        'speed': None,
        'extension': None,
        'currentFirmVersion': None,
        'subDeviceNo': None,
        'subDeviceType': None
    }


    API_URL = '/cloud/v1/deviceManaged/devices'

    METHOD = 'POST'

    FULL_DEV_LIST = [
        LIST_CONF_AIR,
        LIST_CONF_LV131S,
    ]

    @classmethod
    def DEVICE_LIST_RETURN(cls, dev_conf: dict) -> tuple:
        """Test the fan."""
        return (
            {
                'code': 0,
                'result':
                    {
                        'list': [dev_conf]
                    }
            },
            200
        )

    FAN_TEST = ({'code': 0, 'result': {'list': [LIST_CONF_LV131S]}}, 200)

    DEVLIST_ALL = ({'code': 0, 'result': {'list': FULL_DEV_LIST}}, 200)

class DeviceDetails:
    """Responses for get_details() method for all devices.

    class attributes:
    outlets : dict
        Dictionary of outlet responses for each device type.
    switches : dict
        Dictionary of switch responses for each device type.
    bulbs : dict
        Dictionary of bulb responses for each device type.
    fans : dict
        Dictionary of humidifier & air pur responses for each device type.
    all_devices : dict
        Dictionary of all device responses for each device type.

    Example
    -------
    outlets = {'ESW01-EU': {'switches': [{'outlet': 0, 'switch': 'on'}]}}
    """

    fans = call_json_fans.DETAILS_RESPONSES
    all_devices = {
        'fans': fans,
        }


def get_devices_body():
    """Build device body dictionary."""
    body = DEFAULT_BODY
    body['method'] = 'devices'
    return body, 200


def get_details_body():
    body = DEFAULT_BODY
    body['method'] = 'deviceDetail'
    return body, 200


DETAILS_BADCODE = (
    {
        'code': 1,
        'deviceImg': '',
        'activeTime': 1,
        'energy': 1,
        'power': '1',
        'voltage': '1',
    },
    200,
)

STATUS_BODY = {
    'accountID': Defaults.account_id,
    'token': Defaults.token,
    'uuid': 'UUID',
}


def off_body():
    body = STATUS_BODY
    body['status'] = 'off'
    return body, 200


def on_body():
    body = STATUS_BODY
    body['status'] = 'on'
    return body, 200


LOAD_DEVICES_RESPONSE =   {
    "code": 0,
    "msg": "OK",
    "data": {
      "currentPage": 1,
      "pageSize": 10,
      "totalNum": 1,
      "totalPage": 1,
      "list": [
        {
          "deviceId": "1669136175370137602",
          "sn": "1582290393341964289-77f2977b24191a4a:001:0000000000b",
          "brand": "Dreo",
          "model": "DR-HTF008S",
          "productId": "1582290393341964289",
          "productName": "Tower Fan",
          "deviceName": "Main Bedroom Fan",
          "shared": False,
          "series": None,
          "seriesName": "Cruiser Pro T3 S",
          "controlsConf": {
            "template": "DR-HTF008S",
            "lottie": {
              "key": "poweron",
              "frames": [
                {
                  "value": 0,
                  "frame": [
                    0
                  ]
                },
                {
                  "value": 1,
                  "frame": [
                    2
                  ]
                }
              ]
            },
            "cards": [
              {
                "type": 2,
                "title": "device_control_temp",
                "icon": "",
                "image": "",
                "url": "",
                "show": True
              },
              {
                "type": 6,
                "title": "device_settings_title",
                "icon": "ic_setting",
                "image": "",
                "url": "dreo://nav/device/setting?deviceSn=${sn}",
                "show": True,
                "key": "setting"
              }
            ],
            "preference": [
              {
                "id": "200",
                "type": "Panel Sound",
                "title": "device_control_panelsound",
                "image": "ic_mute",
                "reverse": False,
                "cmd": "voiceon"
              },
              {
                "id": "210",
                "type": "Display Auto Off",
                "title": "device_fans_mode_auto_display",
                "image": "ic_display",
                "reverse": True,
                "cmd": "ledalwayson"
              },
              {
                "id": "230",
                "type": "Temperature Unit",
                "title": "device_control_temp_unit",
                "image": "ic_temp_unit"
              }
            ],
            "control": [
              {
                "id": "100",
                "type": "Mode",
                "title": "device_mode",
                "items": [
                  {
                    "text": "device_fans_mode_straight",
                    "textColors": [
                      "#D5D6D7",
                      "#D5D6D7"
                    ],
                    "image": "ic_normal_wind",
                    "imageColors": [
                      "#D5D6D7",
                      "#25D7E4"
                    ],
                    "cmd": "windtype",
                    "value": 1
                  },
                  {
                    "text": "device_fans_mode_natural",
                    "textColors": [
                      "#D5D6D7",
                      "#D5D6D7"
                    ],
                    "image": "ic_natural_wind",
                    "imageColors": [
                      "#D5D6D7",
                      "#2CDD96"
                    ],
                    "cmd": "windtype",
                    "value": 2
                  },
                  {
                    "text": "device_control_mode_sleep",
                    "textColors": [
                      "#D5D6D7",
                      "#D5D6D7"
                    ],
                    "image": "ic_sleep_wind",
                    "imageColors": [
                      "#D5D6D7",
                      "#6249DF"
                    ],
                    "cmd": "windtype",
                    "value": 3
                  },
                  {
                    "text": "device_control_mode_auto",
                    "textColors": [
                      "#D5D6D7",
                      "#D5D6D7"
                    ],
                    "image": "ic_auto_wind",
                    "imageColors": [
                      "#D5D6D7",
                      "#0A80F5"
                    ],
                    "cmd": "windtype",
                    "value": 4
                  }
                ]
              },
              {
                "id": "110",
                "type": "Speed",
                "title": "device_control_speed",
                "items": [
                  {
                    "text": "1",
                    "cmd": "windlevel",
                    "value": 1
                  },
                  {
                    "text": "5",
                    "cmd": "windlevel",
                    "value": 5
                  }
                ]
              },
              {
                "id": "120",
                "type": "Oscillation",
                "title": "device_control_oscillation",
                "items": [],
                "cmd": "shakehorizon"
              }
            ],
            "category": "Tower Fan",
            "setting": [
              {
                "text": "Firmware Version",
                "image": "image.png",
                "value": "1.0.0",
                "url": "dreo://control"
              }
            ]
          },
          "mainConf": {
            "isSmart": True,
            "isWifi": True,
            "isBluetooth": True,
            "isVoiceControl": True
          },
          "resourcesConf": {
            "imageSmallSrc": "https://resources.dreo-cloud.com/app/202302/154b19731975c74404ba60cc6a4af66c08.png",
            "imageFullSrc": "https://resources.dreo-cloud.com/app/202302/16acefeb4c1aaa47c189c693cdf0beb612.zip"
          },
          "servicesConf": [
            {
              "key": "user_manual",
              "value": "https://resources.dreo-cloud.com/app/202302/15e71c34e2b2e24aa79e9b2b4a5733f852.pdf"
            }
          ]
        }
      ]
    }
  }