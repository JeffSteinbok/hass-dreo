"""Integration Tests for Dreo Air Purifiers"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import fan, switch, sensor
from .imports import *  # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase, PATCH_SEND_COMMAND

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_SCHEDULE_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestDreoAirPurifier(IntegrationTestBase):
    """Test Dreo Air Purifiers and PyDreo together."""

    def test_HAP002S(self):  # pylint: disable=invalid-name
        """Load HAP002S air purifier (Macro Pro S) and test HA entity."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HAP002S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_ap = self.pydreo_manager.devices[0]
            assert pydreo_ap.type == "Air Purifier"
            assert pydreo_ap.model == "DR-HAP002S"
            assert pydreo_ap.series_name == "Macro Pro S"
            assert pydreo_ap.speed_range == (1, 18)
            assert pydreo_ap.preset_modes == ["manual"]

            ha_fan = fan.DreoFanHA(pydreo_ap)
            assert ha_fan.speed_count == 18
            assert ha_fan.unique_id is not None
            assert ha_fan.name is not None
            assert ha_fan.preset_modes == ["manual"]

            # Test turn on/off (fan starts ON in fixture, so turn off first)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_ap, {POWERON_KEY: False})
            pydreo_ap.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_ap, {POWERON_KEY: True})
            pydreo_ap.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

            # Test speed (1-18 range); fan off so turn_on fires too
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)
                mock_send_command.assert_any_call(pydreo_ap, {WINDLEVEL_KEY: 18})

            # Test entity inventory
            switches = switch.get_entries([pydreo_ap])
            self.verify_expected_entities(switches, ["Child Lock", "Display Auto Off", "Panel Sound"])
            sensors = sensor.get_entries([pydreo_ap])
            self.verify_expected_entities(sensors, [])

    def test_HAP003S(self):  # pylint: disable=invalid-name
        """Load HAP003S air purifier (Macro Max S) — original revision ("meidi" MCU)."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HAP003S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_ap = self.pydreo_manager.devices[0]
            assert pydreo_ap.type == "Air Purifier"
            assert pydreo_ap.model == "DR-HAP003S"
            assert pydreo_ap.series_name == "Macro Max S"
            assert pydreo_ap.speed_range == (1, 18)
            assert pydreo_ap.preset_modes == ["auto", "manual", "sleep", "turbo"]
            # Original revision ("meidi" MCU) must NOT have auto-silent remapping
            assert pydreo_ap._auto_mode_uses_auto_silent is False  # pylint: disable=protected-access

            ha_fan = fan.DreoFanHA(pydreo_ap)
            assert ha_fan.speed_count == 18
            assert ha_fan.unique_id is not None
            assert ha_fan.name is not None
            assert ha_fan.preset_modes == ["auto", "manual", "sleep", "turbo"]

            # Test turn on/off
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_ap, {POWERON_KEY: True})
            pydreo_ap.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_ap, {POWERON_KEY: False})
            pydreo_ap.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

            # Restore ON state via state update (no command sent) before testing preset mode
            pydreo_ap.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
            pydreo_ap.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "sleep"}})

            # Original revision must send "auto" unchanged
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("auto")
                mock_send_command.assert_called_once_with(pydreo_ap, {WIND_MODE_KEY: "auto"})
            pydreo_ap.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto"}})

            # Other modes must pass through unchanged
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("sleep")
                mock_send_command.assert_called_once_with(pydreo_ap, {WIND_MODE_KEY: "sleep"})

            # Test entity inventory
            switches = switch.get_entries([pydreo_ap])
            self.verify_expected_entities(switches, ["Child Lock", "Display Auto Off", "Panel Sound"])
            sensors = sensor.get_entries([pydreo_ap])
            self.verify_expected_entities(sensors, [])

    def test_HAP003S_2(self):  # pylint: disable=invalid-name
        """Load HAP003S air purifier (Macro Max S/AS) — newer "midea" MCU revision."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HAP003S_2.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_ap = self.pydreo_manager.devices[0]
            assert pydreo_ap.type == "Air Purifier"
            assert pydreo_ap.model == "DR-HAP003S"
            assert pydreo_ap.series_name == "Macro Max S/AS"
            assert pydreo_ap.speed_range == (1, 18)
            assert pydreo_ap.preset_modes == ["auto", "manual", "sleep", "turbo"]
            # Newer "midea" MCU revision must have auto-silent remapping enabled
            assert pydreo_ap._auto_mode_uses_auto_silent is True  # pylint: disable=protected-access

            ha_fan = fan.DreoFanHA(pydreo_ap)
            assert ha_fan.speed_count == 18
            assert ha_fan.unique_id is not None
            assert ha_fan.name is not None
            assert ha_fan.preset_modes == ["auto", "manual", "sleep", "turbo"]

            # Test turn on/off
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_ap, {POWERON_KEY: True})
            pydreo_ap.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_ap, {POWERON_KEY: False})
            pydreo_ap.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

            # Restore ON state via state update (no command sent) before testing preset mode
            pydreo_ap.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
            pydreo_ap.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "sleep"}})

            # Newer revision must remap "auto" preset command to "auto-silent"
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("auto")
                mock_send_command.assert_called_once_with(pydreo_ap, {WIND_MODE_KEY: "auto-silent"})
            pydreo_ap.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto-silent"}})

            # Other modes must pass through unchanged
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("sleep")
                mock_send_command.assert_called_once_with(pydreo_ap, {WIND_MODE_KEY: "sleep"})

            # Test entity inventory
            switches = switch.get_entries([pydreo_ap])
            self.verify_expected_entities(switches, ["Child Lock", "Panel Sound"])
            sensors = sensor.get_entries([pydreo_ap])
            self.verify_expected_entities(sensors, ["pm25"])

    def test_HAP005S(self):  # pylint: disable=invalid-name
        """Load HAP005S air purifier (Macro AP505S) and test HA entity."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HAP005S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_ap = self.pydreo_manager.devices[0]
            assert pydreo_ap.type == "Air Purifier"
            assert pydreo_ap.model == "DR-HAP005S"
            assert pydreo_ap.series_name == "Macro AP505S"
            assert pydreo_ap.speed_range == (1, 4)
            assert pydreo_ap.preset_modes == ["manual"]

            ha_fan = fan.DreoFanHA(pydreo_ap)
            assert ha_fan.speed_count == 4
            assert ha_fan.unique_id is not None
            assert ha_fan.name is not None

            # Test turn on/off
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_ap, {POWERON_KEY: True})
            pydreo_ap.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_ap, {POWERON_KEY: False})
            pydreo_ap.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

            # Test entity inventory
            switches = switch.get_entries([pydreo_ap])
            self.verify_expected_entities(switches, ["Child Lock", "Display Auto Off", "Panel Sound"])
            sensors = sensor.get_entries([pydreo_ap])
            self.verify_expected_entities(sensors, ["pm25"])
