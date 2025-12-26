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
MODE_KEY = "mode"
HTALEVEL_KEY = "htalevel"
OSCON_KEY = "oscon"
OSCMODE_KEY = "oscmode"
OSCANGLE_KEY = "oscangle"
CRUISECONF_KEY = "cruiseconf"
TEMPERATURE_KEY = "temperature"
TARGET_TEMPERATURE_KEY = "templevel"
SLEEPTEMPOFFSET_KEY = "sleeptempoffset"
VOICEON_KEY = "voiceon"
LEDALWAYSON_KEY = "ledalwayson"
LIGHTSENSORON_KEY = "lightsensoron"
MUTEON_KEY = "muteon"
PM25_KEY = "pm25"
FIXEDCONF_KEY = "fixedconf"
DEVON_KEY = "devon"
TIMERON_KEY = "timeron"
COOLDOWN_KEY = "cooldown"
PTCON_KEY = "ptcon"
LIGHTON_KEY = "lighton"
BRIGHTNESS_KEY = "brightness"
COLORTEMP_KEY = "colortemp"
CTLSTATUS_KEY = "ctlstatus"
TIMEROFF_KEY = "timeroff"
ECOLEVEL_KEY = "ecolevel"
ECOLEVEL_RANGE_KEY = "ecolevel_range"
CHILDLOCKON_KEY = "childlockon"
TEMPOFFSET_KEY = "tempoffset"
HUMIDITY_KEY = "rh"
WORKTIME_KEY = "worktime"
TEMP_TARGET_REACHED_KEY = "reachtarget"
TARGET_AUTO_HUMIDITY_KEY = "rhautolevel"
TARGET_HUMIDITY_KEY = "rhlevel"
ATMON_KEY = 'atmon'
ATMCOLOR_KEY = 'atmcolor'
ATMBRI_KEY = 'atmbri'
ATMMODE_KEY = 'atmmode'
RGB_LEVEL = 'rgblevel'
SCHEDULE_ENABLE = 'scheon'

# Preferences Names
# It's possible we should switch to IDs instead of names
PREFERENCE_TYPE_TEMPERATURE_CALIBRATION = "Temperature Calibration"  # ID: 250

# Tower Fans
SHAKEHORIZON_KEY = "shakehorizon"
SHAKEHORIZONANGLE_KEY = "shakehorizonangle"

# Ceiling Fan
FANON_KEY = "fanon"


DREO_API_URL_FORMAT = (
    "https://app-api-{0}.dreo-tech.com"  # {0} is the 2 letter region code
)

DREO_API_PATH = "path"
DREO_API_METHOD = "method"

DREO_API_LOGIN = "login"
DREO_API_DEVICELIST = "devicelist"
DREO_API_DEVICESTATE = "devicestate"
DREO_API_SETTING_GET = "setting_get"
DREO_API_SETTING_PUT = "setting_put"

DREO_API_SETTING_DATA_KEY = "dataKey"
DREO_API_SETTING_DATA_VALUE = "dataValue"

DREO_APIS = {
    DREO_API_LOGIN: {
        DREO_API_PATH: "/api/oauth/login",
        DREO_API_METHOD: "post",
    },
    DREO_API_DEVICELIST: {
        DREO_API_PATH: "/api/v2/user-device/device/list",
        DREO_API_METHOD: "get",
    },
    DREO_API_DEVICESTATE: {
        DREO_API_PATH: "/api/user-device/device/state",
        DREO_API_METHOD: "get",
    },
    DREO_API_SETTING_GET: {
        DREO_API_PATH: "/api/user-device/setting",
        DREO_API_METHOD: "get",
    },
    DREO_API_SETTING_PUT: {
        DREO_API_PATH: "/api/user-device/setting",
        DREO_API_METHOD: "put",
    }
}

class DreoDeviceSetting(StrEnum):
    """Dreo device settings"""
    FAN_TEMP_OFFSET = "kHafFanTempOffsetKey"

DREO_AUTH_REGION_NA = "NA"
DREO_AUTH_REGION_EU = "EU"

DREO_API_REGION_US = "us"
DREO_API_REGION_EU = "eu"

HEATER_MODE_COOLAIR = "coolair"
HEATER_MODE_HOTAIR = "hotair"
HEATER_MODE_ECO = "eco"
HEATER_MODE_OFF = "off"

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
HORIZONTAL_ANGLE_ADJ_KEY = "hangleadj"

VERTICAL_OSCILLATION_KEY = "voscon"
VERTICAL_OSCILLATION_ANGLE_KEY = "voscangle"

MIN_OSC_ANGLE_DIFFERENCE = 30

# Heater oscillation
OSCILLATION_KEY = "oscon"
OSCILLATION_ANGLE_KEY = "oscangle"

WIND_MODE_KEY = "mode"

HORIZONTAL_ANGLE_RANGE = "horizontal_angle_range"
VERTICAL_ANGLE_RANGE = "vertical_angle_range"
SPEED_RANGE = "speed_range"
HEAT_RANGE = "heat_range"
ECOLEVEL_RANGE = "ecolevel_range"
TEMP_RANGE = "temp_range"
TARGET_TEMP_RANGE = "target_temp_range"
TARGET_TEMP_RANGE_ECO = "target_temp_range_eco"
HUMIDITY_RANGE = "humidity_range"

class TemperatureUnit(Enum):
    """Valid possible temperature units."""
    CELSIUS = 0
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

# Device is running in sleep mode
PRESET_SLEEP = "sleep"

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

PRESET_MODE_STRINGS = {
    "device_fans_mode_straight": "normal",
    "device_fans_mode_natural": "natural",
    "device_control_mode_sleep": "sleep",
    "device_fans_mode_sleep": "sleep",
    "device_fans_mode_auto": "auto",
    "device_control_mode_auto": "auto",
    "device_control_mode_turbo": "turbo",
    "base_reverse": "reverse",
    "device_control_custom": "custom",
    "fan_2in1_breeze": "2-in-1 Breeze Mode",
    "device_control_mode_manual": "manual",
    "device_heater_mode_heat": "Heat",
    "device_heater_mode_eco": "Eco",
    "device_heater_mode_fan_only": "Cool Air",
}


class DreoDeviceType(StrEnum):
    """Product names for Dreo devices"""
    TOWER_FAN = "Tower Fan"
    AIR_CIRCULATOR = "Air Circulator"
    AIR_PURIFIER = "Air Purifier"
    CEILING_FAN = "Ceiling Fan"
    HEATER = "Heater"
    AIR_CONDITIONER = "Air Conditioner"
    CHEF_MAKER = "Chef Maker"
    HUMIDIFIER = "Humidifier"
    DEHUMIDIFIER = "Dehumidifier"
    EVAPORATIVE_COOLER = "Evaporative Cooler"
    UNKNOWN = "Unknown"
