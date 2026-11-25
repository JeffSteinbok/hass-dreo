"""Tests for Dreo Fans"""

# pylint: disable=used-before-assignment
import logging
from threading import Event, Thread
from unittest.mock import patch

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
            "lang": "es",
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

    def test_HAP010S_catalog_reads_always_use_spanish_app_headers(self):  # pylint: disable=invalid-name
        """Initial and later reads share RGBIC-only locale headers."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        response = {"code": 0, "data": {"basicEffects": [], "sceneEffects": []}}
        expected_headers = {
            **Helpers.req_headers(self.pydreo_manager),
            "lang": "es",
            "country": "ES",
            "appversion": "3.8.2",
        }

        with patch("custom_components.dreo.pydreo.Helpers.call_api", return_value=(response, 200)) as call_api:
            assert self.pydreo_manager.get_rgbic_effect_catalog(device) == response["data"]
            # Catalog refresh after a later WebSocket change uses the same path.
            assert self.pydreo_manager.get_rgbic_effect_catalog(device) == response["data"]

        assert len(call_api.call_args_list) == 2
        for call in call_api.call_args_list:
            assert call.args[1:4] == (
                "/api/device/rgb-effect/all/list",
                "get",
                {"devicesn": device.serial_number},
            )
            assert call.args[4] == expected_headers

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
        """Repeated same-ID reports schedule one read and do not lose a newer event."""
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
        callback_colors = []
        device.add_attr_callback(lambda: callback_colors.append(device.rgbic_color))
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "2124876509150707712"}
        })
        # Repeated reports before the timer fires coalesce into that same read.
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
                # A second report repeats the same ID while the first GET is in flight.
                device.handle_server_update_base({
                    REPORTED_KEY: {"rgbeffectid": "2124876509150707712"}
                })
                return catalog_with_color("#00ff00")
            return catalog_with_color("#ff020a")

        with patch.object(device._dreo, "get_rgbic_effect_catalog", side_effect=get_catalog):
            scheduled[0]()
            assert device._rgbic_catalog_refresh_cancel is None
            assert device._rgbic_catalog_refresh_running is False

            # A later same-ID report must start a new refresh after the prior one ended.
            device.handle_server_update_base({
                REPORTED_KEY: {"rgbeffectid": "2124876509150707712"}
            })
            assert len(scheduled) == 2
            scheduled[1]()

        assert len(reads) == 3
        assert device.rgbeffectid == "2124876509150707712"
        assert device.rgbic_color == (255, 2, 10)
        assert callback_colors[-1] == (255, 2, 10)
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
            }]}

        device.set_rgbic_effect_catalog(catalog_with_color("#00ff00"))
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({
            REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "constant-id"}
        })
        assert len(scheduled) == 1

        pass_finished = Event()
        allow_worker_release = Event()
        original_pass = device._rgbic_catalog_refresh_pass
        pass_count = 0

        def pause_after_first_pass():
            nonlocal pass_count
            completed_sequence = original_pass()
            pass_count += 1
            if pass_count == 1:
                pass_finished.set()
                if not allow_worker_release.wait(timeout=5):
                    raise AssertionError("test did not release the catalog worker")
            return completed_sequence

        worker = Thread(target=scheduled[0])
        with patch.object(
            device._dreo,
            "get_rgbic_effect_catalog",
            side_effect=[catalog_with_color("#ff0000"), catalog_with_color("#0000ff")],
        ) as get_catalog, patch.object(
            device, "_rgbic_catalog_refresh_pass", side_effect=pause_after_first_pass
        ):
            worker.start()
            try:
                assert pass_finished.wait(timeout=5)
                # This is the vulnerable window: the GET/pass finished but the worker
                # has not yet atomically released its running state.
                device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "constant-id"}})
                assert len(scheduled) == 1
            finally:
                allow_worker_release.set()
            worker.join(timeout=5)

        assert not worker.is_alive()
        assert pass_count == 2
        assert get_catalog.call_count == 2
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

            device.handle_server_update_base({
                REPORTED_KEY: {"rgbeffectid": "constant-id"}
            })
            assert len(scheduled) == 2
            scheduled[1]()

        assert get_catalog.call_count == 2
        assert device.rgbic_color == (0, 102, 255)
        assert device._rgbic_catalog_refresh_cancel is None
        assert device._rgbic_catalog_refresh_running is False

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

    def test_HAP010S_failed_color_write_keeps_single_revision_and_stale_catalog(self):  # pylint: disable=invalid-name
        """A failed HA color write bumps both pre-write revisions and keeps prior effect state."""
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
        read_before_write = device.begin_rgbic_catalog_read()
        assert read_before_write is not None
        catalog_revision, captured_color_revision, captured_effect_revision = read_before_write

        with patch.object(device._dreo, "set_rgbic_effect", return_value=False), patch.object(
            device._outbox, "flush_now", return_value=True
        ):
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is False

        assert device.rgbic_color == (0, 255, 0)
        assert device.rgbic_effect_name == "Constante"
        assert device._rgbic_color_write_revision == captured_color_revision + 1
        assert device._rgbic_effect_write_revision == captured_effect_revision + 1
        device.set_rgbic_effect_catalog(
            catalog,
            expected_rgbic_color_write_revision=captured_color_revision,
            expected_rgbic_effect_write_revision=captured_effect_revision,
            expected_catalog_revision=catalog_revision,
        )
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
        read = device.begin_rgbic_catalog_read()
        assert read is not None
        catalog_revision, color_revision, effect_revision = read

        def load_catalog_during_write(_device):
            assert device.set_rgbic_effect("Ola") is True
            return catalog

        with patch.object(device._dreo, "get_rgbic_effect_catalog", side_effect=load_catalog_during_write), patch.object(
            device._dreo, "set_rgbic_scene_effect", return_value=True
        ), patch.object(device._outbox, "flush_now", return_value=True):
            stale_catalog = device._dreo.get_rgbic_effect_catalog(device)

        applied = device.set_rgbic_effect_catalog(
            stale_catalog,
            expected_rgbic_color_write_revision=color_revision,
            expected_rgbic_effect_write_revision=effect_revision,
            expected_catalog_revision=catalog_revision,
        )
        assert applied is True
        assert device.rgbic_effect_name == "Ola"
        assert device.rgbic_scene_effect_names == ["Ola"]

    def test_HAP010S_post_write_revision_blocks_pre_write_catalog_snapshot(self):  # pylint: disable=invalid-name
        """Catalog snapshots taken after pre-write but before commit must not apply color."""
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
        catalog_revision, pre_write_color_revision, _ = pre_write_snapshot
        assert device._rgbic_color_write_revision == pre_write_color_revision + 1
        device.set_rgbic_effect_catalog(
            catalog,
            expected_rgbic_color_write_revision=pre_write_color_revision,
            expected_catalog_revision=catalog_revision,
        )
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
        stale_color_revision = device._rgbic_color_write_revision
        stale_effect_revision = device._rgbic_effect_write_revision

        with patch.object(device._dreo, "set_rgbic_scene_effect", return_value=True), patch.object(
            device._outbox, "flush_now", return_value=True
        ):
            assert device.set_rgbic_effect("Ola") is True

        device.set_rgbic_effect_catalog(
            catalog,
            expected_rgbic_color_write_revision=stale_color_revision,
            expected_rgbic_effect_write_revision=stale_effect_revision,
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
        (
            "source",
            "constant_id",
            "reported_id",
            "live_id",
            "reported_mode",
            "live_mode",
            "catalog_color",
            "expected_revision",
            "current_revision",
            "initial_color",
            "catalog_received",
            "expected_color",
            "expect_revision_bump",
        ),
        [
            (
                "catalog",
                "constant-id",
                "constant-id",
                "constant-id",
                2,
                2,
                (0, 102, 255),
                None,
                0,
                None,
                True,
                (0, 102, 255),
                False,
            ),
            (
                "catalog",
                "constant-id",
                "scene-id",
                "scene-id",
                2,
                2,
                (0, 102, 255),
                None,
                0,
                (1, 2, 3),
                True,
                None,
                False,
            ),
            (
                "catalog",
                "constant-id",
                "constant-id",
                "constant-id",
                1,
                1,
                (0, 102, 255),
                None,
                0,
                (1, 2, 3),
                True,
                None,
                False,
            ),
            (
                "catalog",
                "constant-id",
                "constant-id",
                "constant-id",
                2,
                2,
                (0, 102, 255),
                0,
                2,
                (9, 9, 9),
                True,
                (9, 9, 9),
                False,
            ),
            (
                "catalog",
                "constant-id",
                "constant-id",
                "constant-id",
                2,
                2,
                None,
                None,
                0,
                (0, 102, 255),
                True,
                None,
                False,
            ),
            (
                "refresh",
                "constant-id",
                "constant-id",
                "constant-id",
                2,
                2,
                (255, 2, 10),
                1,
                1,
                (0, 0, 0),
                True,
                (255, 2, 10),
                False,
            ),
            (
                "refresh",
                "constant-id",
                "constant-id",
                "scene-id",
                2,
                2,
                (255, 2, 10),
                1,
                1,
                (0, 102, 255),
                True,
                None,
                True,
            ),
            (
                "refresh",
                "constant-id",
                "scene-id",
                "constant-id",
                2,
                2,
                (255, 2, 10),
                1,
                1,
                (0, 102, 255),
                True,
                None,
                True,
            ),
            (
                "refresh",
                "constant-id",
                "constant-id",
                "constant-id",
                1,
                2,
                (255, 2, 10),
                1,
                1,
                (0, 102, 255),
                True,
                None,
                True,
            ),
            (
                "refresh",
                "constant-id",
                "constant-id",
                "constant-id",
                2,
                2,
                (255, 2, 10),
                0,
                2,
                (0, 102, 255),
                True,
                (0, 102, 255),
                False,
            ),
            (
                "refresh",
                "constant-id",
                "constant-id",
                "constant-id",
                2,
                2,
                None,
                1,
                1,
                (0, 102, 255),
                True,
                None,
                True,
            ),
            (
                "refresh",
                "constant-id",
                "constant-id",
                "constant-id",
                2,
                2,
                (255, 2, 10),
                1,
                1,
                (0, 102, 255),
                False,
                None,
                True,
            ),
        ],
    )
    def test_HAP010S_apply_rgbic_catalog_color_locked_live_and_snapshot(
        self,
        source,
        constant_id,
        reported_id,
        live_id,
        reported_mode,
        live_mode,
        catalog_color,
        expected_revision,
        current_revision,
        initial_color,
        catalog_received,
        expected_color,
        expect_revision_bump,
    ):  # pylint: disable=invalid-name
        """The catalog color helper honors live and snapshot fields consistently."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device._rgbeffectid = live_id
        device._rgbmode = live_mode
        device._rgbic_color = initial_color
        device._rgbic_color_write_revision = current_revision

        with device._lock:
            if source == "catalog":
                device._apply_rgbic_catalog_color_catalog_locked(
                    color=catalog_color,
                    constant_effect_id=constant_id,
                    expected_rgbic_color_write_revision=expected_revision,
                )
            else:
                device._apply_rgbic_catalog_color_refresh_locked(
                    color=catalog_color,
                    constant_effect_id=constant_id,
                    reported_effect_id=reported_id,
                    reported_rgb_mode=reported_mode,
                    write_revision=expected_revision if expected_revision is not None else 0,
                    catalog_received=catalog_received,
                )

        assert device.rgbic_color == expected_color
        if expect_revision_bump:
            assert device._rgbic_color_write_revision == current_revision + 1
        else:
            assert device._rgbic_color_write_revision == current_revision

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

    def test_HAP010S_failed_catalog_refresh_clears_unconfirmed_color_but_keeps_effects(self):  # pylint: disable=invalid-name
        """A failed GET clears stale RGB without discarding the last effect catalog."""
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
        device.update_state({
            "rgbeffectid": {"state": "constant-id"},
            "rgbmode": {"state": 2},
        })
        device.set_rgbic_effect_catalog(catalog)
        scheduled = []
        device._dreo.set_schedule_call_later(
            lambda _delay, callback: scheduled.append(callback) or (lambda: None)
        )
        device.handle_server_update_base({REPORTED_KEY: {"rgbeffectid": "constant-id"}})
        assert device.rgbic_color == (0, 102, 255)

        with patch.object(device._dreo, "get_rgbic_effect_catalog", return_value=None):
            scheduled[0]()

        assert device.rgbic_color is None
        assert device.rgbic_effect_names == ["Constante"]

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
        stale_read_revision = device._rgbic_color_write_revision

        with patch.object(device._dreo, "set_rgbic_effect", return_value=True):
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is True

        device.set_rgbic_effect_catalog(
            catalog,
            expected_rgbic_color_write_revision=stale_read_revision,
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
        assert device._rgbic_effect_pending is False

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
