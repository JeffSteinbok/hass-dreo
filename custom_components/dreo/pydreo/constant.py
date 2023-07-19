from .fandefinition import *

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
OSCMODE_KEY = "oscmode"
TEMPERATURE_KEY = "temperature"
VOICEON_KEY = "voiceon"
LEDALWAYSON_KEY = "ledalwayson"

DREO_API_URL_FORMAT = (
    "https://app-api-{0}.dreo-cloud.com"  # {0} is the 2 letter region code
)

DREO_API_LIST_PATH = "path"
DREO_API_LIST_METHOD = "method"

DREO_API_LOGIN = "login"
DREO_API_DEVICELIST = "devicelist"
DREO_API_DEVICESTATE = "devicestate"

DREO_APIS = {
    DREO_API_LOGIN: {
        DREO_API_LIST_PATH: "/api/oauth/login",
        DREO_API_LIST_METHOD: "post",
    },
    DREO_API_DEVICELIST: {
        DREO_API_LIST_PATH: "/api/v2/user-device/device/list",
        DREO_API_LIST_METHOD: "get",
    },
    DREO_API_DEVICESTATE: {
        DREO_API_LIST_PATH: "/api/user-device/device/state",
        DREO_API_LIST_METHOD: "get",
    },
}

DREO_AUTH_REGION_NA = "NA"
DREO_AUTH_REGION_EU = "EU"

DREO_API_REGION_US = "us"
DREO_API_REGION_EU = "eu"

FAN_MODE_NORMAL = "normal"
FAN_MODE_NATURAL = "natural"
FAN_MODE_AUTO = "auto"
FAN_MODE_SLEEP = "sleep"
FAN_MODE_TURBO = "turbo"

HORIZONTAL_OSCILLATION_KEY = "hoscon"
HORIZONTAL_OSCILLATION_ANGLE_KEY = "hoscangle"

VERTICAL_OSCILLATION_KEY = "voscon"
VERTICAL_OSCILLATION_ANGLE_KEY = "voscangle"

AIR_CIRCULATOR_WIND_MODE_KEY = "mode"

SUPPORTED_FANS = {
    "DR-HAF001S" : PyDreoFanDefinition(preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
                                       speed_range=(1,4),
                                       oscillation_support= OscillationSupport.HORIZONTAL),

    "DR-HAF003S" : PyDreoFanDefinition(preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO, FAN_MODE_TURBO],
                                       speed_range=(1,8),
                                       oscillation_support= OscillationSupport.HORIZONTAL),

    "DR-HAF004S" : PyDreoFanDefinition(preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO, FAN_MODE_TURBO],
                                       speed_range=(1,9),
                                       oscillation_support= OscillationSupport.BOTH),

    "DR-HTF001S" : PyDreoFanDefinition(preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
                                       speed_range=(1,6),
                                       oscillation_support= OscillationSupport.HORIZONTAL),

    "DR-HTF002S" : PyDreoFanDefinition(preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
                                       speed_range=(1,12),
                                       oscillation_support= OscillationSupport.HORIZONTAL),
                                       
    "DR-HTF004S" : PyDreoFanDefinition(preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
                                       speed_range=(1,4),
                                       oscillation_support= OscillationSupport.HORIZONTAL),

    "DR-HTF007S" : PyDreoFanDefinition(preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
                                       speed_range=(1,9),
                                       oscillation_support= OscillationSupport.HORIZONTAL),

    "DR-HTF008S" : PyDreoFanDefinition(preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
                                       speed_range=(1,5),
                                       oscillation_support= OscillationSupport.HORIZONTAL),
}
