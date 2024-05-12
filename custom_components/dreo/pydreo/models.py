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
    HeaterOscillationAngles
)

from homeassistant.components.climate import (
    SWING_ON,
    SWING_OFF
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

    def __init__(self, preset_modes: list[str], range: dict, hvac_modes: list[str] = None,
                 swing_modes: list[str] = None):
        self.preset_modes = preset_modes
        self.range = range
        self.hvac_modes = hvac_modes
        self.swing_modes = swing_modes


SUPPORTED_FANS = {
    "DR-HTF001S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range = {SPEED_RANGE: (1, 6)}
    ),
    "DR-HTF002S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range = {SPEED_RANGE: (1, 6)}
    ),
    "DR-HTF004S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range = {SPEED_RANGE: (1, 12)}
    ),
    "DR-HTF005S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range = {SPEED_RANGE: (1, 9)}
    ),
    "DR-HTF007S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range = {SPEED_RANGE: (1, 4)}
    ),
    "DR-HTF008S": DreoDeviceDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        range = {SPEED_RANGE: (1, 5)}
    ),   
    "DR-HTF009S": DreoDeviceDetails(
    preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
    range = {SPEED_RANGE: (1, 9)}
    ), 
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
    )
}


SUPPORTED_HEATERS = {
    "DR-HSH004S": DreoDeviceDetails(
        preset_modes=["H1", "H2", "H3"],
        range={
            HEAT_RANGE: (1,3),
            ECOLEVEL_RANGE: (41,85)
        },
        hvac_modes=[HEATER_MODE_COOLAIR, HEATER_MODE_HOTAIR, HEATER_MODE_ECO, HEATER_MODE_OFF],
        swing_modes = [SWING_OFF, SWING_ON]
    ),
    "DR-HSH009S": DreoDeviceDetails(
        preset_modes=["H1", "H2", "H3"],
        range={
            HEAT_RANGE: (1,3),
            ECOLEVEL_RANGE: (41,95)
        },
        hvac_modes=[HEATER_MODE_COOLAIR, HEATER_MODE_HOTAIR, HEATER_MODE_ECO, HEATER_MODE_OFF],
        swing_modes = [HeaterOscillationAngles.OSC, HeaterOscillationAngles.SIXTY, HeaterOscillationAngles.NINETY,
                       HeaterOscillationAngles.ONE_TWENTY]
    ),
    "DR-HSH009AS": DreoDeviceDetails(
        preset_modes=["H1", "H2", "H3"],
        range={
            HEAT_RANGE: (1, 3),
            ECOLEVEL_RANGE: (41, 95)
        },
        hvac_modes=[HEATER_MODE_COOLAIR, HEATER_MODE_HOTAIR, HEATER_MODE_ECO, HEATER_MODE_OFF],
        swing_modes=[HeaterOscillationAngles.OSC, HeaterOscillationAngles.SIXTY, HeaterOscillationAngles.NINETY,
                     HeaterOscillationAngles.ONE_TWENTY]
    ),
    "WH719S": DreoDeviceDetails(
        preset_modes=["H1", "H2", "H3"],
        range={
            HEAT_RANGE: (1,3),
            ECOLEVEL_RANGE: (41,95)
        },
        hvac_modes=[HEATER_MODE_COOLAIR, HEATER_MODE_HOTAIR, HEATER_MODE_ECO, HEATER_MODE_OFF],
        swing_modes = [HeaterOscillationAngles.OSC, HeaterOscillationAngles.SIXTY, HeaterOscillationAngles.NINETY,
                       HeaterOscillationAngles.ONE_TWENTY]
    ),
    "WH739S": DreoDeviceDetails(
        preset_modes=["H1", "H2", "H3"],
        range={
            HEAT_RANGE: (1,3),
            ECOLEVEL_RANGE: (41,95)
        },
        hvac_modes=[HEATER_MODE_COOLAIR, HEATER_MODE_HOTAIR, HEATER_MODE_ECO, HEATER_MODE_OFF],
        swing_modes = [HeaterOscillationAngles.OSC, HeaterOscillationAngles.SIXTY, HeaterOscillationAngles.NINETY,
                       HeaterOscillationAngles.ONE_TWENTY]
    )
}

SUPPORTED_DEVICES = [ 
    ("PyDreoFan", SUPPORTED_FANS), 
    ("PyDreoHeater", SUPPORTED_HEATERS)
]

