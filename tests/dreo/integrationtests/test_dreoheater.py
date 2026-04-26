"""Integration Tests for Dreo Ceiling Fans"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import dreoheater
from custom_components.dreo import sensor
from custom_components.dreo import number

from homeassistant.components.climate import HVACMode

from .imports import *  # pylint: disable=W0401,W0614
from .integrationtestbase import PATCH_SEND_COMMAND, IntegrationTestBase

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_SCHEDULE_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestDreoHeater(IntegrationTestBase):
    """Test Dreo Heaters and PyDreo together."""

    def test_HSH009S(self):  # pylint: disable=invalid-name
        """Load heater and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HSH009S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater: PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == "Heater"
            assert pydreo_heater.model == "DR-HSH009S"

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.hvac_mode == HVACMode.HEAT
            assert heater_ha.preset_mode == "H3"
            assert heater_ha.unique_id is not None
            assert heater_ha.name is not None
            assert heater_ha.is_on is True

            # Test temperature reading
            if heater_ha.current_temperature is not None:
                assert isinstance(heater_ha.current_temperature, (int, float))

            numbers = number.get_entries([pydreo_heater])
            self.verify_expected_entities(numbers, [])

            sensors = sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(sensors, [])

            # Test HVAC mode changes
            # Device is already ON and in HEAT mode. Setting HEAT again should
            # still send the poweron command (fixes stale state after power cycle)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.HEAT)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.OFF)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: False})

            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: "eco"}})
            assert heater_ha.hvac_mode == HVACMode.HEAT

            # Test preset modes (H1, H2, H3)
            assert "H1" in heater_ha.preset_modes
            assert "H2" in heater_ha.preset_modes
            assert "H3" in heater_ha.preset_modes

            # Test setting H1 preset
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H1")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 1})
                mock_send_command.assert_any_call(pydreo_heater, {MODE_KEY: "hotair"})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})
            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: "hotair"}})

            # Test setting H2 preset
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H2")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 2})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 2}})

            # Test setting H3 preset
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H3")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 3})

            pydreo_heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 3}})

    def test_HSH003S(self):  # pylint: disable=invalid-name
        """Load heater and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HSH003S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater: PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == "Heater"
            assert pydreo_heater.model == "DR-HSH003S"
            assert pydreo_heater.poweron is True

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.hvac_mode == HVACMode.HEAT
            assert heater_ha.unique_id is not None

            numbers = number.get_entries([pydreo_heater])
            self.verify_expected_entities(numbers, [])

            sensors = sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(sensors, [])

            # Test multiple HVAC mode changes
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.FAN_ONLY)
                mock_send_command.assert_any_call(pydreo_heater, {MODE_KEY: "coolair"})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.OFF)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: False})

            pydreo_heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: "eco"}})
            assert heater_ha.hvac_mode == HVACMode.HEAT

    def test_HSH034S(self):  # pylint: disable=invalid-name
        """Load heater and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HSH034S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater: PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == "Heater"
            assert pydreo_heater.model == "DR-HSH034S"
            assert pydreo_heater.poweron is False

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.hvac_mode == HVACMode.OFF
            assert heater_ha.unique_id is not None

            numbers = number.get_entries([pydreo_heater])
            self.verify_expected_entities(numbers, [])

            sensors = sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(sensors, [])

            # Test turning heater on and setting mode
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.HEAT)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})
            pydreo_heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
            # Note that this device was set to OFF/Hotair, so mode should remain HEAT
            assert heater_ha.hvac_mode == HVACMode.HEAT

            # Device is now ON. Setting HEAT again should still send poweron command
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.HEAT)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})

            pydreo_heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: "eco"}})
            assert heater_ha.hvac_mode == HVACMode.HEAT

    def test_HSH011(self):  # pylint: disable=invalid-name
        """Load DR-HSH011 oil radiator heater and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HSH011.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater: PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == "Heater"
            assert pydreo_heater.model == "DR-HSH011"
            assert pydreo_heater.poweron is True

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.hvac_mode == HVACMode.HEAT
            assert heater_ha.preset_mode == "H3"
            assert heater_ha.unique_id is not None
            assert heater_ha.name is not None
            assert heater_ha.is_on is True

            # Test temperature reading
            if heater_ha.current_temperature is not None:
                assert isinstance(heater_ha.current_temperature, (int, float))

            numbers = number.get_entries([pydreo_heater])
            self.verify_expected_entities(numbers, [])

            sensors = sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(sensors, [])

            # Test preset modes (H1, H2, H3)
            assert "H1" in heater_ha.preset_modes
            assert "H2" in heater_ha.preset_modes
            assert "H3" in heater_ha.preset_modes

            # Test setting H1 preset
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H1")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 1})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

            # Test setting H2 preset
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H2")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 2})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 2}})

            # Test setting H3 preset
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H3")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 3})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 3}})

            # Test HVAC mode changes
            # Device is already ON and in HEAT mode. Setting HEAT again should
            # still send the poweron command (fixes stale state after power cycle)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.HEAT)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.OFF)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: False})

            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: "eco"}})
            pydreo_heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
            assert heater_ha.hvac_mode == HVACMode.HEAT

    def test_WH714S(self):  # pylint: disable=invalid-name
        """Load WH714S heater and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_WH714S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater: PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == "Heater"
            assert pydreo_heater.model == "DR-HSH034S"
            assert pydreo_heater.series_name == "WH714S"
            assert pydreo_heater.poweron is True
            assert pydreo_heater.mode == "eco"

            # WH714S uses oscmode (integer) for oscillation - oscmode 3 = 90°
            assert pydreo_heater.oscmode == 3

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.hvac_mode == HVACMode.HEAT
            assert heater_ha.preset_mode == PRESET_ECO
            assert heater_ha.unique_id is not None

            # Swing mode should be available since oscmode is not None
            from homeassistant.components.climate import ClimateEntityFeature

            assert heater_ha.supported_features & ClimateEntityFeature.SWING_MODE

            # Current swing mode should map oscmode 3 -> "90°"
            assert heater_ha.swing_mode == "90°"

            # Setting swing mode should send oscmode command (set to "Oscillate" = oscmode 1, different from current 3)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_swing_mode("Oscillate")
                mock_send_command.assert_any_call(pydreo_heater, {OSCMODE_KEY: 1})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_swing_mode("off")
                mock_send_command.assert_any_call(pydreo_heater, {OSCMODE_KEY: 0})

            # Server update for oscmode
            pydreo_heater.handle_server_update({REPORTED_KEY: {OSCMODE_KEY: 1}})
            assert pydreo_heater.oscmode == 1
            assert heater_ha.swing_mode == "Oscillate"

            numbers = number.get_entries([pydreo_heater])
            self.verify_expected_entities(numbers, [])

            sensors = sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(sensors, [])

            # Test turning heater on and setting mode
            # Device is already ON. Setting HEAT should still send poweron command
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.HEAT)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.HEAT)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.OFF)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: False})

            pydreo_heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: "eco"}})
            assert heater_ha.hvac_mode == HVACMode.HEAT

    def test_HSH004S(self):  # pylint: disable=invalid-name
        """Load HSH004S (Atom One S) heater and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HSH004S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater: PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == "Heater"
            assert pydreo_heater.model == "DR-HSH004S"
            assert pydreo_heater.series_name == "Atom One S"

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.hvac_mode == HVACMode.HEAT
            assert heater_ha.preset_mode == "H3"
            assert heater_ha.is_on is True
            assert heater_ha.unique_id is not None
            assert heater_ha.name is not None

            # Test temperature reading
            if heater_ha.current_temperature is not None:
                assert isinstance(heater_ha.current_temperature, (int, float))

            numbers = number.get_entries([pydreo_heater])
            self.verify_expected_entities(numbers, [])

            sensors = sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(sensors, [])

            # Test preset modes (H1, H2, H3)
            assert "H1" in heater_ha.preset_modes
            assert "H2" in heater_ha.preset_modes
            assert "H3" in heater_ha.preset_modes

            # Test setting H1 preset
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H1")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 1})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

            # Test setting H2 preset
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H2")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 2})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 2}})

            # Test setting H3 preset
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H3")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 3})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 3}})

            # Test HVAC mode changes
            # Device is already ON. Setting HEAT should still send poweron command
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.HEAT)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.OFF)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: False})

            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: "hotair"}})
            assert heater_ha.hvac_mode == HVACMode.HEAT

    def test_ptc_update_without_poweron(self):  # pylint: disable=invalid-name
        """Test that when PTC turns on without explicit poweron update, the heater state is updated correctly.

        This test reproduces the issue where heaters turned on externally (via app or manually)
        show PTC as on but the main heater state doesn't update in HA.
        """
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            # Load HSH034S heater that is initially OFF
            self.get_devices_file_name = "get_devices_HSH034S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater: PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.model == "DR-HSH034S"

            # Verify heater starts OFF
            assert pydreo_heater.poweron is False
            assert pydreo_heater.ptcon is False

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.hvac_mode == HVACMode.OFF
            assert heater_ha.is_on is False

            # Simulate external turn-on: PTC turns on without explicit poweron update
            # This simulates what happens when user turns on heater via app or manually
            pydreo_heater.handle_server_update({REPORTED_KEY: {PTCON_KEY: True}})

            # After PTC turns on, the heater should be considered ON
            assert pydreo_heater.ptcon is True, "PTC should be on after update"

            # With the fix, poweron should be inferred from PTC being on
            assert pydreo_heater.poweron is True, "Heater should be on when PTC is on"
            assert heater_ha.is_on is True, "HA entity should show heater as on"
            assert heater_ha.hvac_mode != HVACMode.OFF, "HVAC mode should not be OFF when PTC is on"
