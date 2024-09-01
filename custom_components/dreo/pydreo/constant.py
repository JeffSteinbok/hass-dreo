"""Constants for the PyDreo library."""
from enum import Enum, IntEnum, StrEnum

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
SHAKEHORIZONANGLE_KEY = "shakehorizonangle"
MODE_KEY = "mode"
HTALEVEL_KEY = "htalevel"
OSCON_KEY = "oscon"
OSCMODE_KEY = "oscmode"
OSCANGLE_KEY = "oscangle"
CRUISECONF_KEY = "cruiseconf"
TEMPERATURE_KEY = "temperature"
TARGET_TEMPERATURE_KEY = "templevel"
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
HUMIDITY_KEY = "rh"
TARGET_HUMIDITY_KEY = "rhlevel"


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

AC_ECO_LEVEL_MAP = {
    1 : "10%",
    2 : "20%",
    3 : "30%"
}

OSCANGLE_ANGLE_MAP = {
    "Oscillate" : 0,
    "60°" : 60,
    "90°" : 90,
    "120°" : 120
}

ANGLE_OSCANGLE_MAP = {
    0: "Oscillate",
    60 : "60°",
    90 : "90°",
    120 : "120°"
}

HORIZONTAL_OSCILLATION_KEY = "hoscon"
HORIZONTAL_OSCILLATION_ANGLE_KEY = "hoscangle"

VERTICAL_OSCILLATION_KEY = "voscon"
VERTICAL_OSCILLATION_ANGLE_KEY = "voscangle"

MIN_OSC_ANGLE_DIFFERENCE = 30

# Heater oscillation
OSCILLATION_KEY = "oscon"
OSCILLATION_ANGLE_KEY = "oscangle"

WIND_MODE_KEY = "mode"

SPEED_RANGE = "speed_range"
HEAT_RANGE = "heat_range"
ECOLEVEL_RANGE = "ecolevel_range"
TEMP_RANGE = "temp_range"
TARGET_TEMP_RANGE = "target_temp_range"
TARGET_TEMP_RANGE_ECO = "target_temp_range_eco"
HUMIDITY_RANGE = "humidity_range"

class TemperatureUnit(Enum):
    """Valid possible temperature units."""
    CELCIUS = 0
    FAHRENHEIT = 1

# Fan oscillation modes
class OscillationMode(IntEnum):
    """Possible oscillation modes.  These are bitwise flags."""
    OFF = 0,
    HORIZONTAL = 1,
    VERTICAL = 2,
    BOTH = 3

# Heater oscillation modes
class HeaterOscillationAngles(StrEnum):
    """Possible Heater oscillation angles"""
    OSC = "Oscillate"
    SIXTY = "60°",
    NINETY = "90°",
    ONE_TWENTY = "120°"

#
# The following is copied from homeassistant.components.climate

# Possible swing state
SWING_ON = "on"
SWING_OFF = "off"
# Possible fan state
FAN_ON = "on"
FAN_OFF = "off"
FAN_AUTO = "auto"
FAN_LOW = "low"
FAN_MEDIUM = "medium"
FAN_HIGH = "high"
FAN_TOP = "top"
FAN_MIDDLE = "middle"
FAN_FOCUS = "focus"
FAN_DIFFUSE = "diffuse"
# No preset is active
PRESET_NONE = "none"

# Device is running an energy-saving mode
PRESET_ECO = "eco"

class HVACMode(StrEnum):
    """HVAC mode for climate devices."""

    # All activity disabled / Device is off/standby
    OFF = "off"

    # Heating
    HEAT = "heat"

    # Cooling
    COOL = "cool"

    # The device supports heating/cooling to a range
    HEAT_COOL = "heat_cool"

    # The temperature is set based on a schedule, learned behavior, AI or some
    # other related mechanism. User is not able to adjust the temperature
    AUTO = "auto"

    # Device is in Dry/Humidity mode
    DRY = "dry"

    # Only the fan is on, not fan and another mode like cool
    FAN_ONLY = "fan_only"

FAN_MODE_STRINGS = {
    "device_fans_mode_straight": "normal",
    "device_fans_mode_natural": "natural",
    "device_control_mode_sleep": "sleep",
    "device_fans_mode_sleep": "sleep",
    "device_fans_mode_auto": "auto",
    "device_control_mode_auto": "auto",
    "device_control_mode_turbo": "turbo",
    "base_reverse": "reverse",
    "device_control_custom": "custom"
}
