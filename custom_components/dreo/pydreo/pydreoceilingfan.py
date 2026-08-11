"""Dreo API for controling fans."""

import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Dict

from .constant import (
    FANON_KEY,
    LIGHTON_KEY,
    WINDLEVEL_KEY,
    SPEED_RANGE,
    BRIGHTNESS_KEY,
    COLORTEMP_KEY,
    POWERON_KEY,
    ATMON_KEY,
    ATMCOLOR_KEY,
    ATMBRI_KEY,
    ATMMODE_KEY,
    RGBPRESETSEL_KEY,
    RGBPRESETNUM_KEY,
    RGBEFFECTID_KEY,
    TIMESTAMP_KEY,
)

from .pydreofanbase import PyDreoFanBase
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pydreo import PyDreo


class PyDreoCeilingFan(PyDreoFanBase):
    """Base class for Dreo Fan API Calls.

    Ceiling fans expose several independent loads (fan motor, main light, atmosphere
    light) behind a single whole-device power gate:

        ``<load>_is_on = poweron AND <load>on``

    Protocol behaviour (reverse-engineered against DR-HCF002S hardware):

    * Load keys (``fanon``/``lighton``/``atmon``) are RETAINED across a gate close;
      ``poweron: False`` extinguishes everything physically without reporting the
      load keys, and ``poweron: True`` re-energises every retained-on load.
    * A load command sent while the gate is closed registers logically but does
      nothing physically, so waking a single load requires one atomic command that
      opens the gate and explicitly forces every other load off.
    * The device never closes the gate itself: turning off the last active load
      leaves ``poweron: True``, so the off command must close the gate too.
    * WebSocket messages carry net deltas only, and some units stop reporting
      individual load keys entirely (observed: ``lighton`` on a DR-HCF002S) while
      control keeps working - state can therefore never rely on load-key echoes.
    """

    # Load key -> attribute holding the RETAINED (ungated) value.
    _LOAD_ATTRS = {
        FANON_KEY: "_fanon",
        LIGHTON_KEY: "_light_on",
        ATMON_KEY: "_atm_light_on",
    }

    # Seconds to wait after our own command burst or a gate-open before
    # verifying state via REST; lets the device's trailing deltas land first
    # and debounces a burst into a single verification. Dreo's cloud REST
    # state lags the device by several seconds (field-observed: a readback
    # 4 s after a gate close returned the PRE-close state, re-opened the gate
    # in cache, and the user's next wake command went out without gate keys),
    # so this must sit beyond that ingest lag.
    _STATE_VERIFY_DELAY = 10.0

    # A verification whose REST payload predates our last local write is
    # retried this many times before being accepted as truth. Retrying covers
    # cloud ingest lag; the final acceptance keeps silently-dropped commands
    # self-healing (a drop leaves REST legitimately older than our write).
    _STATE_VERIFY_MAX_STALE_RETRIES = 3

    @staticmethod
    def _clamp_rgb_tuple(rgb: tuple) -> tuple[int, int, int]:
        """Clamp RGB tuple values to 0-255 integers."""
        if len(rgb) != 3:
            raise ValueError(f"RGB tuple must have exactly 3 elements, got {len(rgb)}")
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

        self._speed_range = None
        if device_definition.device_ranges is not None and SPEED_RANGE in device_definition.device_ranges:
            self._speed_range = device_definition.device_ranges[SPEED_RANGE]
        if self._speed_range is None:
            self._speed_range = self.parse_speed_range(details)
        self._preset_modes = device_definition.preset_modes
        if self._preset_modes is None:
            self._preset_modes = self.parse_preset_modes(details)

        self._fan_speed = None
        self._poweron: bool = None  # whole-device gate; None until first seen
        self._fanon: bool = None  # retained fan-motor state
        self._light_on: bool = None
        self._brightness: int = None
        self._color_temp: int = None

        # Cancel handle from PyDreo.schedule_call_later (HA async_call_later or Timer).
        self._state_verify_cancel: Callable[[], None] | None = None
        # Set by dispose() so a delayed verification cannot read after unload.
        self._state_verify_disposed: bool = False
        # Wall-clock time of our last optimistic write; REST payloads whose
        # per-key device timestamps predate this are stale (cloud ingest lag).
        self._last_local_write: float = 0.0
        self._rest_readback_stale = False
        self._stale_readback_retries = 0

        self._atm_light_on: bool = None
        self._atm_brightness: int = None
        self._atm_color: int = None
        self._atm_mode: int = None

        # Brightness range for the atmosphere light (device-specific; defaults to 1-5 for
        # older models, but HCF007S and similar use 1-100).
        self._atm_brightness_range: tuple[int, int] = (1, 5)
        if device_definition.device_ranges is not None and "atm_brightness_range" in device_definition.device_ranges:
            self._atm_brightness_range = device_definition.device_ranges["atm_brightness_range"]

        # RGBIC preset system (used by some ceiling fan variants)
        self._rgb_preset_sel: int = None
        self._rgb_preset_num: int = None

        # RGBIC effect ID system (used by HCF007S and similar) – the device
        # reports/accepts a string-based effect ID (e.g. "2070476690030592000")
        # where the last 3 digits are the effect index.
        self._rgb_effect_id: str = None
        self._rgb_effect_range: tuple[int, int] = None
        if device_definition.device_ranges is not None and "rgb_effect_range" in device_definition.device_ranges:
            self._rgb_effect_range = device_definition.device_ranges["rgb_effect_range"]

        self._wind_type = None
        self._wind_mode = None

        self._device_definition = device_definition

    def parse_preset_modes(self, details: Dict[str, list]) -> tuple[str, int]:
        """Parse the preset modes from the details."""
        preset_modes = []
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            control = controls_conf.get("control", None)
            if control is not None:
                for control_item in control:
                    if control_item.get("type", None) == "CFFan":
                        for mode_item in control_item.get("items", None):
                            text = self.get_mode_string(mode_item.get("text", None))
                            value = mode_item.get("value", None)
                            preset_modes.append((text, value))

        preset_modes.sort(key=lambda tup: tup[1])  # sorts in place
        if len(preset_modes) == 0:
            _LOGGER.debug("parse_preset_modes: No preset modes detected")
            preset_modes = None
        _LOGGER.debug("parse_preset_modes: Detected preset modes - %s", preset_modes)
        return preset_modes

    # ------------------------------------------------------------------
    # The power gate
    # ------------------------------------------------------------------

    @property
    def poweron(self) -> bool | None:
        """The whole-device power gate, or None on models without one (DR-HCF001S).

        Read-only, by deliberate contrast with the read-write ``poweron`` on
        heaters and air conditioners (where it simply is the device's on/off).
        Here the gate is derived per command by ``_finalize_command_params`` from
        the merged batch, and setting it directly would fight that: in
        particular ``poweron: True`` with every load off is the firmware
        chain-pull shape that makes the device set ``fanon`` retained-True on
        its own. Callers switch loads instead and let the gate follow.
        """
        return self._poweron

    def gate_diagnostics(self) -> dict:
        """Retained load values and reconcile-loop health, for diagnostics.

        The retained values are the RAW ungated states, which is the point:
        ``light_on`` False collapses "light off" and "light retained on behind a
        closed gate", and only these can tell them apart.
        """
        diagnostics = {load_key: getattr(self, attr) for load_key, attr in self._LOAD_ATTRS.items()}
        diagnostics["rest_readback_stale"] = self._rest_readback_stale
        diagnostics["stale_readback_retries"] = self._stale_readback_retries
        return diagnostics

    def _gated(self, load_value: bool | None) -> bool | None:
        """Apply the whole-device power gate to a retained load value.

        Returns None when the load itself is unsupported (feature detection relies
        on that). Models without a poweron key (e.g. DR-HCF001S) have no gate and
        report the load value directly.
        """
        if load_value is None:
            return None
        if self._poweron is None:
            return load_value
        return bool(self._poweron) and bool(load_value)

    def _apply_optimistic_state(self, params: dict) -> None:
        """Fold keys we are sending into local state.

        Some units stop emitting control-reports for individual load keys while
        control keeps working (observed with lighton on a DR-HCF002S), so waiting
        for an echo would leave the cache permanently stale. Our own writes plus
        REST refreshes are the source of truth instead. The outbox applies this at
        submit time, so the entity reflects intent immediately and
        ``_finalize_command_params`` reads post-batch load states.
        """
        for key, val in params.items():
            if key == POWERON_KEY:
                self._poweron = val
            elif key in self._LOAD_ATTRS:
                setattr(self, self._LOAD_ATTRS[key], val)
        self._is_on = bool(self.is_on)
        self._last_local_write = time.time()

    def _finalize_command_params(self, params: dict) -> dict:
        """Derive whole-device gate keys for a merged batch just before sending.

        Optimistic state already reflects the batch (applied at submit), so the
        retained load attributes ARE the post-batch load states.

        No same-value skip guards anywhere in this path: redundant sends are
        harmless no-ops, while a skip on a stale cache makes the entity
        permanently unreachable.
        """
        batch_loads = {key: params[key] for key in self._LOAD_ATTRS if key in params}
        if not batch_loads or POWERON_KEY in params:
            # Nothing to gate: a parameter-only batch (e.g. Adaptive Lighting
            # adjusting colortemp while the light is off) must never wake the
            # device - and an explicit poweron is the caller's intent.
            return params

        if self._poweron is False and any(batch_loads.values()):
            final = params | {POWERON_KEY: True, **self._loads_to_force_off(params)}
            _LOGGER.debug("_finalize_command_params: %s + wake keys -> %s", params, final)
            return final

        if self._poweron and not self._any_load_retained_on():
            # The device never closes the gate itself; the last load-off must.
            final = params | {POWERON_KEY: False}
            _LOGGER.debug("_finalize_command_params: %s + gate close -> %s", params, final)
            return final

        return params

    def _loads_to_force_off(self, params: dict) -> dict:
        """Supported loads absent from the batch, to force off during a wake.

        ``poweron: True`` alone re-energises every retained-on load (a light
        press would restart the fan), so waking one load means explicitly
        extinguishing the others. Batch keys are the caller's intent and are
        never overridden - a co-arriving ``atmon: True`` survives the wake.
        """
        return {
            load_key: False
            for load_key, attr in self._LOAD_ATTRS.items()
            if load_key not in params and getattr(self, attr) is not None
        }

    def _any_load_retained_on(self) -> bool:
        """True if any supported load is retained on; unknown (None) counts as off."""
        return any(getattr(self, attr) for attr in self._LOAD_ATTRS.values())

    def _set_load(self, load_key: str, value: bool) -> None:
        """Switch one load on/off.

        Just submits the raw key; ``_finalize_command_params`` derives any gate
        keys from the merged batch at send time, so near-simultaneous setters
        (a scene or linked wall switches switching light and RGB together)
        coalesce into one correct command instead of racing each other.
        """
        self._send_command_batch({load_key: bool(value)})

    # ------------------------------------------------------------------
    # Properties and setters
    # ------------------------------------------------------------------

    @property
    def is_on(self) -> bool | None:
        """Returns True if the fan motor is running (device powered AND fan on)."""
        return self._gated(self._fanon)

    @is_on.setter
    def is_on(self, value: bool):
        """Turn the fan motor on or off."""
        _LOGGER.debug("is_on: is_on.setter - %s", value)
        self._set_load(FANON_KEY, bool(value))

    @property
    def light_on(self) -> bool | None:
        """Returns True if the main light is on (device powered AND light on)."""
        return self._gated(self._light_on)

    @light_on.setter
    def light_on(self, value: bool):
        """Turn the main light on or off."""
        _LOGGER.debug("light_on: light_on.setter - %s", value)
        if self._light_on is None:
            _LOGGER.error("light_on: Light control not supported by this fan model.")
            return
        self._set_load(LIGHTON_KEY, bool(value))

    @property
    def oscillating(self) -> bool:
        return None

    @oscillating.setter
    def oscillating(self, value: bool) -> None:
        raise NotImplementedError(f"Attempting to set oscillating on a device that doesn't support ({value})")

    @property
    def brightness(self) -> int | None:
        """Returns the brightness of the light, or None if not supported."""
        return self._brightness

    @brightness.setter
    def brightness(self, value: int):
        """Set the brightness of the light on the fan."""
        _LOGGER.debug("brightness: brightness.setter - %s", value)
        if self._brightness is None:
            _LOGGER.error("brightness: Brightness not supported by this fan model.")
            return
        if self._brightness == value:
            _LOGGER.debug("brightness: brightness - value already %s, skipping command", value)
            return
        self._send_command(BRIGHTNESS_KEY, value)

    @property
    def color_temperature(self) -> int | None:
        """Returns the color temperature of the light, or None if not supported."""
        return self._color_temp

    @color_temperature.setter
    def color_temperature(self, value: int):
        """Set the color temperature of the light on the fan."""
        _LOGGER.debug("color_temperature: color_temperature.setter - %s", value)
        if self._color_temp is None:
            _LOGGER.error("color_temperature: Color temperature not supported by this fan model.")
            return
        if self._color_temp == value:
            _LOGGER.debug("color_temperature: color_temperature - value already %s, skipping command", value)
            return
        self._send_command(COLORTEMP_KEY, value)

    def turn_light_on(self, brightness: int | None = None, color_temp: int | None = None) -> None:
        """Turn the main light on, optionally setting brightness and/or color temperature.

        Submits all keys as one batch so the device receives the whole desired
        state atomically. Adaptive Lighting and similar integrations send
        brightness/color together with the on command; issuing them as separate
        sequential commands caused the light to intermittently fail to turn on
        (issue #846). ``lighton`` is always included - skipping it when the
        cache already says on would make the light unreachable on a stale cache.
        """
        if self._light_on is None:
            _LOGGER.error("turn_light_on: Light control not supported by this fan model.")
            return

        params: dict = {}
        if brightness is not None and self._brightness is not None and self._brightness != brightness:
            params[BRIGHTNESS_KEY] = brightness
        if color_temp is not None and self._color_temp is not None and self._color_temp != color_temp:
            params[COLORTEMP_KEY] = color_temp
        params[LIGHTON_KEY] = True

        _LOGGER.debug("turn_light_on: enqueueing combined command %s", params)
        self._send_command_batch(params)

    @property
    def atm_light_on(self) -> bool | None:
        """Returns True if the atmosphere light is on (device powered AND atm on)."""
        return self._gated(self._atm_light_on)

    @atm_light_on.setter
    def atm_light_on(self, value: bool):
        """Turn the atmosphere light on or off."""
        _LOGGER.debug("atm_light_on: atm_light_on.setter - %s", value)
        if self._atm_light_on is None:
            _LOGGER.error("atm_light_on: Atmosphere light not supported by this fan model.")
            return
        self._set_load(ATMON_KEY, bool(value))

    @property
    def atm_brightness(self) -> int | None:
        """Returns the brightness of the atmosphere light, or None if not supported."""
        return self._atm_brightness

    @property
    def atm_brightness_range(self) -> tuple[int, int]:
        """Returns the valid brightness range (min, max) for the atmosphere light."""
        return self._atm_brightness_range

    @atm_brightness.setter
    def atm_brightness(self, value: int):
        """Set the brightness of the atmosphere light."""
        _LOGGER.debug("atm_brightness: atm_brightness.setter - %s", value)
        if self._atm_brightness is None:
            _LOGGER.error("atm_brightness: Atmosphere brightness not supported by this fan model.")
            return
        # Clamp to the device-specific valid range
        low, high = self._atm_brightness_range
        brightness = max(low, min(high, value))
        if self._atm_brightness == brightness:
            _LOGGER.debug("atm_brightness: atm_brightness - value already %s, skipping command", brightness)
            return
        self._send_command(ATMBRI_KEY, brightness)

    @property
    def atm_color_rgb(self) -> tuple[int, int, int] | None:
        """Returns the RGB color as a tuple (r, g, b), or None if not supported."""
        if self._atm_color is None:
            return None
        # Extract RGB from 24-bit integer
        return self._unpack_int_to_rgb(self._atm_color)

    @atm_color_rgb.setter
    def atm_color_rgb(self, rgb: tuple[int | float, int | float, int | float]):
        """Set the RGB color of the atmosphere light."""
        # Clamp RGB values and pack into 24-bit integer
        r_int, g_int, b_int = self._clamp_rgb_tuple(rgb)
        color_value = self._pack_rgb_to_int((r_int, g_int, b_int))
        _LOGGER.debug("atm_color_rgb: atm_color_rgb.setter - RGB(%d,%d,%d) -> %d", r_int, g_int, b_int, color_value)
        # Guard on atm_light_on (not _atm_color): some device variants track the atmosphere
        # light via atmon/atmbri but do not echo atmcolor in their state heartbeat.
        # We still allow sending the atmcolor command as long as the atmosphere light
        # feature itself is present on the device.
        if self._atm_light_on is None:
            _LOGGER.error("atm_color_rgb: Atmosphere light not supported by this fan model.")
            return
        if self._atm_color is not None and self._atm_color == color_value:
            _LOGGER.debug("atm_color_rgb: atm_color_rgb - value already %s, skipping command", color_value)
            return
        self._send_command(ATMCOLOR_KEY, color_value)

    @property
    def atm_mode(self) -> int | None:
        """Returns the atmosphere mode (1=Constant, 2=Circle, 3=Breath), or None if not supported."""
        return self._atm_mode

    @property
    def rgb_preset_sel(self) -> int | None:
        """Returns the currently selected RGBIC preset (0-based index), or None if not supported."""
        return self._rgb_preset_sel

    @rgb_preset_sel.setter
    def rgb_preset_sel(self, value: int):
        """Set the RGBIC preset selection (0-based index)."""
        _LOGGER.debug("rgb_preset_sel: rgb_preset_sel.setter - %s", value)
        if self._rgb_preset_sel is None:
            _LOGGER.error("rgb_preset_sel: RGBIC presets not supported by this fan model.")
            return
        if self._rgb_preset_sel == value:
            _LOGGER.debug("rgb_preset_sel: rgb_preset_sel - value already %s, skipping command", value)
            return
        self._send_command(RGBPRESETSEL_KEY, value)

    @property
    def rgb_preset_num(self) -> int | None:
        """Returns the number of available RGBIC presets, or None if not supported."""
        return self._rgb_preset_num

    @property
    def rgb_effect_id(self) -> str | None:
        """Returns the current RGBIC effect ID string, or None if not supported."""
        return self._rgb_effect_id

    @rgb_effect_id.setter
    def rgb_effect_id(self, value: str):
        """Set the RGBIC effect by full effect ID string."""
        _LOGGER.debug("rgb_effect_id: rgb_effect_id.setter - %s", value)
        if self._rgb_effect_id is None:
            _LOGGER.error("rgb_effect_id: RGBIC effect ID not supported by this fan model.")
            return
        if self._rgb_effect_id == value:
            _LOGGER.debug("rgb_effect_id: rgb_effect_id - value already %s, skipping command", value)
            return
        self._send_command(RGBEFFECTID_KEY, value)

    @property
    def rgb_effect_range(self) -> tuple[int, int] | None:
        """Returns the valid range (min, max) of RGBIC effect indices, or None."""
        return self._rgb_effect_range

    # ------------------------------------------------------------------
    # Incoming state (REST payloads and WebSocket deltas)
    # ------------------------------------------------------------------

    def _apply_rest_power_state(self, state: dict) -> None:
        """Apply the REST payload's gate and load keys, skipping stale contradictions.

        Dreo's cloud REST state lags the device by several seconds (observed
        well past 10 s), so a readback inside that window carries PRE-command
        values; applying them would revert the retained cache and the next
        command would derive its gate keys from state that no longer exists
        (field-observed: off-then-quickly-on left the room dark because a
        stale readback re-opened the gate in cache and the wake keys were
        skipped).

        Per key: a REST value that AGREES with the cache is never dangerous
        and always applies; a value that CONTRADICTS the cache applies only if
        stamped after our last local write (a genuine external change). A
        contradiction with an older stamp is either cloud lag or a dropped
        command - it is kept optimistic here and the verification retry loop
        disambiguates.
        """
        stale_keys = []
        for key, attr in ((POWERON_KEY, "_poweron"), *self._LOAD_ATTRS.items()):
            rest_val = self.get_state_update_value(state, key)
            if rest_val != getattr(self, attr) and self._predates_our_last_write(state, key):
                stale_keys.append(key)
                continue
            setattr(self, attr, rest_val)
        self._rest_readback_stale = bool(stale_keys)
        if stale_keys:
            _LOGGER.debug(
                "_apply_rest_power_state: %s REST contradicts local state with pre-write timestamps for %s; keeping optimistic values (cloud lag or dropped command)",
                self.name,
                stale_keys,
            )

    def _predates_our_last_write(self, state: dict, key: str) -> bool:
        """True if the REST entry for ``key`` is stamped before our last local write.

        The device refreshes a key's timestamp ONLY when its value changes (a
        no-op write keeps the old stamp), so a stamp is meaningful solely for a
        value that CONTRADICTS the local cache - old stamps on agreeing values
        are routine. Entries without a timestamp never count as predating
        (models that omit stamps keep the old always-apply behaviour).
        """
        if not self._last_local_write:
            return False
        entry = state.get(key)
        ts = entry.get(TIMESTAMP_KEY) if isinstance(entry, dict) else None
        return isinstance(ts, (int, float)) and ts < self._last_local_write

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("update_state: Processing state")
        super().update_state(state)

        self._fan_speed = self.get_state_update_value(state, WINDLEVEL_KEY)
        if self._fan_speed is None:
            _LOGGER.error("update_state: Unable to get fan speed from state. Check debug logs for more information.")

        # The gate model: retained load values are stored raw, and the properties
        # apply `poweron AND <load>`. The device retains load states across a gate
        # close (REST reports e.g. poweron=False with fanon=True), so gating at
        # read time replaces any priority juggling between the keys here.
        self._apply_rest_power_state(state)
        self._is_on = bool(self.is_on)

        self._brightness = self.get_state_update_value(state, BRIGHTNESS_KEY)
        self._color_temp = self.get_state_update_value(state, COLORTEMP_KEY)

        self._atm_brightness = self.get_state_update_value(state, ATMBRI_KEY)
        self._atm_color = self.get_state_update_value(state, ATMCOLOR_KEY)
        self._atm_mode = self.get_state_update_value(state, ATMMODE_KEY)

        # RGBIC preset system
        self._rgb_preset_sel = self.get_state_update_value(state, RGBPRESETSEL_KEY)
        self._rgb_preset_num = self.get_state_update_value(state, RGBPRESETNUM_KEY)
        self._rgb_effect_id = self.get_state_update_value(state, RGBEFFECTID_KEY)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("handle_server_update: handle_server_update")
        super().handle_server_update(message)

        # Power state (fanon/poweron) is handled by _handle_power_state_update.

        val_light_on = self.get_server_update_key_value(message, LIGHTON_KEY)
        if isinstance(val_light_on, bool):
            self._light_on = val_light_on

        val_brightness = self.get_server_update_key_value(message, BRIGHTNESS_KEY)
        if isinstance(val_brightness, int):
            self._brightness = val_brightness

        val_color_temp = self.get_server_update_key_value(message, COLORTEMP_KEY)
        if isinstance(val_color_temp, int):
            self._color_temp = val_color_temp

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

        # RGBIC preset system
        val_rgb_preset_sel = self.get_server_update_key_value(message, RGBPRESETSEL_KEY)
        if isinstance(val_rgb_preset_sel, int):
            self._rgb_preset_sel = val_rgb_preset_sel

        val_rgb_preset_num = self.get_server_update_key_value(message, RGBPRESETNUM_KEY)
        if isinstance(val_rgb_preset_num, int):
            self._rgb_preset_num = val_rgb_preset_num

        val_rgb_effect_id = self.get_server_update_key_value(message, RGBEFFECTID_KEY)
        if isinstance(val_rgb_effect_id, str):
            self._rgb_effect_id = val_rgb_effect_id

    def _handle_power_state_update(self, message):
        """Ceiling fans: update the retained load values and the power gate.

        Messages are net deltas - only changed keys appear. Retained values are
        stored raw; the properties apply the gate, so a `poweron: False` shows all
        loads off without destroying their retained values (which is exactly what
        the hardware does), and a bare `poweron: True` re-lights whatever was
        retained on. No ordering games needed: the gated result is the same
        whichever key is processed first.
        """
        val_fan_on = self.get_server_update_key_value(message, FANON_KEY)
        if isinstance(val_fan_on, bool):
            self._fanon = val_fan_on
            _LOGGER.debug("_handle_power_state_update: fanon -> %s", val_fan_on)

        val_poweron = self.get_server_update_key_value(message, POWERON_KEY)
        if isinstance(val_poweron, bool):
            gate_opened = val_poweron and self._poweron is False
            self._poweron = val_poweron
            _LOGGER.debug("_handle_power_state_update: poweron (gate) -> %s", val_poweron)
            if gate_opened:
                # Gate-open re-energises retained loads, but some units never
                # report load keys (observed: lighton on a DR-HCF002S), so pull
                # the truth via REST once the trailing deltas have landed.
                self._schedule_state_verification()

        self._is_on = bool(self.is_on)

    # ------------------------------------------------------------------
    # State verification (after every command and every gate-open)
    # ------------------------------------------------------------------

    def _on_command_sent(self) -> None:
        """Verify every command burst against REST truth.

        The hardware drops rapid commands silently and some units never report
        certain load keys, so a debounced REST readback after each send is the
        only reliable confirmation.
        """
        self._stale_readback_retries = 0
        self._schedule_state_verification()

    def _schedule_state_verification(self) -> None:
        """(Re)schedule a one-shot REST state verification, debounced.

        Called after every command we send (our optimistic state must be
        verified - the hardware can silently drop a command) and on gate-open
        (external changes may be invisible - some units never report certain
        load keys). Rescheduling on each call collapses a burst into a single
        verification after the burst quietens.

        Delayed work goes through the host scheduler (HA ``async_call_later``)
        so the integration owns its lifecycle and cancels it on unload.
        """
        with self._lock:
            if self._state_verify_disposed:
                return
            self._cancel_state_verification_locked()
            self._state_verify_cancel = self._dreo.schedule_call_later(self._STATE_VERIFY_DELAY, self._verify_state)

    def _cancel_state_verification_locked(self) -> None:
        """Cancel a pending verification, if any. Caller must hold ``_lock``."""
        if self._state_verify_cancel is None:
            return
        try:
            self._state_verify_cancel()
        except Exception as ex:  # pylint: disable=broad-except
            # Teardown race: the handle may already be invalid.
            _LOGGER.debug("_cancel_state_verification: handle failed for %s: %s", self.name, ex)
        self._state_verify_cancel = None

    def _verify_state(self) -> None:
        """Refresh state via REST; WS deltas may be incomplete on some units.

        A readback whose gate/load keys predate our last write is cloud ingest
        lag, not device truth - update_state keeps the optimistic values and we
        retry after another delay. If REST stays older than our write past the
        retry cap, the command was genuinely dropped and REST IS the truth, so
        the guard is lifted for one final accepting read (self-heal).

        Runs on whichever thread the host scheduler dispatches to (an HA
        executor thread), never the event loop - it makes a blocking REST call.
        """
        with self._lock:
            # This scheduled verification is now running; its handle is spent.
            self._state_verify_cancel = None
            if self._state_verify_disposed:
                return
        if self._outbox.busy:
            # A batch is still queued or in flight; a REST readback now would
            # see pre-batch state and briefly revert optimistic values. Try
            # again after the next quiet stretch.
            self._schedule_state_verification()
            return
        try:
            if self._dreo.load_device_state(self):
                if self._rest_readback_stale:
                    if self._stale_readback_retries < self._STATE_VERIFY_MAX_STALE_RETRIES:
                        self._stale_readback_retries += 1
                        _LOGGER.debug(
                            "_verify_state: %s REST still behind our last write; retry %d/%d",
                            self.name,
                            self._stale_readback_retries,
                            self._STATE_VERIFY_MAX_STALE_RETRIES,
                        )
                        self._schedule_state_verification()
                        return
                    _LOGGER.warning(
                        "_verify_state: %s REST stayed behind our last write after %d retries; accepting REST as truth (command was likely dropped)",
                        self.name,
                        self._STATE_VERIFY_MAX_STALE_RETRIES,
                    )
                    self._last_local_write = 0.0
                    self._dreo.load_device_state(self)
                self._stale_readback_retries = 0
                _LOGGER.debug("_verify_state: REST verification complete for %s", self.name)
                self._do_callbacks()
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.debug("_verify_state: verification failed for %s: %s", self.name, ex)

    def dispose(self) -> None:
        """Also cancel the pending state verification (transport going away)."""
        super().dispose()
        with self._lock:
            self._state_verify_disposed = True
            self._cancel_state_verification_locked()

    def is_feature_supported(self, feature: str) -> bool:
        """Check if this ceiling fan supports a specific feature"""
        if feature == "atm_light":
            return self._atm_light_on is not None
        # atm_color_rgb is only supported if the device has atmcolor (not RGBIC preset system)
        if feature == "atm_color_rgb":
            # Device must have atmosphere light AND direct atmcolor support (not RGBIC presets)
            return self._atm_light_on is not None and self._atm_color is not None
        # Some RGBIC models (e.g. HCF007S) accept atmcolor commands but don't report atmcolor state.
        # This capability is model-defined so HA can expose direct RGB control where supported.
        if feature == "atm_color_rgb_write":
            direct_rgb = (
                self._device_definition is not None
                and self._device_definition.device_ranges is not None
                and self._device_definition.device_ranges.get("supports_direct_rgb_color", False)
            )
            return self._atm_light_on is not None and (self._atm_color is not None or direct_rgb)
        # RGBIC preset system - device has atmon + rgbpresetsel but not atmcolor
        if feature == "rgb_preset":
            return self._atm_light_on is not None and self._rgb_preset_sel is not None
        # RGBIC effect ID system - device uses string-based effect IDs (e.g. HCF007S)
        # Only enabled when the device also has a defined rgb_effect_range in its model
        if feature == "rgb_effect_id":
            return self._rgb_effect_id is not None and self._rgb_effect_range is not None
        return super().is_feature_supported(feature)
