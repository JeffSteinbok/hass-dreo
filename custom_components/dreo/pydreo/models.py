"""Supported device models for the PyDreo library."""
from dataclasses import dataclass

from .constant import (
    FAN_MODE_AUTO,
    FAN_MODE_NATURAL,
    FAN_MODE_NORMAL,
    FAN_MODE_SLEEP,
    FAN_MODE_TURBO,
)

@dataclass
class DreoFanDetails:
    """Represents a Dreo Fan model and capabilities"""

    preset_modes: list[str] 
    """List of possible preset mode names"""

    speed_range: tuple[int, int]
    """Supported speed levels, starting from 1"""

SUPPORTED_FANS = {
    "DR-HTF001S": DreoFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        speed_range=(1, 6),
    ),
    "DR-HTF002S": DreoFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        speed_range=(1, 6),
    ),
    "DR-HTF004S": DreoFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        speed_range=(1, 12),
    ),
    "DR-HTF005S": DreoFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        speed_range=(1, 9),
    ),
    "DR-HTF007S": DreoFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        speed_range=(1, 4),
    ),
    "DR-HTF008S": DreoFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        speed_range=(1, 5),
    ),    
    "DR-HAF001S": DreoFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO, FAN_MODE_TURBO],
        speed_range=(1, 4)
    ),    
    "DR-HAF003S": DreoFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO, FAN_MODE_TURBO],
        speed_range=(1, 8)
    ),
    "DR-HAF004S": DreoFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO, FAN_MODE_TURBO],
        speed_range=(1, 9)
    ),
}
