from typing import TYPE_CHECKING

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