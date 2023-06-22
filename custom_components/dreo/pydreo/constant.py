
LOGGER_NAME = "pydreo"

REPORTED_KEY = "reported"
STATE_KEY = "state"
POWERON_KEY = "poweron"
WINDTYPE_KEY = "windtype"
WINDLEVEL_KEY = "windlevel"
SHAKEHORIZON_KEY = "shakehorizon"
TEMPERATURE_KEY = "temperature"
VOICEON_KEY = "voiceon"
LEDALWAYSON_KEY = "ledalwayson"

FAN_MODE_NORMAL = "normal"
FAN_MODE_NATURAL = "natural"
FAN_MODE_AUTO = "auto"
FAN_MODE_SLEEP = "sleep"

PRESET_MODES = {
    "DR-HTF008S": [FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
    "DR-HTF001S": [FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO]
}

SPEED_RANGES = {  
    # off is not included
    "DR-HTF008S": (1, 5),
    "DR-HTF001S": (1, 6)
}
