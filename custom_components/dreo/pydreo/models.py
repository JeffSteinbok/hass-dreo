"""Supported device models for the PyDreo library."""

from dataclasses import dataclass

from .constant import (
    HORIZONTAL_ANGLE_RANGE,
    SPEED_RANGE,
    HEAT_RANGE,
    ECOLEVEL_RANGE,
    TEMP_RANGE,
    TARGET_TEMP_RANGE,
    TARGET_TEMP_RANGE_ECO,
    DreoHeaterMode,
    HeaterOscillationAngles,
    HUMIDITY_RANGE,
    SWING_ON,
    SWING_OFF,
    DreoDeviceType,
    VERTICAL_ANGLE_RANGE,
    DreoACMode,
    DreoACFanMode
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

    mode_names: list[str] | dict
    """List or dictionary of possible device mode names"""

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
        mode_names: list[str] = None,
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
        if self.device_ranges is None:
            self.device_ranges = {} 
        self.mode_names = mode_names
        self.swing_modes = swing_modes
        self.fan_modes = fan_modes
        self.cooking_modes = cooking_modes
        self.cooking_range = cooking_range

@dataclass
class DreoACDeviceDetails(DreoDeviceDetails):
    """Represents a Dreo Air Conditioner device model and capabilities"""

    def __init__(
        self,
        device_ranges: dict = None,
        modes: list[DreoACMode] = None,
        swing_modes: list[str] = None,
        fan_modes: list[DreoACFanMode] = None,
    ):
        super().__init__(
            device_type=DreoDeviceType.AIR_CONDITIONER,
            device_ranges=device_ranges,
            swing_modes=swing_modes,
        )
        self.modes = modes
        self.fan_modes = fan_modes

@dataclass
class DreoHeaterDeviceDetails(DreoDeviceDetails):
    """Represents a Dreo Heater device model and capabilities"""

    def __init__(
        self,
        device_ranges: dict = None,
        modes: list[DreoHeaterMode] = None,
        swing_modes: list[str] = None
    ):
        # Set default ranges if not provided
        if device_ranges is None:
            device_ranges = {
                HEAT_RANGE: (1, 3),
                ECOLEVEL_RANGE: (41, 95)
            }
        else:
            # Merge provided ranges with defaults
            default_ranges = {
                HEAT_RANGE: (1, 3),
                ECOLEVEL_RANGE: (41, 95)
            }
            device_ranges = {**default_ranges, **device_ranges}
        
        super().__init__(
            device_type=DreoDeviceType.HEATER,
            device_ranges=device_ranges,
            swing_modes=swing_modes,
        )
        self.modes = modes
        if self.modes is None:
            self.modes = [
                DreoHeaterMode.COOLAIR,
                DreoHeaterMode.HOTAIR,
                DreoHeaterMode.ECO,
                DreoHeaterMode.OFF,
            ]


# Supported prefixes.
# These prefixes will be listed along with the models in the below collections.
SUPPORTED_MODEL_PREFIXES = {
    "DR-HTF",
    "DR-HAF",
    "DR-HAP",
    "DR-HPF",
    "DR-HCF",
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
        # Note: Fan preset_modes use tuple format (name, value) despite type annotation.
        # This is required for fans that map preset names to numeric mode values.
        preset_modes=[
            ("normal", 1),
            ("auto", 2),
            ("sleep", 3),
            ("natural", 4),
            ("turbo", 5)
        ],
        device_ranges={
            SPEED_RANGE: (1, 9), 
            VERTICAL_ANGLE_RANGE: (-30, 90)
        }),

    "DR-HPF007S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        device_ranges={
            SPEED_RANGE: (1, 10),
            HORIZONTAL_ANGLE_RANGE: (-75,75),
            VERTICAL_ANGLE_RANGE: (-30,90)
        }),
    
    "DR-HPF005S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        device_ranges={
            SPEED_RANGE: (1, 10),
            HORIZONTAL_ANGLE_RANGE: (-60, 60)
        }),

    # Ceiling Fans
    "DR-HCF": DreoDeviceDetails(device_type=DreoDeviceType.CEILING_FAN),
    
    "DR-HCF002S": DreoDeviceDetails(
        device_type=DreoDeviceType.CEILING_FAN,
        device_ranges={
            SPEED_RANGE: (1, 12)
        }),

    # Air Purifiers
    "DR-HAP": DreoDeviceDetails(device_type=DreoDeviceType.AIR_PURIFIER),

    # Heaters
    "DR-HSH017BS": DreoHeaterDeviceDetails(
        device_ranges={
            ECOLEVEL_RANGE: (41, 85)
        },
    ),
    "DR-HSH003S": DreoHeaterDeviceDetails(
        device_ranges={
            ECOLEVEL_RANGE: (41, 85)
        },
        swing_modes=[SWING_OFF, SWING_ON],
    ),    
    "DR-HSH004S": DreoHeaterDeviceDetails(
        device_ranges={
            ECOLEVEL_RANGE: (41, 85)
        },
        swing_modes=[SWING_OFF, SWING_ON],
    ),
    "DR-HSH006S": DreoHeaterDeviceDetails(
        swing_modes=[SWING_OFF, SWING_ON],
    ),
    "DR-HSH009S": DreoHeaterDeviceDetails(
        swing_modes=[
            HeaterOscillationAngles.OSC,
            HeaterOscillationAngles.SIXTY,
            HeaterOscillationAngles.NINETY,
            HeaterOscillationAngles.ONE_TWENTY,
        ],
    ),
    "DR-HSH009AS": DreoHeaterDeviceDetails(
        swing_modes=[
            HeaterOscillationAngles.OSC,
            HeaterOscillationAngles.SIXTY,
            HeaterOscillationAngles.NINETY,
            HeaterOscillationAngles.ONE_TWENTY,
        ],
    ),
    "DR-HSH017S": DreoHeaterDeviceDetails(
        swing_modes=[SWING_OFF, SWING_ON],
    ),
    "DR-HSH034S": DreoHeaterDeviceDetails(
        swing_modes=[
            HeaterOscillationAngles.OSC,
            HeaterOscillationAngles.SIXTY,
            HeaterOscillationAngles.NINETY,
            HeaterOscillationAngles.ONE_TWENTY,
        ],
    ),
    "DR-HSH010S": DreoHeaterDeviceDetails(),

    # Are these even used?  They don't show up as model numbers.  Should they be a DR prefix?
    "WH714S": DreoHeaterDeviceDetails(
        swing_modes=[
            HeaterOscillationAngles.OSC,
            HeaterOscillationAngles.SIXTY,
            HeaterOscillationAngles.NINETY,
            HeaterOscillationAngles.ONE_TWENTY,
        ],
    ),
    "WH719S": DreoHeaterDeviceDetails(
        swing_modes=[
            HeaterOscillationAngles.OSC,
            HeaterOscillationAngles.SIXTY,
            HeaterOscillationAngles.NINETY,
            HeaterOscillationAngles.ONE_TWENTY,
        ],
    ),
    "WH739S": DreoHeaterDeviceDetails(
        swing_modes=[
            HeaterOscillationAngles.OSC,
            HeaterOscillationAngles.SIXTY,
            HeaterOscillationAngles.NINETY,
            HeaterOscillationAngles.ONE_TWENTY,
        ],
    ),

    # Air Conditioners
    # Note we had HAC-005S and HAC-006S in the list but they are identical.
    "DR-HAC": DreoACDeviceDetails(
        device_ranges={
            TEMP_RANGE: (60, 86),
            TARGET_TEMP_RANGE: (64, 86),
            TARGET_TEMP_RANGE_ECO: (75, 86),
            HUMIDITY_RANGE: (30, 80),
        },
        modes=[DreoACMode.COOL,
               DreoACMode.DRY,
               DreoACMode.FAN,
               DreoACMode.ECO,
               DreoACMode.SLEEP],
        swing_modes=[SWING_OFF, SWING_ON],
        fan_modes=[DreoACFanMode.AUTO, 
                   DreoACFanMode.LOW, 
                   DreoACFanMode.MEDIUM, 
                   DreoACFanMode.HIGH],
    ),

    "DR-KCM001S": DreoDeviceDetails(
        device_type=DreoDeviceType.CHEF_MAKER,
        cooking_modes=COOKING_MODES,
        cooking_range=COOKING_RANGES,
    ),

    "DR-HHM": DreoDeviceDetails(device_type=DreoDeviceType.HUMIDIFIER),

    # Dehumidifiers
        "DR-HDH001S": DreoDeviceDetails(
        device_type=DreoDeviceType.DEHUMIDIFIER,
        device_ranges={
            HUMIDITY_RANGE: (30, 85),
            SPEED_RANGE: (1, 3)
        }
    ),

    "DR-HDH002S": DreoDeviceDetails(
        device_type=DreoDeviceType.DEHUMIDIFIER,
        device_ranges={
            HUMIDITY_RANGE: (30, 85),
            SPEED_RANGE: (1, 3)
        }
    ),

    # Evaporative Coolers
    "DR-HEC": DreoDeviceDetails(
        device_type=DreoDeviceType.EVAPORATIVE_COOLER,
        device_ranges={
            SPEED_RANGE: (1, 4)
        },
    )
}
