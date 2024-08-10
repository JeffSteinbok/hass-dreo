"""Supported device models for the PyDreo library."""

from dataclasses import dataclass

from .constant import (
    FAN_MODE_AUTO,
    FAN_MODE_NATURAL,
    FAN_MODE_NORMAL,
    FAN_MODE_SLEEP,
    FAN_MODE_TURBO,
    HEATER_MODE_COOLAIR,
    HEATER_MODE_HOTAIR,
    HEATER_MODE_ECO,
    HEATER_MODE_OFF,
    SPEED_RANGE,
    HEAT_RANGE,
    ECOLEVEL_RANGE,
    TEMP_RANGE,
    TARGET_TEMP_RANGE,
    TARGET_TEMP_RANGE_ECO,
    HeaterOscillationAngles,
    TEMPERATURE_KEY,
    HUMIDITY_RANGE,
)

from homeassistant.components.climate import (
    SWING_ON,
    SWING_OFF,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    PRESET_NONE,
    PRESET_ECO,
    HVACMode,
)


@dataclass
class DreoDeviceDetails:
    """Represents a Dreo device model and capabilities"""

    preset_modes: list[str]
    """List of possible preset mode names"""

    range: dict
    """Dictionary of different ranges"""

    hvac_modes: list[str]
    """List of possible HVAC mode names"""

    swing_modes: list[str]
    """List of possible swing modes"""

    cooking_modes: list[str]
    """List of possible cooking modes"""

    cooking_range: dict
    """Dictionary of different cooking ranges"""

    def __init__(
        self,
        preset_modes: list[str] = None,
        range: dict = None,
        hvac_modes: list[str] = None,
        swing_modes: list[str] = None,
        fan_modes: list[str] = None,
        cooking_modes: list[str] = None,
        cooking_range: dict = None,
    ):
        self.preset_modes = preset_modes
        self.range = range
        self.hvac_modes = hvac_modes
        self.swing_modes = swing_modes
        self.fan_modes = fan_modes
        self.cooking_modes = cooking_modes
        self.cooking_range = cooking_range


SUPPORTED_FANS = {
    "DR-HAF001S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO, FAN_MODE_TURBO],
        range = {SPEED_RANGE: (1, 4)}
    ),    
    "DR-HAF003S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO, FAN_MODE_TURBO],
        range = {SPEED_RANGE: (1, 8)}
    ),
    "DR-HAF004S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO, FAN_MODE_TURBO],
        range = {SPEED_RANGE: (1, 9)}
    ),
    "DR-HPF002S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO, FAN_MODE_TURBO],
        range = {SPEED_RANGE: (1, 8)}
    ),
    "DR-HPF004S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO, FAN_MODE_TURBO],
        range = {SPEED_RANGE: (1, 9)}
    ),
    "DR-HPF005S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_AUTO, FAN_MODE_TURBO],
        range = {SPEED_RANGE: (1, 9)}
    ),    
    "DR-HTF001S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range={SPEED_RANGE: (1, 6)},
    ),
    "DR-HTF002S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range={SPEED_RANGE: (1, 6)},
    ),
    "DR-HTF004S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range={SPEED_RANGE: (1, 12)},
    ),
    "DR-HTF005S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range={SPEED_RANGE: (1, 9)},
    ),
    "DR-HTF007S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range={SPEED_RANGE: (1, 4)},
    ),
    "DR-HTF008S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range = {SPEED_RANGE: (1, 5)}
    ),
    "DR-HTF009S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range = {SPEED_RANGE: (1, 9)}
    ),
    "DR-HTF010S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range = {SPEED_RANGE: (1, 12)}
    ),    
    "DR-HAF001S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range = {SPEED_RANGE: (1, 4)}
    ),
    "DR-HAF003S": DreoDeviceDetails(
        preset_modes=[
            FAN_MODE_NORMAL,
            FAN_MODE_NATURAL,
            FAN_MODE_SLEEP,
            FAN_MODE_AUTO,
            FAN_MODE_TURBO,
        ],
        range={SPEED_RANGE: (1, 8)},
    ),
    "DR-HAF004S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO, FAN_MODE_TURBO],
        range = {SPEED_RANGE: (1, 9)}
    ),
    "DR-HPF002S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO, FAN_MODE_TURBO],
        range = {SPEED_RANGE: (1, 8)}
    ),
    "DR-HPF001S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO, FAN_MODE_TURBO],
        range = {SPEED_RANGE: (1, 9)}
    ),
   "DR-HCF001S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range = {SPEED_RANGE: (1, 12)}
    )
}


SUPPORTED_HEATERS = {
    "DR-HSH004S": DreoDeviceDetails(
        preset_modes=["H1", "H2", "H3"],
        range={HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 85)},
        hvac_modes=[
            HEATER_MODE_COOLAIR,
            HEATER_MODE_HOTAIR,
            HEATER_MODE_ECO,
            HEATER_MODE_OFF,
        ],
        swing_modes=[SWING_OFF, SWING_ON],
    ),
    "DR-HSH009S": DreoDeviceDetails(
        preset_modes=["H1", "H2", "H3"],
        range={HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
        hvac_modes=[
            HEATER_MODE_COOLAIR,
            HEATER_MODE_HOTAIR,
            HEATER_MODE_ECO,
            HEATER_MODE_OFF,
        ],
        swing_modes=[
            HeaterOscillationAngles.OSC,
            HeaterOscillationAngles.SIXTY,
            HeaterOscillationAngles.NINETY,
            HeaterOscillationAngles.ONE_TWENTY,
        ],
    ),
    "DR-HSH009AS": DreoDeviceDetails(
        preset_modes=["H1", "H2", "H3"],
        range={HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
        hvac_modes=[
            HEATER_MODE_COOLAIR,
            HEATER_MODE_HOTAIR,
            HEATER_MODE_ECO,
            HEATER_MODE_OFF,
        ],
        swing_modes=[
            HeaterOscillationAngles.OSC,
            HeaterOscillationAngles.SIXTY,
            HeaterOscillationAngles.NINETY,
            HeaterOscillationAngles.ONE_TWENTY,
        ],
    ),
    "WH719S": DreoDeviceDetails(
        preset_modes=["H1", "H2", "H3"],
        range={HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
        hvac_modes=[
            HEATER_MODE_COOLAIR,
            HEATER_MODE_HOTAIR,
            HEATER_MODE_ECO,
            HEATER_MODE_OFF,
        ],
        swing_modes=[
            HeaterOscillationAngles.OSC,
            HeaterOscillationAngles.SIXTY,
            HeaterOscillationAngles.NINETY,
            HeaterOscillationAngles.ONE_TWENTY,
        ],
    ),
    "WH739S": DreoDeviceDetails(
        preset_modes=["H1", "H2", "H3"],
        range={HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
        hvac_modes=[
            HEATER_MODE_COOLAIR,
            HEATER_MODE_HOTAIR,
            HEATER_MODE_ECO,
            HEATER_MODE_OFF,
        ],
        swing_modes=[
            HeaterOscillationAngles.OSC,
            HeaterOscillationAngles.SIXTY,
            HeaterOscillationAngles.NINETY,
            HeaterOscillationAngles.ONE_TWENTY,
        ],
    ),
}

SUPPORTED_ACS = {
    "DR-HAC005S": DreoDeviceDetails(
        range={
            TEMP_RANGE: (60, 95),
            TARGET_TEMP_RANGE: (64, 86),
            TARGET_TEMP_RANGE_ECO: (75, 86),
            HUMIDITY_RANGE: (30, 80),
        },
        # TODO Eco is a Present, not HVAC mode (HVACMode.AUTO)
        hvac_modes=[HVACMode.COOL, HVACMode.FAN_ONLY, HVACMode.DRY],
        swing_modes=[SWING_OFF, SWING_ON],
        preset_modes=[PRESET_NONE, PRESET_ECO],
        # TODO Add fan modes, windlevel: 1,2,3,4 (Auto)
        fan_modes=[FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO],
    )
}

COOKING_MODES = [
    "Air Fry",
    "Roast",
    "Defrost",
    "Toast",
    "Reheat",
    "Bake",
    "Broil",
    "Dehydrate",
]

COOKING_RANGES = {
    "Air Fry": {"temp_range": (200, 450), "duration_range": (1, 3600)},
    "Roast": {"temp_range": (200, 450), "duration_range": (1, 3600)},
    "Defrost": {"temp_range": (100, 150), "duration_range": (1, 3600)},
    "Toast": {"temp_range": (200, 400), "duration_range": (1, 600)},
    "Reheat": {"temp_range": (200, 400), "duration_range": (1, 600)},
    "Bake": {"temp_range": (200, 400), "duration_range": (1, 3600)},
    "Broil": {"temp_range": (350, 450), "duration_range": (1, 3600)},
    "Dehydrate": {"temp_range": (100, 175), "duration_range": (1, 43200)},
}

SUPPORTED_COOKERS = {
    "DR-KCM001S": DreoDeviceDetails(
        cooking_modes=COOKING_MODES,
        cooking_range=COOKING_RANGES,
    )
}

SUPPORTED_ACS = {
    "DR-HAC005S": DreoDeviceDetails(
        range={
            TEMP_RANGE: (60, 95),
            TARGET_TEMP_RANGE: (64, 86),
            TARGET_TEMP_RANGE_ECO: (75, 86),
            HUMIDITY_RANGE: (30, 80),
        },
        # TODO Eco is a Present, not HVAC mode (HVACMode.AUTO)
        hvac_modes=[HVACMode.COOL, HVACMode.FAN_ONLY, HVACMode.DRY],
        swing_modes=[SWING_OFF, SWING_ON],
        preset_modes=[PRESET_NONE, PRESET_ECO],
        # TODO Add fan modes, windlevel: 1,2,3,4 (Auto)
        fan_modes=[FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO],
    )
}

SUPPORTED_DEVICES = [ 
    ("PyDreoFan", SUPPORTED_FANS), 
    ("PyDreoHeater", SUPPORTED_HEATERS),
    ("PyDreoAc", SUPPORTED_ACS),
    ("PyDreoChefMaker", SUPPORTED_COOKERS),
]
