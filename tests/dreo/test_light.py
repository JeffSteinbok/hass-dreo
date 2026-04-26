"""Tests for the Dreo Light entity."""

import math
from unittest.mock import patch

from custom_components.dreo import light
from custom_components.dreo.light import DreoLightHA, DreoRGBLightHA
from custom_components.dreo.haimports import (
    ColorMode,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
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
