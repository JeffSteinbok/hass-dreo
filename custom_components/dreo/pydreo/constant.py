"""Constants for the PyDreo library."""
from enum import Enum, IntEnum

LOGGER_NAME = "pydreo"

# Various keys read from server JSON responses.
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
MODE_KEY = "mode"
HTALEVEL_KEY = "htalevel"
OSCON_KEY = "oscon"
OSCMODE_KEY = "oscmode"
TEMPERATURE_KEY = "temperature"
VOICEON_KEY = "voiceon"
LEDALWAYSON_KEY = "ledalwayson"
LIGHTSENSORON_KEY = "lightsensoron"
MUTEON_KEY = "muteon"
FIXEDCONF_KEY = "fixedconf"
DEVON_KEY = "devon"
TIMERON_KEY = "timeron"
COOLDOWN_KEY = "cooldown"
PTCON_KEY = "ptcon"
LIGHTON_KEY = "lighton"
CTLSTATUS_KEY = "ctlstatus"
TIMEROFF_KEY = "timeroff"
ECOLEVEL_KEY = "ecolevel"
ECOLEVEL_RANGE_KEY = "ecolevel_range"
CHILDLOCKON_KEY = "childlockon"
TEMPOFFSET_KEY = "tempoffset"


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
HEATER_MODE_COOLAIR = "coolair"
HEATER_MODE_HOTAIR = "hotair"
HEATER_MODE_ECO = "eco"
HEATER_MODE_OFF = "off"

MODE_LEVEL_MAP = {
    "H1" : 1,
    "H2" : 2,
    "H3" : 3
}

LEVEL_MODE_MAP = {
    1 : "H1",
    2 : "H2",
    3 : "H3"
}

HEATER_MODES = [
    HEATER_MODE_COOLAIR,
    HEATER_MODE_HOTAIR,
    HEATER_MODE_ECO,
    HEATER_MODE_OFF
]

HORIZONTAL_OSCILLATION_KEY = "hoscon"
HORIZONTAL_OSCILLATION_ANGLE_KEY = "hoscangle"

VERTICAL_OSCILLATION_KEY = "voscon"
VERTICAL_OSCILLATION_ANGLE_KEY = "voscangle"

OSCILLATION_KEY = "oscon"

WIND_MODE_KEY = "mode"

SPEED_RANGE = "speed_range"
HEAT_RANGE = "heat_range"
ECOLEVEL_RANGE = "ecolevel_range"

class TemperatureUnit(Enum):
    """Valid possible temperature units."""
    CELCIUS = 0
    FAHRENHEIT = 1

class OscillationMode(IntEnum):
    """Possible oscillation modes.  These are bitwise flags."""
    OFF = 0,
    HORIZONTAL = 1,
    VERTICAL = 2,
    BOTH = 3