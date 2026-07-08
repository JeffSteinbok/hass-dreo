"""Tests for the Dreo Light entity."""

import math
from unittest.mock import patch

from custom_components.dreo import light
from custom_components.dreo.light import DreoLightHA, DreoRGBLightHA, DreoRGBICLightHA
from custom_components.dreo.haimports import (
    ColorMode,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
    ATTR_EFFECT,
)

from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"


class TestDreoLightHA(TestDeviceBase):
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
            assert light_entity.name == "Ceiling Fan Light"
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
            assert rgb_light.name == "Ceiling Fan RGB Light"
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


class TestDreoRGBICLightHA(TestDeviceBase):
    """Test the Dreo RGBIC Light entity (RGBIC effect-based atmosphere light, e.g. HCF007S)."""

    def _make_device(self, atm_bri_range=(1, 100), atm_brightness=50, atm_light_on=True,
                     preset_sel=0, preset_num=4, effect_id="2070476690030592000", effect_range=(0, 7), model=None):
        """Create a mock RGBIC device with default values."""
        device = self.create_mock_device(
            name="Ceiling Fan",
            serial_number="HCF007",
            features={
                "atm_light": True,
                "atm_light_on": atm_light_on,
                "atm_brightness": atm_brightness,
                "rgb_preset_sel": preset_sel,
                "rgb_preset_num": preset_num,
                "rgb_effect_id": effect_id,
            },
        )
        device.model = model
        # atm_brightness_range and rgb_effect_range are properties, not feature flags
        device.atm_brightness_range = atm_bri_range
        device.rgb_effect_range = effect_range
        return device

    def test_rgbic_basic_properties(self):
        """Test RGBIC light entity basic properties."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self._make_device()
            entity = DreoRGBICLightHA(device)
            assert entity.name == "Ceiling Fan RGB Light"
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
            device = self._make_device(model="DR-HCF007S")
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
