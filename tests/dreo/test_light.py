"""Tests for the Dreo Light entity."""

import asyncio
import math
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.dreo import light
from custom_components.dreo.const import DOMAIN, PYDREO_MANAGER
from custom_components.dreo.light import DreoLightHA, DreoRGBLightHA, DreoRGBICLightHA, DreoHumidifierLightHA
from custom_components.dreo.light import Dreo530SRGBICLightHA, DreoAirPurifierAmbientLightHA
from custom_components.dreo.haimports import (
    ColorMode,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
    ATTR_EFFECT,
)

from .integrationtests.integrationtestbase import IntegrationTestBase, PATCH_SEND_COMMAND
from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"


class TestDreoLightHA(TestDeviceBase, IntegrationTestBase):
    """Test the Dreo Light entity."""

    def test_light_get_entries_filters_correctly(self):
        """Test that get_entries creates lights only for devices with light features."""
        # Device with light
        device_with_light = self.create_mock_device(
            name="Ceiling Fan", serial_number="CF001", features={"light_on": True, "brightness": 50, "color_temperature": 25}
        )
        # Device without light
        device_no_light = self.create_mock_device(name="Tower Fan", serial_number="TF001", features={"is_on": True, "fan_speed": 3})

        entities = light.get_entries([device_with_light, device_no_light])
        assert len(entities) == 1
        assert isinstance(entities[0], DreoLightHA)

    def test_light_get_entries_rgb_light(self):
        """Test that get_entries creates RGB light entities for devices with atm_light."""
        device = self.create_mock_device(
            name="Ceiling Fan RGB",
            serial_number="CF002",
            features={
                "light_on": True,
                "brightness": 50,
                "atm_light": True,
                "atm_light_on": True,
                "atm_brightness": 3,
                "atm_color_rgb": (255, 0, 0),
            },
        )

        entities = light.get_entries([device])
        assert len(entities) == 2
        # One standard light and one RGB light
        types = [type(e).__name__ for e in entities]
        assert "DreoLightHA" in types
        assert "DreoRGBLightHA" in types

    def test_light_get_entries_rgbic_effect_light(self):
        """Test that get_entries creates RGBIC light entities for devices with rgb_effect_id."""
        device = self.create_mock_device(
            name="Ceiling Fan RGBIC",
            serial_number="CF007",
            features={
                "light_on": True,
                "brightness": 50,
                "atm_light": True,
                "atm_light_on": True,
                "atm_brightness": 50,
                "rgb_effect_id": "2070476690030592000",
                "rgb_preset_sel": 0,
                "rgb_preset_num": 4,
            },
        )
        device.atm_brightness_range = (1, 100)
        device.rgb_effect_range = (0, 7)

        entities = light.get_entries([device])
        assert len(entities) == 2
        types = [type(e).__name__ for e in entities]
        assert "DreoLightHA" in types
        assert "DreoRGBICLightHA" in types

    def test_light_get_entries_empty(self):
        """Test get_entries returns empty for devices without lights."""
        device = self.create_mock_device(name="Heater", serial_number="HTR001", features={"poweron": True})

        entities = light.get_entries([device])
        assert len(entities) == 0

    def test_light_entity_basic_properties(self):
        """Test basic light entity properties."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Ceiling Fan", serial_number="CF001", features={"light_on": True, "brightness": 75, "color_temperature": 50}
            )

            light_entity = DreoLightHA(device)
            # Name is derived from translation_key + has_entity_name (resolved by the
            # entity platform at runtime), not a hardcoded _attr_name.
            assert light_entity.translation_key == "light"
            assert not hasattr(light_entity, "_attr_name")
            assert light_entity.unique_id == "CF001-light"

    def test_light_is_on(self):
        """Test is_on property."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Ceiling Fan", serial_number="CF001", features={"light_on": True})

            light_entity = DreoLightHA(device)
            assert light_entity.is_on is True

            device.light_on = False
            assert light_entity.is_on is False

    def test_light_turn_on_off(self):
        """Test turn_on and turn_off methods."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Ceiling Fan", serial_number="CF001", features={"light_on": False})

            light_entity = DreoLightHA(device)
            assert light_entity.is_on is False

            light_entity.turn_on()
            assert device.light_on is True

            light_entity.turn_off()
            assert device.light_on is False

    def test_light_color_mode_onoff(self):
        """Test light with only on/off capability."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Display Light", serial_number="DL001", features={"light_on": True})

            light_entity = DreoLightHA(device)
            assert light_entity.color_mode == ColorMode.ONOFF
            assert light_entity.supported_color_modes == {ColorMode.ONOFF}

    def test_light_color_mode_brightness(self):
        """Test light with brightness capability."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Dimmable Light", serial_number="DIM001", features={"light_on": True, "brightness": 50})

            light_entity = DreoLightHA(device)
            assert light_entity.color_mode == ColorMode.BRIGHTNESS
            assert light_entity.supported_color_modes == {ColorMode.BRIGHTNESS}

    def test_light_color_mode_color_temp(self):
        """Test light with color temperature capability."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="CT Light", serial_number="CT001", features={"light_on": True, "brightness": 50, "color_temperature": 50}
            )

            light_entity = DreoLightHA(device)
            assert light_entity.color_mode == ColorMode.COLOR_TEMP
            assert light_entity.supported_color_modes == {ColorMode.COLOR_TEMP}

    def test_light_brightness_conversion(self):
        """Test brightness conversion between device scale and HA scale."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Ceiling Fan", serial_number="CF001", features={"light_on": True, "brightness": 50, "color_temperature": 25}
            )

            light_entity = DreoLightHA(device)
            # Device brightness 50 out of (1, 100) should map to HA's 0-255 scale
            brightness = light_entity.brightness
            assert brightness is not None
            assert 0 < brightness <= 255

    def test_light_brightness_none_when_unsupported(self):
        """Test brightness returns None when not supported."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Simple Light", serial_number="SL001", features={"light_on": True})

            light_entity = DreoLightHA(device)
            assert light_entity.brightness is None

    def test_light_color_temp_kelvin(self):
        """Test color temperature in Kelvin."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="CT Light", serial_number="CT001", features={"light_on": True, "brightness": 50, "color_temperature": 50}
            )

            light_entity = DreoLightHA(device)
            ct = light_entity.color_temp_kelvin
            assert ct is not None
            # 50% should be roughly midway between 2700K and 6500K
            assert 2700 <= ct <= 6500

    def test_light_color_temp_none_when_unsupported(self):
        """Test color temp returns None when not supported."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(name="Bright Only", serial_number="BO001", features={"light_on": True, "brightness": 50})

            light_entity = DreoLightHA(device)
            assert light_entity.color_temp_kelvin is None

    def test_light_turn_on_with_brightness(self):
        """Test turning on light with brightness kwarg."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Ceiling Fan", serial_number="CF001", features={"light_on": False, "brightness": 50, "color_temperature": 25}
            )

            light_entity = DreoLightHA(device)
            # Turn on with brightness (HA uses 0-255 scale)
            light_entity.turn_on(**{ATTR_BRIGHTNESS: 128})
            assert device.light_on is True
            # Brightness should be set on the device (device scale 1-100)
            assert device.brightness is not None

    def test_light_turn_on_with_color_temp(self):
        """Test turning on light with color temperature kwarg."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Ceiling Fan", serial_number="CF001", features={"light_on": False, "brightness": 50, "color_temperature": 25}
            )

            light_entity = DreoLightHA(device)
            light_entity.turn_on(**{ATTR_COLOR_TEMP_KELVIN: 4600})
            assert device.light_on is True
            assert device.color_temperature is not None

    def test_light_turn_on_color_temp_clamped_below_min(self):
        """Color temperature below min_color_temp_kelvin must be clamped, not sent as negative."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Ceiling Fan", serial_number="CF001", features={"light_on": False, "brightness": 50, "color_temperature": 25}
            )

            light_entity = DreoLightHA(device)
            # 1000 K is well below the 2700 K minimum
            light_entity.turn_on(**{ATTR_COLOR_TEMP_KELVIN: 1000})
            assert device.light_on is True
            # color_temperature must be >= 0 (a negative value would be out-of-range)
            assert device.color_temperature >= 0

    def test_light_turn_on_color_temp_clamped_above_max(self):
        """Color temperature above max_color_temp_kelvin must be clamped to 100."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Ceiling Fan", serial_number="CF001", features={"light_on": False, "brightness": 50, "color_temperature": 50}
            )

            light_entity = DreoLightHA(device)
            # 9000 K is above the 6500 K maximum
            light_entity.turn_on(**{ATTR_COLOR_TEMP_KELVIN: 9000})
            assert device.light_on is True
            assert device.color_temperature <= 100


class TestDreoRGBLightHA(TestDeviceBase):
    """Test the Dreo RGB Light entity."""

    def test_rgb_light_properties(self):
        """Test RGB light basic properties."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Ceiling Fan",
                serial_number="CF001",
                features={
                    "atm_light": True,
                    "atm_light_on": True,
                    "atm_brightness": 3,
                    "atm_color_rgb": (255, 100, 0),
                },
            )

            rgb_light = DreoRGBLightHA(device)
            assert rgb_light.translation_key == "rgb_light"
            assert not hasattr(rgb_light, "_attr_name")
            assert rgb_light.unique_id == "CF001-rgb-light"
            assert rgb_light.color_mode == ColorMode.RGB
            assert rgb_light.supported_color_modes == {ColorMode.RGB}

    def test_rgb_light_color(self):
        """Test RGB color property."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Ceiling Fan",
                serial_number="CF001",
                features={
                    "atm_light": True,
                    "atm_light_on": True,
                    "atm_brightness": 3,
                    "atm_color_rgb": (255, 100, 0),
                },
            )

            rgb_light = DreoRGBLightHA(device)
            assert rgb_light.rgb_color == (255, 100, 0)

    def test_rgb_light_turn_on_with_color(self):
        """Test turning on RGB light with color."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Ceiling Fan",
                serial_number="CF001",
                features={
                    "atm_light": True,
                    "atm_light_on": False,
                    "atm_brightness": 3,
                    "atm_color_rgb": (0, 0, 0),
                },
            )

            rgb_light = DreoRGBLightHA(device)
            rgb_light.turn_on(**{ATTR_RGB_COLOR: (0, 255, 0)})
            assert device.atm_light_on is True
            assert device.atm_color_rgb == (0, 255, 0)

    def test_rgb_light_turn_on_with_brightness(self):
        """Test turning on RGB light with brightness."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Ceiling Fan",
                serial_number="CF001",
                features={
                    "atm_light": True,
                    "atm_light_on": False,
                    "atm_brightness": 1,
                    "atm_color_rgb": (255, 0, 0),
                },
            )

            rgb_light = DreoRGBLightHA(device)
            rgb_light.turn_on(**{ATTR_BRIGHTNESS: 200})
            assert device.atm_light_on is True

    def test_rgb_light_is_on_off(self):
        """Test RGB light on/off state."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Ceiling Fan",
                serial_number="CF001",
                features={
                    "atm_light": True,
                    "atm_light_on": True,
                    "atm_brightness": 3,
                },
            )

            rgb_light = DreoRGBLightHA(device)
            assert rgb_light.is_on is True

            rgb_light.turn_off()
            assert device.atm_light_on is False


class TestDreoAirPurifierAmbientLightHA(IntegrationTestBase):
    """Exercise the purifier ambient light with REST state and WebSocket reports."""

    @pytest.mark.parametrize("model", ["HAP007S", "HAP008S", "HAP009S", "HAP010S"])
    def test_entity_uses_model_capability(self, model):
        self.get_devices_file_name = f"get_devices_{model}.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({"reported": {"rgbalwayson": True, "rgblevel": 2}})
        entities = light.get_entries([device])
        if model == "HAP008S":
            (entity,) = entities
            assert isinstance(entity, DreoAirPurifierAmbientLightHA)
            assert entity.translation_key == "ambient_light"
            assert entity.supported_color_modes == {ColorMode.BRIGHTNESS}
        else:
            assert all(not isinstance(entity, DreoAirPurifierAmbientLightHA) for entity in entities)

    def test_power_and_brightness_commands_skip_unchanged_values(self):
        self.get_devices_file_name = "get_devices_HAP008S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        (entity,) = light.get_entries([device])
        assert entity.is_on is True
        assert entity.brightness == 170

        def report_command(target, params):
            target.handle_server_update({"reported": params})

        with patch(PATCH_SEND_COMMAND, side_effect=report_command) as send:
            entity.turn_on(brightness=170)
            send.assert_not_called()
            entity.turn_off()
            send.assert_called_once_with(device, {"rgbalwayson": False})
            assert entity.brightness == 170
            send.reset_mock()
            entity.turn_off()
            send.assert_not_called()
            entity.turn_on()
            send.assert_called_once_with(device, {"rgbalwayson": True})

        with patch(PATCH_SEND_COMMAND, side_effect=report_command) as send:
            entity.turn_off()
            send.reset_mock()
            entity.turn_on(brightness=85)
            send.assert_called_once_with(device, {"rgbalwayson": True, "rgblevel": 1})
            send.reset_mock()
            entity.turn_on(brightness=255)
            send.assert_called_once_with(device, {"rgblevel": 3})
            send.reset_mock()
            entity.turn_on(brightness=170)
            send.assert_called_once_with(device, {"rgblevel": 2})

    @pytest.mark.parametrize("brightness, level", [(1, 1), (42, 1), (43, 1), (254, 3), (255, 3)])
    def test_turn_on_at_brightness_boundaries(self, brightness, level):
        self.get_devices_file_name = "get_devices_HAP008S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        device.handle_server_update({"reported": {"rgbalwayson": False}})
        (entity,) = light.get_entries([device])

        with patch(PATCH_SEND_COMMAND) as send:
            entity.turn_on(brightness=brightness)
            send.assert_called_once_with(device, {"rgbalwayson": True, "rgblevel": level})

    def test_missing_report_does_not_suppress_retry(self):
        self.get_devices_file_name = "get_devices_HAP008S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        (entity,) = light.get_entries([device])

        with patch(PATCH_SEND_COMMAND) as send:
            entity.turn_off()
            entity.turn_off()
            assert send.call_count == 2
            send.assert_called_with(device, {"rgbalwayson": False})
        assert entity.is_on is True

    def test_websocket_reports_match_app_sequence(self):
        self.get_devices_file_name = "get_devices_HAP008S.json"
        self.pydreo_manager.load_devices()
        device = self.pydreo_manager.devices[0]
        (entity,) = light.get_entries([device])
        for report, on, brightness in (
            ({"rgbalwayson": False}, False, 170),
            ({"rgbalwayson": True, "rgblevel": 1}, True, 85),
            ({"rgblevel": 2}, True, 170),
            ({"rgblevel": 3}, True, 255),
            ({"rgbalwayson": False}, False, 255),
        ):
            self.pydreo_manager._transport_consume_message(
                {"method": "control-report", "devicesn": device.serial_number, "reported": report}
            )
            assert entity.is_on is on
            assert entity.brightness == brightness


class TestDreo530SRGBICLightHA(TestDeviceBase, IntegrationTestBase):
    """Tests for the catalog-backed, mode-based purifier RGBIC light."""

    def _make_530s(self):
        self.get_devices_file_name = "get_devices_HAP010S.json"
        self.pydreo_manager.load_devices()
        return self.pydreo_manager.devices[0]

    @staticmethod
    def _hass_stub(manager):
        """Minimal hass with the integration manager, matching production setup."""
        return type("Hass", (), {
            "async_add_executor_job": AsyncMock(side_effect=lambda fn, *args: fn(*args)),
            "data": {DOMAIN: {PYDREO_MANAGER: manager}},
        })()

    def test_get_entries_exposes_only_rgbic_light_and_brightness_range(self):
        device = self._make_530s()
        device.handle_server_update({"reported": {"rgbon": False, "rgbbri": 50}})
        entities = light.get_entries([device])
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, Dreo530SRGBICLightHA)
        assert entity.supported_color_modes == {ColorMode.RGB}
        assert entity.is_on is False
        assert entity._brightness_scale == (1, 100)
        with patch(PATCH_UPDATE_HA_STATE), patch(PATCH_SEND_COMMAND):
            entity.turn_on(brightness=255)
        device.handle_server_update({"reported": {"rgbon": True, "rgbbri": 100}})
        assert device.rgbbri == 100
        assert device.rgbon is True
        with patch(PATCH_UPDATE_HA_STATE), patch(PATCH_SEND_COMMAND):
            entity.turn_on(brightness=0)
        device.handle_server_update({"reported": {"rgbbri": 1}})
        assert device.rgbbri == 1

    def test_rgb_color_uses_existing_530s_entity_and_catalog_constant_entry(self):
        device = self._make_530s()
        device.handle_server_update({"reported": {
            "rgbon": True,
            "rgbbri": 50,
            "rgbmode": 2,
            "rgbeffectid": "constant-id",
        }})
        device.set_rgbic_effect_catalog({
            "basicEffects": [{
                "id": "constant-id",
                "referencedId": "constant-ref",
                "effectType": 0,
                "name": "Luz constante",
                "layouts": [{
                    "viewType": "SEGMENT_COLOR_LIST",
                    "currentSelected": "whole",
                    "wholeColorList": ["#ffffff"],
                    "colorList": ["#abcdef"] * 17,
                }],
            }, {
                "id": "breath-id",
                "referencedId": "breath-ref",
                "effectType": 0,
                "name": "Respirar",
                "layouts": [],
            }],
            "sceneEffects": [{
                "id": "scene-id",
                "referencedId": "scene-ref",
                "effectType": 3,
                "name": "Wave",
                "layouts": [],
            }],
        })
        entities = light.get_entries([device])
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, Dreo530SRGBICLightHA)
        assert entity.rgb_color == (255, 255, 255)

        with patch(PATCH_UPDATE_HA_STATE), patch.object(
            device._dreo, "set_rgbic_effect", return_value=True
        ) as set_effect:
            entity.turn_on(**{ATTR_RGB_COLOR: (255, 0, 0)})
            entity.turn_on(**{ATTR_EFFECT: "Respirar"})

        assert set_effect.call_args_list[0].args == (device, "Luz constante", "#ff0000")
        assert set_effect.call_args_list[1].args == (device, "Respirar")
        assert entity.rgb_color is None
        assert entity.effect == "Respirar"
        assert "Wave" in entity.effect_list

    def test_effect_controls_use_catalog_basics_scenes_and_auto_mode(self):
        device = self._make_530s()
        device.handle_server_update({"reported": {"rgbon": True, "rgbbri": 50, "rgbmode": 2}})
        device.set_rgbic_effect_catalog({
            "basicEffects": [
                {"id": "basic-id", "referencedId": "basic-ref", "effectType": 0, "name": "Respirar"},
                {"id": "incomplete", "effectType": 0, "name": "Incomplete"},
            ],
            "remoteEffects": [{"id": "remote-id", "name": "Remoto"}],
            "sceneEffects": [{"id": "scene-id", "referencedId": "scene-ref", "effectType": 3,
                              "name": "Wave", "sortOrder": 13}],
        })
        entity = light.get_entries([device])[0]
        assert isinstance(entity, Dreo530SRGBICLightHA)
        assert entity.effect_list == ["Respirar", "Wave", Dreo530SRGBICLightHA.INDICATOR_EFFECT]

        with patch(PATCH_UPDATE_HA_STATE), patch(PATCH_SEND_COMMAND) as send:
            entity.turn_on(effect=Dreo530SRGBICLightHA.INDICATOR_EFFECT)
            send.assert_called_once_with(device, {"rgbmode": 1})
        assert entity.effect == Dreo530SRGBICLightHA.INDICATOR_EFFECT
        device.handle_server_update({"reported": {"rgbmode": 1, "rgbeffectid": "1701000000000000011"}})
        assert entity.effect == Dreo530SRGBICLightHA.INDICATOR_EFFECT
        device.handle_server_update({"reported": {"rgbmode": 2}})

        def _apply_manual_effect(name: str) -> bool:
            device._rgbic_effect_name = name
            return True

        for effect_name in ("Respirar", "Wave"):
            with patch(PATCH_UPDATE_HA_STATE), patch.object(
                device, "set_rgbic_effect", side_effect=_apply_manual_effect
            ) as set_effect:
                entity.turn_on(effect=effect_name)
                set_effect.assert_called_once_with(effect_name)
            assert entity.effect == effect_name

        # REST success must retain the requested name even when the follow-up
        # catalog response omits selected=true for every entry.
        unselected_catalog = {
            "basicEffects": [{"id": "basic-id", "referencedId": "basic-ref", "effectType": 0,
                              "name": "Respirar", "selected": False}],
            "sceneEffects": [{"id": "scene-id", "referencedId": "scene-ref", "effectType": 3,
                              "name": "Wave", "selected": False}],
        }
        with patch.object(device._dreo, "set_rgbic_effect", return_value=True), patch.object(
            device._dreo, "set_rgbic_scene_effect", return_value=True
        ), patch.object(device._dreo, "get_rgbic_effect_catalog", return_value=unselected_catalog):
            for effect_name in ("Respirar", "Wave"):
                assert device.set_rgbic_effect(effect_name) is True
                assert entity.effect == effect_name

    def test_websocket_effect_change_refreshes_entity_selection_from_catalog(self):
        device = self._make_530s()
        device.handle_server_update({"reported": {"rgbon": True, "rgbbri": 50, "rgbmode": 2}})
        entity = light.get_entries([device])[0]
        device.set_rgbic_effect_catalog({
            "basicEffects": [{"id": "basic", "referencedId": "basic-ref", "effectType": 0, "name": "Respirar"}],
            "sceneEffects": [{"id": "scene-id", "referencedId": "scene-ref", "effectType": 3,
                              "name": "Wave", "sortOrder": 1}],
        })
        callback_updates = []
        device.add_attr_callback(lambda: callback_updates.append(entity.effect))
        # A loaded catalog resolves the report synchronously by its entry `id`.
        device.handle_server_update_base({"reported": {"rgbeffectid": "scene-id"}})

        assert device.rgbic_effect_name == "Wave"
        assert entity.effect == "Wave"
        assert callback_updates[-1] == "Wave"

    def test_530s_startup_effect_uses_websocket_id_not_stale_rest_snapshot(self):
        """REST seeds the startup name; WebSocket then confirms or replaces it."""
        constant_id = "2124876509150707712"
        circle_id = "2124876509150707714"
        ola_id = "1702000000000000001"
        catalog = {
            "basicEffects": [
                {
                    "id": constant_id,
                    "referencedId": "1700000000000000001",
                    "effectType": 0,
                    "name": "Constante",
                    "layouts": [{
                        "viewType": "SEGMENT_COLOR_LIST",
                        "currentSelected": "whole",
                        "wholeColorList": ["#0066ff"],
                    }],
                },
                {
                    "id": circle_id,
                    "referencedId": "1700000000000000003",
                    "effectType": 0,
                    "name": "Círculo",
                    "layouts": [],
                },
            ],
            "sceneEffects": [{
                "id": ola_id,
                "referencedId": ola_id,
                "effectType": 3,
                "name": "Ola",
            }],
        }
        known_effects = {
            constant_id: "Constante",
            circle_id: "Círculo",
            ola_id: "Ola",
        }
        startup_orders = ("rest_catalog_ws", "rest_ws_catalog", "catalog_rest_ws")

        for rest_id, rest_name in known_effects.items():
            for startup_order in startup_orders:
                # Exercise both a matching WebSocket report and one that
                # corrects a stale REST selection.
                websocket_ids = (rest_id, next(key for key in known_effects if key != rest_id))
                for reported_id in websocket_ids:
                    expected_name = known_effects[reported_id]
                    for previous_device in self.pydreo_manager.devices:
                        previous_device.dispose()
                    self.pydreo_manager.devices.clear()
                    self.pydreo_manager._device_list_by_sn.clear()
                    device = self._make_530s()
                    entity = light.get_entries([device])[0]
                    rest_state = {
                        "rgbmode": {"state": 2},
                        "rgbeffectid": {"state": rest_id},
                    }
                    if startup_order == "catalog_rest_ws":
                        device.set_rgbic_effect_catalog(catalog)
                    device.update_state(rest_state)

                    if startup_order == "rest_ws_catalog":
                        device.handle_server_update({"reported": {"rgbeffectid": reported_id}})
                        assert entity.effect is None  # no names until the catalog arrives
                        device.set_rgbic_effect_catalog(catalog)
                    else:
                        if startup_order == "rest_catalog_ws":
                            device.set_rgbic_effect_catalog(catalog)
                        # Before WS, the catalog may resolve REST provisionally.
                        assert entity.effect == rest_name
                        device.handle_server_update({"reported": {"rgbeffectid": reported_id}})

                    assert device.rgbeffectid == reported_id
                    assert entity.effect == expected_name

                    # REST arriving after the live report cannot revert either
                    # the identifier or the displayed effect name.
                    device.update_state(rest_state)
                    assert device.rgbeffectid == reported_id
                    assert entity.effect == expected_name

    def test_entity_registers_before_rgbic_state_and_updates_when_report_arrives(self):
        """Static model support is enough to register; reports then fill live attributes."""
        device = self._make_530s()
        entity = light.get_entries([device])[0]
        assert isinstance(entity, Dreo530SRGBICLightHA)
        assert device.rgbon is None
        assert device.rgbbri is None
        assert entity.is_on is None
        assert entity.brightness is None

        with patch(PATCH_SEND_COMMAND) as send_command, patch.object(
            device._dreo, "set_rgbic_effect"
        ) as set_effect:
            entity.turn_on(brightness=255)
            entity.turn_on(effect=Dreo530SRGBICLightHA.INDICATOR_EFFECT)
            entity.turn_on(**{ATTR_RGB_COLOR: (0, 255, 0)})
            entity.turn_off()
        send_command.assert_not_called()
        set_effect.assert_not_called()

        # Register the ordinary entity callback, then deliver the first state
        # report as the WebSocket thread would after platform setup.
        manager = device._dreo
        entity.hass = self._hass_stub(manager)
        with patch.object(manager, "get_rgbic_effect_catalog", return_value=None), patch.object(
            entity, "async_write_ha_state"
        ), patch(PATCH_UPDATE_HA_STATE) as schedule_update:
            asyncio.run(entity.async_added_to_hass())
            device.handle_server_update_base({
                "reported": {"rgbon": True, "rgbbri": 100, "rgbmode": 2}
            })
        assert entity.is_on is True
        assert entity.brightness == 255
        schedule_update.assert_called_with(True)

        with patch(PATCH_SEND_COMMAND) as send_command:
            entity.turn_on(effect=Dreo530SRGBICLightHA.INDICATOR_EFFECT)
            send_command.assert_called_once_with(device, {"rgbmode": 1})

    def test_initial_catalog_load_recovers_color_for_reported_constant_effect(self):
        """The initial catalog read recovers color when REST reports the Constant ID."""
        device = self._make_530s()
        device.update_state({
            "rgbmode": {"state": 2},
            "rgbeffectid": {"state": "constant-id"},
        })
        entity = light.get_entries([device])[0]
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
        entity.hass = self._hass_stub(device._dreo)

        with patch.object(device._dreo, "get_rgbic_effect_catalog", return_value=catalog), patch.object(
            entity, "async_write_ha_state"
        ) as write_state:
            asyncio.run(entity.async_added_to_hass())

        assert device.rgbeffectid == "constant-id"
        assert device.rgbmode == 2
        assert entity.rgb_color == (0, 102, 255)
        write_state.assert_called_once()

    def test_stale_initial_catalog_cannot_replace_newer_websocket_catalog(self):
        """A WebSocket refresh applied during startup wins over the pending initial read."""
        async def run_race():
            device = self._make_530s()
            manager = device._dreo
            entity = light.get_entries([device])[0]
            entity.hass = self._hass_stub(manager)
            initial_started = asyncio.Event()
            initial_response = asyncio.get_running_loop().create_future()
            initial_jobs = []

            async def hold_initial_request(fn, *args):
                initial_jobs.append((fn, args))
                initial_started.set()
                return await initial_response

            entity.hass.async_add_executor_job = hold_initial_request
            scheduled = []
            manager.set_schedule_call_later(
                lambda _delay, callback: scheduled.append(callback) or (lambda: None)
            )

            def catalog_with(name, color):
                return {"basicEffects": [{
                    "id": "constant-id",
                    "referencedId": "constant-ref",
                    "effectType": 0,
                    "name": name,
                    "layouts": [{
                        "viewType": "SEGMENT_COLOR_LIST",
                        "currentSelected": "whole",
                        "wholeColorList": [color],
                    }],
                }]}

            old_catalog = catalog_with("Constante antigua", "#ff0000")
            new_catalog = catalog_with("Constante actual", "#0000ff")
            load_task = asyncio.create_task(entity.async_added_to_hass())
            try:
                await initial_started.wait()
                assert initial_jobs[0][0].__name__ == "get_rgbic_effect_catalog"
                assert initial_jobs[0][1] == (device,)
                device.handle_server_update_base({"reported": {
                    "rgbmode": 2,
                    "rgbeffectid": "constant-id",
                }})
                assert len(scheduled) == 1

                with patch.object(manager, "get_rgbic_effect_catalog", return_value=new_catalog) as get_catalog, patch.object(
                    entity, "async_write_ha_state"
                ), patch(PATCH_UPDATE_HA_STATE):
                    scheduled[0]()
                    assert device.rgbic_color == (0, 0, 255)
                    assert device.rgbic_effect_name == "Constante actual"
                    assert entity.effect == "Constante actual"
                    get_catalog.assert_called_once_with(device)

                    initial_response.set_result(old_catalog)
                    await load_task
            finally:
                if not load_task.done():
                    initial_response.cancel()
                    await asyncio.gather(load_task, return_exceptions=True)

            assert device.rgbic_color == (0, 0, 255)
            assert device.rgbic_effect_name == "Constante actual"
            assert entity.effect == "Constante actual"
            assert device._rgbic_catalog_refresh_running is False
            assert device._rgbic_catalog_refresh_cancel is None

        asyncio.run(run_race())

    def test_initial_catalog_load_cannot_overwrite_color_changed_during_request(self):
        """An initial response captured before a local color write is discarded for RGB."""
        device = self._make_530s()
        device.handle_server_update({"reported": {"rgbon": True, "rgbbri": 50, "rgbmode": 2}})
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
        entity = light.get_entries([device])[0]
        entity.hass = self._hass_stub(device._dreo)

        def stale_catalog(_device):
            assert device.set_rgbic_effect(color_rgb=(255, 0, 0)) is True
            return catalog

        with patch.object(device._dreo, "get_rgbic_effect_catalog", side_effect=stale_catalog), patch.object(
            device._dreo, "set_rgbic_effect", return_value=True
        ), patch.object(entity, "async_write_ha_state"):
            asyncio.run(entity.async_added_to_hass())

        assert entity.rgb_color == (255, 0, 0)

    def test_websocket_effect_report_notifies_entity_even_when_catalog_fails(self, caplog):
        device = self._make_530s()
        entity = light.get_entries([device])[0]
        scheduled = []

        def schedule_call_later(_delay, callback):
            scheduled.append(callback)
            return lambda: None

        device._dreo.set_schedule_call_later(schedule_call_later)
        notified = []
        device.add_attr_callback(lambda: notified.append((device.rgbeffectid, entity.effect)))
        device.handle_server_update_base({"reported": {"rgbeffectid": "1701000000000000011"}})
        assert notified == [("1701000000000000011", None)]
        with patch.object(device._dreo, "get_rgbic_effect_catalog", side_effect=RuntimeError("offline")):
            scheduled[0]()
        assert "RGBIC catalog refresh failed" in caplog.text
        assert notified[-1] == ("1701000000000000011", None)

    def test_unknown_effect_id_is_preserved_without_invented_effect_name(self):
        device = self._make_530s()
        entity = light.get_entries([device])[0]
        device.set_rgbic_effect_catalog({
            "basicEffects": [{"id": "catalog-id", "referencedId": "other-id", "effectType": 0,
                              "name": "Contraste", "selected": True}],
        })
        device.handle_server_update_base({"reported": {"rgbeffectid": "1701000000000000011"}})
        assert device.rgbeffectid == "1701000000000000011"
        assert entity.effect is None

    def test_unknown_device_report_invalidates_optimistic_ha_effect_immediately(self):
        device = self._make_530s()
        device.handle_server_update({"reported": {"rgbmode": 2}})
        device.set_rgbic_effect_catalog({
            "basicEffects": [{"id": "basic", "referencedId": "ref", "effectType": 0, "name": "Respirar"}],
        })
        entity = light.get_entries([device])[0]
        with patch.object(device._dreo, "set_rgbic_effect", return_value=True):
            assert device.set_rgbic_effect("Respirar") is True
            device.handle_server_update_base({"reported": {"rgbeffectid": "1701000000000000011"}})
            assert entity.effect is None
        assert entity.effect is None

    def test_unknown_device_report_is_unidentified_without_timing_heuristic(self):
        device = self._make_530s()
        device.handle_server_update({"reported": {"rgbmode": 2}})
        device.set_rgbic_effect_catalog({
            "basicEffects": [{"id": "basic", "referencedId": "ref", "effectType": 0, "name": "Respirar"}],
        })
        entity = light.get_entries([device])[0]
        scheduled = []
        device._dreo.set_schedule_call_later(lambda _delay, callback: scheduled.append(callback) or (lambda: None))
        with patch.object(device._dreo, "set_rgbic_effect", return_value=True):
            assert device.set_rgbic_effect("Respirar") is True
        # A loaded catalog without this `id` invalidates the optimistic name
        # synchronously; no fetch/timing heuristic can retain it.
        device.handle_server_update_base({"reported": {"rgbeffectid": "1701000000000000011"}})
        assert entity.effect is None

    def test_real_catalog_ids_resolve_scene_and_basic_entries(self):
        device = self._make_530s()
        entity = light.get_entries([device])[0]
        device.set_rgbic_effect_catalog({
            "basicEffects": [{
                "id": "2124876509150707714",
                "referencedId": "1700000000000000003",
                "effectType": 0,
                "name": "Círculo",
            }],
            "sceneEffects": [
                {"id": "1702000000000000004", "referencedId": "1702000000000000004",
                 "effectType": 3, "name": "Halloween"},
                {"id": "1702000000000000002", "referencedId": "1702000000000000002",
                 "effectType": 3, "name": "Flor de cerezo"},
            ],
            # Remote effects are deliberately excluded from this model's map.
            "remoteEffects": [{"id": "remote-id", "name": "Remote"}],
        })

        for effect_id, localized_name in (
            ("1702000000000000004", "Halloween"),
            ("1702000000000000002", "Flor de cerezo"),
            ("2124876509150707714", "Círculo"),
        ):
            device.handle_server_update_base({"reported": {"rgbeffectid": effect_id}})
            assert entity.effect == localized_name
        assert device._rgbic_effect_id_to_name["2124876509150707714"] == "Círculo"
        assert "1700000000000000003" not in device._rgbic_effect_id_to_name

    def test_ha_basic_effect_name_survives_correlated_catalog_id_report(self):
        device = self._make_530s()
        device.handle_server_update({"reported": {"rgbmode": 2}})
        entity = light.get_entries([device])[0]
        catalog = {"basicEffects": [{
            "id": "2124876509150707714",
            "referencedId": "1700000000000000003",
            "effectType": 0,
            "name": "Círculo",
            "selected": False,
        }]}
        device.set_rgbic_effect_catalog(catalog)
        with patch.object(device._dreo, "get_rgbic_effect_catalog", return_value=catalog), patch.object(
            device._dreo, "set_rgbic_effect", return_value=True
        ):
            assert device.set_rgbic_effect("Círculo") is True
            assert entity.effect == "Círculo"
            device.handle_server_update_base({"reported": {"rgbeffectid": "2124876509150707714"}})
        assert entity.effect == "Círculo"

    def test_indicator_selection_still_uses_rgbmode_one(self):
        device = self._make_530s()
        device.handle_server_update({"reported": {"rgbon": True, "rgbbri": 50, "rgbmode": 2}})
        entity = light.get_entries([device])[0]
        with patch(PATCH_UPDATE_HA_STATE), patch(PATCH_SEND_COMMAND) as send:
            entity.turn_on(effect=Dreo530SRGBICLightHA.INDICATOR_EFFECT)
            send.assert_called_once_with(device, {"rgbmode": 1})
        assert entity.effect == Dreo530SRGBICLightHA.INDICATOR_EFFECT

    def test_catalog_resolves_only_an_exact_reported_effect_id(self):
        device = self._make_530s()
        entity = light.get_entries([device])[0]
        device.set_rgbic_effect_catalog({
            "basicEffects": [{"id": "catalog-id", "referencedId": "other-ref", "effectType": 0,
                              "name": "Exact match", "selected": False}],
        })
        device.handle_server_update_base({"reported": {"rgbeffectid": "catalog-id"}})
        assert entity.effect == "Exact match"

    def test_async_added_loads_catalog_and_handles_none_or_failure(self):
        device = self._make_530s()
        device.handle_server_update({"reported": {"rgbon": True, "rgbbri": 50, "rgbmode": 2}})
        entity = light.get_entries([device])[0]
        catalog = {"basicEffects": [{"id": "one", "referencedId": "ref", "effectType": 0, "name": "Effect One"}]}
        manager = device._dreo
        with patch.object(manager, "get_rgbic_effect_catalog", return_value=catalog), patch.object(
            entity, "async_write_ha_state"
        ) as write_state:
            entity.hass = self._hass_stub(manager)
            asyncio.run(entity.async_added_to_hass())
        assert entity.effect_list == ["Effect One", Dreo530SRGBICLightHA.INDICATOR_EFFECT]
        write_state.assert_called_once()

        with patch.object(manager, "get_rgbic_effect_catalog", return_value=None), patch.object(
            entity, "async_write_ha_state"
        ), patch("custom_components.dreo.light.DreoLightHA.async_added_to_hass"):
            entity.hass = self._hass_stub(manager)
            asyncio.run(entity.async_added_to_hass())
        # A failed/empty later fetch must not discard the last successfully
        # loaded catalog from this PyDreo device.
        assert entity.effect_list == ["Effect One", Dreo530SRGBICLightHA.INDICATOR_EFFECT]

        with patch.object(manager, "get_rgbic_effect_catalog", side_effect=RuntimeError("catalog unavailable")), patch.object(
            entity, "async_write_ha_state"
        ), patch("custom_components.dreo.light.DreoLightHA.async_added_to_hass"):
            entity.hass = self._hass_stub(manager)
            asyncio.run(entity.async_added_to_hass())
        assert entity.effect_list == ["Effect One", Dreo530SRGBICLightHA.INDICATOR_EFFECT]

    def test_unknown_effect_is_logged_and_not_silently_ignored(self, caplog):
        device = self._make_530s()
        entity = light.get_entries([device])[0]
        with patch(PATCH_UPDATE_HA_STATE):
            entity.turn_on(effect="missing effect")
        assert "Unknown RGBIC effect" in caplog.text
        assert device.rgbon is None
        assert device.rgbbri is None


class TestDreoRGBICLightHA(TestDeviceBase):
    """Test the Dreo RGBIC Light entity (RGBIC effect-based atmosphere light, e.g. HCF007S)."""

    def _make_device(self, atm_bri_range=(1, 100), atm_brightness=50, atm_light_on=True,
                     preset_sel=0, preset_num=4, effect_id="2070476690030592000", effect_range=(0, 7), direct_rgb=False):
        """Create a mock RGBIC device with default values."""
        features = {
            "atm_light": True,
            "atm_light_on": atm_light_on,
            "atm_brightness": atm_brightness,
            "rgb_preset_sel": preset_sel,
            "rgb_preset_num": preset_num,
            "rgb_effect_id": effect_id,
        }
        if direct_rgb:
            features["atm_color_rgb_write"] = True

        device = self.create_mock_device(
            name="Ceiling Fan",
            serial_number="HCF007",
            features=features,
        )
        # atm_brightness_range and rgb_effect_range are properties, not feature flags
        device.atm_brightness_range = atm_bri_range
        device.rgb_effect_range = effect_range
        return device

    def test_rgbic_basic_properties(self):
        """Test RGBIC light entity basic properties."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device()
            entity = DreoRGBICLightHA(device)
            assert entity.translation_key == "rgb_light"
            assert not hasattr(entity, "_attr_name")
            assert entity.unique_id == "HCF007-rgb-light"

    def test_rgbic_color_mode_is_brightness(self):
        """RGBIC entity must use BRIGHTNESS color mode so HA shows a brightness slider."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device()
            entity = DreoRGBICLightHA(device)
            assert entity.color_mode == ColorMode.BRIGHTNESS
            assert ColorMode.BRIGHTNESS in entity.supported_color_modes

    def test_hcf007s_rgbic_color_mode_is_rgb(self):
        """HCF007S RGBIC entity should expose direct RGB color control."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device(direct_rgb=True)
            entity = DreoRGBICLightHA(device)
            assert entity.color_mode == ColorMode.RGB
            assert ColorMode.RGB in entity.supported_color_modes

            entity.turn_on(**{ATTR_RGB_COLOR: (0, 255, 0)})
            assert device.atm_color_rgb == (0, 255, 0)

    def test_rgbic_effect_list_from_effect_range(self):
        """Effect list should use rgb_effect_range from device definition."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device(effect_range=(0, 7))
            entity = DreoRGBICLightHA(device)
            assert entity.effect_list == [f"Effect {i}" for i in range(1, 9)]

    def test_rgbic_effect_list_fallback_to_preset_num(self):
        """When rgb_effect_range is not set and rgb_effect_id is absent, fall back to rgb_preset_num."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device(preset_num=4, effect_range=None, effect_id=None)
            device.rgb_effect_range = None
            # Remove rgb_effect_id from supported features to trigger preset path
            device._supported_features = [f for f in device._supported_features if f != "rgb_effect_id"]
            entity = DreoRGBICLightHA(device)
            assert entity.effect_list == ["Preset 1", "Preset 2", "Preset 3", "Preset 4"]

    def test_rgbic_current_effect(self):
        """Current effect should reflect the effect index from the rgbeffectid."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device(effect_id="2070476690030592003")
            entity = DreoRGBICLightHA(device)
            assert entity.effect == "Effect 4"

    def test_rgbic_current_effect_zero(self):
        """Effect index 0 should show as 'Effect 1'."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device(effect_id="2070476690030592000")
            entity = DreoRGBICLightHA(device)
            assert entity.effect == "Effect 1"

    def test_rgbic_turn_on_selects_effect(self):
        """turn_on with an effect kwarg should set atm_light_on and send the correct effect ID."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device(atm_light_on=False, effect_id="2070476690030592000")
            entity = DreoRGBICLightHA(device)
            entity.turn_on(**{ATTR_EFFECT: "Effect 3"})
            assert device.atm_light_on is True
            assert device.rgb_effect_id == "2070476690030592002"

    def test_rgbic_turn_on_with_brightness(self):
        """turn_on with brightness kwarg should set atm_brightness via the correct 1-100 scale."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device(atm_light_on=False, atm_brightness=1)
            entity = DreoRGBICLightHA(device)
            # HA brightness 255 should map to device brightness 100
            entity.turn_on(**{ATTR_BRIGHTNESS: 255})
            assert device.atm_light_on is True
            assert device.atm_brightness == 100

    def test_rgbic_brightness_scale_uses_device_range(self):
        """DreoRGBICLightHA must read atm_brightness_range from the device for correct scaling."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device(atm_bri_range=(1, 100), atm_brightness=50)
            entity = DreoRGBICLightHA(device)
            # brightness property should convert 50/100 to HA scale (roughly 127/255)
            ha_brightness = entity.brightness
            assert ha_brightness is not None
            assert 120 <= ha_brightness <= 135  # ~50% of 255

    def test_rgbic_is_on_off(self):
        """is_on should reflect atm_light_on; turn_off should clear it."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device(atm_light_on=True)
            entity = DreoRGBICLightHA(device)
            assert entity.is_on is True
            entity.turn_off()
            assert device.atm_light_on is False

    def test_rgbic_parse_effect_index(self):
        """Test static method for parsing effect index from ID string."""
        assert DreoRGBICLightHA._parse_effect_index("2070476690030592000") == 0
        assert DreoRGBICLightHA._parse_effect_index("2070476690030592007") == 7
        assert DreoRGBICLightHA._parse_effect_index(None) is None
        assert DreoRGBICLightHA._parse_effect_index("ab") is None

    def test_rgbic_build_effect_id(self):
        """Test static method for building an effect ID from base + index."""
        assert DreoRGBICLightHA._build_effect_id("2070476690030592000", 3) == "2070476690030592003"
        assert DreoRGBICLightHA._build_effect_id("2070476690030592000", 0) == "2070476690030592000"
        assert DreoRGBICLightHA._build_effect_id(None, 0) is None


    def test_hcf002s_api_rgbic_exposes_rgb_and_named_effects(self):
        """The newer HCF002S API path exposes RGB color plus the basic effect names."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device(effect_range=None, effect_id=None)
            device._supported_features.append("rgbic_effect_api")
            device.rgbic_color = (128, 0, 255)
            device.rgbic_effect_name = "Constant"
            device.rgbic_effect_names = [
                "Constant", "Breath", "Cycle", "Marquee", "Flow", "Flash", "Starlight", "Chase"
            ]
            entity = DreoRGBICLightHA(device)

            assert entity.color_mode == ColorMode.RGB
            assert entity.supported_color_modes == {ColorMode.RGB}
            assert entity.rgb_color == (128, 0, 255)
            assert entity.effect == "Constant"
            assert entity.effect_list == device.rgbic_effect_names

    def test_hcf002s_api_rgbic_turn_on_routes_color_and_effect(self):
        """HA RGB/effect requests are routed through set_rgbic_effect on the new API path."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device(effect_range=None, effect_id=None)
            device._supported_features.append("rgbic_effect_api")
            device.rgbic_color = None
            device.rgbic_effect_name = None
            device.rgbic_effect_names = ["Constant", "Breath"]
            calls = []
            device.set_rgbic_effect = lambda effect, color_rgb=None: calls.append((effect, color_rgb))
            entity = DreoRGBICLightHA(device)

            entity.turn_on(**{ATTR_RGB_COLOR: (128, 0, 255)})
            assert calls[-1] == ("Constant", (128, 0, 255))

            entity.turn_on(**{ATTR_EFFECT: "Breath"})
            assert calls[-1] == ("Breath", None)

class TestDreoHumidifierLightHA(TestDeviceBase):
    """Test the Dreo humidifier ambient light entity (atmosphere light on humidifiers)."""

    def _make_device(self, atm_color=True, atm_brightness=True):
        """Create a mock humidifier device using the newer atm_* firmware path."""
        features = {"atm_on": True}
        if atm_color:
            features["atm_color"] = "255,255,255"
        if atm_brightness:
            features["atm_brightness"] = 50
        return self.create_mock_device(
            name="Humidifier",
            serial_number="HHM015S",
            features=features,
        )

    def test_humidifier_light_basic_properties(self):
        """Entity must localize its name via translation_key and not hardcode _attr_name."""
        with patch(PATCH_UPDATE_HA_STATE):
            entity = DreoHumidifierLightHA(self._make_device())
            assert entity.translation_key == "ambient_light"
            assert not hasattr(entity, "_attr_name")
            assert entity.unique_id == "HHM015S-ambient-light"

    def test_humidifier_light_color_and_brightness_yields_single_valid_mode(self):
        """A device supporting both atm_color and atm_brightness must expose RGB only.

        Home Assistant forbids combining ColorMode.BRIGHTNESS with any color mode
        (RGB already implies brightness). Combining them raises HomeAssistantError
        when the entity is added, so supported_color_modes must be a single mode.
        """
        # Local import so the test explicitly exercises HA's validation rule.
        from homeassistant.components.light import valid_supported_color_modes

        with patch(PATCH_UPDATE_HA_STATE):
            entity = DreoHumidifierLightHA(self._make_device(atm_color=True, atm_brightness=True))
            modes = entity.supported_color_modes
            assert modes == {ColorMode.RGB}
            assert ColorMode.BRIGHTNESS not in modes
            # Must pass HA's own validator (raises vol.Invalid otherwise).
            valid_supported_color_modes(modes)
            assert entity.color_mode in modes

    def test_humidifier_light_brightness_only(self):
        """A device with brightness but no color should expose BRIGHTNESS only."""
        from homeassistant.components.light import valid_supported_color_modes

        with patch(PATCH_UPDATE_HA_STATE):
            entity = DreoHumidifierLightHA(self._make_device(atm_color=False, atm_brightness=True))
            modes = entity.supported_color_modes
            assert modes == {ColorMode.BRIGHTNESS}
            valid_supported_color_modes(modes)
            assert entity.color_mode in modes

    def test_humidifier_light_onoff_only(self):
        """A device with neither color nor brightness should expose ONOFF only."""
        from homeassistant.components.light import valid_supported_color_modes

        with patch(PATCH_UPDATE_HA_STATE):
            entity = DreoHumidifierLightHA(self._make_device(atm_color=False, atm_brightness=False))
            modes = entity.supported_color_modes
            assert modes == {ColorMode.ONOFF}
            valid_supported_color_modes(modes)
            assert entity.color_mode in modes

