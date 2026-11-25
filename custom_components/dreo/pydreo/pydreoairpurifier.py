"""Dreo API for controling air purifiers."""

import logging
import re
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
        # REST snapshots can lag; WebSocket `rgbeffectid` updates take priority
        # once received (the ID may still be wrong — that is a firmware issue).
        #
        # RGBIC catalog synchronization tokens (do not merge without tracing races):
        # - ``_rgbic_catalog_request_revision``: monotonic id per catalog GET intent.
        # - ``_rgbic_catalog_applied_revision``: last catalog response applied to state.
        # - ``_rgbic_catalog_refresh_requested``: WebSocket burst sequence for refresh catch-up.
        # - ``_rgbic_catalog_refresh_running`` / ``_rgbic_catalog_refresh_cancel``:
        #   single refresh worker lifetime.
        # - ``_rgbic_color_write_revision``: invalidates in-flight catalog color applies
        #   after local color changes, mode invalidation, or unconfirmed refresh GETs.
        # - ``_rgbic_effect_write_revision``: same for optimistic ``rgbic_effect_name``
        #   resolution from a stale catalog list.
        # - ``_rgbic_effect_id_reported`` / ``_rgbic_mode_authoritative``:
        #   REST fallbacks for live id/mode.
        # - ``_rgbic_effect_pending``: suppresses effect-name clearing during local writes.
        self._rgbic_effect_id_reported = False
        self._rgbic_effect_names: list[str] = []
        self._rgbic_scene_effect_names: list[str] = []
        self._rgbic_effect_id_to_name: dict[str, str] = {}
        self._rgbic_effect_catalog_loaded = False
        self._rgbic_catalog_request_revision = 0
        self._rgbic_catalog_applied_revision = 0
        self._rgbic_effect_name: str | None = None
        self._rgbic_effect_write_revision = 0
        self._rgbic_color_effect_name: str | None = None
        self._rgbic_color: tuple[int, int, int] | None = None
        self._rgbic_color_effect_id: str | None = None
        self._rgbic_effect_pending = False
        self._rgbic_catalog_refresh_cancel = None
        self._rgbic_catalog_refresh_running = False
        self._rgbic_catalog_refresh_requested = 0
        self._rgbic_color_write_revision = 0
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
        self._set_rgbic_mode_state(value, authoritative=True)
        self._do_callbacks()

    def _invalidate_rgbic_color(self, *, force: bool = False) -> None:
        """Clear an unconfirmed manual color and invalidate in-flight reads."""
        with self._lock:
            if force or self._rgbic_color is not None:
                self._rgbic_color_write_revision += 1
                self._rgbic_color = None

    def _set_rgbic_mode_state(
        self,
        value: int,
        *,
        authoritative: bool,
    ) -> None:
        """Apply local or reported mode state with consistent color invalidation."""
        previous_mode = self._rgbmode
        self._rgbmode = value
        if authoritative:
            # REST may seed startup but must not roll back a local or live mode.
            self._rgbic_mode_authoritative = True
        if value == 1:
            self._rgbic_effect_name = None
            self._invalidate_rgbic_color(force=previous_mode != 1)
        elif previous_mode != value and not self._rgbic_effect_pending:
            if self._rgbic_effect_name not in self.rgbic_selectable_effect_names:
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

    def begin_rgbic_catalog_read(self) -> tuple[int, int, int] | None:
        """Reserve a catalog-read revision and snapshot local write revisions."""
        with self._lock:
            if self._rgbic_catalog_refresh_disposed:
                return None
            self._rgbic_catalog_request_revision += 1
            return (
                self._rgbic_catalog_request_revision,
                self._rgbic_color_write_revision,
                self._rgbic_effect_write_revision,
            )

    @staticmethod
    def _rgbic_color_effect(catalog: dict) -> dict | None:
        """Find the unique basic effect exposing the whole-ring segment layout."""
        candidates = []
        for effect in catalog.get("basicEffects") or []:
            if not isinstance(effect, dict) or effect.get("effectType") != 0:
                continue
            if not effect.get("id") or not effect.get("name") or not effect.get("referencedId"):
                continue
            if any(
                isinstance(layout, dict)
                and layout.get("viewType") == "SEGMENT_COLOR_LIST"
                and layout.get("currentSelected") == "whole"
                and "wholeColorList" in layout
                for layout in (effect.get("layouts") or [])
            ):
                candidates.append(effect)
        return candidates[0] if len(candidates) == 1 else None

    @staticmethod
    def _rgbic_color_from_effect(effect: dict | None) -> tuple[int, int, int] | None:
        """Parse the selected wholeColorList hex value without guessing defaults."""
        if effect is None:
            return None
        for layout in effect.get("layouts") or []:
            if not (
                isinstance(layout, dict)
                and layout.get("viewType") == "SEGMENT_COLOR_LIST"
                and layout.get("currentSelected") == "whole"
            ):
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

    def _apply_rgbic_catalog_color_catalog_locked(
        self,
        *,
        color: tuple[int, int, int] | None,
        constant_effect_id: str | None,
        expected_rgbic_color_write_revision: int | None,
    ) -> None:
        """Apply catalog color using live ``rgbeffectid`` / ``rgbmode``. Caller holds ``_lock``."""
        if (
            expected_rgbic_color_write_revision is not None
            and expected_rgbic_color_write_revision != self._rgbic_color_write_revision
        ):
            _LOGGER.debug(
                "Ignoring initial RGBIC catalog color after a newer local HA write"
            )
            return
        if (
            self._rgbeffectid is not None
            and self._rgbeffectid == constant_effect_id
            and self._rgbmode != 1
        ):
            self._rgbic_color = color
            if color is None:
                _LOGGER.debug(
                    "RGBIC catalog confirmed no identifiable whole-ring color"
                )
            else:
                _LOGGER.debug(
                    "RGBIC catalog loaded persisted whole-ring color RGB=%s",
                    color,
                )
            return
        self._rgbic_color = None
        _LOGGER.debug("RGBIC catalog color is not active for the reported device state")

    def _apply_rgbic_catalog_color_refresh_locked(
        self,
        *,
        color: tuple[int, int, int] | None,
        constant_effect_id: str | None,
        reported_effect_id: str | None,
        reported_rgb_mode: int | None,
        write_revision: int,
        catalog_received: bool,
    ) -> None:
        """Apply refresh color using pre-GET snapshot plus live confirmation. Caller holds ``_lock``."""
        if write_revision != self._rgbic_color_write_revision:
            _LOGGER.debug("Ignoring stale RGBIC catalog color after a newer local HA write")
            return
        if (
            catalog_received
            and color is not None
            and constant_effect_id is not None
            and reported_effect_id == constant_effect_id
            and self._rgbeffectid == constant_effect_id
            and reported_rgb_mode != 1
            and self._rgbmode != 1
        ):
            self._rgbic_color = color
            self._rgbic_color_effect_id = constant_effect_id
            _LOGGER.debug("RGBIC catalog color refreshed from DREO RGB=%s", color)
            return
        # Stale revision responses return above; a matching revision that cannot
        # confirm the active Constant color must clear any unconfirmed display.
        self._rgbic_color_write_revision += 1
        self._rgbic_color = None
        _LOGGER.debug(
            "Cleared unconfirmed RGBIC color after %s catalog response",
            "valid incomplete" if catalog_received else "failed",
        )

    def set_rgbic_effect_catalog(
        self,
        catalog: dict,
        *,
        update_rgbic_color: bool = True,
        expected_rgbic_color_write_revision: int | None = None,
        expected_rgbic_effect_write_revision: int | None = None,
        expected_catalog_revision: int | None = None,
        parsed_catalog: _RgbicCatalogParse | None = None,
    ) -> bool:
        """Cache selectable basic/scene effects and resolve WebSocket IDs by entry id."""
        parsed = parsed_catalog or self._parse_rgbic_catalog_side_effects(catalog)
        effects = parsed.effects
        scene_effects = parsed.scene_effects
        color_effect = parsed.color_effect
        effect_id_to_name = parsed.effect_id_to_name
        color = parsed.whole_ring_color if update_rgbic_color else None
        with self._lock:
            if self._rgbic_catalog_refresh_disposed:
                return False
            if expected_catalog_revision is None:
                self._rgbic_catalog_request_revision += 1
                expected_catalog_revision = self._rgbic_catalog_request_revision
            if expected_catalog_revision <= self._rgbic_catalog_applied_revision:
                _LOGGER.debug(
                    "Ignoring stale RGBIC catalog response revision=%s applied=%s",
                    expected_catalog_revision,
                    self._rgbic_catalog_applied_revision,
                )
                return False

            self._rgbic_catalog_applied_revision = expected_catalog_revision
            self._rgbic_effect_names = [item["name"] for item in effects]
            self._rgbic_color_effect_name = color_effect.get("name") if color_effect else None
            self._rgbic_color_effect_id = str(color_effect["id"]) if color_effect else None
            self._rgbic_scene_effect_names = [item["name"] for item in scene_effects]
            self._rgbic_effect_id_to_name = effect_id_to_name
            self._rgbic_effect_catalog_loaded = True
            if (
                expected_rgbic_effect_write_revision is None
                or expected_rgbic_effect_write_revision == self._rgbic_effect_write_revision
            ):
                self._resolve_rgbic_effect_id()
            else:
                _LOGGER.debug("Preserving newer local RGBIC effect selection after catalog refresh")
            if update_rgbic_color:
                self._apply_rgbic_catalog_color_catalog_locked(
                    color=color,
                    constant_effect_id=self._rgbic_color_effect_id,
                    expected_rgbic_color_write_revision=expected_rgbic_color_write_revision,
                )
        return True

    def _resolve_rgbic_effect_id(self) -> None:
        """Map ``rgbeffectid`` to a catalog name; unknown IDs stay unlabeled."""
        self._rgbic_effect_name = self._rgbic_effect_id_to_name.get(self._rgbeffectid)

    def _clear_rgbic_catalog_refresh_cancel_locked(
        self,
        pending_marker: object,
        cancel_handle: object,
    ) -> None:
        """Drop the refresh handle when this worker still owns it. Caller holds ``_lock``."""
        if self._rgbic_catalog_refresh_cancel is pending_marker or (
            cancel_handle is not None
            and self._rgbic_catalog_refresh_cancel is cancel_handle
        ):
            self._rgbic_catalog_refresh_cancel = None

    def _rgbic_catalog_refresh_pass(self) -> int | None:
        """Run one catalog GET and return its sequence, or None if disposed."""
        with self._lock:
            if self._rgbic_catalog_refresh_disposed:
                return None
            self._rgbic_catalog_request_revision += 1
            catalog_revision = self._rgbic_catalog_request_revision
            sequence = self._rgbic_catalog_refresh_requested
            write_revision = self._rgbic_color_write_revision
            effect_write_revision = self._rgbic_effect_write_revision
            reported_effect_id = self._rgbeffectid
            rgb_mode = self._rgbmode
        _LOGGER.debug(
            "Refreshing RGBIC catalog after WebSocket effect report sequence=%s effect_id=%s",
            sequence,
            reported_effect_id,
        )
        try:
            catalog = self._dreo.get_rgbic_effect_catalog(self)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("RGBIC catalog refresh failed for %s", self.name)
            catalog = None

        parsed_catalog = (
            self._parse_rgbic_catalog_side_effects(catalog) if catalog is not None else None
        )
        color_effect_id = (
            str(parsed_catalog.color_effect["id"]) if parsed_catalog and parsed_catalog.color_effect else None
        )
        color = parsed_catalog.whole_ring_color if parsed_catalog is not None else None

        with self._lock:
            if self._rgbic_catalog_refresh_disposed:
                return None
            if sequence != self._rgbic_catalog_refresh_requested:
                _LOGGER.debug(
                    "RGBIC catalog response superseded by a newer WebSocket event; refreshing again"
                )
                return sequence

        if catalog is not None:
            catalog_applied = self.set_rgbic_effect_catalog(
                catalog,
                update_rgbic_color=False,
                expected_rgbic_effect_write_revision=effect_write_revision,
                expected_catalog_revision=catalog_revision,
                parsed_catalog=parsed_catalog,
            )
            if not catalog_applied:
                with self._lock:
                    return None if self._rgbic_catalog_refresh_disposed else sequence

        with self._lock:
            if self._rgbic_catalog_refresh_disposed:
                return None
            if sequence != self._rgbic_catalog_refresh_requested:
                return sequence
            if catalog_revision < self._rgbic_catalog_applied_revision:
                _LOGGER.debug(
                    "Ignoring stale RGBIC catalog response revision=%s applied=%s",
                    catalog_revision,
                    self._rgbic_catalog_applied_revision,
                )
                return sequence
            if effect_write_revision != self._rgbic_effect_write_revision:
                _LOGGER.debug("Preserving newer local RGBIC effect selection after stale catalog read")
            self._apply_rgbic_catalog_color_refresh_locked(
                color=color,
                constant_effect_id=color_effect_id,
                reported_effect_id=reported_effect_id,
                reported_rgb_mode=rgb_mode,
                write_revision=write_revision,
                catalog_received=catalog is not None,
            )

        if catalog is not None or self._rgbic_color is None:
            self._do_callbacks()
        return sequence

    def _schedule_rgbic_catalog_refresh(self) -> None:
        """Refresh the catalog once per WebSocket burst, then catch up newer events."""
        with self._lock:
            if self._rgbic_catalog_refresh_disposed:
                return
            self._rgbic_catalog_refresh_requested += 1
            if self._rgbic_catalog_refresh_running or self._rgbic_catalog_refresh_cancel is not None:
                return
            pending_marker = object()
            self._rgbic_catalog_refresh_cancel = pending_marker

        cancel_handle = None

        def _refresh() -> None:
            with self._lock:
                self._clear_rgbic_catalog_refresh_cancel_locked(pending_marker, cancel_handle)
                if self._rgbic_catalog_refresh_disposed:
                    return
                self._rgbic_catalog_refresh_running = True

            attempted_sequence = None
            try:
                while True:
                    with self._lock:
                        if self._rgbic_catalog_refresh_disposed:
                            self._rgbic_catalog_refresh_running = False
                            self._clear_rgbic_catalog_refresh_cancel_locked(pending_marker, cancel_handle)
                            return
                        attempted_sequence = self._rgbic_catalog_refresh_requested

                    completed_sequence = self._rgbic_catalog_refresh_pass()

                    with self._lock:
                        if self._rgbic_catalog_refresh_disposed or completed_sequence is None:
                            self._rgbic_catalog_refresh_running = False
                            self._clear_rgbic_catalog_refresh_cancel_locked(pending_marker, cancel_handle)
                            return
                        if completed_sequence != self._rgbic_catalog_refresh_requested:
                            continue

                        # Check the sequence and release the running flag atomically.
                        # An event after this point sees an idle worker and schedules
                        # another one; an earlier event is caught by the comparison.
                        self._rgbic_catalog_refresh_running = False
                        self._clear_rgbic_catalog_refresh_cancel_locked(pending_marker, cancel_handle)
                        return
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("RGBIC catalog refresh processing failed for %s", self.name)
                with self._lock:
                    retry_for_new_event = (
                        not self._rgbic_catalog_refresh_disposed
                        and attempted_sequence is not None
                        and attempted_sequence != self._rgbic_catalog_refresh_requested
                    )
                    self._rgbic_catalog_refresh_running = False
                    self._clear_rgbic_catalog_refresh_cancel_locked(pending_marker, cancel_handle)
                if retry_for_new_event:
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
                cancel_handle = cancel
                self._rgbic_catalog_refresh_cancel = cancel
            else:
                cancel()

    def dispose(self) -> None:
        """Cancel a pending RGBIC catalog read before tearing down the device."""
        with self._lock:
            cancel = self._rgbic_catalog_refresh_cancel
            self._rgbic_catalog_refresh_cancel = None
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
        requested_color: tuple[int, int, int] | None = None
        color_hex: str | None = None
        if color_rgb is not None:
            requested_color = tuple(max(0, min(255, int(component))) for component in color_rgb)
            color_hex = "#" + "".join(f"{component:02x}" for component in requested_color)
            effect_name = self._rgbic_color_effect_name

        if effect_name is None:
            return False
        is_basic = effect_name in self._rgbic_effect_names
        is_scene = effect_name in self._rgbic_scene_effect_names
        if (
            not self._device_definition.supports_rgbic_mode_light
            or self._rgbmode is None
            or not (is_basic or is_scene)
        ):
            return False

        with self._lock:
            # Pre-write bump: any catalog read that captured the prior revision
            # must not apply color or resolve effect names while REST is in flight.
            self._rgbic_color_write_revision += 1
            self._rgbic_effect_write_revision += 1

        self._rgbic_effect_pending = True
        try:
            # First drain on/brightness writes from the light action. Then send
            # rgbmode=2 and wait for its control reply before the dependent REST POST.
            if not self.set_rgbic_mode(2):
                self._rgbic_effect_pending = False
                return False
            if is_scene:
                success = self._dreo.set_rgbic_scene_effect(self, effect_name)
            elif color_hex is not None:
                success = self._dreo.set_rgbic_effect(self, effect_name, color_hex)
            else:
                success = self._dreo.set_rgbic_effect(self, effect_name)
        except Exception:
            self._rgbic_effect_pending = False
            raise
        if success:
            # DREO does not ACK effect names; keep the HA-requested label until
            # `rgbeffectid` reports a different catalog id (or an unknown id).
            with self._lock:
                # Post-write bump: separates the in-flight epoch from the committed
                # HA selection so reads that observed only the pre-write revision
                # still cannot apply a stale catalog over the finished write.
                self._rgbic_color_write_revision += 1
                self._rgbic_effect_write_revision += 1
                self._rgbic_effect_name = effect_name
                self._rgbic_color = requested_color
                if requested_color is not None:
                    self._rgbic_color_effect_id = next(
                        (
                            effect_id
                            for effect_id, name in self._rgbic_effect_id_to_name.items()
                            if name == effect_name
                        ),
                        None,
                    )
                self._rgbic_effect_pending = False
                self._rgbic_mode_authoritative = True
                self._rgbic_effect_id_reported = True
            self._do_callbacks()
        else:
            with self._lock:
                self._rgbic_effect_pending = False
            if requested_color is not None:
                self._schedule_rgbic_catalog_refresh()
        return success

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
            if (
                not self._rgbic_mode_authoritative
                and isinstance(rest_rgbmode, int)
                and not isinstance(rest_rgbmode, bool)
            ):
                self._set_rgbic_mode_state(rest_rgbmode, authoritative=False)
            effect_id = self.get_state_update_value(state, RGBEFFECTID_KEY)
            # REST may prime startup; a live WebSocket report or successful local
            # effect write makes later REST IDs stale until the next live report.
            if not self._rgbic_effect_id_reported:
                if effect_id is not None:
                    self._rgbeffectid = str(effect_id)
                    if self._rgbic_effect_catalog_loaded:
                        self._resolve_rgbic_effect_id()

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

        if self._device_definition.supports_rgbic_mode_light:
            val_rgbon = self.get_server_update_key_value(message, RGBON_KEY)
            if isinstance(val_rgbon, bool):
                self._rgbon = val_rgbon
            val_rgbbri = self.get_server_update_key_value(message, RGB_BRI)
            if isinstance(val_rgbbri, int) and not isinstance(val_rgbbri, bool):
                self._rgbbri = val_rgbbri
            val_rgbmode = self.get_server_update_key_value(message, RGB_MODE)
            if isinstance(val_rgbmode, int) and not isinstance(val_rgbmode, bool):
                self._set_rgbic_mode_state(val_rgbmode, authoritative=True)
            val_effect_id = self.get_server_update_key_value(message, RGBEFFECTID_KEY)
            if isinstance(val_effect_id, (str, int)) and not isinstance(val_effect_id, bool):
                val_effect_id = str(val_effect_id)
                previous_effect_id = self._rgbeffectid
                was_reported = self._rgbic_effect_id_reported
                self._rgbeffectid = val_effect_id
                self._rgbic_effect_id_reported = True
                effect_id_changed = val_effect_id != previous_effect_id
                _LOGGER.debug(
                    "Received 530S RGBIC rgbeffectid report=%s changed=%s",
                    val_effect_id,
                    effect_id_changed,
                )
                if effect_id_changed or not was_reported:
                    if self._rgbic_effect_catalog_loaded:
                        self._resolve_rgbic_effect_id()
                    else:
                        self._rgbic_effect_name = None
                    self._rgbic_effect_pending = False
                    if effect_id_changed and val_effect_id != self._rgbic_color_effect_id:
                        with self._lock:
                            self._rgbic_color_write_revision += 1
                            self._rgbic_color = None
                constant_color_active = (
                    self._rgbic_effect_catalog_loaded
                    and val_effect_id == self._rgbic_color_effect_id
                    and self._rgbmode != 1
                )
                if constant_color_active or not self._rgbic_effect_catalog_loaded:
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
