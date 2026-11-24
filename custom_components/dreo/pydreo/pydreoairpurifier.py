"""Dreo API for controling air purifiers."""

import logging
from typing import TYPE_CHECKING, Dict

from .constant import LIFETIME_KEY, PURIFYON_KEY, RGBON_KEY, RGB_BRI, RGB_MODE, RGBEFFECTID_KEY
from .pydreofanbase import PyDreoFanBase
from .models import DreoDeviceDetails

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pydreo import PyDreo


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
        # RGBIC mode-based ambient light (brightness values physically observed: 30, 50, 70, and 100).
        self._rgbon: bool | None = None
        self._rgbbri: int | None = None
        self._rgbmode: int | None = None
        self._rgbeffectid: str | None = None
        self._rgbic_effect_names: list[str] = []
        self._rgbic_scene_effect_names: list[str] = []
        self._rgbic_effect_id_to_name: dict[str, str] = {}
        self._rgbic_effect_catalog_loaded = False
        self._rgbic_effect_name: str | None = None
        self._rgbic_effect_pending = False
        self._rgbic_catalog_refresh_cancel = None

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
        self._rgbmode = value
        if value == 1:
            self._rgbic_effect_name = None
        elif not self._rgbic_effect_pending and self._rgbic_effect_name not in self.rgbic_selectable_effect_names:
            self._rgbic_effect_name = None
        self._do_callbacks()

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
        """Best known selected manual effect name."""
        return self._rgbic_effect_name

    def set_rgbic_effect_catalog(self, catalog: dict) -> None:
        """Cache selectable basic/scene effects and resolve WebSocket IDs by entry id."""
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
        self._rgbic_effect_names = [item["name"] for item in effects]
        self._rgbic_scene_effect_names = [item["name"] for item in scene_effects]
        # DREO's WebSocket rgbeffectid equals the catalog entry `id` for both
        # basicEffects and sceneEffects. `referencedId` is the REST sub-effect
        # resource and is deliberately not used as a lookup key. remoteEffects
        # have a separate schema and are not exposed for this purifier.
        self._rgbic_effect_id_to_name = {
            str(item["id"]): item["name"]
            for item in [*effects, *scene_effects]
            if item.get("id") is not None
        }
        self._rgbic_effect_catalog_loaded = True
        self._resolve_rgbic_effect_id()

    def _resolve_rgbic_effect_id(self) -> None:
        """Resolve the current device ID from the localized selectable catalog."""
        self._rgbic_effect_name = self._rgbic_effect_id_to_name.get(self._rgbeffectid)

    def _schedule_rgbic_catalog_refresh(self) -> None:
        """Load the catalog once when an effect ID arrives before the catalog."""
        pending_marker = object()
        with self._lock:
            if self._rgbic_catalog_refresh_cancel is not None:
                return
            self._rgbic_catalog_refresh_cancel = pending_marker

        def _refresh() -> None:
            with self._lock:
                if self._rgbic_catalog_refresh_cancel is pending_marker:
                    self._rgbic_catalog_refresh_cancel = None
            try:
                catalog = self._dreo.get_rgbic_effect_catalog(self)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("RGBIC catalog refresh failed for %s", self.name)
                return
            if catalog is not None:
                self.set_rgbic_effect_catalog(catalog)
            # The WebSocket update itself must reach HA even when the catalog
            # request fails or cannot resolve the ID.
            self._do_callbacks()

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
        if callable(cancel):
            cancel()
        super().dispose()

    def set_rgbic_effect(self, effect_name: str) -> bool:
        """Apply a basic or scene effect after the observed WebSocket mode transition."""
        is_basic = effect_name in self._rgbic_effect_names
        is_scene = effect_name in self._rgbic_scene_effect_names
        if (
            not self._device_definition.supports_rgbic_mode_light
            or self._rgbmode is None
            or not (is_basic or is_scene)
        ):
            return False

        self._rgbic_effect_pending = True
        try:
            # First drain on/brightness writes from the light action. Then send
            # rgbmode=2 and wait for its control reply before the dependent REST POST.
            if not self.set_rgbic_mode(2):
                self._rgbic_effect_pending = False
                return False
            if is_scene:
                success = self._dreo.set_rgbic_scene_effect(self, effect_name)
            else:
                success = self._dreo.set_rgbic_effect(self, effect_name)
        except Exception:
            self._rgbic_effect_pending = False
            raise
        if success:
            # The catalog may omit its selected marker even though the effect POST
            # succeeded. Keep the requested name optimistically until a different
            # device effect ID is reported; no correlated ACK is exposed by DREO.
            self._rgbic_effect_name = effect_name
            self._rgbic_effect_pending = False
            self._do_callbacks()
        else:
            self._rgbic_effect_pending = False
        return success

    def update_state(self, state: dict):
        """Process the state dictionary from the REST API."""
        _LOGGER.debug("update_state: update_state")
        super().update_state(state)
        if self._device_definition.filter_life_percent:
            self._filter_life = self.get_state_update_value(state, LIFETIME_KEY)
        self._purify_on = self.get_state_update_value(state, PURIFYON_KEY)
        if self._device_definition.supports_rgbic_mode_light:
            self._rgbon = self.get_state_update_value(state, RGBON_KEY)
            self._rgbbri = self.get_state_update_value(state, RGB_BRI)
            self._rgbmode = self.get_state_update_value(state, RGB_MODE)
            effect_id = self.get_state_update_value(state, RGBEFFECTID_KEY)
            self._rgbeffectid = str(effect_id) if effect_id is not None else None

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

        if self._device_definition.supports_rgbic_mode_light:
            val_rgbon = self.get_server_update_key_value(message, RGBON_KEY)
            if isinstance(val_rgbon, bool):
                self._rgbon = val_rgbon
            val_rgbbri = self.get_server_update_key_value(message, RGB_BRI)
            if isinstance(val_rgbbri, int) and not isinstance(val_rgbbri, bool):
                self._rgbbri = val_rgbbri
            val_rgbmode = self.get_server_update_key_value(message, RGB_MODE)
            if isinstance(val_rgbmode, int) and not isinstance(val_rgbmode, bool):
                previous_mode = self._rgbmode
                self._rgbmode = val_rgbmode
                if val_rgbmode == 1 or (previous_mode != val_rgbmode and not self._rgbic_effect_pending):
                    self._rgbic_effect_name = None
            val_effect_id = self.get_server_update_key_value(message, RGBEFFECTID_KEY)
            if isinstance(val_effect_id, (str, int)) and not isinstance(val_effect_id, bool):
                val_effect_id = str(val_effect_id)
                previous_effect_id = self._rgbeffectid
                self._rgbeffectid = val_effect_id
                if val_effect_id != previous_effect_id:
                    # The catalog `id` is the verified WebSocket identifier.
                    # Resolve immediately when cached; otherwise fetch once.
                    if self._rgbic_effect_catalog_loaded:
                        self._resolve_rgbic_effect_id()
                    else:
                        self._rgbic_effect_name = None
                        self._schedule_rgbic_catalog_refresh()
                    self._rgbic_effect_pending = False

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
