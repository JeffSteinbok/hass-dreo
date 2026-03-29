"""Tests for the Dreo Switch entity."""
# pylint: disable=E1123
from unittest.mock import patch

from custom_components.dreo import switch
from custom_components.dreo.switch import DreoSwitchHA, DreoSwitchEntityDescription, SWITCHES

from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_UPDATE_HA_STATE = f'{PATCH_BASE_PATH}.schedule_update_ha_state'


class TestDreoSwitchHA(TestDeviceBase):
    """Test the Dreo Switch entity."""

    def test_switch_get_entries_filters_by_feature(self):
        """Test that get_entries only creates switches for supported features."""
        # Device with child lock and panel sound
        device_with_features = self.create_mock_device(
            name="Test Fan",
            serial_number="FAN001",
            features={
                "childlockon": True,
                "panel_sound": False,
            }
        )
        # Device with no switch features
        device_no_features = self.create_mock_device(
            name="Test Basic Fan",
            serial_number="FAN002",
            features={
                "is_on": True,
                "fan_speed": 3,
            }
        )

        entities = switch.get_entries([device_with_features, device_no_features])
        assert len(entities) == 2
        keys = [e.entity_description.key for e in entities]
        assert "Child Lock" in keys
        assert "Panel Sound" in keys

    def test_switch_get_entries_empty_for_no_devices(self):
        """Test that get_entries returns empty list when no devices support switches."""
        device = self.create_mock_device(
            name="Simple Device",
            serial_number="DEV001",
            features={"is_on": True}
        )
        entities = switch.get_entries([device])
        assert len(entities) == 0

    def test_switch_get_entries_all_switch_types(self):
        """Test that all defined switch types can be created."""
        # Create a device that supports all switch features
        features = {}
        for sw in SWITCHES:
            features[sw.attr_name] = False

        device = self.create_mock_device(
            name="Full Feature Device",
            serial_number="FULL001",
            features=features
        )

        entities = switch.get_entries([device])
        assert len(entities) == len(SWITCHES)

    def test_switch_entity_properties(self):
        """Test the switch entity basic properties."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Test Fan",
                serial_number="FAN001",
                features={"childlockon": True}
            )

            desc = DreoSwitchEntityDescription(
                key="Child Lock",
                translation_key="childlockon",
                attr_name="childlockon",
                icon="mdi:lock",
            )

            sw = DreoSwitchHA(device, desc)
            assert sw.name == "Test Fan Child Lock"
            assert sw.unique_id == "FAN001-Child Lock"
            assert sw.entity_description.key == "Child Lock"
            assert sw.entity_description.icon == "mdi:lock"

    def test_switch_is_on(self):
        """Test the is_on property reads from device attribute."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Test Fan",
                serial_number="FAN001",
                features={"childlockon": True}
            )

            desc = DreoSwitchEntityDescription(
                key="Child Lock",
                translation_key="childlockon",
                attr_name="childlockon",
                icon="mdi:lock",
            )

            sw = DreoSwitchHA(device, desc)
            assert sw.is_on is True

            # Change the device attribute
            device.childlockon = False
            assert sw.is_on is False

    def test_switch_turn_on(self):
        """Test turning a switch on."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Test Fan",
                serial_number="FAN001",
                features={"childlockon": False}
            )

            desc = DreoSwitchEntityDescription(
                key="Child Lock",
                translation_key="childlockon",
                attr_name="childlockon",
                icon="mdi:lock",
            )

            sw = DreoSwitchHA(device, desc)
            assert sw.is_on is False

            sw.turn_on()
            assert device.childlockon is True
            assert sw.is_on is True

    def test_switch_turn_off(self):
        """Test turning a switch off."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Test Fan",
                serial_number="FAN001",
                features={"childlockon": True}
            )

            desc = DreoSwitchEntityDescription(
                key="Child Lock",
                translation_key="childlockon",
                attr_name="childlockon",
                icon="mdi:lock",
            )

            sw = DreoSwitchHA(device, desc)
            assert sw.is_on is True

            sw.turn_off()
            assert device.childlockon is False
            assert sw.is_on is False

    def test_switch_oscillation_types(self):
        """Test horizontal and vertical oscillation switches."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Test Air Circulator",
                serial_number="AC001",
                features={
                    "horizontally_oscillating": False,
                    "vertically_oscillating": True,
                }
            )

            entities = switch.get_entries([device])
            assert len(entities) == 2

            horiz = next(e for e in entities if e.entity_description.key == "Horizontally Oscillating")
            vert = next(e for e in entities if e.entity_description.key == "Vertically Oscillating")

            assert horiz.is_on is False
            assert vert.is_on is True

            horiz.turn_on()
            assert device.horizontally_oscillating is True

            vert.turn_off()
            assert device.vertically_oscillating is False

    def test_switch_repr(self):
        """Test the repr method of DreoSwitchHA."""
        with patch(PATCH_UPDATE_HA_STATE):
            device = self.create_mock_device(
                name="Test Device",
                serial_number="DEV001",
                features={"oscon": True}
            )

            desc = DreoSwitchEntityDescription(
                key="Oscillating",
                translation_key="oscon",
                attr_name="oscon",
                icon="mdi:rotate-360",
            )

            sw = DreoSwitchHA(device, desc)
            repr_str = repr(sw)
            assert "DreoSwitchHA" in repr_str

    def test_switch_multiple_devices(self):
        """Test get_entries with multiple devices each having different switches."""
        device1 = self.create_mock_device(
            name="Fan",
            serial_number="FAN001",
            features={"oscon": True, "childlockon": False}
        )
        device2 = self.create_mock_device(
            name="Heater",
            serial_number="HTR001",
            features={"ptcon": True, "panel_sound": False}
        )

        entities = switch.get_entries([device1, device2])
        assert len(entities) == 4

        # Verify correct device association
        fan_switches = [e for e in entities if "Fan" in e.name]
        heater_switches = [e for e in entities if "Heater" in e.name]
        assert len(fan_switches) == 2
        assert len(heater_switches) == 2
