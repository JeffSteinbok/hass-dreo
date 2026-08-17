"""Dreo API for controling fans."""

import logging
import threading
import time
from typing import TYPE_CHECKING, Callable, Dict

from .constant import (
    HORIZONTAL_OSCILLATION_KEY,
    HORIZONTAL_OSCILLATION_ANGLE_KEY,
    HORIZONTAL_ANGLE_ADJ_KEY,
    VERTICAL_OSCILLATION_KEY,
    VERTICAL_OSCILLATION_ANGLE_KEY,
    CRUISECONF_KEY,
    MIN_OSC_ANGLE_DIFFERENCE,
    OSCMODE_KEY,
    FIXEDCONF_KEY,
    FIXEDCONF_SETTLE_SECONDS_KEY,
    OscillationMode,
    HORIZONTAL_ANGLE_RANGE,
    VERTICAL_ANGLE_RANGE,
    ATMON_KEY,
    ATMCOLOR_KEY,
    ATMBRI_KEY,
    ATMMODE_KEY,
    LIGHTON_KEY,
    HWFPON_KEY,
    HWFPANGLE_KEY,
    HBODYCNT_KEY,
    WINDTYPE_KEY,
    WIND_MODE_KEY,
)

from .commandoutbox import OutboxTiming
from .helpers import Helpers
from .pydreofanbase import PyDreoFanBase
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(__name__)

# Cloud control-reply can echo the requested fixedconf before the device moves.
# control-report is the later device confirmation and carries encoder updates,
# so it must remain authoritative along with method "report".
_FIXEDCONF_OPTIMISTIC_METHODS = frozenset({"control-reply"})

# Default: no inter-command settle (most air circulators handle rapid fixedconf).
# Models that need a longer interval set FIXEDCONF_SETTLE_SECONDS_KEY (float seconds)
# in SUPPORTED_DEVICES device_ranges (models.py).
_FIXEDCONF_SETTLE_SECONDS_DEFAULT = 0.0

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoAirCirculator(PyDreoFanBase):
    """Base class for Dreo Fan API Calls.

    Fixedconf settle threading (HA)
    --------------------------------
    Angle setters run on HA **executor** threads. When a model needs settle
    delay, ``_set_fixed_conf`` records the latest target and schedules send via
    ``PyDreo.schedule_call_later`` (HA: event-loop ``async_call_later``, then
    the settle body runs again on an **executor**). Shared fixedconf state is
    guarded by ``_fixed_conf_lock``; the lock is never held across waits.
    ``dispose()`` / unload cancel outstanding schedules.
    """

    # Opt out of command batching: ``_set_fixed_conf`` clears its in-flight
    # tracking in an ``except`` around ``_send_command`` and re-raises, which
    # only works while the send is synchronous. This class also paces itself
    # already via the fixedconf settle delay, so it gains nothing from the
    # outbox. See commandoutbox.OutboxTiming.
    _COMMAND_TIMING = OutboxTiming.IMMEDIATE

    @staticmethod
    def _clamp_rgb_tuple(rgb: tuple) -> tuple[int, int, int]:
        """Clamp RGB tuple values to 0-255 integers."""
        return tuple(max(0, min(255, int(round(c)))) for c in rgb)

    @staticmethod
    def _pack_rgb_to_int(rgb: tuple[int, int, int]) -> int:
        """Pack RGB tuple into 24-bit integer."""
        r, g, b = rgb
        return (r << 16) | (g << 8) | b

    @staticmethod
    def _unpack_int_to_rgb(color: int) -> tuple[int, int, int]:
        """Unpack 24-bit integer to RGB tuple."""
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        return (r, g, b)

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        super().__init__(device_definition, details, dreo)

        self._horizontal_angle_range = None
        # Check if the device has a horizontal angle range defined in the device definition
        # If not, parse the horizontal angle range from the details
        if device_definition.device_ranges is not None and HORIZONTAL_ANGLE_RANGE in device_definition.device_ranges:
            self._horizontal_angle_range = device_definition.device_ranges[HORIZONTAL_ANGLE_RANGE]
        if self._horizontal_angle_range is None:
            self._horizontal_angle_range = self.parse_swing_angle_range(details, "hor")

        self._vertical_angle_range = None
        # Check if the device has a vertical angle range defined in the device definition
        # If not, parse the vertical angle range from the details
        if device_definition.device_ranges is not None and VERTICAL_ANGLE_RANGE in device_definition.device_ranges:
            self._vertical_angle_range = device_definition.device_ranges[VERTICAL_ANGLE_RANGE]
        if self._vertical_angle_range is None:
            self._vertical_angle_range = self.parse_swing_angle_range(details, "ver")

        self._osc_mode = None
        self._cruise_conf = None
        self._fixed_conf = None
        self._angle_preset_options: list[str] = []
        # Last fixedconf value we commanded (for reject detection / logging)
        self._last_commanded_fixed_conf: str | None = None
        # Position reported when the last fixedconf command was sent (reject = snap-back)
        self._fixed_conf_at_command: str | None = None
        # Serialize fixedconf command state; never sleep while holding this lock.
        self._fixed_conf_lock = threading.Lock()
        # Serialize transport writes without blocking websocket state updates.
        self._fixed_conf_send_lock = threading.Lock()
        self._last_fixed_conf_command_time: float | None = None
        # Latest desired fixedconf when settle delays a send (coalesces rapid HA updates).
        self._pending_fixed_conf: str | None = None
        # Cancel handle from PyDreo.schedule_call_later (HA async_call_later or Timer).
        self._fixed_conf_cancel: Callable[[], None] | None = None
        # Set by dispose() so a delayed callback cannot send after unload.
        self._fixed_conf_disposed: bool = False
        # Model-specific settle from SUPPORTED_DEVICES; overridable in unit tests.
        settle = None
        if device_definition.device_ranges is not None:
            settle = device_definition.device_ranges.get(FIXEDCONF_SETTLE_SECONDS_KEY)
        self._fixed_conf_settle_seconds: float = (
            float(settle) if settle is not None else _FIXEDCONF_SETTLE_SECONDS_DEFAULT
        )

        self._horizontally_oscillating = None
        self._vertically_oscillating = None

        # Oscillation angle for older firmware (single angle value, not min/max range)
        self._horizontal_oscillation_angle = None
        self._vertical_oscillation_angle = None

        # Horizontal angle adjustment (simpler angle control, similar to Tower Fan)
        self._horizontal_angle_adj = None

        # Atmosphere (RGB) light support
        self._atm_light_on: bool = None
        self._atm_brightness: int = None
        self._atm_color: int = None
        self._atm_mode: int = None
        self._atm_brightness_range: tuple[int, int] = (1, 5)
        if device_definition.device_ranges is not None and "atm_brightness_range" in device_definition.device_ranges:
            self._atm_brightness_range = device_definition.device_ranges["atm_brightness_range"]

        # Panel/display light (e.g. DR-HPF015S)
        self._display_light: bool = None

        # Presence-based follow support (e.g. DR-HPF007S)
        self._follow_me: bool = None
        self._follow_me_angle: int = None
        self._people_detected: int = None

    def turn_on_with_preset_mode(self, preset_mode: str) -> None:
        """Atomically turn on the fan and select a preset mode."""
        if self._preset_modes is None:
            raise NotImplementedError("Attempting to set preset_mode on a device that doesn't support modes.")

        key = WINDTYPE_KEY if self._wind_type is not None else WIND_MODE_KEY if self._wind_mode is not None else None
        if key is None:
            raise NotImplementedError("Attempting to set preset_mode on a device that doesn't support wind type or wind mode keys.")

        numeric_value = Helpers.value_from_name(self._preset_modes, preset_mode)
        if numeric_value is None:
            raise ValueError(f"Preset mode {preset_mode} is not in the acceptable list: {self.preset_modes}")
        if self._power_on_key is None:
            raise NotImplementedError("Attempting to turn on a device with an unknown power key.")

        self._send_command_batch({self._power_on_key: True, key: numeric_value})

    def _uses_hangleadj_for_horizontal(self) -> bool:
        """Check if device uses hangleadj (simpler angle control) instead of hoscangle."""
        return self._horizontal_angle_adj is not None

    def _has_vertical_osc_angle_disabled(self) -> bool:
        """Check if vertical oscillation angle should be disabled (voscangle is 0 and device uses hangleadj)."""
        return self._horizontal_angle_adj is not None and self._vertical_oscillation_angle == 0

    @staticmethod
    def parse_swing_angle_range(details: Dict[str, list], direction: str) -> tuple[int, int] | None:
        """Parse the swing angle range from the details."""
        controls_conf = details.get("controlsConf", None)
        if controls_conf is None:
            return None

        swing_angle = controls_conf.get("swingAngle", None)
        if swing_angle is None:
            _LOGGER.debug("get_angle_range: no swing angle detected")
            return None

        fixed_angle = swing_angle.get("fixedAngle", None)
        if fixed_angle is None:
            _LOGGER.debug("get_angle_range: no fixed angle detected")
            return None

        angle = fixed_angle.get(direction + "Angle", None)
        zero_angle = fixed_angle.get(direction + "ZeroAngle", None)
        if angle is None or zero_angle is None:
            return None

        return -zero_angle, angle - zero_angle

    def parse_preset_modes(self, details: Dict[str, list]) -> tuple[str, int]:
        """Parse the preset modes from the details."""
        preset_modes = []
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            control = controls_conf.get("control", None)
            if control is not None:
                for control_item in control:
                    if control_item.get("type", None) == "Mode":
                        for mode_item in control_item.get("items", None):
                            text = self.get_mode_string(mode_item.get("text", None))
                            value = mode_item.get("value", None)
                            preset_modes.append((text, value))
            schedule = controls_conf.get("schedule", None)
            if schedule is not None:
                modes = schedule.get("modes", None)
                if modes is not None:
                    for mode_item in modes:
                        text = self.get_mode_string(mode_item.get("title", None))
                        value = mode_item.get("value", None)
                        if (text, value) not in preset_modes:
                            preset_modes.append((text, value))

        preset_modes.sort(key=lambda tup: tup[1])  # sorts in place
        if len(preset_modes) == 0:
            _LOGGER.debug("parse_preset_modes: No preset modes detected")
            preset_modes = None
        _LOGGER.debug("parse_preset_modes: Detected preset modes - %s", preset_modes)
        return preset_modes

    @property
    def horizontal_angle_range(self):
        """Get the horizontal swing angle range"""
        return self._horizontal_angle_range

    @property
    def vertical_angle_range(self):
        """Get the vertical swing angle range"""
        return self._vertical_angle_range

    @property
    def oscillating(self) -> bool:
        """Returns `True` if either horizontal or vertical oscillation is on."""
        if self._horizontally_oscillating is not None:
            if self._vertically_oscillating is not None:
                return self._horizontally_oscillating or self._vertically_oscillating
            return self._horizontally_oscillating
        if self._osc_mode is not None:
            return self._osc_mode != OscillationMode.OFF
        return None

    @oscillating.setter
    def oscillating(self, value: bool) -> None:
        """Enable or disable oscillation"""
        _LOGGER.debug("oscillating.setter: Setting oscillation")

        if self._horizontally_oscillating is not None:
            self.horizontally_oscillating = value
            self.vertically_oscillating = False
        elif self._osc_mode is not None:
            new_osc_mode = OscillationMode.HORIZONTAL if value else OscillationMode.OFF
            if self._osc_mode == new_osc_mode:
                _LOGGER.debug("oscillating.setter: value already %s, skipping command", value)
                return
            self._send_command(OSCMODE_KEY, new_osc_mode)
        else:
            raise NotImplementedError("Attempting to set oscillating on a device that doesn't support.")

    @property
    def horizontally_oscillating(self) -> bool:
        """Returns `True` if horizontal oscillation is on."""
        if self._horizontally_oscillating is not None:
            return self._horizontally_oscillating
        if self._osc_mode is not None:
            return (self._osc_mode & OscillationMode.HORIZONTAL) != OscillationMode.OFF

        # Note we do not consider a fan with JUST horizontal oscillation to have a seperate
        # horizontal oscillation switch.
        return None

    @horizontally_oscillating.setter
    def horizontally_oscillating(self, value: bool) -> None:
        """Enable or disable vertical oscillation"""
        _LOGGER.debug("horizontally_oscillating: horizontally_oscillating.setter: Setting horizontal oscillation")
        if self._horizontally_oscillating is not None:
            if self._horizontally_oscillating == value:
                _LOGGER.debug("oscillating.setter: value already %s, skipping command", value)
                return
            self._send_command(HORIZONTAL_OSCILLATION_KEY, value)
        elif self._osc_mode is not None:
            osc_computed = None
            if value:
                osc_computed = self._osc_mode | OscillationMode.HORIZONTAL
            else:
                osc_computed = self._osc_mode & ~OscillationMode.HORIZONTAL
            if self._osc_mode == osc_computed:
                _LOGGER.debug("horizontally_oscillating: horizontally_oscillating.setter: value already %s, skipping command", value)
                return
            self._send_command(OSCMODE_KEY, osc_computed)
        else:
            raise NotImplementedError("Horizontal oscillation is not supported.")

    @property
    def horizontal_osc_angle_left_range(self):
        """Get the left horizontal oscillation angle range."""
        return self.horizontal_angle_range

    @property
    def horizontal_osc_angle_right_range(self):
        """Get the right horizontal oscillation angle range."""
        return self.horizontal_angle_range

    @property
    def vertically_oscillating(self):
        """Returns `True` if vertical oscillation is on."""
        if self._vertically_oscillating is not None:
            return self._vertically_oscillating
        if self._osc_mode is not None:
            return self._osc_mode & OscillationMode.VERTICAL != OscillationMode.OFF

        return None

    @vertically_oscillating.setter
    def vertically_oscillating(self, value: bool) -> None:
        """Enable or disable vertical oscillation"""
        if self._horizontally_oscillating is not None:
            # hoscon/voscon device — send voscon command
            if self._vertically_oscillating == value:
                _LOGGER.debug("vertically_oscillating.setter: value already %s, skipping command", value)
                return
            self._send_command(VERTICAL_OSCILLATION_KEY, value)
        elif self._osc_mode is not None:
            osc_computed = None
            if value:
                osc_computed = self._osc_mode | OscillationMode.VERTICAL
            else:
                osc_computed = self._osc_mode & ~OscillationMode.VERTICAL
            if self._osc_mode == osc_computed:
                _LOGGER.debug("vertically_oscillating.setter: value already %s, skipping command", value)
                return
            self._send_command(OSCMODE_KEY, osc_computed)
        else:
            raise NotImplementedError("Vertical oscillation is not supported.")

    @property
    def vertical_osc_angle_top_range(self):
        """Get the top vertical oscillation angle range."""
        return self.vertical_angle_range

    @property
    def vertical_osc_angle_bottom_range(self):
        """Get the bottom vertical oscillation angle range."""
        return self.vertical_angle_range

    def set_horizontal_oscillation_angle(self, angle: int) -> None:
        """Set the horizontal oscillation angle."""
        _LOGGER.debug("set_horizontal_oscillation_angle: Setting angle to %s", angle)
        if self._horizontally_oscillating is None:
            raise NotImplementedError("This device does not support horizontal oscillation")

        self._send_command(HORIZONTAL_OSCILLATION_ANGLE_KEY, angle)

    def set_vertical_oscillation_angle(self, angle: int) -> None:
        """Set the vertical oscillation angle."""
        _LOGGER.debug("set_vertical_oscillation_angle: Setting angle to %s", angle)
        if self._vertically_oscillating is None:
            raise NotImplementedError("This device does not support vertical oscillation")

        self._send_command(VERTICAL_OSCILLATION_ANGLE_KEY, angle)

    @property
    def vertical_osc_angle_top(self) -> int:
        """Get the current top vertical oscillation angle."""
        if self._cruise_conf is not None:
            parts = self._cruise_conf.split(",")
            if len(parts) >= 4:
                return int(parts[0])
        return None

    @vertical_osc_angle_top.setter
    def vertical_osc_angle_top(self, value: int) -> None:
        """Set the top vertical oscillation angle."""
        _LOGGER.debug("vertical_osc_angle_top.setter: Setting top angle")
        if self._cruise_conf is not None:
            cruise_conf_values = self._cruise_conf.split(",")
            if len(cruise_conf_values) < 4:
                _LOGGER.warning("vertical_osc_angle_top: cruise_conf has unexpected format: %s", self._cruise_conf)
                return
            bottom_angle = int(cruise_conf_values[2])
            # 30 deg is the minimum top-bottom and left-right difference for the tested fan (DR-HAF003S)
            if value - bottom_angle < MIN_OSC_ANGLE_DIFFERENCE:
                raise ValueError(f"Top angle must be at least {MIN_OSC_ANGLE_DIFFERENCE} greater than bottom angle")
            # Note that HA seems to send this in as a float, so we need to convert to int just in case
            new_value = int(value)
            if int(cruise_conf_values[0]) == new_value:
                _LOGGER.debug("vertical_osc_angle_top: vertical_osc_angle_top - value already %s, skipping command", new_value)
                return
            cruise_conf_values[0] = new_value
            self._send_command(CRUISECONF_KEY, ",".join(map(str, cruise_conf_values)))

    @property
    def vertical_osc_angle_bottom(self) -> int:
        """Get the current bottom vertical oscillation angle."""
        if self._cruise_conf is not None:
            parts = self._cruise_conf.split(",")
            if len(parts) >= 4:
                return int(parts[2])
        return None

    @vertical_osc_angle_bottom.setter
    def vertical_osc_angle_bottom(self, value: int) -> None:
        """Set the bottom vertical oscillation angle."""
        _LOGGER.debug("vertical_osc_angle_bottom: vertical_osc_angle_bottom.setter: Setting bottom angle")
        if self._cruise_conf is not None:
            cruise_conf_values = self._cruise_conf.split(",")
            if len(cruise_conf_values) < 4:
                _LOGGER.warning("vertical_osc_angle_bottom: cruise_conf has unexpected format: %s", self._cruise_conf)
                return
            top_angle = int(cruise_conf_values[0])
            # 30 deg is the minimum top-bottom and left-right difference for the tested fan (DR-HAF003S)
            if top_angle - value < MIN_OSC_ANGLE_DIFFERENCE:
                raise ValueError(f"Bottom angle must be at least {MIN_OSC_ANGLE_DIFFERENCE} less than top angle")
            # Note that HA seems to send this in as a float, so we need to convert to int just in case
            new_value = int(value)
            if int(cruise_conf_values[2]) == new_value:
                _LOGGER.debug("vertical_osc_angle_bottom: vertical_osc_angle_bottom - value already %s, skipping command", new_value)
                return
            cruise_conf_values[2] = new_value
            self._send_command(CRUISECONF_KEY, ",".join(map(str, cruise_conf_values)))

    @property
    def horizontal_osc_angle_right(self) -> int:
        """Get the current right horizontal oscillation angle."""
        if self._cruise_conf is not None:
            parts = self._cruise_conf.split(",")
            if len(parts) >= 4:
                return int(parts[1])
        return None

    @horizontal_osc_angle_right.setter
    def horizontal_osc_angle_right(self, value: int) -> None:
        """Set the right horizontal oscillation angle."""
        _LOGGER.debug("horizontal_osc_angle_right: horizontal_osc_angle_right.setter: Setting right angle")
        if self._cruise_conf is not None:
            cruise_conf_values = self._cruise_conf.split(",")
            if len(cruise_conf_values) < 4:
                _LOGGER.warning("horizontal_osc_angle_right: cruise_conf has unexpected format: %s", self._cruise_conf)
                return
            left_angle = int(cruise_conf_values[3])
            # 30 deg is the minimum top-bottom and left-right difference for the tested fan (DR-HAF003S)
            if value - left_angle < MIN_OSC_ANGLE_DIFFERENCE:
                raise ValueError(f"Right angle must be at least {MIN_OSC_ANGLE_DIFFERENCE} greater than left angle")
            # Note that HA seems to send this in as a float, so we need to convert to int just in case
            new_value = int(value)
            if int(cruise_conf_values[1]) == new_value:
                _LOGGER.debug("horizontal_osc_angle_right: horizontal_osc_angle_right - value already %s, skipping command", new_value)
                return
            cruise_conf_values[1] = new_value
            self._send_command(CRUISECONF_KEY, ",".join(map(str, cruise_conf_values)))

    @property
    def horizontal_osc_angle_left(self) -> int:
        """Get the current left horizontal oscillation angle."""
        if self._cruise_conf is not None:
            parts = self._cruise_conf.split(",")
            if len(parts) >= 4:
                return int(parts[3])
        return None

    @horizontal_osc_angle_left.setter
    def horizontal_osc_angle_left(self, value: int) -> None:
        """Set the left horizontal oscillation angle."""
        _LOGGER.debug("horizontal_osc_angle_left: horizontal_osc_angle_left.setter: Setting left angle")
        if self._cruise_conf is not None:
            cruise_conf_values = self._cruise_conf.split(",")
            if len(cruise_conf_values) < 4:
                _LOGGER.warning("horizontal_osc_angle_left: cruise_conf has unexpected format: %s", self._cruise_conf)
                return
            right_angle = int(cruise_conf_values[1])
            # 30 deg is the minimum top-bottom and left-right difference for the tested fan (DR-HAF003S)
            if right_angle - value < MIN_OSC_ANGLE_DIFFERENCE:
                raise ValueError(f"Left angle must be at least {MIN_OSC_ANGLE_DIFFERENCE} less than right angle")
            # Note that HA seems to send this in as a float, so we need to convert to int just in case
            new_value = int(value)
            if int(cruise_conf_values[3]) == new_value:
                _LOGGER.debug("horizontal_osc_angle_left: horizontal_osc_angle_left.setter: value already %s, skipping command", new_value)
                return
            cruise_conf_values[3] = new_value
            self._send_command(CRUISECONF_KEY, ",".join(map(str, cruise_conf_values)))

    @property
    def horizontal_angle(self) -> int:
        """Get the current fixed horizontal angle."""
        # First check if hangleadj is available (simpler angle control)
        if self._horizontal_angle_adj is not None:
            return self._horizontal_angle_adj
        # Otherwise use fixedconf (more complex angle control)
        if self._fixed_conf is not None:
            return int(self._fixed_conf.split(",")[1])
        return None

    @staticmethod
    def _normalize_fixed_conf(value: str) -> str | None:
        """Normalize fixedconf strings to 'vertical,horizontal' format."""
        if not isinstance(value, str):
            return None
        parts = value.split(",")
        if len(parts) != 2:
            return None
        try:
            vertical = int(parts[0].strip())
            horizontal = int(parts[1].strip())
        except ValueError:
            return None
        return f"{vertical},{horizontal}"

    def _add_angle_preset_option(self, value: str | None) -> None:
        """Track fixedconf values as available 3D angle presets."""
        normalized = self._normalize_fixed_conf(value)
        if normalized is not None and normalized not in self._angle_preset_options:
            self._angle_preset_options.append(normalized)

    def _remaining_fixed_conf_settle_seconds(self) -> float:
        """Seconds left in the settle window since the last fixedconf send.

        Caller must hold ``_fixed_conf_lock``.
        """
        settle = self._fixed_conf_settle_seconds
        if settle <= 0 or self._last_fixed_conf_command_time is None:
            return 0.0
        remaining = settle - (time.monotonic() - self._last_fixed_conf_command_time)
        return remaining if remaining > 0 else 0.0

    def _cancel_fixed_conf_timer_locked(self) -> None:
        """Cancel any scheduled delayed fixedconf send. Caller holds the lock."""
        cancel = self._fixed_conf_cancel
        if cancel is not None:
            self._fixed_conf_cancel = None
            try:
                cancel()
            except Exception as ex:  # pylint: disable=broad-except
                # Cleanup path: cancel may race unload/loop close; never raise here.
                _LOGGER.debug(
                    "_cancel_fixed_conf_timer_locked: cancel failed (%s): %s",
                    type(ex).__name__,
                    ex,
                )

    def _notify_fixed_conf_ui(self) -> None:
        """Push settle-state changes to HA (must not hold ``_fixed_conf_lock``)."""
        self._do_callbacks()

    @property
    def fixed_conf_settle_pending(self) -> bool:
        """True while a fixedconf command is queued waiting for settle delay."""
        with self._fixed_conf_lock:
            return self._pending_fixed_conf is not None and self._fixed_conf_cancel is not None

    @property
    def fixed_conf_pending_target(self) -> str | None:
        """Queued fixedconf target (vertical,horizontal), or None if not settling."""
        with self._fixed_conf_lock:
            if self._pending_fixed_conf is not None and self._fixed_conf_cancel is not None:
                return self._pending_fixed_conf
            return None

    @property
    def fixed_conf_settle_seconds(self) -> float:
        """Inter-command settle delay in seconds (0 = no delay).

        Runtime-tunable for diagnostics: faster motors may use a lower value;
        increase if mid-move rejects appear under rapid dual-axis updates.
        """
        return self._fixed_conf_settle_seconds

    @fixed_conf_settle_seconds.setter
    def fixed_conf_settle_seconds(self, value: float) -> None:
        """Set settle delay (seconds). Clamped to >= 0."""
        self._fixed_conf_settle_seconds = max(0.0, float(value))
        self._notify_fixed_conf_ui()

    @property
    def fixed_conf_commanded(self) -> str | None:
        """Last fixedconf value commanded to the device (may still be in flight)."""
        with self._fixed_conf_lock:
            return self._last_commanded_fixed_conf

    @property
    def fixed_conf_reported(self) -> str | None:
        """Last device-reported fixedconf (authoritative encoder position)."""
        return self._normalize_fixed_conf(self._fixed_conf)

    @property
    def fixed_conf_debug_state(self) -> dict:
        """Diagnostic snapshot: reported / commanded / pending / settle timing."""
        with self._fixed_conf_lock:
            pending = (
                self._pending_fixed_conf
                if self._pending_fixed_conf is not None and self._fixed_conf_cancel is not None
                else None
            )
            remaining = self._remaining_fixed_conf_settle_seconds()
            return {
                "reported": self._normalize_fixed_conf(self._fixed_conf),
                "commanded": self._last_commanded_fixed_conf,
                "pending_target": pending,
                "settle_seconds": self._fixed_conf_settle_seconds,
                "settle_remaining_seconds": round(remaining, 3) if remaining > 0 else 0.0,
                "settle_pending": pending is not None,
            }

    def dispose(self) -> None:
        """Cancel delayed fixedconf work on integration unload / transport stop.

        Delayed settle work is scheduled via ``PyDreo.schedule_call_later``. In
        Home Assistant that is ``async_call_later`` (wired in the integration
        setup); cancel handles are also cleared on config-entry unload. Callers
        must still invoke dispose so device-level pending state is cleared.
        """
        with self._fixed_conf_send_lock:
            with self._fixed_conf_lock:
                self._fixed_conf_disposed = True
                self._pending_fixed_conf = None
                self._cancel_fixed_conf_timer_locked()
                self._clear_in_flight_fixed_conf()
                _LOGGER.debug("dispose: cancelled fixedconf settle for %s", self.name)
        self._notify_fixed_conf_ui()

    def _clear_in_flight_fixed_conf(self) -> bool:
        """Clear tracking state for an in-flight fixedconf command.

        Returns True if commanded/at-command tracking was non-empty (UI should refresh).
        Caller must hold ``_fixed_conf_lock``.
        """
        changed = (
            self._last_commanded_fixed_conf is not None or self._fixed_conf_at_command is not None
        )
        self._last_commanded_fixed_conf = None
        self._fixed_conf_at_command = None
        return changed

    def _base_fixed_conf_for_axis_update(self) -> str | None:
        """Best-known fixedconf when composing a single-axis update.

        Prefer a pending delayed target, then the last commanded value, then the
        last device-reported position so rapid HA axis updates do not clobber
        each other while waiting for a device report.
        """
        return (
            self._pending_fixed_conf
            or self._last_commanded_fixed_conf
            or self._normalize_fixed_conf(self._fixed_conf)
        )

    def _maybe_log_fixed_conf_reject(self, reported: str | None, previous: str | None) -> bool:
        """Log a reject only when the device snaps back to the pre-command position.

        Intermediate encoder reports while the head is still traveling are common
        and must not be treated as failures. A true reject (seen on DR-HPF017S)
        reports the same fixedconf that was current when the command was sent.

        On confirm or reject, clears in-flight commanded tracking.

        Returns True when diagnostic state changed (commanded cleared) so the
        caller can invoke ``_notify_fixed_conf_ui()`` outside the lock. Callers
        must not forget notify when this returns True.

        Caller must hold ``_fixed_conf_lock`` when shared state may race with
        timers or setters.
        """
        commanded = self._last_commanded_fixed_conf
        if commanded is None or reported is None:
            return False

        if reported == commanded:
            _LOGGER.debug("fixedconf: Device confirmed angle %s", commanded)
            return self._clear_in_flight_fixed_conf()

        # Still moving toward target (or to some other intermediate position).
        if self._fixed_conf_at_command is None or reported != self._fixed_conf_at_command:
            _LOGGER.debug(
                "fixedconf: intermediate report %s while commanding %s (started at %s)",
                reported,
                commanded,
                self._fixed_conf_at_command,
            )
            return False

        # Reported position equals pre-command position and is not the target → reject.
        # Intentionally no auto-retry: a true reject often means the pan/tilt
        # subsystem needs app-side recalibration; retrying would spam the device.
        _LOGGER.warning(
            "fixedconf: %s (%s) rejected angle %s (reported %s, was %s). "
            "Recalibrate pan/tilt in the Dreo app (device settings / calibration), "
            "then reload this Home Assistant integration if entities stay out of sync. "
            "Model notes: https://github.com/JeffSteinbok/hass-dreo/blob/main/SUPPORTED_MODELS.md "
            "(see DR-HPF017S / air circulators).",
            self.name,
            self.serial_number,
            commanded,
            reported,
            previous,
        )
        return self._clear_in_flight_fixed_conf()

    def _dispatch_fixed_conf_locked(self, normalized: str) -> str | None:
        """Prepare an immediate fixedconf send. Caller must hold ``_fixed_conf_lock``."""
        if self._fixed_conf_disposed:
            _LOGGER.debug("_set_fixed_conf: disposed; skipping send of %s", normalized)
            return None
        # If a previous command never confirmed, surface that before sending again.
        self._maybe_log_fixed_conf_reject(
            self._normalize_fixed_conf(self._fixed_conf), self._fixed_conf
        )

        self._fixed_conf_at_command = self._normalize_fixed_conf(self._fixed_conf)
        self._last_commanded_fixed_conf = normalized
        self._pending_fixed_conf = None
        self._last_fixed_conf_command_time = time.monotonic()
        _LOGGER.debug("_set_fixed_conf: commanding fixedconf %s", normalized)
        return normalized

    def _send_fixed_conf(self, normalized: str) -> None:
        """Send a prepared fixedconf command without holding the state lock."""
        with self._fixed_conf_send_lock:
            with self._fixed_conf_lock:
                if self._fixed_conf_disposed:
                    return
            try:
                self._send_command(FIXEDCONF_KEY, normalized)
            except Exception as ex:
                # Avoid stuck commanded/pending diagnostics if I/O fails mid-send.
                _LOGGER.error(
                    "_set_fixed_conf: send failed for %s on %s (%s): %s",
                    normalized,
                    self.name,
                    type(ex).__name__,
                    ex,
                )
                with self._fixed_conf_lock:
                    self._clear_in_flight_fixed_conf()
                    self._last_fixed_conf_command_time = None
                raise

    def _on_fixed_conf_settle_timer(self) -> None:
        """Delayed callback: send the latest pending fixedconf after settle.

        Invoked by the host scheduler (HA ``async_call_later`` via executor, or
        the standalone Timer fallback). Safe to call from a worker thread.
        """
        notify = False
        send = None
        try:
            with self._fixed_conf_lock:
                self._fixed_conf_cancel = None
                if self._fixed_conf_disposed:
                    _LOGGER.debug("_set_fixed_conf: disposed; dropping settle callback")
                    return
                pending = self._pending_fixed_conf
                if pending is None:
                    return
                if self._normalize_fixed_conf(self._fixed_conf) == pending:
                    _LOGGER.debug(
                        "_set_fixed_conf: pending %s already reported; skipping delayed send",
                        pending,
                    )
                    self._pending_fixed_conf = None
                    notify = True
                else:
                    send = self._dispatch_fixed_conf_locked(pending)
                    notify = True
            if send is not None:
                self._send_fixed_conf(send)
        except Exception:
            # Send failure cleared in-flight state; still refresh diagnostics.
            self._notify_fixed_conf_ui()
            raise
        if notify:
            self._notify_fixed_conf_ui()

    def _set_fixed_conf(self, value: str) -> None:
        """Send a fixedconf command (vertical,horizontal).

        Serializes fixed-angle commands. On models that need it (e.g. DR-HPF017S),
        enforces a settle interval so rapid successive HA updates cannot stack
        while the motor is still moving.

        Settle is non-blocking: setters return immediately and schedule the
        latest desired command via ``PyDreo.schedule_call_later`` when a previous
        move still needs to settle. Under Home Assistant that uses
        ``async_call_later`` (event-loop lifecycle); elsewhere a Timer fallback
        is used. The lock is only held for brief state updates, never across a wait.
        """
        normalized = self._normalize_fixed_conf(value)
        if normalized is None:
            raise ValueError(f"Invalid fixedconf format: {value}")

        notify = False
        send = None
        try:
            with self._fixed_conf_lock:
                if self._fixed_conf_disposed:
                    _LOGGER.debug("_set_fixed_conf: disposed; ignoring command %s", normalized)
                    return

                if self._normalize_fixed_conf(self._fixed_conf) == normalized:
                    # Already at target; drop any stale delayed send of this value.
                    if self._pending_fixed_conf == normalized:
                        self._pending_fixed_conf = None
                        self._cancel_fixed_conf_timer_locked()
                        notify = True
                    _LOGGER.debug("_set_fixed_conf: value already %s, skipping command", normalized)
                else:
                    # Always keep the latest desired target (coalesce rapid updates).
                    self._pending_fixed_conf = normalized
                    remaining = self._remaining_fixed_conf_settle_seconds()
                    if remaining <= 0:
                        self._cancel_fixed_conf_timer_locked()
                        send = self._dispatch_fixed_conf_locked(normalized)
                        notify = True
                    else:
                        # Schedule a single delayed send of the latest pending value.
                        # Do not block the caller (HA entity setters / executor threads).
                        _LOGGER.debug(
                            "_set_fixed_conf: scheduling fixedconf %s in %.1fs (interval=%.1fs)",
                            normalized,
                            remaining,
                            self._fixed_conf_settle_seconds,
                        )
                        self._cancel_fixed_conf_timer_locked()
                        # Host scheduler (HA async_call_later) or Timer fallback.
                        self._fixed_conf_cancel = self._dreo.schedule_call_later(
                            remaining, self._on_fixed_conf_settle_timer
                        )
                        notify = True
            if send is not None:
                self._send_fixed_conf(send)
        except Exception:
            # Send failed after clearing in-flight; refresh diagnostics for HA.
            self._notify_fixed_conf_ui()
            raise
        if notify:
            self._notify_fixed_conf_ui()

    @property
    def angle_preset(self) -> str | None:
        """Get the current 3D angle preset value."""
        return self._normalize_fixed_conf(self._fixed_conf)

    @angle_preset.setter
    def angle_preset(self, value: str) -> None:
        """Set the current 3D angle preset value.

        Angle presets are the device's fixedconf string (vertical,horizontal).
        Delegate to ``_set_fixed_conf`` so presets share settle delay, command
        coalescing, reject detection, and lock serialization with the horizontal
        / vertical angle number entities — not a separate code path.
        """
        if self._fixed_conf is None:
            raise NotImplementedError("3D angle presets are not supported on this device model.")
        normalized = self._normalize_fixed_conf(value)
        if normalized is None:
            raise ValueError(f"Invalid 3D angle preset format: {value}")
        if self.angle_preset == normalized:
            _LOGGER.debug("angle_preset: Angle preset value already %s, skipping command", normalized)
            return
        self._set_fixed_conf(normalized)

    @property
    def angle_preset_options(self) -> list[str]:
        """Get all discovered 3D angle preset values."""
        return self._angle_preset_options

    @horizontal_angle.setter
    def horizontal_angle(self, value: int) -> None:
        """Set the horizontal angle."""
        _LOGGER.debug("horizontal_angle: horizontal_angle.setter")
        # First check if hangleadj is available (simpler angle control)
        if self._horizontal_angle_adj is not None:
            # Note that HA seems to send this in as a float, so we need to convert to int just in case
            new_value = int(value)
            if self._horizontal_angle_adj == new_value:
                _LOGGER.debug("horizontal_angle: horizontal_angle - value already %s, skipping command", new_value)
                return
            self._send_command(HORIZONTAL_ANGLE_ADJ_KEY, new_value)
        # Otherwise use fixedconf (more complex angle control)
        elif self._fixed_conf is not None:
            # Note that HA seems to send this in as a float, so we need to convert to int just in case
            new_value = int(value)
            with self._fixed_conf_lock:
                base = self._base_fixed_conf_for_axis_update()
            if base is None:
                return
            current_value = int(base.split(",")[1])
            if current_value == new_value:
                _LOGGER.debug("horizontal_angle: horizontal_angle - value already %s, skipping command", new_value)
                return
            # Compose against pending/commanded/reported base so a vertical set
            # still in-flight is not overwritten by a horizontal update.
            self._set_fixed_conf(f"{base.split(',')[0]},{new_value}")

    @property
    def vertical_angle(self) -> int:
        """Get the current fixed vertical angle."""
        if self._fixed_conf is not None:
            return int(self._fixed_conf.split(",")[0])
        return None

    @vertical_angle.setter
    def vertical_angle(self, value: int) -> None:
        """Set the vertical angle."""
        _LOGGER.debug("vertical_angle.setter: Setting vertical angle")
        if self._fixed_conf is not None:
            # Note that HA seems to send this in as a float, we need to convert to int just in case
            new_value = int(value)
            with self._fixed_conf_lock:
                base = self._base_fixed_conf_for_axis_update()
            if base is None:
                return
            current_value = int(base.split(",")[0])
            if current_value == new_value:
                _LOGGER.debug("vertical_angle: vertical_angle - value already %s, skipping command", new_value)
                return
            self._set_fixed_conf(f"{new_value},{base.split(',')[1]}")

    @property
    def horizontal_oscillation_angle(self) -> int:
        """Get the current horizontal oscillation angle (for older firmware).

        Note: This is only used for devices that have hoscangle as an integer value
        and do NOT have hangleadj (newer simpler angle control).
        """
        # If hangleadj is available, this device doesn't use horizontal_oscillation_angle
        if self._uses_hangleadj_for_horizontal():
            return None

        if self._horizontal_oscillation_angle is not None:
            return self._horizontal_oscillation_angle
        return None

    @horizontal_oscillation_angle.setter
    def horizontal_oscillation_angle(self, value: int) -> None:
        """Set the horizontal oscillation angle (for older firmware)."""
        _LOGGER.debug("horizontal_oscillation_angle: horizontal_oscillation_angle.setter")
        # If hangleadj is available, this device doesn't use horizontal_oscillation_angle
        if self._uses_hangleadj_for_horizontal():
            raise NotImplementedError("This device uses horizontal_angle instead")

        if self._horizontal_oscillation_angle is not None:
            # Note that HA seems to send this in as a float, so we need to convert to int just in case
            new_value = int(value)
            if self._horizontal_oscillation_angle == new_value:
                _LOGGER.debug("horizontal_oscillation_angle: horizontal_oscillation_angle - value already %s, skipping command", new_value)
                return
            self._send_command(HORIZONTAL_OSCILLATION_ANGLE_KEY, new_value)

    @property
    def horizontal_oscillation_angle_range(self):
        """Get the horizontal oscillation angle range (for older firmware)."""
        # If hangleadj is available, this device doesn't use horizontal_oscillation_angle
        if self._uses_hangleadj_for_horizontal():
            return None
        return self.horizontal_angle_range

    @property
    def vertical_oscillation_angle(self) -> int:
        """Get the current vertical oscillation angle (for older firmware).

        Note: This is only used for devices that have voscangle as a non-zero integer value.
        If the device has hangleadj and voscangle is 0, it likely doesn't support vertical angle.
        """
        # If voscangle is 0 and hangleadj is present, the device likely doesn't support vertical angle
        if self._has_vertical_osc_angle_disabled():
            return None

        if self._vertical_oscillation_angle is not None:
            return self._vertical_oscillation_angle
        return None

    @vertical_oscillation_angle.setter
    def vertical_oscillation_angle(self, value: int) -> None:
        """Set the vertical oscillation angle (for older firmware)."""
        _LOGGER.debug("vertical_oscillation_angle: vertical_oscillation_angle.setter")
        # If voscangle is 0 and hangleadj is present, the device likely doesn't support vertical angle
        if self._has_vertical_osc_angle_disabled():
            raise NotImplementedError("This device does not support vertical oscillation angle")

        if self._vertical_oscillation_angle is not None:
            # Note that HA seems to send this in as a float, so we need to convert to int just in case
            new_value = int(value)
            if self._vertical_oscillation_angle == new_value:
                _LOGGER.debug("vertical_oscillation_angle: vertical_oscillation_angle - value already %s, skipping command", new_value)
                return
            self._send_command(VERTICAL_OSCILLATION_ANGLE_KEY, new_value)

    @property
    def vertical_oscillation_angle_range(self):
        """Get the vertical oscillation angle range (for older firmware)."""
        # If voscangle is 0 and hangleadj is present, the device likely doesn't support vertical angle
        if self._has_vertical_osc_angle_disabled():
            return None
        return self.vertical_angle_range

    @property
    def atm_light_on(self) -> bool | None:
        """Returns True if the atmosphere light is on, False otherwise."""
        return self._atm_light_on

    @atm_light_on.setter
    def atm_light_on(self, value: bool):
        """Set if the atmosphere light is on or off."""
        _LOGGER.debug("atm_light_on: atm_light_on.setter - %s", value)
        if self._atm_light_on is None:
            _LOGGER.error("atm_light_on: Atmosphere light not supported by this fan model.")
            return
        if self._atm_light_on == value:
            _LOGGER.debug("atm_light_on: atm_light_on - value already %s, skipping command", value)
            return
        self._send_command(ATMON_KEY, value)

    @property
    def atm_brightness(self) -> int | None:
        """Returns the brightness of the atmosphere light (1-5), or None if not supported."""
        return self._atm_brightness

    @atm_brightness.setter
    def atm_brightness(self, value: int):
        """Set the brightness of the atmosphere light."""
        _LOGGER.debug("atm_brightness: atm_brightness.setter - %s", value)
        if self._atm_brightness is None:
            _LOGGER.error("atm_brightness: Atmosphere brightness not supported by this fan model.")
            return
        min_brightness, max_brightness = self._atm_brightness_range
        brightness = max(min_brightness, min(max_brightness, value))
        if self._atm_brightness == brightness:
            _LOGGER.debug("atm_brightness: atm_brightness - value already %s, skipping command", brightness)
            return
        self._send_command(ATMBRI_KEY, brightness)

    @property
    def atm_color_rgb(self) -> tuple[int, int, int] | None:
        """Returns the RGB color as a tuple (r, g, b), or None if not supported."""
        if self._atm_color is None:
            return None
        return self._unpack_int_to_rgb(self._atm_color)

    @atm_color_rgb.setter
    def atm_color_rgb(self, rgb: tuple[int | float, int | float, int | float]):
        """Set the RGB color of the atmosphere light."""
        r_int, g_int, b_int = self._clamp_rgb_tuple(rgb)
        color_value = self._pack_rgb_to_int((r_int, g_int, b_int))
        _LOGGER.debug("atm_color_rgb: atm_color_rgb.setter - RGB(%d,%d,%d) -> %d", r_int, g_int, b_int, color_value)
        if self._atm_color is None:
            _LOGGER.error("atm_color_rgb: Atmosphere color not supported by this fan model.")
            return
        if self._atm_color == color_value:
            _LOGGER.debug("atm_color_rgb: atm_color_rgb - value already %s, skipping command", color_value)
            return
        self._send_command(ATMCOLOR_KEY, color_value)

    @property
    def atm_mode(self) -> int | None:
        """Returns the atmosphere mode (1=Constant, 2=Circle, 3=Breath), or None if not supported."""
        return self._atm_mode

    def is_feature_supported(self, feature: str) -> bool:
        """Check if this air circulator supports a specific feature."""
        if feature == "atm_light":
            return self._atm_light_on is not None
        if feature == "angle_preset":
            return self._fixed_conf is not None
        if feature in {
            "fixed_conf_settle_pending",
            "fixed_conf_settle_seconds",
            "fixed_conf_debug_state",
        }:
            # Diagnostic settle UI for models that can queue angle commands.
            # Feature stays available after runtime settle is tuned to 0 so the
            # diagnostic number entity remains usable for self-tuning.
            return self._fixed_conf is not None and (
                self._fixed_conf_settle_seconds > 0
                or (
                    self._device_definition.device_ranges is not None
                    and FIXEDCONF_SETTLE_SECONDS_KEY in self._device_definition.device_ranges
                )
            )
        return super().is_feature_supported(feature)

    @property
    def display_light(self) -> bool:
        """Is the panel display light on."""
        return self._display_light

    @display_light.setter
    def display_light(self, value: bool) -> None:
        """Set the panel display light on or off."""
        _LOGGER.debug("PyDreoAirCirculator:display_light.setter(%s) --> %s", self, value)
        if self._display_light is None:
            raise NotImplementedError("Attempting to set display_light on a device that doesn't support it.")
        self._send_command(LIGHTON_KEY, value)

    @property
    def follow_me(self) -> bool:
        """Is presence-based follow mode on."""
        return self._follow_me

    @follow_me.setter
    def follow_me(self, value: bool) -> None:
        """Enable or disable presence-based follow mode."""
        _LOGGER.debug("PyDreoAirCirculator:follow_me.setter(%s) --> %s", self, value)
        if self._follow_me is None:
            raise NotImplementedError("Attempting to set follow_me on a device that doesn't support it.")
        self._send_command(HWFPON_KEY, value)

    @property
    def follow_me_angle(self) -> int:
        """Horizontal angle toward the person detected by the presence sensor."""
        return self._follow_me_angle

    @property
    def people_detected(self) -> int:
        """Number of people currently detected by the presence sensor."""
        return self._people_detected

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("update_state: Processing state")
        super().update_state(state)

        self._horizontally_oscillating = self.get_state_update_value(state, HORIZONTAL_OSCILLATION_KEY)
        self._vertically_oscillating = self.get_state_update_value(state, VERTICAL_OSCILLATION_KEY)
        self._osc_mode = self.get_state_update_value(state, OSCMODE_KEY)
        self._cruise_conf = self.get_state_update_value(state, CRUISECONF_KEY)
        self._fixed_conf = self.get_state_update_value(state, FIXEDCONF_KEY)
        self._add_angle_preset_option(self._fixed_conf)

        # Parse hoscangle - only use if it's an integer, not a string like "0,0"
        hoscangle_val = self.get_state_update_value(state, HORIZONTAL_OSCILLATION_ANGLE_KEY)
        if isinstance(hoscangle_val, int):
            self._horizontal_oscillation_angle = hoscangle_val

        # Parse voscangle - only use if it's an integer
        voscangle_val = self.get_state_update_value(state, VERTICAL_OSCILLATION_ANGLE_KEY)
        if isinstance(voscangle_val, int):
            self._vertical_oscillation_angle = voscangle_val

        self._horizontal_angle_adj = self.get_state_update_value(state, HORIZONTAL_ANGLE_ADJ_KEY)

        self._atm_light_on = self.get_state_update_value(state, ATMON_KEY)
        self._atm_brightness = self.get_state_update_value(state, ATMBRI_KEY)
        self._atm_color = self.get_state_update_value(state, ATMCOLOR_KEY)
        self._atm_mode = self.get_state_update_value(state, ATMMODE_KEY)

        self._display_light = self.get_state_update_value(state, LIGHTON_KEY)
        self._follow_me = self.get_state_update_value(state, HWFPON_KEY)
        self._follow_me_angle = self.get_state_update_value(state, HWFPANGLE_KEY)
        self._people_detected = self.get_state_update_value(state, HBODYCNT_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("handle_server_update: handle_server_update")
        super().handle_server_update(message)

        val_horiz_oscillation = self.get_server_update_key_value(message, HORIZONTAL_OSCILLATION_KEY)
        if isinstance(val_horiz_oscillation, bool):
            self._horizontally_oscillating = val_horiz_oscillation

        val_vert_oscillation = self.get_server_update_key_value(message, VERTICAL_OSCILLATION_KEY)
        if isinstance(val_vert_oscillation, bool):
            self._vertically_oscillating = val_vert_oscillation

        val_osc_mode = self.get_server_update_key_value(message, OSCMODE_KEY)
        if isinstance(val_osc_mode, int):
            self._osc_mode = val_osc_mode

        val_cruiseconf = self.get_server_update_key_value(message, CRUISECONF_KEY)
        if isinstance(val_cruiseconf, str):
            self._cruise_conf = val_cruiseconf

        val_fixed_conf = self.get_server_update_key_value(message, FIXEDCONF_KEY)
        if isinstance(val_fixed_conf, str):
            method = message.get("method")
            # control-reply may echo the requested value before the motor moves.
            # control-report and report carry authoritative encoder positions.
            if method in _FIXEDCONF_OPTIMISTIC_METHODS:
                _LOGGER.debug(
                    "fixedconf: Ignoring optimistic %s value %s (waiting for device report)",
                    method,
                    val_fixed_conf,
                )
            else:
                # Centralize UI refresh: confirm/reject clear commanded via
                # _maybe_log_fixed_conf_reject; pending clear when report matches queue.
                notify_settle = False
                with self._fixed_conf_lock:
                    previous = self._fixed_conf
                    self._fixed_conf = val_fixed_conf
                    self._add_angle_preset_option(self._fixed_conf)
                    if self._maybe_log_fixed_conf_reject(
                        self._normalize_fixed_conf(val_fixed_conf), previous
                    ):
                        notify_settle = True
                    # If the device already reports the delayed target, drop the timer.
                    if (
                        self._pending_fixed_conf is not None
                        and self._normalize_fixed_conf(val_fixed_conf) == self._pending_fixed_conf
                    ):
                        self._pending_fixed_conf = None
                        self._cancel_fixed_conf_timer_locked()
                        notify_settle = True
                if notify_settle:
                    self._notify_fixed_conf_ui()

        val_horiz_osc_angle = self.get_server_update_key_value(message, HORIZONTAL_OSCILLATION_ANGLE_KEY)
        if isinstance(val_horiz_osc_angle, int):
            self._horizontal_oscillation_angle = val_horiz_osc_angle

        val_vert_osc_angle = self.get_server_update_key_value(message, VERTICAL_OSCILLATION_ANGLE_KEY)
        if isinstance(val_vert_osc_angle, int):
            self._vertical_oscillation_angle = val_vert_osc_angle

        val_horiz_angle_adj = self.get_server_update_key_value(message, HORIZONTAL_ANGLE_ADJ_KEY)
        if isinstance(val_horiz_angle_adj, int):
            self._horizontal_angle_adj = val_horiz_angle_adj

        val_atm_on = self.get_server_update_key_value(message, ATMON_KEY)
        if isinstance(val_atm_on, bool):
            self._atm_light_on = val_atm_on

        val_atm_brightness = self.get_server_update_key_value(message, ATMBRI_KEY)
        if isinstance(val_atm_brightness, int):
            self._atm_brightness = val_atm_brightness

        val_atm_color = self.get_server_update_key_value(message, ATMCOLOR_KEY)
        if isinstance(val_atm_color, int):
            self._atm_color = val_atm_color

        val_atm_mode = self.get_server_update_key_value(message, ATMMODE_KEY)
        if isinstance(val_atm_mode, int):
            self._atm_mode = val_atm_mode

        val_display_light = self.get_server_update_key_value(message, LIGHTON_KEY)
        if isinstance(val_display_light, bool):
            self._display_light = val_display_light

        val_follow_me = self.get_server_update_key_value(message, HWFPON_KEY)
        if isinstance(val_follow_me, bool):
            self._follow_me = val_follow_me

        val_follow_me_angle = self.get_server_update_key_value(message, HWFPANGLE_KEY)
        if isinstance(val_follow_me_angle, int):
            self._follow_me_angle = val_follow_me_angle

        val_people_detected = self.get_server_update_key_value(message, HBODYCNT_KEY)
        if isinstance(val_people_detected, int):
            self._people_detected = val_people_detected
