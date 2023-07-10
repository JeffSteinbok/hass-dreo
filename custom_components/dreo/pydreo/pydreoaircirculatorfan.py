import logging
from typing import Dict
from typing import TYPE_CHECKING

from .pydreobasedevice import PyDreoBaseDevice, UnknownModelError
from .models import SUPPORTED_AIR_CIRCULATOR_FANS
from .constant import (
    AIR_CIRCULATOR_WIND_MODE_KEY,
    HORIZONTAL_OSCILLATION_ANGLE_KEY,
    HORIZONTAL_OSCILLATION_KEY,
    LOGGER_NAME,
    POWERON_KEY,
    PRESET_MODES_KEY,
    SPEED_RANGE_KEY,
    STATE_KEY,
    TEMPERATURE_KEY,
    VERTICAL_OSCILLATION_ANGLE_KEY,
    VERTICAL_OSCILLATION_KEY,
    WINDLEVEL_KEY,
    WINDTYPE_KEY,
)


if TYPE_CHECKING:
    from pydreo import PyDreo

_LOGGER = logging.getLogger(LOGGER_NAME)


class PyDreoAirCirculatorFan(PyDreoBaseDevice):
    """Base class for Dreo Air Circulator Fan API Calls."""

    def __init__(self, details: Dict[str, list], dreo: "PyDreo") -> None:
        """Initialize air devices."""
        super().__init__(details, dreo)

        if self.model not in SUPPORTED_AIR_CIRCULATOR_FANS:
            raise UnknownModelError(self.model)

        fan_details = SUPPORTED_AIR_CIRCULATOR_FANS[self.model]

        self._speed_range = fan_details.speed_range
        self._preset_modes = fan_details.preset_modes

        self._horizontal_oscillation_angles = fan_details.horizontal_oscillation_angles
        self._vertical_oscillation_angles = fan_details.vertical_oscillation_angles

    def handle_server_update(self, message):
        _LOGGER.debug("{}: got {} message **".format(self.name, message))

        valPoweron = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(valPoweron, bool):
            self._is_on = valPoweron

        valWindMode = self.get_server_update_key_value(
            message, AIR_CIRCULATOR_WIND_MODE_KEY
        )
        if isinstance(valWindMode, int):
            self._windMode = valWindMode

        # HAVE TO FIGURE OUT HOW TO DO THE MAPPING EXACTLY
        valWindLevel = self.get_server_update_key_value(message, WINDLEVEL_KEY)
        if isinstance(valWindLevel, int):
            self._fan_speed = valWindLevel

        valTemperature = self.get_server_update_key_value(message, TEMPERATURE_KEY)
        if isinstance(valTemperature, int):
            self._temperature = valTemperature

        valHorizontalOscillation = self.get_server_update_key_value(
            message, HORIZONTAL_OSCILLATION_KEY
        )
        if isinstance(valHorizontalOscillation, bool):
            self._horizontally_oscillating = valHorizontalOscillation

        valVerticalOscillation = self.get_server_update_key_value(
            message, VERTICAL_OSCILLATION_KEY
        )
        if isinstance(valVerticalOscillation, bool):
            self._vertically_oscillating = valVerticalOscillation

    @property
    def speed_range(self):
        return self._speed_range

    @property
    def preset_modes(self):
        return self._preset_modes

    @property
    def is_on(self):
        """Returns `True` if the device is on, `False` otherwise."""
        return self._is_on

    @property
    def fan_speed(self):
        return self._fan_speed

    @property
    def preset_mode(self):
        return self.preset_modes[self._windType - 1]

    @property
    def temperature(self):
        return self._temperature

    @property
    def oscillating(self):
        return self._horizontally_oscillating or self._vertically_oscillating

    @property
    def horizontally_oscillating(self):
        return self._horizontally_oscillating

    @property
    def vertically_oscillating(self):
        return self._vertically_oscillating

    def supports_horizontal_oscillation(self):
        return self._horizontally_oscillating is not None

    def supports_vertical_oscillation(self) -> bool:
        return self._vertically_oscillating is not None

    def supported_horizontal_oscillation_angles(self) -> dict[str, int] | None:
        return self._horizontal_oscillation_angles

    def supported_vertical_oscillation_angles(self) -> dict[str, int] | None:
        return self._vertical_oscillation_angles

    def oscillate_horizontally(self, oscillating: bool) -> None:
        _LOGGER.debug("PyDreoAirCirculatorFan:oscillate_horizontally")
        self._send_command(HORIZONTAL_OSCILLATION_KEY, oscillating)

    def update_state(self, state: dict):
        _LOGGER.debug("PyDreoAirCirculatorFan:update_state")
        super().update_state(state)
        self._fan_speed = state[WINDLEVEL_KEY][STATE_KEY]
        self._windType = state[AIR_CIRCULATOR_WIND_MODE_KEY][STATE_KEY]
        self._temperature = state[TEMPERATURE_KEY][STATE_KEY]
        self._horizontally_oscillating = state[HORIZONTAL_OSCILLATION_KEY][STATE_KEY]
        self._vertically_oscillating = state[VERTICAL_OSCILLATION_KEY][STATE_KEY]

    def set_power(self, value: bool):
        _LOGGER.debug("PyDreoAirCirculatorFan:set_power")
        self._send_command(POWERON_KEY, value)

    def set_preset_mode(self, preset_mode: str):
        _LOGGER.debug("PyDreoAirCirculatorFan:set_preset_mode")
        if preset_mode in self.preset_modes:
            self._send_command(WINDTYPE_KEY, self._preset_modes.index(preset_mode) + 1)
        else:
            _LOGGER.error(
                "Preset mode %s is not in the acceptable list: %s",
                preset_mode,
                self._preset_modes,
            )

    def change_fan_speed(self, fan_speed: int):
        _LOGGER.debug("PyDreoAirCirculatorFan:change_fan_speed")
        if fan_speed >= self._speed_range[0] and fan_speed <= self._speed_range[1]:
            self._send_command(WINDLEVEL_KEY, fan_speed)
        else:
            _LOGGER.error(
                "Fan speed %s is not in the acceptable range: %s",
                fan_speed,
                self._speed_range,
            )

    # NOTE: some of these fans can oscillate horizontally and vertically
    # since HA's fan entity only supports a single oscillation option,
    # this method prefers horizontal oscillation over vertical oscillation
    # when present.
    def oscillate(self, oscillating: bool) -> None:
        _LOGGER.debug("PyDreoAirCirculatorFan:oscillate")
        if self.supports_horizontal_oscillation():
            self.oscillate_horizontally(oscillating)
        elif self.supports_vertical_oscillation():
            self.oscillate_vertically(oscillating)
        else:
            _LOGGER.error("This device does not support oscillation")

    def oscillate_vertically(self, oscillating: bool) -> None:
        _LOGGER.debug("PyDreoAirCirculatorFan:oscillate_vertically")
        self._send_command(VERTICAL_OSCILLATION_KEY, oscillating)

    def set_horizontal_oscillation_angle(self, angle: int) -> None:
        _LOGGER.debug("PyDreoAirCirculatorFan:set_horizontal_oscillation_angle")
        if not self.supports_horizontal_oscillation():
            _LOGGER.error("This device does not support horizontal oscillation")
            return

        if (
            self_horizontal_oscillation_angles is not None
            and angle in self._horizontal_oscillation_angles.values()
        ):
            self._send_command(HORIZONTAL_OSCILLATION_ANGLE_KEY, angle)
        else:
            _LOGGER.error(
                "Angle %s is not supported for this device, supported angles are: %s",
                angle,
                self._horizontal_oscillation_angles,
            )

    def set_vertical_oscillation_angle(self, angle: int) -> None:
        _LOGGER.debug("PyDreoAirCirculatorFan:set_vertical_oscillation_angle")
        if not self.supports_vertical_oscillation():
            _LOGGER.error("This device does not support vertical oscillation")
            return

        if (
            self_vertical_oscillation_angles is not None
            and angle in self._vertical_oscillation_angles.values()
        ):
            self._send_command(VERTICAL_OSCILLATION_ANGLE_KEY, angle)
        else:
            _LOGGER.error(
                "Angle %s is not supported for this device, supported angles are: %s",
                angle,
                self._vertical_oscillation_angles,
            )
            return
