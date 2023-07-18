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
    preset_modes: list[str]
    speed_range: tuple[int, int]


SUPPORTED_TOWER_FANS = {
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
    "DR-HTF007S": DreoFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        speed_range=(1, 4),
    ),
    "DR-HTF008S": DreoFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        speed_range=(1, 5),
    ),
}

SUPPORTED_AIR_CIRCULATOR_FANS = {
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
    )    
}
