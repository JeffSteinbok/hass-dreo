
LOGGER_NAME = "pydreo"

ACCESS_TOKEN_KEY = "access_token"
REGION_KEY = "region"
DATA_KEY = "data"
LIST_KEY = "list"
MIXED_KEY = "mixed"
DEVICEID_KEY = "deviceid"
DEVICESN_KEY = "deviceSn"
REPORTED_KEY = "reported"
STATE_KEY = "state"
POWERON_KEY = "poweron"
WINDTYPE_KEY = "windtype"
WINDLEVEL_KEY = "windlevel"
SHAKEHORIZON_KEY = "shakehorizon"
TEMPERATURE_KEY = "temperature"
VOICEON_KEY = "voiceon"
LEDALWAYSON_KEY = "ledalwayson"

DREO_API_URL_FORMAT = "https://app-api-{0}.dreo-cloud.com" # {0} is the 2 letter region code

DREO_API_LIST_PATH = "path"
DREO_API_LIST_METHOD = "method"

DREO_API_LOGIN = "login"
DREO_API_DEVICELIST = "devicelist"
DREO_API_DEVICESTATE = "devicestate"

DREO_APIS =  {
    DREO_API_LOGIN : { DREO_API_LIST_PATH: '/api/oauth/login',
               DREO_API_LIST_METHOD: 'post' },
    DREO_API_DEVICELIST: { DREO_API_LIST_PATH: '/api/v2/user-device/device/list',
                    DREO_API_LIST_METHOD: 'get' },
    DREO_API_DEVICESTATE: { DREO_API_LIST_PATH: '/api/user-device/device/state',
                    DREO_API_LIST_METHOD: 'get' }                    
}

DREO_AUTH_REGION_NA = "NA"
DREO_AUTH_REGION_EU = "EU"

DREO_API_REGION_US = "us"
DREO_API_REGION_EU = "eu"

FAN_MODE_NORMAL = "normal"
FAN_MODE_NATURAL = "natural"
FAN_MODE_AUTO = "auto"
FAN_MODE_SLEEP = "sleep"

PRESET_MODES_KEY = "preset_modes"
SPEED_RANGE_KEY = "speed_range"

SUPPORTED_FANS = {
    "DR-HTF001S": {
        PRESET_MODES_KEY: [FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        SPEED_RANGE_KEY: (1, 6)
    },
    "DR-HTF002S": {
        PRESET_MODES_KEY: [FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        SPEED_RANGE_KEY: (1, 6)
    },
    "DR-HTF004S": {
        PRESET_MODES_KEY: [FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        SPEED_RANGE_KEY: (1, 12)
    },
    "DR-HTF007S": {
        PRESET_MODES_KEY: [FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        SPEED_RANGE_KEY: (1, 4)
    },
    "DR-HTF008S": {
        PRESET_MODES_KEY: [FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        SPEED_RANGE_KEY: (1, 5)
    },
}