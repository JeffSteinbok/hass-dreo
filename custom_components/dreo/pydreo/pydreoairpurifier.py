"""Dreo API for controlling air purifiers."""

import logging
import re
import time
from typing import TYPE_CHECKING, Dict, NamedTuple

from .constant import (
    LIFETIME_KEY,
    PURIFYON_KEY,
    RGB_ALWAYS_ON,
    RGB_BRI,
    RGB_LEVEL,
    RGB_MODE,
    RGBEFFECTID_KEY,
    RGBON_KEY,
)
from .pydreofanbase import PyDreoFanBase
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pydreo import PyDreo


class _RgbicCatalogParse(NamedTuple):
    """Selectable effects and whole-ring color data extracted from one catalog."""

    effects: list[dict]
    scene_effects: list[dict]
    color_effect: dict | None
    effect_id_to_name: dict[str, str]
    whole_ring_color: tuple[int, int, int] | None


class PyDreoAirPurifier(PyDreoFanBase):
    """Class for Dreo Air Purifier API Calls."""

    def __init__(self, device_definition: DreoDeviceDetails, details: Dict[str, list], dreo: "PyDreo"):
        """Initialize air devices."""
        _LOGGER.debug("__init__: __init__")
        super().__init__(device_definition, details, dreo)
        # Set by _hap003s_mcu_override after device state is loaded when the "midea" or "001" MCU is
        # detected.  When True, _send_command remaps the "auto" mode value to "auto-silent"
        # before transmission because that hardware revision rejects the plain "auto" string.
        self._auto_mode_uses_auto_silent: bool = False
        # Alternate command string to send in place of the plain "auto" mode value for models that
        # reject "auto" (e.g. DR-HAP009S requires "auto-regular").  None means send "auto" unchanged.
        # Takes effect only when _auto_mode_uses_auto_silent is not set.
        self._auto_mode_command_value: str | None = None
        # Remaining filter life in percent ("lifetime"), only for models flagged filter_life_percent.
        self._filter_life: int | None = None
        # Purification toggle. On this model fan speed changes have no physical
        # effect unless purification is on (issue #933).  None if the device doesn't report it.
        self._purify_on: bool | None = None
        self._ambient_light_on: bool | None = None
        self._ambient_light_level: int | None = None
        # RGBIC mode-based ambient light (brightness values physically observed: 30, 50, 70, and 100).
        self._rgbon: bool | None = None
        self._rgbbri: int | None = None
        self._rgbmode: int | None = None
        self._rgbeffectid: str | None = None
        # REST snapshots can lag; a WebSocket report or HA write wins once seen.
        # ``_rgbic_generation`` drops a catalog response when a newer read started
        # or a successful HA effect/color write committed. A failed read releases
        # its claim so an older in-flight response can still apply.
        # ``_skip_next_constant_refresh`` skips one Constant GET after a successful
        # HA color write. DREO is expected to echo that write over WebSocket;
        # expiry limits the impact if that echo never arrives.
        self._rgbic_effect_id_reported = False
        self._skip_next_constant_refresh: float | None = None
        self._rgbic_effect_names: list[str] = []
        self._rgbic_scene_effect_names: list[str] = []
        self._rgbic_effect_id_to_name: dict[str, str] = {}
        self._rgbic_effect_catalog_loaded = False
        self._rgbic_effect_name: str | None = None
        self._rgbic_generation = 0
        self._rgbic_color_effect_name: str | None = None
        self._rgbic_color: tuple[int, int, int] | None = None
        self._rgbic_color_effect_id: str | None = None
        self._rgbic_catalog_refresh_cancel = None
        self._rgbic_catalog_refresh_running = False
        self._rgbic_catalog_refresh_pending = False
        self._rgbic_catalog_refresh_disposed = False
        self._rgbic_mode_authoritative = False

    def parse_speed_range_from_control_node(self, control_node) -> tuple[int, int]:
        """Parse the speed range from a control node"""
        # This is done differently for air purifiers than for other fan types
        for control_item in control_node:
            if control_item.get("value", None) == "manual":
                speed_low = control_item.get("items", None)[0].get("value", None)
                speed_high = control_item.get("items", None)[1].get("value", None)
                speed_range = (speed_low, speed_high)
                return speed_range
        return None

    def parse_preset_modes(self, details: Dict[str, list]) -> tuple[str, str]:
        """Parse the preset modes from the details."""
        preset_modes = []
        controls_conf = details.get("controlsConf", None)
        if controls_conf is not None:
            control = controls_conf.get("control", None)
            if control is not None:
                for control_item in control:
                    if control_item.get("type", None) == "Mode":
                        for mode_item in control_item.get("items", None):
                            value = mode_item.get("value", None)
                            preset_modes.append((value, value))
                    elif control_item.get("type", None) == "Manual":
                        value = control_item.get("value", None)
                        preset_modes.append((value, value))

        preset_modes.sort(key=lambda tup: tup[1])  # sorts in place
        if len(preset_modes) == 0:
            _LOGGER.debug("parse_preset_modes: No preset modes detected")
            preset_modes = None
        _LOGGER.debug("parse_preset_modes: Detected preset modes - %s", preset_modes)
        return preset_modes

    @property
    def oscillating(self) -> bool:
        return None

    @oscillating.setter
    def oscillating(self, value: bool) -> None:
        raise NotImplementedError(f"Attempting to set oscillating on a device that doesn't support ({value})")

    @property
    def filter_life(self) -> int | None:
        """Return the remaining filter life in percent, if the purifier reports it."""
        return self._filter_life

    @property
    def purifyon(self) -> bool | None:
        """Is purification on?"""
        return self._purify_on

    @purifyon.setter
    def purifyon(self, value: bool) -> None:
        """Turn purification on or off"""
        _LOGGER.debug("purifyon: purifyon.setter(%s) --> %s", self.name, value)
        if self._purify_on is None:
            raise NotImplementedError("PyDreoAirPurifier: Attempting to set purifyon on a device that doesn't support.")
        if self._purify_on == value:
            _LOGGER.debug("purifyon: purifyon - value already %s, skipping command", value)
            return
        self._send_command(PURIFYON_KEY, value)

    @property
    def ambient_light_on(self) -> bool | None:
        """Return whether the ambient light is on."""
        return self._ambient_light_on

    @property
    def ambient_light_level(self) -> int | None:
        """Return the last ambient light brightness level."""
        return self._ambient_light_level

    def set_ambient_light(self, on: bool, level: int | None = None) -> None:
        """Send changed power and brightness together."""
        levels = self.device_definition.ambient_light_levels
        if levels is None:
            raise NotImplementedError("Ambient light levels are unsupported.")
        if level is not None and (type(level) is not int or level not in levels):
            raise ValueError(f"Ambient light level must be one of {levels}.")

        params = {RGB_ALWAYS_ON: on}
        if level is not None:
            params[RGB_LEVEL] = level
        self._send_command_batch(params)

    def _finalize_command_params(self, params: dict) -> dict:
        """Skip unchanged light fields after queued changes have been merged."""
        params = super()._finalize_command_params(params)
        if RGB_ALWAYS_ON in params and params[RGB_ALWAYS_ON] == self._ambient_light_on:
            del params[RGB_ALWAYS_ON]
        if RGB_LEVEL in params and params[RGB_LEVEL] == self._ambient_light_level:
            del params[RGB_LEVEL]
        return params

    def _update_ambient_light(self, on: bool | None, level: int | None) -> None:
        """Merge ambient light fields independently when present and valid."""
        levels = self.device_definition.ambient_light_levels
        if levels is not None:
            if isinstance(on, bool):
                self._ambient_light_on = on
            if type(level) is int and level in levels:
                self._ambient_light_level = level

    @property
    def rgbon(self) -> bool | None:
        """Whether the RGBIC mode light is on."""
        return self._rgbon

    @rgbon.setter
    def rgbon(self, value: bool) -> None:
        if not self._device_definition.supports_rgbic_mode_light or self._rgbon is None:
            raise NotImplementedError("RGBIC power is unsupported without reported RGBIC state.")
        if self._rgbon == value:
            return
        self._send_command(RGBON_KEY, value)

    @property
    def rgbbri(self) -> int | None:
        """RGBIC brightness reported by this device."""
        return self._rgbbri

    @rgbbri.setter
    def rgbbri(self, value: int) -> None:
        if not self._device_definition.supports_rgbic_mode_light or self._rgbbri is None:
            raise NotImplementedError("RGBIC brightness is unsupported without reported RGBIC state.")
        value = int(value)
        if self._rgbbri == value:
            return
        self._send_command(RGB_BRI, value)

    @property
    def rgbmode(self) -> int | None:
        """Current RGBIC mode (1=air quality, 2=manual effects)."""
        return self._rgbmode

    @rgbmode.setter
    def rgbmode(self, value: int) -> None:
        """Select one of the two supported RGBIC modes."""
        if not self._device_definition.supports_rgbic_mode_light or self._rgbmode is None:
            raise NotImplementedError("RGBIC mode is unsupported without reported 530S state.")
        if isinstance(value, bool) or not isinstance(value, int) or value not in (1, 2):
            raise ValueError("RGBIC mode must be 1 (air quality) or 2 (manual effects).")
        if self._rgbmode == value:
            return
        self._send_command(RGB_MODE, value)
        with self._lock:
            self._apply_rgbic_mode_locked(value, authoritative=True)
        self._do_callbacks()

    def _apply_rgbic_mode_locked(self, value: int, *, authoritative: bool) -> None:
        """Store mode and drop manual color when indicator mode is active. Caller holds ``_lock``."""
        previous_mode = self._rgbmode
        self._rgbmode = value
        if authoritative:
            self._rgbic_mode_authoritative = True
        if value == 1:
            self._rgbic_effect_name = None
            self._rgbic_color = None
            self._skip_next_constant_refresh = None
        elif previous_mode != value and self._rgbic_effect_name not in self.rgbic_selectable_effect_names:
            self._rgbic_effect_name = None

    def set_rgbic_mode(self, value: int) -> bool:
        """Send a mode command as an ordered WebSocket write."""
        if (
            not self._device_definition.supports_rgbic_mode_light
            or self._rgbmode is None
            or isinstance(value, bool)
            or not isinstance(value, int)
            or value not in (1, 2)
        ):
            return False
        if not self._outbox.flush_now():
            return False
        previous_mode = self._rgbmode
        try:
            self.rgbmode = value
            return self._outbox.flush_now()
        except Exception:
            self._rgbmode = previous_mode
            self._do_callbacks()
            raise

    @property
    def rgbeffectid(self) -> str | None:
        """Last reported RGBIC effect identifier; read-only metadata."""
        return self._rgbeffectid

    @property
    def rgbic_effect_names(self) -> list[str]:
        """Basic effects available from the live RGBIC catalog."""
        return list(self._rgbic_effect_names)

    @property
    def rgbic_scene_effect_names(self) -> list[str]:
        """Scene effects (effectType 3) from the live RGBIC catalog."""
        return list(self._rgbic_scene_effect_names)

    @property
    def rgbic_selectable_effect_names(self) -> list[str]:
        """Basic and scene effect names exposed to Home Assistant."""
        return [*self._rgbic_effect_names, *self._rgbic_scene_effect_names]

    @property
    def rgbic_effect_name(self) -> str | None:
        """Catalog label for the current ``rgbeffectid``, when exactly known."""
        return self._rgbic_effect_name

    @property
    def rgbic_color(self) -> tuple[int, int, int] | None:
        """Last known whole-ring color from a local write or the live catalog."""
        return self._rgbic_color

    def begin_rgbic_catalog_read(self) -> int | None:
        """Claim the next catalog-read generation, or None if the device is disposed."""
        with self._lock:
            if self._rgbic_catalog_refresh_disposed:
                return None
            self._rgbic_generation += 1
            return self._rgbic_generation

    def handle_websocket_reconnect(self) -> None:
        """Let REST seed RGBIC state again after the transport reconnects."""
        if not self._device_definition.supports_rgbic_mode_light:
            return
        with self._lock:
            self._rgbic_mode_authoritative = False
            self._rgbic_effect_id_reported = False
            self._skip_next_constant_refresh = None
            # Invalidate catalog requests started before this reconnect.
            self._rgbic_generation += 1

    def _abandon_rgbic_catalog_read(self, generation: int) -> None:
        """Drop this read's claim when it failed and no newer read or HA write took over."""
        with self._lock:
            if not self._rgbic_catalog_refresh_disposed and self._rgbic_generation == generation:
                self._rgbic_generation -= 1

    @staticmethod
    def _rgbic_whole_color_layout(layout: object) -> bool:
        """True when a catalog layout exposes persisted whole-ring color data."""
        return (
            isinstance(layout, dict)
            and layout.get("viewType") == "SEGMENT_COLOR_LIST"
            and "wholeColorList" in layout
        )

    @staticmethod
    def _rgbic_color_effect(catalog: dict) -> dict | None:
        """Find the unique basic effect exposing whole-ring color in its layouts."""
        candidates = []
        for effect in catalog.get("basicEffects") or []:
            if not isinstance(effect, dict) or effect.get("effectType") != 0:
                continue
            if not effect.get("id") or not effect.get("name") or not effect.get("referencedId"):
                continue
            if any(
                PyDreoAirPurifier._rgbic_whole_color_layout(layout)
                for layout in (effect.get("layouts") or [])
            ):
                candidates.append(effect)
        return candidates[0] if len(candidates) == 1 else None

    @staticmethod
    def _rgbic_color_from_effect(effect: dict | None) -> tuple[int, int, int] | None:
        """Parse wholeColorList hex regardless of whether segments or whole is selected."""
        if effect is None:
            return None
        for layout in effect.get("layouts") or []:
            if not PyDreoAirPurifier._rgbic_whole_color_layout(layout):
                continue
            colors = layout.get("wholeColorList")
            if not isinstance(colors, list) or not colors or not isinstance(colors[0], str):
                continue
            value = colors[0]
            if re.fullmatch(r"#[0-9A-Fa-f]{6}", value) is None:
                continue
            try:
                packed = int(value[1:], 16)
            except ValueError:
                continue
            return ((packed >> 16) & 0xFF, (packed >> 8) & 0xFF, packed & 0xFF)
        return None

    @staticmethod
    def _parse_rgbic_catalog_side_effects(catalog: dict) -> _RgbicCatalogParse:
        """Extract selectable basic/scene effects and Constant whole-ring color."""
        effects = [
            item for item in (catalog.get("basicEffects") or [])
            if isinstance(item, dict)
            and item.get("effectType") == 0
            and item.get("name")
            and item.get("id")
            and item.get("referencedId")
        ]
        scene_effects = [
            item for item in (catalog.get("sceneEffects") or [])
            if isinstance(item, dict)
            and item.get("effectType") == 3
            and item.get("name")
            and item.get("id")
            and item.get("referencedId")
        ]
        scene_effects.sort(
            key=lambda item: (
                item.get("sortOrder") is None,
                item.get("sortOrder", 0),
                item.get("name", ""),
            )
        )
        color_effect = PyDreoAirPurifier._rgbic_color_effect(catalog)
        # DREO's WebSocket rgbeffectid equals the catalog entry `id` for both
        # basicEffects and sceneEffects. `referencedId` is the REST sub-effect
        # resource and is deliberately not used as a lookup key. remoteEffects
        # have a separate schema and are not exposed for this purifier.
        effect_id_to_name = {
            str(item["id"]): item["name"]
            for item in [*effects, *scene_effects]
            if item.get("id") is not None
        }
        whole_ring_color = PyDreoAirPurifier._rgbic_color_from_effect(color_effect)
        return _RgbicCatalogParse(
            effects,
            scene_effects,
            color_effect,
            effect_id_to_name,
            whole_ring_color,
        )

    def set_rgbic_effect_catalog(
        self,
        catalog: dict,
        *,
        expected_rgbic_generation: int | None = None,
    ) -> bool:
        """Store one catalog and apply its color from the live effect id and mode."""
        parsed = self._parse_rgbic_catalog_side_effects(catalog)
        with self._lock:
            if self._rgbic_catalog_refresh_disposed:
                return False
            if expected_rgbic_generation is not None and expected_rgbic_generation != self._rgbic_generation:
                _LOGGER.debug("Ignoring stale RGBIC catalog response")
                return False

            color_effect = parsed.color_effect
            self._rgbic_effect_names = [item["name"] for item in parsed.effects]
            self._rgbic_scene_effect_names = [item["name"] for item in parsed.scene_effects]
            self._rgbic_effect_id_to_name = parsed.effect_id_to_name
            self._rgbic_color_effect_name = color_effect.get("name") if color_effect else None
            self._rgbic_color_effect_id = str(color_effect["id"]) if color_effect else None
            self._rgbic_effect_catalog_loaded = True
            self._rgbic_effect_name = self._rgbic_effect_id_to_name.get(self._rgbeffectid)
            constant_active = (
                self._rgbic_color_effect_id is not None
                and self._rgbeffectid == self._rgbic_color_effect_id
                and self._rgbmode != 1
            )
            self._rgbic_color = parsed.whole_ring_color if constant_active else None
            applied_color = self._rgbic_color

        if constant_active and applied_color is not None:
            _LOGGER.debug("RGBIC catalog color refreshed from DREO RGB=%s", applied_color)
        elif constant_active:
            _LOGGER.debug("RGBIC catalog confirmed no identifiable whole-ring color")
        else:
            _LOGGER.debug("RGBIC catalog color is not active for the reported device state")
        return True

    def fetch_rgbic_catalog(self) -> bool:
        """GET the effect catalog. A failed read leaves the last known state unchanged."""
        generation = self.begin_rgbic_catalog_read()
        if generation is None:
            return False
        try:
            catalog = self._dreo.get_rgbic_effect_catalog(self)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("RGBIC catalog refresh failed for %s", self.name)
            catalog = None
        # Missing data (`None` or `{}`) is a failed read: keep the last catalog and color.
        if not isinstance(catalog, dict) or not catalog:
            self._abandon_rgbic_catalog_read(generation)
            return False
        applied = self.set_rgbic_effect_catalog(catalog, expected_rgbic_generation=generation)
        if not applied:
            self._abandon_rgbic_catalog_read(generation)
        return applied

    def _schedule_rgbic_catalog_refresh(self) -> None:
        """Run one catalog worker, and one more pass when another report arrives mid-read."""
        with self._lock:
            if self._rgbic_catalog_refresh_disposed:
                return
            if self._rgbic_catalog_refresh_running or self._rgbic_catalog_refresh_cancel is not None:
                self._rgbic_catalog_refresh_pending = True
                return
            pending_marker = object()
            self._rgbic_catalog_refresh_cancel = pending_marker

        def _refresh() -> None:
            with self._lock:
                self._rgbic_catalog_refresh_cancel = None
                if self._rgbic_catalog_refresh_disposed:
                    return
                self._rgbic_catalog_refresh_running = True
            try:
                while True:
                    with self._lock:
                        if self._rgbic_catalog_refresh_disposed:
                            self._rgbic_catalog_refresh_running = False
                            return
                        self._rgbic_catalog_refresh_pending = False
                    if self.fetch_rgbic_catalog():
                        self._do_callbacks()
                    with self._lock:
                        if self._rgbic_catalog_refresh_disposed:
                            self._rgbic_catalog_refresh_running = False
                            return
                        if self._rgbic_catalog_refresh_pending:
                            continue
                        self._rgbic_catalog_refresh_running = False
                        return
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("RGBIC catalog refresh processing failed for %s", self.name)
                with self._lock:
                    retry = self._rgbic_catalog_refresh_pending and not self._rgbic_catalog_refresh_disposed
                    self._rgbic_catalog_refresh_running = False
                    self._rgbic_catalog_refresh_pending = False
                    self._rgbic_catalog_refresh_cancel = None
                if retry:
                    self._schedule_rgbic_catalog_refresh()

        try:
            cancel = self._dreo.schedule_call_later(0, _refresh)
        except Exception:
            with self._lock:
                if self._rgbic_catalog_refresh_cancel is pending_marker:
                    self._rgbic_catalog_refresh_cancel = None
            raise
        with self._lock:
            if self._rgbic_catalog_refresh_cancel is pending_marker:
                self._rgbic_catalog_refresh_cancel = cancel
            else:
                cancel()

    def dispose(self) -> None:
        """Cancel a pending RGBIC catalog read before tearing down the device."""
        with self._lock:
            cancel = self._rgbic_catalog_refresh_cancel
            self._rgbic_catalog_refresh_cancel = None
            self._rgbic_catalog_refresh_pending = False
            self._rgbic_catalog_refresh_disposed = True
        if callable(cancel):
            cancel()
        super().dispose()

    def set_rgbic_effect(
        self,
        effect_name: str | None = None,
        color_rgb: tuple[int | float, int | float, int | float] | None = None,
    ) -> bool:
        """Apply a basic/scene effect, or set the catalog's whole-ring color effect."""
        if not self._device_definition.supports_rgbic_mode_light:
            return False

        requested_color: tuple[int, int, int] | None = None
        color_hex: str | None = None
        with self._lock:
            if color_rgb is not None:
                requested_color = tuple(max(0, min(255, int(component))) for component in color_rgb)
                color_hex = "#" + "".join(f"{component:02x}" for component in requested_color)
                effect_name = self._rgbic_color_effect_name
                if effect_name is None:
                    _LOGGER.warning(
                        "RGBIC color change requested for %s but no Constant effect with "
                        "SEGMENT_COLOR_LIST wholeColorList was found in the catalog; "
                        "skipping edit/batch write",
                        self.name,
                    )
                    return False

            if effect_name is None:
                return False
            write_effect_name = effect_name
            is_basic = write_effect_name in self._rgbic_effect_names
            is_scene = write_effect_name in self._rgbic_scene_effect_names
            if self._rgbmode is None or not (is_basic or is_scene):
                return False

        # Drain on/brightness, confirm manual mode, then the REST effect write.
        if not self.set_rgbic_mode(2):
            return False
        if is_scene:
            success = self._dreo.set_rgbic_scene_effect(self, write_effect_name)
        elif color_hex is not None:
            success = self._dreo.set_rgbic_effect(self, write_effect_name, color_hex)
        else:
            success = self._dreo.set_rgbic_effect(self, write_effect_name)
        if not success:
            if requested_color is not None:
                self._schedule_rgbic_catalog_refresh()
            return False

        with self._lock:
            self._rgbic_generation += 1
            self._rgbic_effect_name = write_effect_name
            self._rgbic_color = requested_color
            self._skip_next_constant_refresh = time.monotonic() + 5 if requested_color is not None else None
            self._rgbic_mode_authoritative = True
            self._rgbic_effect_id_reported = True
        self._do_callbacks()
        return True

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("update_state: update_state")
        super().update_state(state)
        if self._device_definition.filter_life_percent:
            self._filter_life = self.get_state_update_value(state, LIFETIME_KEY)
        self._purify_on = self.get_state_update_value(state, PURIFYON_KEY)

        if self.device_definition.ambient_light_levels is not None:
            self._update_ambient_light(
                self.get_state_update_value(state, RGB_ALWAYS_ON),
                self.get_state_update_value(state, RGB_LEVEL),
            )
        if self._device_definition.supports_rgbic_mode_light:
            self._rgbon = self.get_state_update_value(state, RGBON_KEY)
            self._rgbbri = self.get_state_update_value(state, RGB_BRI)
            rest_rgbmode = self.get_state_update_value(state, RGB_MODE)
            effect_id = self.get_state_update_value(state, RGBEFFECTID_KEY)
            with self._lock:
                if (
                    not self._rgbic_mode_authoritative
                    and isinstance(rest_rgbmode, int)
                    and not isinstance(rest_rgbmode, bool)
                ):
                    self._apply_rgbic_mode_locked(rest_rgbmode, authoritative=False)
                if not self._rgbic_effect_id_reported and isinstance(effect_id, (str, int)) and not isinstance(effect_id, bool):
                    effect_id = str(effect_id)
                    changed = effect_id != self._rgbeffectid
                    self._rgbeffectid = effect_id
                    if changed and self._rgbic_color_effect_id is not None and effect_id != self._rgbic_color_effect_id:
                        self._rgbic_color = None
                    if self._rgbic_effect_catalog_loaded:
                        self._rgbic_effect_name = self._rgbic_effect_id_to_name.get(effect_id)

    def handle_server_update(self, message):
        """Process a websocket update"""
        _LOGGER.debug("handle_server_update: handle_server_update")
        super().handle_server_update(message)
        if self._device_definition.filter_life_percent:
            val_filter_life = self.get_server_update_key_value(message, LIFETIME_KEY)
            if isinstance(val_filter_life, int):
                self._filter_life = val_filter_life

        val_purify_on = self.get_server_update_key_value(message, PURIFYON_KEY)
        if isinstance(val_purify_on, bool):
            self._purify_on = val_purify_on

        if self.device_definition.ambient_light_levels is not None:
            self._update_ambient_light(
                self.get_server_update_key_value(message, RGB_ALWAYS_ON),
                self.get_server_update_key_value(message, RGB_LEVEL),
            )

        if not self._device_definition.supports_rgbic_mode_light:
            return

        val_rgbon = self.get_server_update_key_value(message, RGBON_KEY)
        if isinstance(val_rgbon, bool):
            self._rgbon = val_rgbon
        val_rgbbri = self.get_server_update_key_value(message, RGB_BRI)
        if isinstance(val_rgbbri, int) and not isinstance(val_rgbbri, bool):
            self._rgbbri = val_rgbbri

        val_rgbmode = self.get_server_update_key_value(message, RGB_MODE)
        val_effect_id = self.get_server_update_key_value(message, RGBEFFECTID_KEY)
        schedule_catalog_refresh = False
        effect_log: tuple[str, bool] | None = None
        with self._lock:
            if isinstance(val_rgbmode, int) and not isinstance(val_rgbmode, bool):
                self._apply_rgbic_mode_locked(val_rgbmode, authoritative=True)
            if isinstance(val_effect_id, (str, int)) and not isinstance(val_effect_id, bool):
                val_effect_id = str(val_effect_id)
                was_reported = self._rgbic_effect_id_reported
                changed = val_effect_id != self._rgbeffectid
                self._rgbeffectid = val_effect_id
                self._rgbic_effect_id_reported = True
                echo_expired = (
                    self._skip_next_constant_refresh is not None
                    and time.monotonic() >= self._skip_next_constant_refresh
                )
                if echo_expired:
                    self._skip_next_constant_refresh = None
                effect_log = (val_effect_id, changed)
                if self._rgbic_effect_catalog_loaded:
                    self._rgbic_effect_name = self._rgbic_effect_id_to_name.get(val_effect_id)
                elif changed or not was_reported:
                    self._rgbic_effect_name = None
                if changed and self._rgbic_color_effect_id is not None and val_effect_id != self._rgbic_color_effect_id:
                    self._rgbic_color = None

                constant_active = (
                    self._rgbic_effect_catalog_loaded
                    and val_effect_id == self._rgbic_color_effect_id
                    and self._rgbmode != 1
                )
                if not self._rgbic_effect_catalog_loaded:
                    if changed or not was_reported:
                        schedule_catalog_refresh = True
                elif constant_active and self._skip_next_constant_refresh is not None:
                    self._skip_next_constant_refresh = None
                elif constant_active:
                    schedule_catalog_refresh = True
                else:
                    self._skip_next_constant_refresh = None

        if effect_log is not None:
            _LOGGER.debug(
                "Received 530S RGBIC rgbeffectid report=%s changed=%s",
                effect_log[0],
                effect_log[1],
            )
        if schedule_catalog_refresh:
            self._schedule_rgbic_catalog_refresh()

    def _send_command(self, command_key: str, value) -> None:
        """Override to remap the 'auto' mode command for models that reject the plain "auto" string.

        Some hardware/firmware revisions reject the plain "auto" mode command and require a
        variant instead.  Newer DR-HAP003S units ("midea"/"001" MCU) require "auto-silent"
        (_auto_mode_uses_auto_silent); DR-HAP009S requires "auto-regular"
        (_auto_mode_command_value).  The device reports the variant back as its state;
        PyDreoFanBase.preset_mode normalizes mode variants by stripping any "-<suffix>" (so
        "auto-silent"/"auto-regular" resolve to "auto").  This keeps the Home Assistant-facing
        preset name stable across hardware/firmware variants.
        """
        if command_key == "mode" and value == "auto":
            if self._auto_mode_uses_auto_silent:
                value = "auto-silent"
            elif self._auto_mode_command_value is not None:
                value = self._auto_mode_command_value
            if value != "auto":
                _LOGGER.debug("PyDreoAirPurifier._send_command: remapping 'auto' to '%s' for %s", value, self.model)
        super()._send_command(command_key, value)
