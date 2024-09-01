"""Supported device models for the PyDreo library."""

from dataclasses import dataclass

from .constant import (
    HEATER_MODE_COOLAIR,
    HEATER_MODE_HOTAIR,
    HEATER_MODE_ECO,
    HEATER_MODE_OFF,
    HEAT_RANGE,
    ECOLEVEL_RANGE,
    TEMP_RANGE,
    TARGET_TEMP_RANGE,
    TARGET_TEMP_RANGE_ECO,
    HeaterOscillationAngles,
    HUMIDITY_RANGE,
    SWING_ON,
    SWING_OFF,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    PRESET_NONE,
    PRESET_ECO,
    HVACMode
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

# Supported prefixes.
# These prefixes will be listed along with the models in the below collections.
SUPPORTED_MODEL_PREFIXES = {
    "DR-HTF",
    "DR-HAF",
    "DR-HPF",
    "DR-HCF",
    "DR-HSH",
    "WH", 
    "DR-HAC"
}

SUPPORTED_FANS = {
    "DR-HTF": DreoDeviceDetails(),
    "DR-HAF": DreoDeviceDetails(),
    "DR-HPF": DreoDeviceDetails(),
    "DR-HCF": DreoDeviceDetails()
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
