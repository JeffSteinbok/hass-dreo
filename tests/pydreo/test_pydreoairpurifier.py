"""Tests for Dreo Fans"""

# pylint: disable=used-before-assignment
import logging
from copy import copy
from collections.abc import Callable
from threading import Barrier, Event, Lock, Thread
from unittest.mock import MagicMock, patch

import pytest

from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HAP010S_BASIC_EFFECT_NAMES = [
    "Respirar",
    "Centelleo",
    "Latido",
    "Arcoiris",
    "Oleaje",
    "Respirar lento",
    "Luz constante",
    "Brillo suave",
]

HAP010S_SCENE_EFFECT_NAMES = [
    "Wave",
    "Cherry Blossom",
    "Christmas",
    "Halloween",
    "Birthday Party",
    "Firefly",
]


class _GateLock:
    """Non-reentrant lock wrapper that can delay release for overlap tests."""

    def __init__(self, inner: Lock):
        self._inner = inner
        self.delay_release = False
        self.delay_from_release = 1
        self._releases_seen = 0
        self.hold_reached = Event()
        self.continue_release = Event()
        self.acquire_contended = Event()

    def acquire(self, blocking: bool = True):
        if blocking and self._inner.locked():
            self.acquire_contended.set()
        return self._inner.acquire(blocking)

    def release(self):
        self._releases_seen += 1
        if (
            self.delay_release
            and self._inner.locked()
            and self._releases_seen >= self.delay_from_release
        ):
            self.hold_reached.set()
            if not self.continue_release.wait(timeout=5.0):
                self.continue_release.set()
            self.delay_release = False
        self._inner.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        del exc_type, exc, tb
        self.release()


def _start_thread(
    target: Callable[..., object],
    /,
    *args,
    daemon: bool = True,
    **kwargs,
) -> tuple[Thread, list[BaseException]]:
    """Start a thread and collect any uncaught exception for later propagation."""
    errors: list[BaseException] = []

    def _run() -> None:
        try:
            target(*args, **kwargs)
        except BaseException as exc:  # pragma: no cover - test helper
            errors.append(exc)

    thread = Thread(target=_run, daemon=daemon)
    thread.start()
    return thread, errors


def _join_thread(thread: Thread, errors: list[BaseException], *, timeout: float = 5.0) -> None:
    thread.join(timeout=timeout)
    if thread.is_alive():
        raise AssertionError("background thread did not finish before timeout")
    if errors:
        raise errors[0]


def _hap010s_rgbic_catalog() -> dict:
    """Catalog fixture with eight basics and six scenes (IDs are synthetic, not production)."""
    basics = [
        {
            "id": f"catalog-basic-id-{index}",
            "referencedId": f"catalog-basic-ref-{index}",
            "effectType": 0,
            "name": name,
            "layouts": [{"effectParamKey": "speedValue", "viewType": "SPEED"}],
        }
        for index, name in enumerate(HAP010S_BASIC_EFFECT_NAMES, start=1)
    ]
    scenes = [
        {
            "id": f"catalog-scene-id-{index}",
            "referencedId": f"catalog-scene-ref-{index}",
            "effectType": 3,
            "name": name,
            "layouts": [],
            "sortOrder": 12 + index,
        }
        for index, name in enumerate(HAP010S_SCENE_EFFECT_NAMES, start=1)
    ]
    return {"basicEffects": basics, "sceneEffects": scenes}


def _ack_control_send(manager, device, params: dict) -> None:
    manager._transport_consume_message(
        {
            "devicesn": device.serial_number,
            "method": "control-report",
            "reported": params,
        }
    )


class TestPyDreoAirPurifier(TestBase):
    """Test TestPyDreoAirPurifier class."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("#aBcD09", (171, 205, 9)),
            ("#000000", (0, 0, 0)),
            ("#FFFFFF", (255, 255, 255)),
        ],
    )
    def test_rgbic_color_from_effect_accepts_six_digit_hex(self, value, expected):
        """A whole-ring color must parse exactly six hexadecimal digits."""
        effect = {
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": [value],
            }]
        }
        assert PyDreoAirPurifier._rgbic_color_from_effect(effect) == expected

    @pytest.mark.parametrize(
        "value",
        [
            "#abcde",
            "#1234567",
            "123456",
            "##123456",
            "#12G456",
            " #123456",
            "#１２３４５６",
        ],
    )
    def test_rgbic_color_from_effect_rejects_invalid_hex(self, value):
        """Malformed or non-RGB hex values must not be treated as colors."""
        effect = {
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": [value],
            }]
        }
        assert PyDreoAirPurifier._rgbic_color_from_effect(effect) is None

    @staticmethod
    def _constant_catalog_effect(
        *,
        current_selected: str,
        whole_color: str = "#0066ff",
        effect_id: str = "constant-id",
        effect_name: str = "Constante",
        color_list: list[str] | None = None,
    ) -> dict:
        layout: dict = {
            "viewType": "SEGMENT_COLOR_LIST",
            "currentSelected": current_selected,
            "wholeColorList": [whole_color],
        }
        if color_list is not None:
            layout["colorList"] = list(color_list)
        return {
            "basicEffects": [{
                "id": effect_id,
                "referencedId": "constant-ref",
                "effectType": 0,
                "name": effect_name,
                "layouts": [layout],
            }],
        }

    def test_rgbic_color_effect_detects_constant_whole_mode(self):
        """Constant is found when the DREO app saved whole-ring mode."""
        catalog = self._constant_catalog_effect(current_selected="whole")
        effect = PyDreoAirPurifier._rgbic_color_effect(catalog)
        assert effect is not None
        assert effect["name"] == "Constante"

    def test_rgbic_color_effect_detects_constant_segments_mode(self):
        """Constant is found when the DREO app saved segments mode."""
        catalog = self._constant_catalog_effect(current_selected="segment")
        effect = PyDreoAirPurifier._rgbic_color_effect(catalog)
        assert effect is not None
        assert effect["name"] == "Constante"

    def test_rgbic_color_from_effect_reads_whole_color_in_segments_mode(self):
        """wholeColorList color is read while segments is selected in the catalog."""
        effect = self._constant_catalog_effect(current_selected="segment")["basicEffects"][0]
        assert PyDreoAirPurifier._rgbic_color_from_effect(effect) == (0, 102, 255)

    def test_HAP010S_color_write_from_segments_catalog_forces_whole(self):  # pylint: disable=invalid-name
        """A color write from a segments catalog edits wholeColorList and selects whole."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2}})
        segment_colors = [
            "#110022",
            "#220044",
            "#330066",
            "#440088",
            "#5500aa",
        ]
        catalog = self._constant_catalog_effect(
            current_selected="segment",
            color_list=segment_colors,
        )
        device.set_rgbic_effect_catalog(catalog)
        assert device._rgbic_color_effect_name == "Constante"

        posted_payloads: list = []

        def fake_send(dev, params):
            _ack_control_send(self.pydreo_manager, dev, params)

        def fake_call_api(_url, api, _method, payload, _headers):
            if api == "/api/device/rgb-effect/all/list":
                return {"code": 0, "data": catalog}, 200
            if api == "/api/device/rgb-effect/edit/batch":
                posted_payloads.append(payload)
                return {"code": 0, "data": {}}, 200
            return None, 500

        with patch(PATCH_SEND_COMMAND, side_effect=fake_send), patch(
            "custom_components.dreo.pydreo.Helpers.call_api",
            side_effect=fake_call_api,
        ):
            assert device.set_rgbic_effect(color_rgb=(255, 128, 64)) is True

        layout = posted_payloads[0][0]["subEffects"][0]["layouts"][0]
        assert layout["currentSelected"] == "whole"
        assert layout["wholeColorList"] == ["#ff8040"]
        assert layout["colorList"] == segment_colors
        assert device.rgbic_color == (255, 128, 64)

    def test_HAP010S_color_write_before_catalog_loaded_logs_warning(self, caplog):  # pylint: disable=invalid-name
        """A color request before the catalog loads fails without edit/batch writes."""
        caplog.set_level(logging.WARNING, logger="custom_components.dreo.pydreo.pydreoairpurifier")
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2}})
        assert device._rgbic_color_effect_name is None
        assert device._rgbic_effect_catalog_loaded is False

        with patch.object(device._dreo, "set_rgbic_effect") as mock_write, patch(
            "custom_components.dreo.pydreo.Helpers.call_api"
        ) as mock_api:
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is False

        mock_write.assert_not_called()
        mock_api.assert_not_called()
        assert "no Constant effect" in caplog.text
        assert "SEGMENT_COLOR_LIST wholeColorList" in caplog.text

    def test_HAP010S_color_write_without_constant_logs_warning(self, caplog):  # pylint: disable=invalid-name
        """A color request without a Constant layout fails and logs a clear warning."""
        caplog.set_level(logging.WARNING, logger="custom_components.dreo.pydreo.pydreoairpurifier")
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2}})
        device.set_rgbic_effect_catalog({
            "basicEffects": [{
                "id": "no-color-basic",
                "referencedId": "no-color-ref",
                "effectType": 0,
                "name": "Respirar",
                "layouts": [{"viewType": "SPEED", "value": 50}],
            }],
        })

        with patch.object(device._dreo, "set_rgbic_effect") as mock_write:
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is False

        mock_write.assert_not_called()
        assert "no Constant effect" in caplog.text
        assert "SEGMENT_COLOR_LIST wholeColorList" in caplog.text

    def test_HAP002S(self):  # pylint: disable=invalid-name
        """Test DR-HAP002S Air Purifier (Macro Pro S)."""

        self.get_devices_file_name = "get_devices_HAP002S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP002S"
        assert air_purifier.series_name == "Macro Pro S"
        assert air_purifier.speed_range == (1, 18)
        assert air_purifier.preset_modes == ["manual"]

    def test_HAP003S(self):  # pylint: disable=invalid-name
        """Test DR-HAP003S Air Purifier (Macro Max S) — original revision ("meidi" MCU).

        The original hardware revision uses "auto" as both the command and the state value.
        Setting preset_mode to "auto" must send the unchanged "auto" string.
        """

        self.get_devices_file_name = "get_devices_HAP003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP003S"
        assert air_purifier.series_name == "Macro Max S"
        assert air_purifier.speed_range == (1, 18)
        assert air_purifier.preset_modes == ["auto", "manual", "sleep", "turbo"]
        # Original revision must NOT have the auto-silent remap flag set
        assert air_purifier._auto_mode_uses_auto_silent is False  # pylint: disable=protected-access
        # And must not carry the HAP009S auto-regular command override
        assert air_purifier._auto_mode_command_value is None  # pylint: disable=protected-access

        # Setting auto on the original revision must send "auto" unchanged
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "sleep"  # move away from current mode first
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "sleep"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "auto"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "auto"})

    def test_HAP003S_2(self):  # pylint: disable=invalid-name
        """Test DR-HAP003S Air Purifier (Macro Max S/AS) — newer "midea" MCU revision.

        This hardware revision rejects the plain "auto" mode command.  The device requires
        "auto-silent" to be sent.  The _auto_mode_uses_auto_silent flag must be set by the
        MCU override, and preset_mode="auto" must translate to command value "auto-silent".
        State updates reporting "auto-silent" must still resolve to preset_mode "auto".
        """

        self.get_devices_file_name = "get_devices_HAP003S_2.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP003S"
        assert air_purifier.series_name == "Macro Max S/AS"
        assert air_purifier.speed_range == (1, 18)
        assert air_purifier.preset_modes == ["auto", "manual", "sleep", "turbo"]
        # Newer "midea" MCU revision must have the auto-silent remap flag set
        assert air_purifier._auto_mode_uses_auto_silent is True  # pylint: disable=protected-access

        # Setting auto on the new revision must send "auto-silent"
        with patch(PATCH_SEND_COMMAND):
            air_purifier.preset_mode = "sleep"  # move away from current mode first
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "sleep"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "auto"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "auto-silent"})

        # Other modes must remain unchanged
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto-silent"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "sleep"})

        # State updates with "auto-silent" must resolve to preset_mode "auto"
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto-silent"}})
        assert air_purifier.preset_mode == "auto"

    def test_HAP003S_3(self):  # pylint: disable=invalid-name
        """Test DR-HAP003S Air Purifier (Macro Max S/AS) — newer "001" MCU revision.

        This hardware revision (firmware v1.0.51) also rejects the plain "auto" mode command.
        The device requires "auto-silent" to be sent.  The _auto_mode_uses_auto_silent flag
        must be set by the MCU override, and preset_mode="auto" must translate to command
        value "auto-silent". State updates reporting "auto-silent" must still resolve to
        preset_mode "auto".
        """

        self.get_devices_file_name = "get_devices_HAP003S_3.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP003S"
        assert air_purifier.series_name == "Macro Max S/AS"
        assert air_purifier.speed_range == (1, 18)
        assert air_purifier.preset_modes == ["auto", "manual", "sleep", "turbo"]
        # Newer "001" MCU revision must have the auto-silent remap flag set
        assert air_purifier._auto_mode_uses_auto_silent is True  # pylint: disable=protected-access

        # Setting auto on the new revision must send "auto-silent"
        with patch(PATCH_SEND_COMMAND):
            air_purifier.preset_mode = "sleep"  # move away from current mode first
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "sleep"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "auto"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "auto-silent"})

        # Other modes must remain unchanged
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto-silent"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "sleep"})

        # State updates with "auto-silent" must resolve to preset_mode "auto"
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto-silent"}})
        assert air_purifier.preset_mode == "auto"

    def test_HAP003S_4(self):  # pylint: disable=invalid-name
        """Test DR-HAP003S Air Purifier (Macro Max S/AS) with the "SC95F8616B-2/US" MCU (issue #957).

        Fixture from the issue's diagnostics. These units reject plain "auto" ("instruction
        validate failed", 500003), report their auto state as "auto-regular", and switch to
        auto when sent "auto-regular".
        """

        self.get_devices_file_name = "get_devices_HAP003S_4.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP003S"
        assert air_purifier.series_name == "Macro Max S/AS"
        assert air_purifier.speed_range == (1, 18)
        assert air_purifier.preset_modes == ["auto", "manual", "sleep", "turbo"]
        assert air_purifier._auto_mode_uses_auto_silent is False  # pylint: disable=protected-access
        # The diagnostics report the auto state as "auto-regular"
        assert air_purifier.preset_mode == "auto"

        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "turbo"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "auto"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "auto-regular"})
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto-regular"}})
        assert air_purifier.preset_mode == "auto"

        # turbo, sleep and manual are sent unchanged
        for mode in ("turbo", "sleep", "manual"):
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                air_purifier.preset_mode = mode
                mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: mode})
            air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: mode}})

    def test_HAP005S(self):  # pylint: disable=invalid-name
        """Test DR-HAP005S Air Purifier (Macro AP505S)."""

        self.get_devices_file_name = "get_devices_HAP005S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP005S"
        assert air_purifier.series_name == "Macro AP505S"
        assert air_purifier.speed_range == (1, 4)
        assert air_purifier.preset_modes == ["manual"]

    def test_HAP007S(self):  # pylint: disable=invalid-name
        """Test DR-HAP007S Air Purifier (337S/337AS) with empty controlsConf."""

        self.get_devices_file_name = "get_devices_HAP007S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP007S"
        assert air_purifier.series_name == "337S/337AS"
        assert air_purifier.speed_range == (1, 4)
        assert air_purifier.preset_modes == ["auto", "manual", "sleep", "turbo"]
        assert air_purifier.preset_mode == "turbo"
        assert air_purifier.filter_life == 89
        assert air_purifier.is_feature_supported("filter_life")

        # Rejects plain "auto" ("instruction validate failed") and requires "auto-regular"
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "sleep"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "auto"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "auto-regular"})
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto-regular"}})
        assert air_purifier.preset_mode == "auto"

        # Filter life also arrives over the websocket
        air_purifier.handle_server_update({REPORTED_KEY: {"lifetime": 88}})
        assert air_purifier.filter_life == 88

    def test_HAP009S(self):  # pylint: disable=invalid-name
        """Test DR-HAP009S Air Purifier with empty controlsConf."""

        self.get_devices_file_name = "get_devices_HAP009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP009S"
        assert air_purifier.series_name == "539S/539AS"
        assert air_purifier.speed_range == (1, 4)
        assert air_purifier.preset_modes == ["auto", "manual", "sleep", "turbo"]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "sleep"})

        # DR-HAP009S rejects plain "auto" and requires "auto-regular" (issue #860)
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "sleep"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "auto"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "auto-regular"})

        # State updates reporting "auto-regular" must resolve back to preset_mode "auto"
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto-regular"}})
        assert air_purifier.preset_mode == "auto"

        # Other preset modes must be sent unchanged (no auto remap leakage)
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto-regular"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "turbo"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "turbo"})

    def test_HAP009S_auto_regular_override_flag(self):  # pylint: disable=invalid-name
        """DR-HAP009S must set the auto-regular command override and NOT the auto-silent flag."""
        self.get_devices_file_name = "get_devices_HAP009S.json"
        self.pydreo_manager.load_devices()
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP009S"
        # pylint: disable=protected-access
        assert air_purifier._auto_mode_command_value == "auto-regular"
        assert air_purifier._auto_mode_uses_auto_silent is False
        # pylint: enable=protected-access

    def test_HAP008S(self):  # pylint: disable=invalid-name
        """Test DR-HAP008S Air Purifier with empty controlsConf."""
        self.get_devices_file_name = "get_devices_HAP008S.json"
        self.pydreo_manager.load_devices()
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP008S"
        assert air_purifier.series_name == "338S"
        assert air_purifier.speed_range == (1, 4)
        assert air_purifier.preset_modes == ["auto", "manual", "sleep", "turbo"]

        # DR-HAP008S rejects plain "auto" and requires "auto-regular" (issue #932)
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "sleep"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "auto"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "auto-regular"})

    def test_HAP010S(self):  # pylint: disable=invalid-name
        """Test DR-HAP010S (530S) Air Purifier with empty controlsConf."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP010S"
        assert air_purifier.series_name == "530S"
        assert air_purifier.speed_range == (1, 4)
        assert air_purifier.preset_modes == ["auto", "manual", "sleep", "turbo"]

        # DR-HAP010S also requires "auto-regular" (reported on issue #932)
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "sleep"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "auto"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "auto-regular"})

    def test_HAP010S_purifyon(self):  # pylint: disable=invalid-name
        """DR-HAP010S exposes the purification toggle (issue #933)."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.purifyon is False
        assert air_purifier.is_feature_supported("purifyon")

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.purifyon = True
            mock_send_command.assert_called_once_with(air_purifier, {"purifyon": True})

        air_purifier.handle_server_update({REPORTED_KEY: {"purifyon": True}})
        assert air_purifier.purifyon is True

        # Same value -- no command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.purifyon = True
            mock_send_command.assert_not_called()

        air_purifier.handle_server_update({REPORTED_KEY: {"purifyon": False}})
        assert air_purifier.purifyon is False

    def test_HAP010S_rgbic_state_and_commands(self):  # pylint: disable=invalid-name
        """530S RGBIC power and brightness use the observed rgbon/rgbbri fields."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbon": True, "rgbbri": 100}})
        assert device.rgbon is True
        assert device.rgbbri == 100
        assert device.is_feature_supported("rgbon")
        assert device.is_feature_supported("rgbbri")
        with patch(PATCH_SEND_COMMAND) as send:
            device.rgbon = False
            send.assert_called_once_with(device, {"rgbon": False})
        with patch(PATCH_SEND_COMMAND) as send:
            device.rgbbri = 50
            send.assert_called_once_with(device, {"rgbbri": 50})
        device.handle_server_update({REPORTED_KEY: {"rgbbri": 25}})
        assert device.rgbbri == 25

    def test_HAP010S_rgbic_mode_and_effect_payload(self):  # pylint: disable=invalid-name
        """530S mode writes use observed values and basic effects use the captured REST shape."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 1, "rgbeffectid": "1701000000000000011"}})
        assert device.rgbmode == 1
        assert device.rgbeffectid == "1701000000000000011"

        with patch(PATCH_SEND_COMMAND) as send:
            device.rgbmode = 2
            send.assert_called_once_with(device, {"rgbmode": 2})
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2}})

        catalog = {
            "code": 0,
            "msg": "OK",
            "data": {
                "basicEffects": [{
                    "id": "2124876509150707713",
                    "name": "Respirar",
                    "effectType": 0,
                    "extendedType": 0,
                    "referencedId": "1700000000000000002",
                    "selected": False,
                    "layouts": [
                        {
                            "colorList": ["#FF0000", "#FF8000"],
                            "effectParamKey": "colors",
                            "maxListSize": 8,
                            "title": "é¢œè‰²åˆ—è¡¨",
                            "viewType": "COLOR_LIST",
                        },
                        {
                            "effectParamKey": "speedValue",
                            "range": {"first": 1, "last": 100, "step": 1},
                            "title": "base_speed",
                            "value": 70.0,
                            "valueType": "INT",
                            "viewType": "SPEED",
                        },
                    ],
                }],
                # The caller deliberately exposes only basic effects, not these categories.
                "remoteEffects": [{"name": "remote", "effectType": 2}],
                "sceneEffects": [{"name": "scene", "effectType": 3}],
            },
        }
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 1}})
        with patch(PATCH_SEND_COMMAND) as send, patch(
            "custom_components.dreo.pydreo.Helpers.call_api",
            side_effect=[(catalog, 200), ({"code": 0, "msg": "OK", "data": {}}, 200)],
        ) as call_api:
            device.set_rgbic_effect_catalog(catalog["data"])
            assert device.rgbic_effect_names == ["Respirar"]
            assert device.set_rgbic_effect("Respirar") is True
            send.assert_called_once_with(device, {"rgbmode": 2})

        assert call_api.call_args_list[0].args[1:4] == (
            "/api/device/rgb-effect/all/list",
            "get",
            {"devicesn": device.serial_number},
        )
        catalog_headers = call_api.call_args_list[0].args[4]
        expected_catalog_headers = {
            **Helpers.req_headers(self.pydreo_manager),
            "lang": "en",
            "country": "ES",
            "appversion": "3.8.2",
        }
        assert catalog_headers == expected_catalog_headers
        assert call_api.call_args_list[1].args[1:4] == (
            "/api/device/rgb-effect/edit/batch",
            "post",
            [{
                "applyToDevice": True,
                "devicesn": device.serial_number,
                "effectType": 0,
                "id": "2124876509150707713",
                "name": "Respirar",
                "subEffects": [{
                    "effectId": "1700000000000000002",
                    "layouts": catalog["data"]["basicEffects"][0]["layouts"],
                }],
            }],
        )
        write_headers = call_api.call_args_list[1].args[4]
        assert write_headers == Helpers.req_headers(self.pydreo_manager)
        assert write_headers["lang"] == "en"
        assert "country" not in write_headers
        assert device.rgbic_effect_name == "Respirar"

    def test_HAP010S_catalog_uses_configured_language_and_english_fallback(self):  # pylint: disable=invalid-name
        """530S catalog reads use HA language and retry in English after failure."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        response = {"code": 0, "data": _hap010s_rgbic_catalog()}
        self.pydreo_manager.catalog_language = "fr"

        with patch("custom_components.dreo.pydreo.Helpers.call_api", side_effect=[({"code": 8}, 200), (response, 200)]) as call_api:
            assert self.pydreo_manager.get_rgbic_effect_catalog(device) == response["data"]

        assert len(call_api.call_args_list) == 2
        for call, language in zip(call_api.call_args_list, ("fr", "en")):
            assert call.args[1:4] == (
                "/api/device/rgb-effect/all/list",
                "get",
                {"devicesn": device.serial_number},
            )
            assert call.args[4] == {
                **Helpers.req_headers(self.pydreo_manager),
                "lang": language,
                "country": "ES",
                "appversion": "3.8.2",
            }

    def test_HAP010S_regional_empty_catalog_recovers_in_english(self):
        self.pydreo_manager.catalog_language = PyDreo(
            "EMAIL", "PASSWORD", language="pt-BR"
        ).catalog_language
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        empty = {"code": 0, "data": {"basicEffects": [], "sceneEffects": []}}
        english = {"code": 0, "data": _hap010s_rgbic_catalog()}

        with patch(
            "custom_components.dreo.pydreo.Helpers.call_api",
            side_effect=[(empty, 200), (english, 200)],
        ) as call_api:
            assert self.pydreo_manager.get_rgbic_effect_catalog(device) == english["data"]

        assert [call.args[4]["lang"] for call in call_api.call_args_list] == ["pt", "en"]

    def test_HAP010S_empty_english_fallback_catalog_returns_none(self):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        self.pydreo_manager.catalog_language = "pt"
        empty = {"code": 0, "data": {"basicEffects": [], "sceneEffects": []}}

        with patch(
            "custom_components.dreo.pydreo.Helpers.call_api",
            side_effect=[(empty, 200), (empty, 200)],
        ) as call_api:
            assert self.pydreo_manager.get_rgbic_effect_catalog(device) is None

        assert [call.args[4]["lang"] for call in call_api.call_args_list] == ["pt", "en"]

    def test_HAP010S_empty_requested_english_catalog_does_not_retry(self):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        self.pydreo_manager.catalog_language = "en"
        empty = {"code": 0, "data": {"basicEffects": [], "sceneEffects": []}}

        with patch("custom_components.dreo.pydreo.Helpers.call_api", return_value=(empty, 200)) as call_api:
            assert self.pydreo_manager.get_rgbic_effect_catalog(device) is None

        assert call_api.call_count == 1

    def test_HAP010S_valid_localized_catalog_does_not_retry(self):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        self.pydreo_manager.catalog_language = "de"
        localized = {"code": 0, "data": _hap010s_rgbic_catalog()}

        with patch("custom_components.dreo.pydreo.Helpers.call_api", return_value=(localized, 200)) as call_api:
            assert self.pydreo_manager.get_rgbic_effect_catalog(device) == localized["data"]

        assert call_api.call_count == 1
        assert call_api.call_args.args[4]["lang"] == "de"

    def test_HAP010S_catalog_does_not_retry_when_language_is_english(self):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        self.pydreo_manager.catalog_language = "en"
        with patch("custom_components.dreo.pydreo.Helpers.call_api", return_value=({"code": 1}, 200)) as call_api:
            assert self.pydreo_manager.get_rgbic_effect_catalog(device) is None
        assert call_api.call_count == 1

    def test_other_device_catalog_keeps_spanish_language(self):
        self.get_devices_file_name = "get_devices_HAP003S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        self.pydreo_manager.catalog_language = "fr"
        response = {"code": 0, "data": {}}
        with patch("custom_components.dreo.pydreo.Helpers.call_api", return_value=(response, 200)) as call_api:
            assert self.pydreo_manager.get_rgbic_effect_catalog(device) == {}
        assert call_api.call_count == 1
        assert call_api.call_args.args[4]["lang"] == "es"
        assert call_api.call_args.args[4]["country"] == "ES"

    def test_HAP010S_segment_suffix_stays_english_with_localized_effect_name(self):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "1", "name": "Constante", "effectType": 0,
            "referencedId": "2", "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "wholeColorList": ["#000000"],
                "colorList": ["#000000"],
            }],
        }], "sceneEffects": []})
        assert "Constante (segments)" in device.rgbic_selectable_effect_names

    def test_HAP010S_auto_mode_command_and_websocket_state(self):  # pylint: disable=invalid-name
        """Automatic air-quality mode is selected only by the captured rgbmode=1 command."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2}})
        with patch(PATCH_SEND_COMMAND) as send:
            device.rgbmode = 1
            send.assert_called_once_with(device, {"rgbmode": 1})
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 1, "rgbeffectid": "1701000000000000011"}})
        assert device.rgbmode == 1
        assert device.rgbeffectid == "1701000000000000011"

        device.update_state({
            "rgbmode": {"state": 2},
            "rgbeffectid": {"state": "1702000000000000001"},
        })
        # A subsequent REST snapshot cannot replace a live WebSocket mode or effect ID.
        assert device.rgbmode == 1
        assert device.rgbeffectid == "1701000000000000011"

    def test_other_purifiers_do_not_expose_530s_rgbic_writes(self):
        """The new RGBIC attributes and commands remain specific to DR-HAP010S."""
        self.get_devices_file_name = "get_devices_HAP008S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 1, "rgbeffectid": "anything"}})
        assert device.rgbmode is None
        assert device.rgbeffectid is None
        assert not device.is_feature_supported("rgbmode")
        assert not device.is_feature_supported("rgbeffectid")

    def test_HAP010S_websocket_effect_report_resolves_from_loaded_catalog(self):  # pylint: disable=invalid-name
        """A changed effect ID resolves immediately without another catalog request."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog({
            "basicEffects": [{
                "id": "old-id",
                "referencedId": "old-ref",
                "effectType": 0,
                "name": "Previous effect",
            }, {
                "id": "new-id",
                "referencedId": "referenced-id",
                "effectType": 0,
                "name": "Wave from current catalog",
            }],
        })
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "old-id"}})
        with patch.object(self.pydreo_manager, "get_rgbic_effect_catalog") as get_catalog:
            device.handle_server_update({REPORTED_KEY: {"rgbeffectid": "new-id"}})

        get_catalog.assert_not_called()
        assert device.rgbeffectid == "new-id"
        assert device.rgbic_effect_name == "Wave from current catalog"

    def test_HAP010S_effect_id_only_update_is_string_and_keeps_unknown_unlabeled(self):  # pylint: disable=invalid-name
        """An ID-only WebSocket message is retained without guessing from selected flags."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog({
            "basicEffects": [{
                "id": "catalog-basic-id",
                "referencedId": "1700000000000000011",
                "effectType": 0,
                "name": "Wrong if matched by prefix",
                "selected": True,
            }],
        })
        device.handle_server_update({REPORTED_KEY: {"rgbeffectid": 1701000000000000011}})
        assert device.rgbmode is None
        assert device.rgbeffectid == "1701000000000000011"
        assert isinstance(device.rgbeffectid, str)
        assert device.rgbic_effect_name is None

    def test_HAP010S_repeated_constant_id_refreshes_color_and_catches_up_latest_catalog(
        self, caplog
    ):  # pylint: disable=invalid-name
        """Repeated same-ID reports refresh Constant color without redundant HA-write GETs."""
        caplog.set_level(logging.DEBUG, logger="custom_components.dreo.pydreo.pydreoairpurifier")
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]

        def catalog_with_color(color):
            return {"basicEffects": [{
                "id": "2124876509150707712",
                "referencedId": "1700000000000000001",
                "effectType": 0,
                "name": "Constante",
                "layouts": [{
                    "viewType": "SEGMENT_COLOR_LIST",
                    "currentSelected": "whole",
                    "wholeColorList": [color],
                    "colorList": ["#ffffff"] * 17,
                }],
            }]}

        device.set_rgbic_effect_catalog(catalog_with_color("#00ff00"))
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "2124876509150707712"}
        })
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbeffectid": "2124876509150707712"}
        })
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbeffectid": "2124876509150707712"}
        })
        assert len(scheduled) == 1

        reads = []

        def get_catalog(_device):
            reads.append(True)
            if len(reads) == 1:
                device.handle_server_update_base({
                    REPORTED_KEY: {"rgbeffectid": "2124876509150707712"}
                })
                return catalog_with_color("#00ff00")
            return catalog_with_color("#ff020a")

        with patch.object(device._dreo, "get_rgbic_effect_catalog", side_effect=get_catalog):
            scheduled[0]()
            assert device._rgbic_catalog_refresh_cancel is None
            assert device._rgbic_catalog_refresh_running is False

            device.handle_server_update_base({
                REPORTED_KEY: {"rgbeffectid": "2124876509150707712"}
            })
            assert len(scheduled) == 2
            scheduled[1]()

        assert len(reads) == 3
        assert device.rgbeffectid == "2124876509150707712"
        assert device.rgbic_color == (255, 2, 10)
        assert "Received 530S RGBIC rgbeffectid report=2124876509150707712 changed=False" in caplog.text
        assert "RGBIC catalog color refreshed from DREO RGB=(255, 2, 10)" in caplog.text

    def test_HAP010S_catalog_refresh_does_not_lose_event_during_worker_release(self):  # pylint: disable=invalid-name
        """An event between a completed pass and worker release causes another read."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]

        def catalog_with_color(color):
            return {"basicEffects": [{
                "id": "constant-id",
                "referencedId": "constant-ref",
                "effectType": 0,
                "name": "Constante",
                "layouts": [{
                    "viewType": "SEGMENT_COLOR_LIST",
                    "currentSelected": "whole",
                    "wholeColorList": [color],
                }],
            }, {
                "id": "other-id",
                "referencedId": "other-ref",
                "effectType": 0,
                "name": "Other",
                "layouts": [],
            }]}

        device.set_rgbic_effect_catalog(catalog_with_color("#00ff00"))
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "other-id"}
        })
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbeffectid": "constant-id"}
        })
        assert len(scheduled) == 1

        pass_finished = Event()
        allow_worker_release = Event()
        original_fetch = device.fetch_rgbic_catalog
        pass_count = 0

        def pause_after_first_fetch():
            nonlocal pass_count
            applied = original_fetch()
            pass_count += 1
            if pass_count == 1:
                pass_finished.set()
                if not allow_worker_release.wait(timeout=5):
                    raise AssertionError("test did not release the catalog worker")
            return applied

        worker = None
        worker_errors: list[BaseException] = []
        with patch.object(
            device._dreo,
            "get_rgbic_effect_catalog",
            side_effect=[catalog_with_color("#ff0000"), catalog_with_color("#0000ff")],
        ) as get_catalog, patch.object(
            device, "fetch_rgbic_catalog", side_effect=pause_after_first_fetch
        ):
            worker, worker_errors = _start_thread(scheduled[0])
            try:
                assert pass_finished.wait(timeout=5)
                # A real effect-id change during worker release must queue another read.
                device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "other-id"}})
                device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "constant-id"}})
                assert device._rgbic_catalog_refresh_pending is True
            finally:
                allow_worker_release.set()
            _join_thread(worker, worker_errors)

        assert not worker.is_alive()
        assert pass_count == get_catalog.call_count == 2
        assert device.rgbic_color == (0, 0, 255)
        assert len(scheduled) == 1
        assert device._rgbic_catalog_refresh_running is False
        assert device._rgbic_catalog_refresh_cancel is None

    def test_HAP010S_catalog_refresh_releases_handle_after_api_error(self):  # pylint: disable=invalid-name
        """A failed read clears the pending handle so a later report can retry once."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog = {"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
                "colorList": ["#ffffff"] * 17,
            }],
        }, {
            "id": "other-id",
            "referencedId": "other-ref",
            "effectType": 0,
            "name": "Other",
            "layouts": [],
        }]}
        device.set_rgbic_effect_catalog(catalog)
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "constant-id"}
        })

        with patch.object(
            device._dreo,
            "get_rgbic_effect_catalog",
            side_effect=[RuntimeError("catalog unavailable"), catalog],
        ) as get_catalog:
            scheduled[0]()
            assert device._rgbic_catalog_refresh_cancel is None
            assert device._rgbic_catalog_refresh_running is False

            device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "other-id"}})
            device.handle_server_update_base({
                REPORTED_KEY: {"rgbeffectid": "constant-id"}
            })
            assert len(scheduled) == 2
            scheduled[1]()

        assert get_catalog.call_count == 2
        assert device.rgbic_color == (0, 102, 255)
        assert device._rgbic_catalog_refresh_cancel is None
        assert device._rgbic_catalog_refresh_running is False

    def test_HAP010S_local_write_echo_does_not_schedule_catalog_refresh(self):  # pylint: disable=invalid-name
        """HA color that selects Constant must not GET on echo; a later app report may."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]

        def catalog_with_color(color_hex: str):
            return {"basicEffects": [{
                "id": "constant-id",
                "referencedId": "constant-ref",
                "effectType": 0,
                "name": "Constante",
                "layouts": [{
                    "viewType": "SEGMENT_COLOR_LIST",
                    "currentSelected": "whole",
                    "wholeColorList": [color_hex],
                }],
            }, {
                "id": "contrast-id",
                "referencedId": "contrast-ref",
                "effectType": 0,
                "name": "Contraste",
                "layouts": [],
            }]}

        device.set_rgbic_effect_catalog(catalog_with_color("#00ff00"))
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "contrast-id"}
        })
        with patch.object(device._dreo, "set_rgbic_effect", return_value=True), patch.object(
            device._outbox, "flush_now", return_value=True
        ):
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is True

        device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "constant-id"}})
        assert scheduled == []
        assert device.rgbic_color == (255, 0, 0)

        device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "constant-id"}})
        assert len(scheduled) == 1
        with patch.object(
            device._dreo,
            "get_rgbic_effect_catalog",
            return_value=catalog_with_color("#0000ff"),
        ) as get_catalog:
            scheduled[0]()
        assert get_catalog.call_count == 1
        assert device.rgbic_color == (0, 0, 255)

    def _hap010s_constant_contrast_catalog(self, constant_color: str = "#00ff00"):
        return {"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": [constant_color],
            }],
        }, {
            "id": "contrast-id",
            "referencedId": "contrast-ref",
            "effectType": 0,
            "name": "Contraste",
            "layouts": [],
        }]}

    def test_HAP010S_constant_echo_marker_immediate_contrast_to_constant_skips_get(self):  # pylint: disable=invalid-name
        """A. Immediate WS echo after HA selects Constant must not schedule a catalog GET."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog(self._hap010s_constant_contrast_catalog())
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "contrast-id"}
        })
        with patch.object(device._dreo, "set_rgbic_effect", return_value=True), patch.object(
            device._outbox, "flush_now", return_value=True
        ):
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is True

        device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "constant-id"}})
        assert scheduled == []

    def test_HAP010S_constant_echo_before_expiry_skips_get(self):  # pylint: disable=invalid-name
        """A Constant echo before its five-second deadline consumes the marker."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog(self._hap010s_constant_contrast_catalog())
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "contrast-id"}})
        with patch.object(device._dreo, "set_rgbic_effect", return_value=True), patch.object(
            device._outbox, "flush_now", return_value=True
        ), patch("custom_components.dreo.pydreo.pydreoairpurifier.time.monotonic", return_value=10):
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is True
        with patch("custom_components.dreo.pydreo.pydreoairpurifier.time.monotonic", return_value=14.9):
            device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "constant-id"}})

        assert device._skip_next_constant_refresh is None
        assert scheduled == []

    def test_HAP010S_constant_echo_after_expiry_refreshes_catalog(self):  # pylint: disable=invalid-name
        """When the expected echo is absent, a later Constant report refreshes."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog(self._hap010s_constant_contrast_catalog())
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "contrast-id"}})
        with patch.object(device._dreo, "set_rgbic_effect", return_value=True), patch.object(
            device._outbox, "flush_now", return_value=True
        ), patch("custom_components.dreo.pydreo.pydreoairpurifier.time.monotonic", return_value=10):
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is True
        with patch("custom_components.dreo.pydreo.pydreoairpurifier.time.monotonic", return_value=15):
            device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "constant-id"}})

        assert device._skip_next_constant_refresh is None
        assert len(scheduled) == 1

    def test_HAP010S_reconnect_recovers_rgbic_and_keeps_newer_websocket_state(self):  # pylint: disable=invalid-name
        """Reconnect recovery reloads state/catalog while a newer WS report wins over REST."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog(self._hap010s_constant_contrast_catalog())
        scheduled = []
        self.pydreo_manager.set_schedule_call_later(
            lambda _delay, work: scheduled.append(work) or (lambda: None)
        )
        device.handle_server_update_base({REPORTED_KEY: {"rgbmode": 1, "rgbeffectid": "indicator-id"}})
        stale_catalog_generation = device.begin_rgbic_catalog_read()

        self.pydreo_manager._transport_reconnected()
        assert device._rgbic_mode_authoritative is False
        assert device._rgbic_effect_id_reported is False
        assert device._rgbic_generation > stale_catalog_generation
        assert device.set_rgbic_effect_catalog(
            self._hap010s_constant_contrast_catalog(),
            expected_rgbic_generation=stale_catalog_generation,
        ) is False
        self.pydreo_manager._transport_reconnected()
        assert len(scheduled) == 2

        def _load_with_new_websocket_report(
            _device,
            *,
            expected_transport_reconnect_generation,
        ):
            assert expected_transport_reconnect_generation == self.pydreo_manager._transport_reconnect_generation
            device.handle_server_update_base({
                REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "new-live-id"}
            })
            device.update_state({
                "rgbmode": {"state": 1},
                "rgbeffectid": {"state": "stale-rest-id"},
            })
            return True

        with patch.object(self.pydreo_manager, "load_device_state", side_effect=_load_with_new_websocket_report) as load_state, patch.object(
            device, "fetch_rgbic_catalog", return_value=True
        ) as fetch_catalog, patch.object(device, "_do_callbacks"):
            scheduled[0]()
            load_state.assert_not_called()
            scheduled[1]()

        load_state.assert_called_once_with(
            device,
            expected_transport_reconnect_generation=self.pydreo_manager._transport_reconnect_generation,
        )
        fetch_catalog.assert_called_once_with()
        assert device.rgbmode == 2
        assert device.rgbeffectid == "new-live-id"

    def test_reconnect_refresh_failure_does_not_block_other_devices(self, caplog):
        """A failed device refresh is logged and later devices still recover."""
        import copy

        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        first_device = self.pydreo_manager.devices[0]
        second_details = copy.deepcopy(self.pydreo_manager.raw_response["data"]["list"][0])
        second_details["deviceId"] = "second-device-id"
        second_details["sn"] = "HAP010S_2"
        second_details["deviceName"] = "Second 530S"
        self.pydreo_manager._process_devices([second_details])
        second_device = self.pydreo_manager.devices[1]
        scheduled = []
        self.pydreo_manager.set_schedule_call_later(
            lambda _delay, work: scheduled.append(work) or (lambda: None)
        )

        def load_state(device, *, expected_transport_reconnect_generation):
            assert expected_transport_reconnect_generation == self.pydreo_manager._transport_reconnect_generation
            if device is first_device:
                raise RuntimeError("simulated first-device recovery failure")
            return True

        with patch.object(self.pydreo_manager, "load_device_state", side_effect=load_state) as load, patch.object(
            first_device, "fetch_rgbic_catalog"
        ) as first_catalog, patch.object(
            second_device, "fetch_rgbic_catalog", return_value=True
        ) as second_catalog, patch.object(second_device, "_do_callbacks") as second_callbacks:
            self.pydreo_manager._transport_reconnected()
            assert len(scheduled) == 1
            scheduled[0]()

        assert load.call_count == 2
        assert load.call_args_list[0].args == (first_device,)
        assert load.call_args_list[1].args == (second_device,)
        first_catalog.assert_not_called()
        second_catalog.assert_called_once_with()
        second_callbacks.assert_called_once_with()
        assert f"RGBIC state refresh failed for {first_device.name}" in caplog.text
        assert "simulated first-device recovery failure" in caplog.text

    @pytest.mark.parametrize(
        ("state_applied", "catalog_applied", "should_notify"),
        [
            (True, True, True),
            (True, False, True),
            (False, True, True),
            (False, False, False),
        ],
    )
    def test_reconnect_refresh_notifies_when_either_operation_succeeds(
        self, state_applied, catalog_applied, should_notify
    ):
        """Notify after reconnect only when state or catalog was applied."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        scheduled = []
        self.pydreo_manager.set_schedule_call_later(
            lambda _delay, work: scheduled.append(work) or (lambda: None)
        )

        with patch.object(
            self.pydreo_manager, "load_device_state", return_value=state_applied
        ) as load_state, patch.object(
            device, "fetch_rgbic_catalog", return_value=catalog_applied
        ) as fetch_catalog, patch.object(device, "_do_callbacks") as callbacks:
            self.pydreo_manager._transport_reconnected()
            assert len(scheduled) == 1
            scheduled[0]()

        load_state.assert_called_once_with(
            device,
            expected_transport_reconnect_generation=self.pydreo_manager._transport_reconnect_generation,
        )
        fetch_catalog.assert_called_once_with()
        assert callbacks.call_count == int(should_notify)

    def test_non_rgbic_purifier_reconnect_does_not_schedule_rgbic_recovery(self):
        """Purifiers without RGBIC mode lighting do not trigger extra recovery calls."""
        self.get_devices_file_name = "get_devices_HAP009S.json"
        self.pydreo_manager.load_devices()
        scheduler = MagicMock()
        self.pydreo_manager.set_schedule_call_later(scheduler)

        self.pydreo_manager._transport_reconnected()

        scheduler.assert_not_called()

    def test_pending_reconnect_recovery_is_ignored_after_unload(self):
        """A queued recovery becomes inert once transport teardown advances its generation."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        scheduled = []
        self.pydreo_manager.set_schedule_call_later(
            lambda _delay, work: scheduled.append(work) or (lambda: None)
        )
        self.pydreo_manager._transport_reconnected()

        with patch.object(self.pydreo_manager._transport, "stop_transport"), patch.object(
            self.pydreo_manager, "load_device_state"
        ) as load_state:
            self.pydreo_manager.stop_transport()
            scheduled[0]()

        load_state.assert_not_called()

    def test_inflight_reconnect_rest_response_is_ignored_after_second_reconnect(self):
        """An older in-flight REST snapshot cannot apply after a newer reconnect report."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog(self._hap010s_constant_contrast_catalog())
        scheduled = []
        self.pydreo_manager.set_schedule_call_later(
            lambda _delay, work: scheduled.append(work) or (lambda: None)
        )
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 1, "rgbeffectid": "old-id"}
        })
        self.pydreo_manager._transport_reconnected()
        request_generation = self.pydreo_manager._transport_reconnect_generation

        def _reconnect_while_request_is_inflight(*_args, **_kwargs):
            self.pydreo_manager._transport_reconnected()
            device.handle_server_update_base({
                REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "new-live-id"}
            })
            return {
                "code": 0,
                "data": {"mixed": {
                    "rgbmode": {"state": 1},
                    "rgbeffectid": {"state": "stale-rest-id"},
                }},
            }, 200

        with patch.object(
            self.pydreo_manager,
            "call_dreo_api",
            side_effect=_reconnect_while_request_is_inflight,
        ):
            assert self.pydreo_manager.load_device_state(
                device,
                expected_transport_reconnect_generation=request_generation,
            ) is False

        assert device.rgbmode == 2
        assert device.rgbeffectid == "new-live-id"

    def test_HAP010S_constant_echo_marker_cleared_by_intermediate_effect(self):  # pylint: disable=invalid-name
        """C. A non-Constant report clears the marker so a later Constant report refreshes."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog(self._hap010s_constant_contrast_catalog())
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "contrast-id"}
        })
        with patch.object(device._dreo, "set_rgbic_effect", return_value=True), patch.object(
            device._outbox, "flush_now", return_value=True
        ):
            assert device.set_rgbic_effect(color_rgb=(10, 20, 30)) is True
        assert device._skip_next_constant_refresh is not None

        device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "contrast-id"}})
        assert device._skip_next_constant_refresh is None

        device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "constant-id"}})
        assert len(scheduled) == 1

    def test_HAP010S_stale_catalog_read_cannot_overwrite_newer_local_rgb_write(self):  # pylint: disable=invalid-name
        """An in-flight app refresh cannot replace a newer successful HA color write."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog = {"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#00ff00"],
                "colorList": ["#ffffff"] * 17,
            }],
        }]}
        device.set_rgbic_effect_catalog(catalog)
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "constant-id"}
        })

        def stale_read(_device):
            assert device.set_rgbic_effect(color_rgb=(255, 255, 255)) is True
            return catalog

        with patch.object(device._dreo, "get_rgbic_effect_catalog", side_effect=stale_read), patch.object(
            device._dreo, "set_rgbic_effect", return_value=True
        ):
            scheduled[0]()

        assert device.rgbic_color == (255, 255, 255)

    def test_HAP010S_failed_color_write_keeps_known_color_and_effect(self):  # pylint: disable=invalid-name
        """A failed HA color write does not arm echo suppression or replace known state."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog = {
            "basicEffects": [{
                "id": "constant-id",
                "referencedId": "constant-ref",
                "effectType": 0,
                "name": "Constante",
                "layouts": [{
                    "viewType": "SEGMENT_COLOR_LIST",
                    "currentSelected": "whole",
                    "wholeColorList": ["#00ff00"],
                }],
            }],
            "sceneEffects": [{
                "id": "wave-id",
                "referencedId": "wave-ref",
                "effectType": 3,
                "name": "Ola",
            }],
        }
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "constant-id"}})
        device.set_rgbic_effect_catalog(catalog)
        assert device.rgbic_color == (0, 255, 0)
        assert device.rgbic_effect_name == "Constante"

        with patch.object(device._dreo, "set_rgbic_effect", return_value=False), patch.object(
            device._outbox, "flush_now", return_value=True
        ):
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is False

        assert device._skip_next_constant_refresh is None
        assert device.rgbic_color == (0, 255, 0)
        assert device.rgbic_effect_name == "Constante"

    def test_HAP010S_pending_catalog_read_preserves_optimistic_effect_name(self):  # pylint: disable=invalid-name
        """A catalog GET started before a local write cannot relabel the HA effect."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog = {
            "basicEffects": [{
                "id": "constant-id",
                "referencedId": "constant-ref",
                "effectType": 0,
                "name": "Constante",
                "layouts": [{
                    "viewType": "SEGMENT_COLOR_LIST",
                    "currentSelected": "whole",
                    "wholeColorList": ["#00ff00"],
                }],
            }],
            "sceneEffects": [{
                "id": "wave-id",
                "referencedId": "wave-ref",
                "effectType": 3,
                "name": "Ola",
            }],
        }
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2}})
        device.set_rgbic_effect_catalog(catalog)
        generation = device.begin_rgbic_catalog_read()
        assert generation is not None

        def load_catalog_during_write(_device):
            assert device.set_rgbic_effect("Ola") is True
            return catalog

        with patch.object(device._dreo, "get_rgbic_effect_catalog", side_effect=load_catalog_during_write), patch.object(
            device._dreo, "set_rgbic_scene_effect", return_value=True
        ), patch.object(device._outbox, "flush_now", return_value=True):
            stale_catalog = device._dreo.get_rgbic_effect_catalog(device)

        applied = device.set_rgbic_effect_catalog(
            stale_catalog,
            expected_rgbic_generation=generation,
        )
        assert applied is False
        assert device.rgbic_effect_name == "Ola"
        assert device.rgbic_scene_effect_names == ["Ola"]

    def test_HAP010S_post_write_revision_blocks_pre_write_catalog_snapshot(self):  # pylint: disable=invalid-name
        """A catalog read started during a color write cannot overwrite the committed color."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "constant-id"}})
        catalog = {"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#ff0000"],
            }],
        }]}
        device.set_rgbic_effect_catalog(catalog)
        assert device.rgbic_color == (255, 0, 0)

        pre_write_snapshot = None

        def capture_read_during_rest(_device, _effect_name, _color_hex):
            nonlocal pre_write_snapshot
            pre_write_snapshot = device.begin_rgbic_catalog_read()
            return True

        with patch.object(device._dreo, "set_rgbic_effect", side_effect=capture_read_during_rest), patch.object(
            device._outbox, "flush_now", return_value=True
        ):
            assert device.set_rgbic_effect(color_rgb=(0, 255, 0)) is True

        assert device.rgbic_color == (0, 255, 0)
        assert pre_write_snapshot is not None
        assert device._rgbic_generation == pre_write_snapshot + 1
        assert device.set_rgbic_effect_catalog(
            catalog,
            expected_rgbic_generation=pre_write_snapshot,
        ) is False
        assert device.rgbic_color == (0, 255, 0)

    def test_HAP010S_refresh_constant_apply_updates_color_effect_id(self):  # pylint: disable=invalid-name
        """A successful refresh keeps the Constant catalog id aligned with the color."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog = {"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#00ff00"],
            }],
        }]}
        device.set_rgbic_effect_catalog(catalog)
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "constant-id"}
        })
        assert len(scheduled) == 1
        device._rgbic_color_effect_id = "stale-constant-id"
        with patch.object(device._dreo, "get_rgbic_effect_catalog", return_value=catalog):
            scheduled[0]()

        assert device.rgbic_color == (0, 255, 0)
        assert device._rgbic_color_effect_id == "constant-id"

    def test_HAP010S_stale_catalog_read_preserves_newer_local_effect_selection(
        self,
    ):  # pylint: disable=invalid-name
        """An older in-flight catalog cannot replace a successful local effect name."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog = {
            "basicEffects": [{
                "id": "constant-id",
                "referencedId": "constant-ref",
                "effectType": 0,
                "name": "Constante",
                "layouts": [{
                    "viewType": "SEGMENT_COLOR_LIST",
                    "currentSelected": "whole",
                    "wholeColorList": ["#00ff00"],
                }],
            }],
            "sceneEffects": [{
                "id": "wave-id",
                "referencedId": "wave-ref",
                "effectType": 3,
                "name": "Ola",
            }],
        }
        device.set_rgbic_effect_catalog(catalog)
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "constant-id"}
        })

        def stale_read(_device):
            assert device.set_rgbic_effect("Ola") is True
            return catalog

        with patch.object(device._dreo, "get_rgbic_effect_catalog", side_effect=stale_read), patch.object(
            device._dreo, "set_rgbic_scene_effect", return_value=True
        ), patch.object(device._outbox, "flush_now", return_value=True):
            scheduled[0]()

        assert device.rgbic_effect_names == ["Constante"]
        assert device.rgbic_scene_effect_names == ["Ola"]
        assert device.rgbic_effect_name == "Ola"

        # A later WebSocket confirmation still resolves against the refreshed catalog.
        device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "wave-id"}})
        assert device.rgbic_effect_name == "Ola"

    def test_HAP010S_initial_catalog_read_preserves_newer_local_effect_selection(
        self,
    ):  # pylint: disable=invalid-name
        """An initial catalog response cannot replace an effect selected while loading."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog = {
            "basicEffects": [{
                "id": "constant-id",
                "referencedId": "constant-ref",
                "effectType": 0,
                "name": "Constante",
                "layouts": [{
                    "viewType": "SEGMENT_COLOR_LIST",
                    "currentSelected": "whole",
                    "wholeColorList": ["#00ff00"],
                }],
            }],
            "sceneEffects": [{
                "id": "wave-id",
                "referencedId": "wave-ref",
                "effectType": 3,
                "name": "Ola",
            }],
        }
        device.update_state({"rgbmode": {"state": 2}})
        device.set_rgbic_effect_catalog(catalog)
        stale_generation = device._rgbic_generation

        with patch.object(device._dreo, "set_rgbic_scene_effect", return_value=True), patch.object(
            device._outbox, "flush_now", return_value=True
        ):
            assert device.set_rgbic_effect("Ola") is True

        device.set_rgbic_effect_catalog(
            catalog,
            expected_rgbic_generation=stale_generation,
        )

        assert device.rgbic_effect_name == "Ola"
        assert device.rgbic_scene_effect_names == ["Ola"]

    @pytest.mark.parametrize(
        ("effect_id", "rgb_mode", "expected_color"),
        [
            ("constant-catalog-id", 2, (0, 102, 255)),
            ("scene-id", 2, None),
            ("unrecognized-effect", 2, None),
            (None, 2, None),
            (None, 1, None),
        ],
    )
    def test_HAP010S_catalog_color_requires_reported_constant_effect(
        self, effect_id, rgb_mode, expected_color
    ):  # pylint: disable=invalid-name
        """Only a reported matching Constant ID can activate its persisted color."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.update_state({
            "rgbeffectid": {"state": effect_id},
            "rgbmode": {"state": rgb_mode},
        })

        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-catalog-id",
            "referencedId": "constant-resource-id",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
                "colorList": ["#ffffff"] * 17,
            }],
        }]})

        assert device.rgbic_color == expected_color

    @pytest.mark.parametrize(
        "layout",
        [
            {"viewType": "SEGMENT_COLOR_LIST", "currentSelected": "whole"},
            {
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["not-a-hex-color"],
            },
        ],
    )
    def test_HAP010S_valid_catalog_without_parseable_color_clears_previous_color(
        self, layout
    ):  # pylint: disable=invalid-name
        """A successful catalog without a valid whole color invalidates stale RGB."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.update_state({
            "rgbeffectid": {"state": "constant-id"},
            "rgbmode": {"state": 2},
        })
        device._rgbic_color = (0, 102, 255)

        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-resource-id",
            "effectType": 0,
            "name": "Constante",
            "layouts": [layout],
        }]})

        assert device.rgbic_color is None

    def test_HAP010S_rest_mode_indicator_invalidates_manual_color(self):  # pylint: disable=invalid-name
        """A REST mode-one update clears previously active manual RGB color."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device._rgbmode = 2
        device._rgbeffectid = "constant-id"
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-resource-id",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
            }],
        }]})
        assert device.rgbic_color == (0, 102, 255)

        device.update_state({"rgbmode": {"state": 1}})

        assert device.rgbmode == 1
        assert device.rgbic_color is None

    def test_HAP010S_websocket_mode_indicator_invalidates_manual_color(self):  # pylint: disable=invalid-name
        """A live WebSocket transition to indicator mode clears the manual RGB value."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device._rgbmode = 2
        device._rgbic_color = (0, 102, 255)

        device.handle_server_update_base({REPORTED_KEY: {"rgbmode": 1}})

        assert device.rgbmode == 1
        assert device.rgbic_color is None

    def test_HAP010S_local_mode_indicator_invalidates_manual_color(self):  # pylint: disable=invalid-name
        """A local switch to indicator mode clears the previously selected RGB value."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device._rgbmode = 2
        device._rgbic_color = (0, 102, 255)

        with patch(PATCH_SEND_COMMAND):
            device.rgbmode = 1

        assert device.rgbmode == 1
        assert device.rgbic_color is None

    def test_HAP010S_stale_rest_mode_does_not_clear_newer_local_color(self):  # pylint: disable=invalid-name
        """After a local/WebSocket mode update, stale REST mode cannot erase RGB."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.update_state({"rgbmode": {"state": 2}})
        device.handle_server_update_base({REPORTED_KEY: {"rgbmode": 2}})
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-resource-id",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
            }],
        }]})
        with patch.object(device._dreo, "set_rgbic_effect", return_value=True), patch.object(
            device._outbox, "flush_now", return_value=True
        ):
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is True

        device.update_state({"rgbmode": {"state": 1}})

        assert device.rgbmode == 2
        assert device.rgbic_color == (255, 0, 0)

    def test_HAP010S_failed_refresh_pass_null_snapshot_keeps_ha_color(self):  # pylint: disable=invalid-name
        """A failed catalog GET keeps a confirmed HA color when no effect is active."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog = {"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#00ff00"],
            }],
        }]}
        device.set_rgbic_effect_catalog(catalog)
        device._rgbeffectid = None
        device._rgbmode = None
        device._rgbic_color = (12, 34, 56)

        with patch.object(device._dreo, "get_rgbic_effect_catalog", return_value=None):
            assert device.fetch_rgbic_catalog() is False

        assert device.rgbic_color == (12, 34, 56)

    def test_HAP010S_failed_catalog_refresh_keeps_confirmed_ha_color_and_effects(self):  # pylint: disable=invalid-name
        """A failed GET keeps the last known color and effect catalog metadata."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog = {"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-resource-id",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
            }],
        }]}
        device.update_state({"rgbmode": {"state": 2}})
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "constant-id"}
        })
        device.set_rgbic_effect_catalog(catalog)
        assert len(scheduled) == 1
        assert device.rgbic_color == (0, 102, 255)

        with patch.object(device._dreo, "get_rgbic_effect_catalog", return_value=None):
            scheduled[0]()

        assert device.rgbic_color == (0, 102, 255)
        assert device.rgbic_effect_names == ["Constante"]

    def test_HAP010S_pending_refresh_after_ha_write_keeps_color_on_failed_get(self):  # pylint: disable=invalid-name
        """Jeff sequence: scheduled refresh, HA color write, then failed GET keeps state."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog = {
            "basicEffects": [{
                "id": "constant-id",
                "referencedId": "constant-resource-id",
                "effectType": 0,
                "name": "Constante",
                "layouts": [{
                    "viewType": "SEGMENT_COLOR_LIST",
                    "currentSelected": "whole",
                    "wholeColorList": ["#0066ff"],
                }],
            }],
            "sceneEffects": [{
                "id": "wave-id",
                "referencedId": "wave-ref",
                "effectType": 3,
                "name": "Ola",
            }],
        }
        device.set_rgbic_effect_catalog(catalog)
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "constant-id"}
        })
        assert len(scheduled) == 1
        with patch.object(device._dreo, "set_rgbic_effect", return_value=True), patch.object(
            device._outbox, "flush_now", return_value=True
        ):
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is True

        assert device.rgbic_color == (255, 0, 0)
        assert device.rgbic_effect_name == "Constante"
        assert device._rgbic_color_effect_id == "constant-id"

        with patch.object(device._dreo, "get_rgbic_effect_catalog", return_value=None):
            scheduled[0]()

        assert device.rgbic_color == (255, 0, 0)
        assert device.rgbic_effect_names == ["Constante"]
        assert device.rgbic_scene_effect_names == ["Ola"]
        assert device.rgbic_effect_name == "Constante"
        assert device._rgbic_color_effect_id == "constant-id"
        assert device._rgbic_effect_id_to_name.get("wave-id") == "Ola"

    def test_HAP010S_effect_change_does_not_restore_constant_color(self):  # pylint: disable=invalid-name
        """Leaving Constant clears its color, and a later catalog read does not restore it."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog = {"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#00ff00"],
            }],
        }, {
            "id": "contrast-id",
            "referencedId": "contrast-ref",
            "effectType": 0,
            "name": "Contraste",
            "layouts": [],
        }]}
        device._rgbmode = 2
        device._rgbeffectid = "constant-id"
        device.set_rgbic_effect_catalog(catalog)
        assert device.rgbic_color == (0, 255, 0)

        device.update_state({"rgbeffectid": {"state": "contrast-id"}})

        assert device.rgbeffectid == "contrast-id"
        assert device.rgbic_color is None
        device.set_rgbic_effect_catalog(catalog)
        assert device.rgbic_color is None
        assert device.rgbic_effect_name == "Contraste"

    def test_HAP010S_repeated_rest_effect_id_does_not_bump_generation(self):  # pylint: disable=invalid-name
        """Repeated REST priming with the same rgbeffectid must not advance generation."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
            }],
        }]})

        device.update_state({"rgbeffectid": {"state": "constant-id"}, "rgbmode": {"state": 2}})
        generation_after_first = device._rgbic_generation
        device.update_state({"rgbeffectid": {"state": "constant-id"}})

        assert device._rgbic_generation == generation_after_first

    def test_HAP010S_rest_after_websocket_does_not_revert_effect_or_generation(self):  # pylint: disable=invalid-name
        """Live WebSocket rgbeffectid remains authoritative over later REST snapshots."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "live-id"}})
        generation_after_ws = device._rgbic_generation

        device.update_state({
            "rgbmode": {"state": 1},
            "rgbeffectid": {"state": "stale-rest-id"},
        })

        assert device.rgbeffectid == "live-id"
        assert device._rgbic_generation == generation_after_ws

    def test_HAP010S_rest_after_local_write_does_not_revert_state(self):  # pylint: disable=invalid-name
        """REST cannot roll back a successful HA RGBIC write or its generation."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
            }],
        }]})
        device.update_state({"rgbmode": {"state": 2}, "rgbeffectid": {"state": "constant-id"}})
        assert device._rgbic_effect_id_reported is False
        assert device._rgbic_mode_authoritative is False

        with patch.object(device._dreo, "set_rgbic_effect", return_value=True), patch.object(
            device._outbox, "flush_now", return_value=True
        ):
            assert device.set_rgbic_effect(color_rgb=(255, 128, 64)) is True

        assert device._rgbic_effect_id_reported is True
        assert device._rgbic_mode_authoritative is True
        generation_after_write = device._rgbic_generation
        assert device.rgbic_color == (255, 128, 64)
        assert device.rgbeffectid == "constant-id"

        device.update_state({
            "rgbmode": {"state": 1},
            "rgbeffectid": {"state": "other-rest-id"},
        })

        assert device.rgbmode == 2
        assert device.rgbeffectid == "constant-id"
        assert device.rgbic_color == (255, 128, 64)
        assert device._rgbic_generation == generation_after_write

    @pytest.mark.parametrize(
        "bad_value",
        [None, True, False, 3.14, [], "not-present"],
    )
    def test_HAP010S_invalid_rest_effect_id_is_ignored(self, bad_value):  # pylint: disable=invalid-name
        """Invalid REST rgbeffectid values must not change id or generation."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device._rgbmode = 2
        device._rgbeffectid = "kept-id"
        generation_before = device._rgbic_generation

        if bad_value == "not-present":
            device.update_state({"rgbmode": {"state": 2}})
        else:
            device.update_state({"rgbeffectid": {"state": bad_value}})

        assert device.rgbeffectid == "kept-id"
        assert device._rgbic_generation == generation_before

    def test_HAP010S_rest_mode_and_effect_id_change_clears_manual_color(self):  # pylint: disable=invalid-name
        """One REST update to indicator mode and a new effect id clears the manual color."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.update_state({"rgbmode": {"state": 2}, "rgbeffectid": {"state": "constant-id"}})
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
            }],
        }]})
        assert device.rgbic_color == (0, 102, 255)

        device.update_state({
            "rgbmode": {"state": 1},
            "rgbeffectid": {"state": "other-rest-id"},
        })

        assert device.rgbmode == 1
        assert device.rgbeffectid == "other-rest-id"
        assert device.rgbic_color is None

    def test_HAP010S_concurrent_rest_blocked_until_websocket_releases_lock(self):  # pylint: disable=invalid-name
        """Stale REST cannot interleave with an in-flight WebSocket RGBIC update."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "live-id",
            "referencedId": "live-ref",
            "effectType": 0,
            "name": "Live",
            "layouts": [],
        }]})
        device._rgbmode = 2
        device._rgbic_effect_id_reported = False
        gate = _GateLock(device._lock)
        device._lock = gate
        gate.delay_release = True
        rest_done = Event()
        rest_thread = None
        ws_thread = None

        def apply_stale_rest():
            device.update_state({
                "rgbmode": {"state": 1},
                "rgbeffectid": {"state": "stale-rest"},
            })
            rest_done.set()

        ws_errors: list[BaseException] = []
        rest_errors: list[BaseException] = []
        try:
            ws_thread, ws_errors = _start_thread(
                device.handle_server_update,
                {REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "live-id"}},
            )
            assert gate.hold_reached.wait(timeout=5.0)
            rest_thread, rest_errors = _start_thread(apply_stale_rest)
            assert gate.acquire_contended.wait(timeout=5.0)
            gate.continue_release.set()
        finally:
            gate.continue_release.set()
            if ws_thread is not None:
                _join_thread(ws_thread, ws_errors)
            if rest_thread is not None:
                _join_thread(rest_thread, rest_errors)

        assert device.rgbeffectid == "live-id"
        assert device.rgbmode == 2
        assert rest_done.is_set()

    def test_HAP010S_concurrent_websocket_waits_for_local_write_lock(self):  # pylint: disable=invalid-name
        """WebSocket RGBIC handling cannot interleave the post-write HA success path."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
            }],
        }]})
        device.update_state({"rgbmode": {"state": 2}, "rgbeffectid": {"state": "constant-id"}})
        gate = _GateLock(device._lock)
        device._lock = gate
        gate.delay_release = True
        gate.delay_from_release = 2
        ha_done = Event()
        ha_thread = None
        ws_thread = None
        ha_errors: list[BaseException] = []
        ws_errors: list[BaseException] = []

        def write_ha_color():
            with patch.object(device._dreo, "set_rgbic_effect", return_value=True), patch.object(
                device._outbox, "flush_now", return_value=True
            ):
                assert device.set_rgbic_effect(color_rgb=(10, 20, 30)) is True
            ha_done.set()

        def report_ws():
            device.handle_server_update({REPORTED_KEY: {"rgbeffectid": "constant-id", "rgbmode": 2}})

        try:
            ha_thread, ha_errors = _start_thread(write_ha_color)
            assert gate.hold_reached.wait(timeout=5.0)
            ws_thread, ws_errors = _start_thread(report_ws)
            assert gate.acquire_contended.wait(timeout=5.0)
            gate.continue_release.set()
        finally:
            gate.continue_release.set()
            if ha_thread is not None:
                _join_thread(ha_thread, ha_errors)
            if ws_thread is not None:
                _join_thread(ws_thread, ws_errors)

        assert ha_done.is_set()
        assert device.rgbic_color == (10, 20, 30)
        assert device._rgbic_effect_id_reported is True

    def test_HAP010S_websocket_mode_and_effect_id_share_one_transition(self):  # pylint: disable=invalid-name
        """Mode and effect id from the same WebSocket message stay coherent."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.update_state({"rgbmode": {"state": 2}, "rgbeffectid": {"state": "constant-id"}})
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
            }],
        }, {
            "id": "other-id",
            "referencedId": "other-ref",
            "effectType": 0,
            "name": "Other",
            "layouts": [],
        }]})

        device.handle_server_update({
            REPORTED_KEY: {"rgbmode": 1, "rgbeffectid": "other-id"}
        })

        assert device.rgbmode == 1
        assert device.rgbeffectid == "other-id"
        assert device.rgbic_color is None
        assert device.rgbic_effect_name == "Other"

    def test_HAP010S_set_rgbic_effect_mode_failure_does_not_publish_color(self):  # pylint: disable=invalid-name
        """A failed rgbmode step must not publish a color or arm echo suppression."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
            }],
        }]})
        device.update_state({"rgbmode": {"state": 2}})

        with patch.object(device, "set_rgbic_mode", return_value=False):
            assert device.set_rgbic_effect(color_rgb=(1, 2, 3)) is False

        assert device._skip_next_constant_refresh is None
        assert device.rgbic_color is None
        assert device.rgbic_effect_name is None

    def test_HAP010S_set_rgbic_effect_rest_failure_keeps_known_color(self):  # pylint: disable=invalid-name
        """A failed REST edit/batch must not publish an optimistic color or skip the next refresh."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.update_state({"rgbmode": {"state": 2}, "rgbeffectid": {"state": "constant-id"}})
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
            }],
        }]})
        assert device.rgbic_color == (0, 102, 255)
        assert device.rgbic_effect_name == "Constante"

        with patch.object(device, "set_rgbic_mode", return_value=True) as set_mode, patch.object(
            device._dreo, "set_rgbic_effect", return_value=False
        ) as rest_write, patch.object(device._outbox, "flush_now", return_value=True):
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is False

        set_mode.assert_called_once_with(2)
        rest_write.assert_called_once()
        assert device._skip_next_constant_refresh is None
        assert device.rgbic_color == (0, 102, 255)
        assert device.rgbic_effect_name == "Constante"
        assert not device._rgbic_effect_id_reported
        assert not device._rgbic_mode_authoritative

    def test_HAP010S_set_rgbic_effect_rest_exception_keeps_prior_color(self):  # pylint: disable=invalid-name
        """A REST exception during a color write must not publish that color."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
            }],
        }]})
        device.update_state({"rgbmode": {"state": 2}})

        with patch.object(device._dreo, "set_rgbic_effect", side_effect=RuntimeError("REST failed")), patch.object(
            device._outbox, "flush_now", return_value=True
        ):
            with pytest.raises(RuntimeError, match="REST failed"):
                device.set_rgbic_effect(color_rgb=(1, 2, 3))

        assert device._skip_next_constant_refresh is None
        assert device.rgbic_color is None
        assert device.rgbic_effect_name is None

    def test_HAP010S_color_write_uses_constant_name_captured_under_lock(self):  # pylint: disable=invalid-name
        """The Constant name must be read under ``_lock``, not before contending for it."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
            }],
        }]})
        device.update_state({"rgbmode": {"state": 2}})
        posted: list[str] = []
        renamed = "ConstanteRenombrada"
        gate = _GateLock(device._lock)
        device._lock = gate
        write_thread = None
        write_errors: list[BaseException] = []
        main_holds_lock = False

        def fake_rest(_device, effect_name, _color_hex):
            posted.append(effect_name)
            return True

        def write_ha_color() -> None:
            with patch.object(device._dreo, "set_rgbic_effect", side_effect=fake_rest), patch.object(
                device._outbox, "flush_now", return_value=True
            ):
                assert device.set_rgbic_effect(color_rgb=(4, 5, 6)) is True

        try:
            gate.acquire()
            main_holds_lock = True
            write_thread, write_errors = _start_thread(write_ha_color)
            assert gate.acquire_contended.wait(timeout=5.0)
            device._rgbic_color_effect_name = renamed
            device._rgbic_effect_names = [renamed]
            device._rgbic_effect_id_to_name["constant-id"] = renamed
            gate.release()
            main_holds_lock = False
        finally:
            if main_holds_lock:
                gate.release()
            if write_thread is not None:
                _join_thread(write_thread, write_errors)

        assert posted == [renamed]

    def test_HAP010S_rgbic_lock_contention_completes_without_deadlock(self):  # pylint: disable=invalid-name
        """Concurrent RGBIC entry points must finish without hanging."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog({"basicEffects": [{
            "id": "constant-id",
            "referencedId": "constant-ref",
            "effectType": 0,
            "name": "Constante",
            "layouts": [],
        }]})
        device._rgbmode = 2
        worker_count = 8
        barrier = Barrier(worker_count)

        def churn(index: int) -> None:
            barrier.wait(timeout=5.0)
            if index % 2 == 0:
                device.update_state({"rgbeffectid": {"state": "constant-id"}})
            else:
                device.handle_server_update({REPORTED_KEY: {"rgbeffectid": "constant-id"}})

        threads: list[Thread] = []
        errors: list[list[BaseException]] = []
        try:
            for index in range(worker_count):
                thread, thread_errors = _start_thread(churn, index)
                threads.append(thread)
                errors.append(thread_errors)
        finally:
            for thread, thread_errors in zip(threads, errors):
                _join_thread(thread, thread_errors)

    def test_HAP010S_initial_catalog_read_does_not_replace_newer_ha_color(self):  # pylint: disable=invalid-name
        """Initial catalog response is ignored for RGB if HA wrote a color during its request."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device._rgbmode = 2
        catalog = {"basicEffects": [{
            "id": "constant-catalog-id",
            "referencedId": "constant-resource-id",
            "effectType": 0,
            "name": "Constante",
            "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST",
                "currentSelected": "whole",
                "wholeColorList": ["#0066ff"],
                "colorList": ["#ffffff"] * 17,
            }],
        }]}
        device.set_rgbic_effect_catalog(catalog)
        stale_generation = device._rgbic_generation

        with patch.object(device._dreo, "set_rgbic_effect", return_value=True):
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is True

        device.set_rgbic_effect_catalog(
            catalog,
            expected_rgbic_generation=stale_generation,
        )
        assert device.rgbic_color == (255, 0, 0)

    def test_HAP010S_non_constant_effect_report_does_not_refresh_catalog(self):  # pylint: disable=invalid-name
        """Catalog color refreshes are scoped to the structurally identified Constant effect."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog({
            "basicEffects": [{
                "id": "constant-id",
                "referencedId": "constant-ref",
                "effectType": 0,
                "name": "Constante",
                "layouts": [{
                    "viewType": "SEGMENT_COLOR_LIST",
                    "currentSelected": "whole",
                    "wholeColorList": ["#00ff00"],
                }],
            }, {
                "id": "contrast-id",
                "referencedId": "contrast-ref",
                "effectType": 0,
                "name": "Contraste",
                "layouts": [],
            }],
        })
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )

        device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "contrast-id"}})

        assert scheduled == []

    def test_HAP010S_catalog_id_matches_websocket_id_not_referenced_id(self):  # pylint: disable=invalid-name
        """The 530S uses catalog id; the response's English name is not displayed."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2}})
        localized_catalog = {
            "basicEffects": [{
                "id": "2124876509150707714",
                "referencedId": "1700000000000000003",
                "effectType": 0,
                "name": "Círculo",
                "layouts": [],
            }],
        }
        device.set_rgbic_effect_catalog(localized_catalog)

        def fake_send(dev, params):
            _ack_control_send(self.pydreo_manager, dev, params)

        posted_payloads = []

        def fake_call_api(_url, api, _method, payload, _headers):
            if api == "/api/device/rgb-effect/all/list":
                return {"code": 0, "data": localized_catalog}, 200
            if api == "/api/device/rgb-effect/edit/batch":
                posted_payloads.append(payload)
                return {"code": 0, "data": {
                    "id": "2124876509150707714",
                    "referencedId": "1700000000000000003",
                    "name": "Cycle",
                }}, 200
            return None, 500

        with patch(PATCH_SEND_COMMAND, side_effect=fake_send), patch(
            "custom_components.dreo.pydreo.Helpers.call_api", side_effect=fake_call_api
        ):
            assert device.set_rgbic_effect("Círculo") is True

        assert device.rgbic_effect_name == "Círculo"
        assert posted_payloads[0][0]["effectType"] == 0
        assert posted_payloads[0][0]["id"] == "2124876509150707714"
        assert posted_payloads[0][0]["subEffects"][0]["effectId"] == "1700000000000000003"
        device.handle_server_update({REPORTED_KEY: {"rgbeffectid": "2124876509150707714"}})
        assert device.rgbic_effect_name == "Círculo"

    def test_HAP010S_real_websocket_id_is_not_guessed_from_remote_catalog(self):  # pylint: disable=invalid-name
        """The observed 1701 ID stays unresolved when no catalog ID matches exactly."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog({
            "remoteEffects": [{
                "id": "remote-entry-id",
                "referencedId": "remote-base-id",
                "name": "Example remote name",
                "subRemoteEffect": {"effectId": "remote-base-id", "effectName": "Example remote name"},
            }],
        })
        device.handle_server_update({REPORTED_KEY: {"rgbeffectid": "1701000000000000011"}})
        assert device.rgbeffectid == "1701000000000000011"
        assert device.rgbic_effect_name is None

    def test_purifyon_not_supported_without_state(self):
        """Purifiers that don't report purifyon must not get the switch."""
        self.get_devices_file_name = "get_devices_HAP008S.json"
        self.pydreo_manager.load_devices()
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.purifyon is None
        assert not air_purifier.is_feature_supported("purifyon")

    def test_air_purifier_preset_mode_variant_mapping(self):
        """Mode variants like auto-regular should still map to the base preset mode."""
        self.get_devices_file_name = "get_devices_HAP003S.json"
        self.pydreo_manager.load_devices()
        air_purifier = self.pydreo_manager.devices[0]

        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto-regular"}})
        assert air_purifier.preset_mode == "auto"

        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "sleep-regular"}})
        assert air_purifier.preset_mode == "sleep"

        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "manual"}})
        assert air_purifier.preset_mode == "manual"

    def test_air_purifier_set_preset_mode_uses_mode_key(self):
        """Air purifier preset mode changes should send the mode command."""
        self.get_devices_file_name = "get_devices_HAP003S.json"
        self.pydreo_manager.load_devices()
        air_purifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "sleep"})

    def test_HAP010S_catalog_exposes_eight_basics_and_six_scenes(self):  # pylint: disable=invalid-name
        """Effect names and ordering come from the live catalog fields, not hardcoded constants."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.set_rgbic_effect_catalog(_hap010s_rgbic_catalog())

        assert device.rgbic_effect_names == HAP010S_BASIC_EFFECT_NAMES
        assert device.rgbic_scene_effect_names == HAP010S_SCENE_EFFECT_NAMES
        assert device.rgbic_selectable_effect_names == [
            *HAP010S_BASIC_EFFECT_NAMES,
            *HAP010S_SCENE_EFFECT_NAMES,
        ]

    @pytest.mark.parametrize("scene_name", HAP010S_SCENE_EFFECT_NAMES)
    def test_HAP010S_each_scene_posts_scene_catalog_rest_payload(  # pylint: disable=invalid-name
        self, scene_name
    ):
        """Every scene issues edit/batch with effectType 3 and catalog ids after rgbmode=2."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 1}})
        catalog = _hap010s_rgbic_catalog()
        device.set_rgbic_effect_catalog(catalog)
        scene = next(item for item in catalog["sceneEffects"] if item["name"] == scene_name)
        ws_batches: list[dict] = []
        rest_posts: list[list] = []

        def fake_send(dev, params):
            ws_batches.append(dict(params))
            _ack_control_send(self.pydreo_manager, dev, params)

        def fake_call_api(_url, api, method, payload, _headers):
            if api == "/api/device/rgb-effect/all/list":
                return {"code": 0, "data": catalog}, 200
            if api == "/api/device/rgb-effect/edit/batch":
                rest_posts.append(payload)
                return {"code": 0, "data": {}}, 200
            return None, 500

        with patch(PATCH_SEND_COMMAND, side_effect=fake_send), patch(
            "custom_components.dreo.pydreo.Helpers.call_api",
            side_effect=fake_call_api,
        ):
            assert device.set_rgbic_effect(scene_name) is True

        assert ws_batches == [{"rgbmode": 2}]
        assert len(rest_posts) == 1
        posted = rest_posts[0][0]
        assert posted["effectType"] == 3
        assert posted["name"] == scene_name
        assert posted["id"] == scene["id"]
        assert posted["subEffects"][0]["effectId"] == scene["referencedId"]
        assert device.rgbic_effect_name == scene_name

    @pytest.mark.parametrize("basic_name", HAP010S_BASIC_EFFECT_NAMES)
    def test_HAP010S_each_basic_posts_basic_catalog_rest_payload(  # pylint: disable=invalid-name
        self, basic_name
    ):
        """Every basic effect issues edit/batch with effectType 0 and catalog ids after rgbmode=2."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 1}})
        catalog = _hap010s_rgbic_catalog()
        device.set_rgbic_effect_catalog(catalog)
        basic = next(item for item in catalog["basicEffects"] if item["name"] == basic_name)
        ws_batches: list[dict] = []
        rest_posts: list[list] = []

        def fake_send(dev, params):
            ws_batches.append(dict(params))
            _ack_control_send(self.pydreo_manager, dev, params)

        def fake_call_api(_url, api, method, payload, _headers):
            if api == "/api/device/rgb-effect/all/list":
                return {"code": 0, "data": catalog}, 200
            if api == "/api/device/rgb-effect/edit/batch":
                rest_posts.append(payload)
                return {"code": 0, "data": {}}, 200
            return None, 500

        with patch(PATCH_SEND_COMMAND, side_effect=fake_send), patch(
            "custom_components.dreo.pydreo.Helpers.call_api",
            side_effect=fake_call_api,
        ):
            assert device.set_rgbic_effect(basic_name) is True

        assert ws_batches == [{"rgbmode": 2}]
        assert rest_posts[0][0]["effectType"] == 0
        assert rest_posts[0][0]["id"] == basic["id"]
        assert rest_posts[0][0]["name"] == basic_name

    def test_HAP010S_effect_apply_drains_power_before_mode_then_rest(self):  # pylint: disable=invalid-name
        """Pending rgbon/rgbbri flush before rgbmode=2, then REST edit/batch for the effect."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 1, "rgbon": False, "rgbbri": 25}})
        catalog = _hap010s_rgbic_catalog()
        device.set_rgbic_effect_catalog(catalog)
        ws_batches: list[dict] = []
        rest_posts: list[list] = []

        def fake_send(dev, params):
            ws_batches.append(dict(params))
            _ack_control_send(self.pydreo_manager, dev, params)

        def fake_call_api(_url, api, method, payload, _headers):
            if api == "/api/device/rgb-effect/all/list":
                return {"code": 0, "data": catalog}, 200
            if api == "/api/device/rgb-effect/edit/batch":
                rest_posts.append(payload)
                return {"code": 0, "data": {}}, 200
            return None, 500

        with patch(PATCH_SEND_COMMAND, side_effect=fake_send), patch(
            "custom_components.dreo.pydreo.Helpers.call_api",
            side_effect=fake_call_api,
        ):
            device.rgbon = True
            device.rgbbri = 50
            assert device.set_rgbic_effect(HAP010S_BASIC_EFFECT_NAMES[0]) is True

        rgbmode_idx = next(
            i for i, batch in enumerate(ws_batches) if batch.get("rgbmode") == 2
        )
        power_batches = ws_batches[:rgbmode_idx]
        sent_keys = {key for batch in power_batches for key in batch}
        assert sent_keys >= {"rgbon", "rgbbri"}
        assert power_batches[0]["rgbon"] is True
        assert any(batch.get("rgbbri") == 50 for batch in power_batches)
        assert ws_batches[rgbmode_idx] == {"rgbmode": 2}
        assert len(ws_batches) == rgbmode_idx + 1
        assert rest_posts[0][0]["name"] == HAP010S_BASIC_EFFECT_NAMES[0]

    def test_HAP010S_reapplying_effect_does_not_require_selected_flag(self):  # pylint: disable=invalid-name
        """A successful local command remains visible even if the catalog is unselected."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog = _hap010s_rgbic_catalog()
        selected_name = HAP010S_BASIC_EFFECT_NAMES[0]
        catalog["basicEffects"][0]["selected"] = True
        device.set_rgbic_effect_catalog(catalog)
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2}})

        def fake_send(dev, params):
            _ack_control_send(self.pydreo_manager, dev, params)

        def fake_call_api(_url, api, _method, _payload, _headers):
            if api == "/api/device/rgb-effect/all/list":
                return {"code": 0, "data": catalog}, 200
            if api == "/api/device/rgb-effect/edit/batch":
                return {"code": 0, "data": {}}, 200
            return None, 500

        with patch(PATCH_SEND_COMMAND, side_effect=fake_send), patch(
            "custom_components.dreo.pydreo.Helpers.call_api", side_effect=fake_call_api
        ):
            assert device.set_rgbic_effect(selected_name) is True

        assert device.rgbic_effect_name == selected_name
        assert device._skip_next_constant_refresh is None

    @pytest.mark.parametrize(
        ("rgb", "expected_hex"),
        [((255, 0, 0), "#ff0000"), ((0, 0, 255), "#0000ff"), ((255, 255, 255), "#ffffff")],
    )
    def test_HAP010S_rgb_color_updates_only_catalog_whole_color_list(
        self, rgb, expected_hex
    ):  # pylint: disable=invalid-name
        """Global RGB color uses localized catalog IDs and preserves all segment colors."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        color_list = [f"#{index:02x}{index:02x}{index:02x}" for index in range(17)]
        constant = {
            "id": "catalog-constant-id",
            "referencedId": "catalog-constant-resource",
            "effectType": 0,
            "name": "Luz constante",
            "selected": False,
            "layouts": [{
                "currentSelected": "whole",
                "wholeColorList": ["#123456"],
                "colorList": color_list,
                "effectParamKey": "colors",
                "viewType": "SEGMENT_COLOR_LIST",
            }],
        }
        catalog = {"basicEffects": [constant], "sceneEffects": []}
        device.set_rgbic_effect_catalog(catalog)
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2}})
        posted = []

        def fake_send(dev, params):
            _ack_control_send(self.pydreo_manager, dev, params)

        def fake_call_api(_url, api, _method, payload, _headers):
            if api == "/api/device/rgb-effect/all/list":
                return {"code": 0, "data": catalog}, 200
            if api == "/api/device/rgb-effect/edit/batch":
                posted.extend(payload)
                return {"code": 0, "data": {}}, 200
            return None, 500

        with patch(PATCH_SEND_COMMAND, side_effect=fake_send), patch(
            "custom_components.dreo.pydreo.Helpers.call_api", side_effect=fake_call_api
        ):
            assert device.set_rgbic_effect(color_rgb=rgb) is True

        entry = posted[0]
        assert entry["name"] == "Luz constante"
        assert entry["id"] == "catalog-constant-id"
        assert entry["subEffects"][0]["effectId"] == "catalog-constant-resource"
        layout = entry["subEffects"][0]["layouts"][0]
        assert layout["wholeColorList"] == [expected_hex]
        assert layout["colorList"] == color_list
        assert len(layout["colorList"]) == 17
        assert layout["currentSelected"] == "whole"
        assert device.rgbic_effect_name == "Luz constante"
        assert device.rgbic_color == rgb

    def test_segments_effect_payload_uses_original_catalog_identity_and_preserves_colors(self):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        segment_colors = ["#110022", "#220044"]
        effect = {
            "id": "constant-id", "referencedId": "constant-ref", "effectType": 0,
            "name": "Constante", "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST", "currentSelected": "whole",
                "wholeColorList": ["#abcdef"], "colorList": segment_colors,
            }],
        }
        entry = self.pydreo_manager._prepare_rgbic_edit_batch_entry(
            device, effect, effect_name="Constante", current_selected="segment"
        )
        assert entry["id"] == "constant-id"
        assert entry["name"] == "Constante"
        layout = entry["subEffects"][0]["layouts"][0]
        assert layout["currentSelected"] == "segment"
        assert layout["wholeColorList"] == ["#abcdef"]
        assert layout["colorList"] == segment_colors

    def test_uniform_rgb_updates_every_whole_color_layout_and_preserves_segments(self):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        effect = {"id": "id", "referencedId": "ref", "layouts": [
            {"viewType": "SEGMENT_COLOR_LIST", "wholeColorList": ["#000000"],
             "colorList": ["#112233"], "currentSelected": "segment"},
            {"viewType": "SEGMENT_COLOR_LIST", "wholeColorList": ["#ffffff"],
             "colorList": ["#445566"], "currentSelected": "segment"},
        ]}
        entry = self.pydreo_manager._prepare_rgbic_edit_batch_entry(
            device, effect, effect_name="Constant", color="#aBcDeF"
        )
        layouts = entry["subEffects"][0]["layouts"]
        assert [layout["wholeColorList"] for layout in layouts] == [["#abcdef"], ["#abcdef"]]
        assert [layout["colorList"] for layout in layouts] == [["#112233"], ["#445566"]]
        assert [layout["currentSelected"] for layout in layouts] == ["whole", "whole"]

    def test_uniform_rgb_keeps_hcf_hexadecimal_uppercase(self):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device._device_definition = copy(device._device_definition)
        device._device_definition.supports_rgbic_mode_light = False
        effect = {"id": "id", "referencedId": "ref", "layouts": [
            {"wholeColorList": ["#000000"], "colorList": ["#112233"]},
            {"wholeColorList": ["#ffffff"], "colorList": ["#445566"]},
        ]}
        entry = self.pydreo_manager._prepare_rgbic_edit_batch_entry(
            device, effect, effect_name="Constant", color="#aBcDeF"
        )
        layouts = entry["subEffects"][0]["layouts"]
        assert [layout["wholeColorList"] for layout in layouts] == [["#ABCDEF"], ["#ABCDEF"]]
        assert [layout["colorList"] for layout in layouts] == [["#112233"], ["#445566"]]

    def test_whole_selection_updates_every_segment_layout(self):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        effect = {"id": "id", "referencedId": "ref", "layouts": [
            {"viewType": "SEGMENT_COLOR_LIST", "wholeColorList": ["#000000"], "colorList": ["#112233"]},
            {"viewType": "SEGMENT_COLOR_LIST", "wholeColorList": ["#ffffff"], "colorList": ["#445566"]},
        ]}
        entry = self.pydreo_manager._prepare_rgbic_edit_batch_entry(
            device, effect, effect_name="Constant", current_selected="whole"
        )
        layouts = entry["subEffects"][0]["layouts"]
        assert [layout["currentSelected"] for layout in layouts] == ["whole", "whole"]
        assert [layout["colorList"] for layout in layouts] == [["#112233"], ["#445566"]]
        assert [layout["wholeColorList"] for layout in layouts] == [["#000000"], ["#ffffff"]]

    def test_segment_catalog_read_and_write_use_same_first_valid_layout(self):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog_colors = ["#112233", "#445566"]
        effect = {
            "id": "constant-id", "referencedId": "constant-ref", "effectType": 0,
            "name": "Constante",
            "layouts": [
                {"viewType": "SEGMENT_COLOR_LIST", "colorList": ["#000000"]},
                {"viewType": "SEGMENT_COLOR_LIST", "wholeColorList": ["not validated"],
                 "colorList": catalog_colors, "currentSelected": "whole", "effectParamKey": "keep"},
                {"viewType": "SEGMENT_COLOR_LIST", "wholeColorList": ["#fedcba"],
                 "colorList": ["#aaaaaa", "#bbbbbb"], "currentSelected": "whole"},
            ],
        }
        catalog = {"basicEffects": [effect], "sceneEffects": []}
        device.set_rgbic_effect_catalog(catalog)
        assert device.rgbic_segment_colors == catalog_colors

        requested = ["#010203", "#a0b0c0"]
        with patch.object(self.pydreo_manager, "get_rgbic_effect_catalog", return_value=catalog), \
             patch.object(self.pydreo_manager, "_post_rgbic_edit_batch", return_value=True) as post:
            assert self.pydreo_manager.set_rgbic_segment_colors(device, requested)

        entry = post.call_args.args[1][0]
        layouts = entry["subEffects"][0]["layouts"]
        assert entry["id"] == "constant-id"
        assert entry["name"] == "Constante"
        assert layouts[1]["effectParamKey"] == "keep"
        assert layouts[0] == effect["layouts"][0]
        assert layouts[1]["colorList"] == requested
        assert layouts[1]["wholeColorList"] == ["not validated"]
        assert layouts[1]["currentSelected"] == "segment"
        assert layouts[2] == effect["layouts"][2]

    @pytest.mark.parametrize("colors", [[], ["red"], ["#123456", "#bad"]])
    def test_segment_write_rejects_invalid_hex_colors(self, colors):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        with patch.object(self.pydreo_manager, "get_rgbic_effect_catalog") as get_catalog, \
             patch.object(self.pydreo_manager, "_post_rgbic_edit_batch") as post:
            assert not self.pydreo_manager.set_rgbic_segment_colors(device, colors)
        get_catalog.assert_not_called()
        post.assert_not_called()

    def test_segment_write_rejects_catalog_length_mismatch_and_api_failure(self):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        catalog = {"basicEffects": [{
            "id": "constant-id", "referencedId": "constant-ref", "effectType": 0,
            "name": "Constante", "layouts": [{
                "viewType": "SEGMENT_COLOR_LIST", "wholeColorList": ["#abcdef"],
                "colorList": ["#123456", "#789abc"],
            }],
        }]}
        with patch.object(self.pydreo_manager, "get_rgbic_effect_catalog", return_value=catalog), \
             patch.object(self.pydreo_manager, "_post_rgbic_edit_batch", return_value=False) as post:
            assert not self.pydreo_manager.set_rgbic_segment_colors(device, ["#ffffff"])
            post.assert_not_called()
            assert not self.pydreo_manager.set_rgbic_segment_colors(device, ["#ffffff", "#000000"])
            post.assert_called_once()

    def test_segment_write_rejects_incompatible_device(self):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device._device_definition = copy(device._device_definition)
        device._device_definition.supports_rgbic_mode_light = False
        with patch.object(self.pydreo_manager, "get_rgbic_effect_catalog") as get_catalog:
            assert not self.pydreo_manager.set_rgbic_segment_colors(device, ["#ffffff"])
        get_catalog.assert_not_called()
