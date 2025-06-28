"""Supported device models for the PyDreo library."""

from dataclasses import dataclass

from .constant import (
    SPEED_RANGE,
    HEATER_MODE_COOLAIR,
    HEATER_MODE_HOTAIR,
    HEATER_MODE_ECO,
    HEATER_MODE_OFF,
    HEAT_RANGE,
    ECOLEVEL_RANGE,
    SPEED_RANGE,
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
    HVACMode,
    DreoDeviceType
)

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


@dataclass
class DreoDeviceDetails:
    """Represents a Dreo device model and capabilities"""

    device_type: DreoDeviceType
    """The type of device"""

    preset_modes: list[str]
    """List of possible preset mode names"""

    device_ranges: dict[range]
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
        device_type: DreoDeviceType = None,
        preset_modes: list[str] = None,
        device_ranges: dict = None,
        hvac_modes: list[str] = None,
        swing_modes: list[str] = None,
        fan_modes: list[str] = None,
        cooking_modes: list[str] = None,
        cooking_range: dict = None,
    ):
        if (device_type is None):
            raise ValueError("device_type is required")

        self.device_type = device_type
        self.preset_modes = preset_modes
        self.device_ranges = device_ranges
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
    "DR-HAP",
    "DR-HPF",
    "DR-HCF",
    "DR-HSH",
    "WH",
    "DR-HAC",
    "DR-HHM",
    "DR-HEC"
}

SUPPORTED_DEVICES = {
    # Tower Fans
    "DR-HTF": DreoDeviceDetails(device_type=DreoDeviceType.TOWER_FAN),

    # Air Circulators
    "DR-HAF": DreoDeviceDetails(device_type=DreoDeviceType.AIR_CIRCULATOR),
    "DR-HPF": DreoDeviceDetails(device_type=DreoDeviceType.AIR_CIRCULATOR),
    "DR-HPF008S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        device_ranges={SPEED_RANGE: (1, 9)}),

    # Ceiling Fans
    "DR-HCF": DreoDeviceDetails(device_type=DreoDeviceType.CEILING_FAN),

    # Air Purifiers
    "DR-HAP": DreoDeviceDetails(device_type=DreoDeviceType.AIR_PURIFIER),

    # Heaters
    "DR-HSH017BS": DreoDeviceDetails(
        device_type=DreoDeviceType.HEATER,
        preset_modes=["H1", "H2", "H3"],
        device_ranges={HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 85)},
        hvac_modes=[
            HEATER_MODE_COOLAIR,
            HEATER_MODE_HOTAIR,
            HEATER_MODE_ECO,
            HEATER_MODE_OFF,
        ],
    ),
    "DR-HSH004S": DreoDeviceDetails(
        device_type=DreoDeviceType.HEATER,
        preset_modes=["H1", "H2", "H3"],
        device_ranges={HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 85)},
        hvac_modes=[
            HEATER_MODE_COOLAIR,
            HEATER_MODE_HOTAIR,
            HEATER_MODE_ECO,
            HEATER_MODE_OFF,
        ],
        swing_modes=[SWING_OFF, SWING_ON],
    ),
    "DR-HSH006S": DreoDeviceDetails(
        device_type=DreoDeviceType.HEATER,
        preset_modes=["H1", "H2", "H3"],
        device_ranges={HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
        hvac_modes=[
            HEATER_MODE_COOLAIR,
            HEATER_MODE_HOTAIR,
            HEATER_MODE_ECO,
            HEATER_MODE_OFF,
        ],
        swing_modes=[SWING_OFF, SWING_ON],
    ),
    "DR-HSH009S": DreoDeviceDetails(
        device_type=DreoDeviceType.HEATER,
        preset_modes=["H1", "H2", "H3"],
        device_ranges={HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
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
        device_type=DreoDeviceType.HEATER,
        preset_modes=["H1", "H2", "H3"],
        device_ranges={HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
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
    "DR-HSH017S": DreoDeviceDetails(
        device_type=DreoDeviceType.HEATER,
        preset_modes=["H1", "H2", "H3"],
        device_ranges={HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
        hvac_modes=[
            HEATER_MODE_COOLAIR,
            HEATER_MODE_HOTAIR,
            HEATER_MODE_ECO,
            HEATER_MODE_OFF,
        ],
        swing_modes=[SWING_OFF, SWING_ON],
    ),    
    # Are these even used?  They don't show up as model numbers.  Should they be a DR prefix?
    "WH719S": DreoDeviceDetails(
        device_type=DreoDeviceType.HEATER,
        preset_modes=["H1", "H2", "H3"],
        device_ranges={HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
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
        device_type=DreoDeviceType.HEATER,
        preset_modes=["H1", "H2", "H3"],
        device_ranges={HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
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

    # Air Conditioners
    # Note we had HAC-005S and HAC-006S in the list but they are identical.
    "DR-HAC": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CONDITIONER,
        device_ranges={
            TEMP_RANGE: (60, 86),
            TARGET_TEMP_RANGE: (64, 86),
            TARGET_TEMP_RANGE_ECO: (75, 86),
            HUMIDITY_RANGE: (30, 80),
        },
        # TODO Eco is a Present, not HVAC mode (HVACMode.AUTO)
        hvac_modes=[
            HVACMode.OFF,
            HVACMode.COOL, 
            HVACMode.FAN_ONLY, 
            HVACMode.DRY
        ],
        swing_modes=[SWING_OFF, SWING_ON],
        preset_modes=[PRESET_NONE, PRESET_ECO],
        # TODO Add fan modes, windlevel: 1,2,3,4 (Auto)
        fan_modes=[FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO],
    ),

    "DR-KCM001S": DreoDeviceDetails(
        device_type=DreoDeviceType.CHEF_MAKER,
        cooking_modes=COOKING_MODES,
        cooking_range=COOKING_RANGES,
    ),

    "DR-HHM": DreoDeviceDetails(device_type=DreoDeviceType.HUMIDIFIER),

    # Evaporative Coolers
    "DR-HEC": DreoDeviceDetails(
        device_type=DreoDeviceType.EVAPORATIVE_COOLER,
        device_ranges={
            SPEED_RANGE: (1, 4)
        },
    )
}
