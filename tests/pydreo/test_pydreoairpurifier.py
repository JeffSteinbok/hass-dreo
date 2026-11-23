"""Tests for Dreo Fans"""

# pylint: disable=used-before-assignment
import logging
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
        assert device.rgbic_effect_name == "Respirar"

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
        assert device.rgbmode == 2
        assert device.rgbeffectid == "1702000000000000001"

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

    def test_HAP010S_websocket_effect_report_refreshes_catalog_selection(self):  # pylint: disable=invalid-name
        """A changed manual effect report refreshes the selected catalog name off-thread."""
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "old-id"}})
        scheduled = self.install_manual_scheduler()
        selected_catalog = {
            "basicEffects": [{
                "id": "catalog-id",
                "referencedId": "referenced-id",
                "effectType": 0,
                "name": "Wave from current catalog",
                "selected": True,
            }],
        }
        with patch.object(self.pydreo_manager, "get_rgbic_effect_catalog", return_value=selected_catalog) as get_catalog:
            device.handle_server_update({REPORTED_KEY: {"rgbmode": 2, "rgbeffectid": "new-id"}})
            assert len(scheduled) == 1
            self.fire_last_scheduled(scheduled)

        get_catalog.assert_called_once_with(device)
        assert device.rgbeffectid == "new-id"
        assert device.rgbic_effect_name == "Wave from current catalog"

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
