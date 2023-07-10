from dataclasses import dataclass

from .constant import (
    FAN_MODE_AUTO,
    FAN_MODE_NATURAL,
    FAN_MODE_NORMAL,
    FAN_MODE_SLEEP,
    FAN_MODE_TURBO,
)


@dataclass
class TowerFanDetails:
    preset_modes: list[str]
    speed_range: tuple[int, int]


@dataclass
class AirCirculatorFanDetails(TowerFanDetails):
    horizontal_oscillation_angles: dict[str, int] | None
    vertical_oscillation_angles: dict[str, int] | None


SUPPORTED_TOWER_FANS = {
    "DR-HTF001S": TowerFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        speed_range=(1, 6),
    ),
    "DR-HTF002S": TowerFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        speed_range=(1, 6),
    ),
    "DR-HTF004S": TowerFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        speed_range=(1, 12),
    ),
    "DR-HTF007S": TowerFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        speed_range=(1, 4),
    ),
    "DR-HTF008S": TowerFanDetails(
        preset_modes=[FAN_MODE_NORMAL, FAN_MODE_NATURAL, FAN_MODE_SLEEP, FAN_MODE_AUTO],
        speed_range=(1, 5),
    ),
}

SUPPORTED_AIR_CIRCULATOR_FANS = {
    "DR-HAF003S": AirCirculatorFanDetails(
        preset_modes=[
            FAN_MODE_NORMAL,
            FAN_MODE_NATURAL,
            FAN_MODE_SLEEP,
            FAN_MODE_AUTO,
            FAN_MODE_TURBO,
        ],
        speed_range=(1, 8),
        horizontal_oscillation_angles={
            "30": 30,
            "60": 60,
            "90": 90,
            "120": 120,
        },
        vertical_oscillation_angles={
            # The Dreo App labels the vertical oscillation angles as 45, 75, and 105,
            # but sends values 30, 60, and 90 respectively
            "45": 30,
            "75": 60,
            "105": 90,
        },
    ),
}
