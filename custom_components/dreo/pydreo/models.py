"""Supported device models for the PyDreo library."""

from dataclasses import dataclass
from typing import Callable

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
    DreoACFanMode,
    POWERON_KEY,
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

    device_ranges: dict[str, tuple]
    """Dictionary of different ranges"""

    mode_names: list[str] | dict
    """List or dictionary of possible device mode names"""

    swing_modes: list[str]
    """List of possible swing modes"""

    cooking_modes: list[str]
    """List of possible cooking modes"""

    cooking_range: dict
    """Dictionary of different cooking ranges"""

    override_fn: Callable | None
    """Optional function called once after initial state load to apply hardware-specific overrides."""

    ambient_light_levels: tuple | None
    """Valid rgblevel values for the ambient light ring. None = not set (use default).
    Examples: (0, 2) = off/full only, (0, 1, 2) = off/low/full."""

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
        override_fn: Callable | None = None,
        ambient_light_levels: tuple | None = None,
    ):
        if device_type is None:
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
        self.override_fn = override_fn
        self.ambient_light_levels = ambient_light_levels


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

    def __init__(self, device_ranges: dict = None, modes: list[DreoHeaterMode] = None, swing_modes: list[str] = None):
        # Set default ranges if not provided
        if device_ranges is None:
            device_ranges = {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)}
        else:
            # Merge provided ranges with defaults
            default_ranges = {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)}
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
SUPPORTED_MODEL_PREFIXES = {"DR-HTF", "DR-HAF", "DR-HAP", "DR-HPF", "DR-HCF", "WH", "DR-HAC", "DR-HHM", "DR-HEC"}

# MCU hardware model strings used to identify specific hardware revisions.
_MCU_HAF004S_OLD_REV = "SC95F8613B"
_MCU_HTF007S_OLD_REV = ("CMS89F7518", "CMS89F7518/EUR", "CMS89F7518/USA")
_MCU_HAP003S_AUTO_SILENT_REV = "midea"


def _haf004s_mcu_override(device) -> None:
    """Restrict vertical angle range to (0, 90) for DR-HAF004S units with the SC95F8613B MCU.

    Older hardware revisions using this chip cannot physically reach negative vertical
    angles.  Newer revisions report a different chip string and use the full range
    parsed from the API, so this function intentionally leaves them untouched.
    """
    if device.raw_state is None:
        return
    mixed = device.raw_state.get("data", {}).get("mixed", {})
    mcu_obj = mixed.get("mcu_hardware_model", {})
    mcu_model = mcu_obj.get("state", "") if isinstance(mcu_obj, dict) else ""
    if mcu_model == _MCU_HAF004S_OLD_REV:
        device._vertical_angle_range = (0, 90)  # pylint: disable=protected-access


def _htf007s_mcu_override(device) -> None:
    """Restrict speed range to (1, 4) for DR-HTF007S units with CMS89F7518 MCU variants.

    Older hardware revisions of the Nomad One S using CMS89F7518 (bare), CMS89F7518/EUR,
    or CMS89F7518/USA only support 4 speed steps. Newer revisions report a different chip
    string and support 8 speed steps, so this function intentionally leaves them untouched.
    """
    if device.raw_state is None:
        return
    mixed = device.raw_state.get("data", {}).get("mixed", {})
    mcu_obj = mixed.get("mcu_hardware_model", {})
    mcu_model = mcu_obj.get("state", "") if isinstance(mcu_obj, dict) else ""
    if mcu_model in _MCU_HTF007S_OLD_REV:
        device._speed_range = (1, 4)  # pylint: disable=protected-access


def _hap003s_mcu_override(device) -> None:
    """Enable auto-silent command remapping for DR-HAP003S units with the "midea" MCU.

    A newer hardware revision of the Macro Max S/AS uses a "midea" MCU that rejects the
    plain "auto" mode command string.  These units require "auto-silent" to be sent instead.
    Units with a different MCU (e.g. "meidi") accept "auto" directly and are left untouched.
    """
    if device.raw_state is None:
        return
    mixed = device.raw_state.get("data", {}).get("mixed", {})
    mcu_obj = mixed.get("mcu_hardware_model", {})
    mcu_model = mcu_obj.get("state", "") if isinstance(mcu_obj, dict) else ""
    if mcu_model == _MCU_HAP003S_AUTO_SILENT_REV:
        device._auto_mode_uses_auto_silent = True  # pylint: disable=protected-access


SUPPORTED_DEVICES = {
    # Tower Fans
    "DR-HTF": DreoDeviceDetails(device_type=DreoDeviceType.TOWER_FAN),
    "DR-HTF007S": DreoDeviceDetails(
        device_type=DreoDeviceType.TOWER_FAN,
        preset_modes=[
            ("normal", 1),
            ("natural", 2),
            ("sleep", 3),
            ("auto", 4),
        ],
        # Newer hardware revision (default): 8 speed steps.
        # Older revision (_MCU_HTF007S_OLD_REV MCU): restricted to 4 by _htf007s_mcu_override.
        device_ranges={SPEED_RANGE: (1, 8)},
        override_fn=_htf007s_mcu_override,
    ),
    "DR-HTF011S": DreoDeviceDetails(
        device_type=DreoDeviceType.TOWER_FAN,
        preset_modes=[
            ("normal", 1),
            ("natural", 2),
            ("sleep", 3),
            ("auto", 4),
        ],
        device_ranges={SPEED_RANGE: (1, 9)},
    ),
    "DR-HTF018S": DreoDeviceDetails(
        device_type=DreoDeviceType.TOWER_FAN,
        preset_modes=[
            ("normal", 1),
            ("natural", 2),
            ("sleep", 3),
            ("auto", 4),
        ],
        device_ranges={SPEED_RANGE: (1, 9)},
    ),
    "DR-HTF017S": DreoDeviceDetails(
        device_type=DreoDeviceType.TOWER_FAN,
        preset_modes=[
            ("normal", 1),
            ("natural", 2),
            ("sleep", 3),
            ("auto", 4),
        ],
        device_ranges={SPEED_RANGE: (1, 4)},
    ),
    "DR-HTF024S": DreoDeviceDetails(
        device_type=DreoDeviceType.TOWER_FAN,
        preset_modes=[
            ("normal", 1),
            ("natural", 2),
            ("sleep", 3),
            ("auto", 4),
        ],
        device_ranges={SPEED_RANGE: (1, 9)},
    ),
    "DR-HTF021S": DreoDeviceDetails(
        device_type=DreoDeviceType.TOWER_FAN,
        preset_modes=[
            ("normal", 1),
            ("natural", 2),
            ("sleep", 3),
            ("auto", 4),
        ],
        device_ranges={SPEED_RANGE: (1, 12)},
    ),
    "DR-HTF518S": DreoDeviceDetails(
        device_type=DreoDeviceType.TOWER_FAN,
        preset_modes=[
            ("normal", 1),
            ("natural", 2),
            ("sleep", 3),
            ("auto", 4),
        ],
        device_ranges={SPEED_RANGE: (1, 9)},
    ),
    # Air Circulators
    "DR-HAF": DreoDeviceDetails(device_type=DreoDeviceType.AIR_CIRCULATOR),
    # DR-HAF001S: The API may return controlsConf with only a template reference,
    # so preset_modes and speed_range are hardcoded here to ensure full functionality.
    "DR-HAF001S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        preset_modes=[("normal", 1), ("natural", 2), ("sleep", 3), ("auto", 4)],
        device_ranges={SPEED_RANGE: (1, 4)},
    ),
    "DR-HAF004S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        override_fn=_haf004s_mcu_override,
    ),
    "DR-HAF008S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        preset_modes=[("normal", 1), ("natural", 2), ("sleep", 3), ("auto", 4), ("turbo", 5)],
        device_ranges={SPEED_RANGE: (1, 9)},
    ),
    "DR-HPF": DreoDeviceDetails(device_type=DreoDeviceType.AIR_CIRCULATOR),
    # HPF-series devices: The API returns controlsConf with only a template reference
    # (e.g. {"template": "DR-HPF002S"}) and no control/schedule.modes data, so
    # parse_preset_modes() cannot auto-detect modes. Preset modes must be hardcoded here.
    # TODO: Investigate whether the official Dreo Open API provides full controlsConf
    # data that would allow auto-detection of preset modes for these devices.
    "DR-HPF008S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        # Note: Fan preset_modes use tuple format (name, value) despite type annotation.
        # This is required for fans that map preset names to numeric mode values.
        preset_modes=[("normal", 1), ("auto", 2), ("sleep", 3), ("natural", 4), ("turbo", 5)],
        device_ranges={SPEED_RANGE: (1, 9), VERTICAL_ANGLE_RANGE: (-30, 90), "atm_brightness_range": (1, 3)},
    ),
    "DR-HPF015S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        preset_modes=[("normal", 1), ("auto", 2), ("sleep", 3), ("natural", 4), ("turbo", 5), ("custom", 6)],
        device_ranges={SPEED_RANGE: (1, 12), HORIZONTAL_ANGLE_RANGE: (-75, 75), VERTICAL_ANGLE_RANGE: (-10, 90)},
    ),
    "DR-HPF017S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        preset_modes=[("normal", 1), ("auto", 2), ("sleep", 3), ("natural", 4), ("turbo", 5), ("custom", 6)],
        device_ranges={SPEED_RANGE: (1, 12), HORIZONTAL_ANGLE_RANGE: (-75, 75), VERTICAL_ANGLE_RANGE: (-30, 90)},
    ),
    "DR-HPF007S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        preset_modes=[("normal", 1), ("natural", 2), ("sleep", 3), ("auto", 4), ("turbo", 5), ("custom", 6)],
        device_ranges={SPEED_RANGE: (1, 10), HORIZONTAL_ANGLE_RANGE: (-75, 75), VERTICAL_ANGLE_RANGE: (-30, 90)},
    ),
    "DR-HPF005S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        preset_modes=[("normal", 1), ("natural", 2), ("sleep", 3), ("auto", 4), ("turbo", 5), ("custom", 6)],
        device_ranges={SPEED_RANGE: (1, 10), HORIZONTAL_ANGLE_RANGE: (-60, 60)},
    ),
    "DR-HPF020S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        preset_modes=[("normal", 1), ("auto", 2), ("sleep", 3), ("natural", 4), ("turbo", 5), ("custom", 6)],
        device_ranges={SPEED_RANGE: (1, 9), HORIZONTAL_ANGLE_RANGE: (-60, 60), VERTICAL_ANGLE_RANGE: (-30, 90)},
    ),
    "DR-HPF022S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        preset_modes=[("normal", 1), ("natural", 2), ("sleep", 3), ("auto", 4), ("turbo", 5)],
        device_ranges={SPEED_RANGE: (1, 9), HORIZONTAL_ANGLE_RANGE: (-60, 60), VERTICAL_ANGLE_RANGE: (-30, 90)},
    ),
    "DR-HPF025S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        preset_modes=[("normal", 1), ("auto", 2), ("sleep", 3), ("natural", 4), ("turbo", 5)],
        device_ranges={SPEED_RANGE: (1, 9), HORIZONTAL_ANGLE_RANGE: (-60, 60), VERTICAL_ANGLE_RANGE: (-30, 90)},
    ),
    "DR-HPF004S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_CIRCULATOR,
        preset_modes=[("normal", 1), ("natural", 2), ("sleep", 3), ("auto", 4), ("turbo", 5), ("custom", 6)],
        device_ranges={SPEED_RANGE: (1, 9), HORIZONTAL_ANGLE_RANGE: (-75, 75), VERTICAL_ANGLE_RANGE: (-30, 90)},
    ),
    # Ceiling Fans
    "DR-HCF": DreoDeviceDetails(device_type=DreoDeviceType.CEILING_FAN),
    "DR-HCF001S": DreoDeviceDetails(
        device_type=DreoDeviceType.CEILING_FAN,
        preset_modes=[("normal", 1), ("natural", 2), ("sleep", 3), ("reverse", 4)],
        device_ranges={SPEED_RANGE: (1, 12)},
    ),
    "DR-HCF002S": DreoDeviceDetails(device_type=DreoDeviceType.CEILING_FAN, device_ranges={SPEED_RANGE: (1, 12)}),
    "DR-HCF007S": DreoDeviceDetails(
        device_type=DreoDeviceType.CEILING_FAN,
        preset_modes=[("normal", 1), ("natural", 2), ("sleep", 3), ("reverse", 4)],
        device_ranges={SPEED_RANGE: (1, 12), "atm_brightness_range": (1, 100), "rgb_effect_range": (0, 7), "supports_direct_rgb_color": True},
    ),
    "DR-HCF521S": DreoDeviceDetails(device_type=DreoDeviceType.CEILING_FAN, device_ranges={SPEED_RANGE: (1, 12)}),
    # Air Purifiers
    "DR-HAP": DreoDeviceDetails(device_type=DreoDeviceType.AIR_PURIFIER),
    "DR-HAP003S": DreoDeviceDetails(
        device_type=DreoDeviceType.AIR_PURIFIER,
        # Newer hardware revision ("midea" MCU, seriesName "Macro Max S/AS") rejects the plain
        # "auto" mode command and requires "auto-silent" instead.  The override sets a flag on
        # the device instance so PyDreoAirPurifier._send_command can remap the command value.
        # The original revision ("meidi" MCU, seriesName "Macro Max S") is left untouched.
        override_fn=_hap003s_mcu_override,
    ),
    # Heaters
    "DR-HSH017BS": DreoHeaterDeviceDetails(
        device_ranges={ECOLEVEL_RANGE: (41, 85)},
    ),
    "DR-HSH003S": DreoHeaterDeviceDetails(
        swing_modes=[SWING_OFF, SWING_ON],
    ),
    "DR-HSH004S": DreoHeaterDeviceDetails(
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
    "DR-HSH011": DreoHeaterDeviceDetails(),
    "DR-HSH011S": DreoHeaterDeviceDetails(),
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
        modes=[DreoACMode.COOL, DreoACMode.DRY, DreoACMode.FAN, DreoACMode.ECO, DreoACMode.SLEEP],
        swing_modes=[SWING_OFF, SWING_ON],
        fan_modes=[DreoACFanMode.AUTO, DreoACFanMode.LOW, DreoACFanMode.MEDIUM, DreoACFanMode.HIGH],
    ),
    "DR-KCM001S": DreoDeviceDetails(
        device_type=DreoDeviceType.CHEF_MAKER,
        cooking_modes=COOKING_MODES,
        cooking_range=COOKING_RANGES,
    ),
    "DR-HHM": DreoDeviceDetails(device_type=DreoDeviceType.HUMIDIFIER, ambient_light_levels=(0, 2)),
    "DR-HHM003S": DreoDeviceDetails(
        device_type=DreoDeviceType.HUMIDIFIER,
        ambient_light_levels=(0, 1, 2),
    ),
    # DR-HHM015S (HM755S): supports rgbmode (0=humidity indicator, 1=fixed color),
    # rgbcolor, and rgbth (humidity thresholds).  Brightness is on/full only (no low level).
    "DR-HHM015S": DreoDeviceDetails(
        device_type=DreoDeviceType.HUMIDIFIER,
        ambient_light_levels=(0, 2),
    ),
    "DR-HHM014S": DreoDeviceDetails(
        device_type=DreoDeviceType.HUMIDIFIER,
        preset_modes=[
            ("normal", 0),
            ("auto", 1),
            ("sleep", 2),
        ],
    ),
    "DR-HHM005S": DreoDeviceDetails(
        device_type=DreoDeviceType.HUMIDIFIER,
        preset_modes=[
            ("auto", 1),
            ("normal", 0),
            ("sleep", 2),
        ],
    ),
    "DR-HHM006S": DreoDeviceDetails(
        device_type=DreoDeviceType.HUMIDIFIER,
        preset_modes=[
            ("normal", 0),
            ("auto", 1),
            ("sleep", 2),
        ],
    ),
    # Dehumidifiers
    "DR-HDH001S": DreoDeviceDetails(device_type=DreoDeviceType.DEHUMIDIFIER, device_ranges={HUMIDITY_RANGE: (30, 85), SPEED_RANGE: (1, 3)}),
    "DR-HDH002S": DreoDeviceDetails(device_type=DreoDeviceType.DEHUMIDIFIER, device_ranges={HUMIDITY_RANGE: (30, 85), SPEED_RANGE: (1, 3)}),
    "DR-HDH003S": DreoDeviceDetails(device_type=DreoDeviceType.DEHUMIDIFIER, device_ranges={HUMIDITY_RANGE: (30, 85), SPEED_RANGE: (1, 3)}),
    "DR-HDH005S": DreoDeviceDetails(device_type=DreoDeviceType.DEHUMIDIFIER, device_ranges={HUMIDITY_RANGE: (30, 85), SPEED_RANGE: (1, 3)}),
    # Evaporative Coolers
    "DR-HEC": DreoDeviceDetails(
        device_type=DreoDeviceType.EVAPORATIVE_COOLER,
        device_ranges={SPEED_RANGE: (1, 4)},
    ),
    # DR-HEC006S is the TurboCool Misting Fan 516S.
    # controlsConf is empty so speed range and preset modes must be hardcoded.
    # DR-HEC006S has +/-75° oscillation range and the turbo-mode is 4
    # Asymmetric horizontal oscillation is also supported with left/right angles
    "DR-HEC006S": DreoDeviceDetails(
        device_type=DreoDeviceType.EVAPORATIVE_COOLER,
        preset_modes=[("normal", 1), ("turbo", 4)],
        device_ranges={
            SPEED_RANGE: (1, 6),
            HORIZONTAL_ANGLE_RANGE: (-75, 75),
            "horizontal_osc_angle_left_range": (-75, 75),
            "horizontal_osc_angle_right_range": (-75, 75),
        },
    ),
    # DR-HEC005S is the TurboCool Misting Fan 765S.
    # It has 12 fan speeds and can expose an empty controlsConf.
    # Without an explicit mapping it falls back to generic DR-HEC defaults.
    "DR-HEC005S": DreoDeviceDetails(
        device_type=DreoDeviceType.EVAPORATIVE_COOLER,
        preset_modes=[("normal", 1), ("natural", 4), ("sleep", 3), ("auto", 2)],
        device_ranges={SPEED_RANGE: (1, 12), "fog_level_range": (1, 4)},
    ),
}
