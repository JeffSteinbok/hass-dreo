"""Integration Tests for Dreo Ceiling Fans"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import MagicMock, patch
from custom_components.dreo import binary_sensor
from custom_components.dreo import dreoheater
from custom_components.dreo import light
from custom_components.dreo import sensor
from custom_components.dreo import number
from custom_components.dreo import switch
from custom_components.dreo import select

from homeassistant.components.climate import ATTR_TEMPERATURE, PRESET_ECO, PRESET_NONE, SWING_OFF, ClimateEntityFeature, HVACMode
from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode
from homeassistant.const import UnitOfTemperature

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
            assert heater_ha.translation_key == "heater"
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

            # Verify ecolevel range uses the correct 41-95°F range (not the old 41-85°F)
            assert heater_ha.max_temp == 95
            assert heater_ha.min_temp == 41

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
                # Turning off must NOT send a mode="off" command - "off" is not a real
                # device mode and causes state sync problems when powering back on.
                for call_args in mock_send_command.call_args_list:
                    params = call_args[0][1]
                    assert not (MODE_KEY in params and params[MODE_KEY] == "off"), (
                        "set_hvac_mode(OFF) must not send {mode: 'off'} to the device"
                    )

            # Simulate server ACK: only poweron=false, no mode (common real-world pattern).
            # hvac_mode must be OFF.
            pydreo_heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
            assert heater_ha.hvac_mode == HVACMode.OFF

            # Simulate server turning the device back on with only poweron=true and no mode.
            # This is the key automation bug scenario: if the ACK for the turn-on command
            # doesn't include the mode, hvac_mode must still correctly show HEAT (not OFF).
            pydreo_heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
            assert heater_ha.hvac_mode == HVACMode.HEAT, (
                "hvac_mode must be HEAT when device is on, even if the WebSocket "
                "power-on update does not include the mode"
            )

            # Simulate server sending an empty mode string (happens when heater is off).
            # The last known active mode must be preserved.
            pydreo_heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: ""}})
            assert heater_ha.hvac_mode == HVACMode.OFF
            # Powering back on - hvac_mode must still be HEAT (not OFF).
            pydreo_heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
            assert heater_ha.hvac_mode == HVACMode.HEAT, (
                "hvac_mode must be HEAT after power-on even when the server sent an "
                "empty mode string while the device was off"
            )

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

    def test_HSH040S(self):  # pylint: disable=invalid-name
        """Load HSH040S (720S) heater and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HSH040S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater: PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == "Heater"
            assert pydreo_heater.model == "DR-HSH040S"
            assert pydreo_heater.series_name == "720S"

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.is_on is True
            assert heater_ha.hvac_mode == HVACMode.HEAT
            assert sorted(heater_ha.hvac_modes) == sorted([HVACMode.HEAT, HVACMode.FAN_ONLY, HVACMode.OFF])
            assert heater_ha.preset_mode == PRESET_ECO
            assert sorted(heater_ha.preset_modes) == sorted([PRESET_ECO, "H1", "H2", "H3"])
            assert heater_ha.current_temperature == 70
            assert heater_ha.target_temperature == 68
            assert heater_ha.min_temp == 41
            assert heater_ha.max_temp == 95
            assert heater_ha.swing_modes is None
            assert not heater_ha.supported_features & ClimateEntityFeature.SWING_MODE
            assert heater_ha.supported_features & ClimateEntityFeature.TARGET_TEMPERATURE
            assert heater_ha.supported_features & ClimateEntityFeature.PRESET_MODE

            # PTC is read-only on this model: no switch, a "heating" binary sensor instead.
            switches = switch.get_entries([pydreo_heater])
            self.verify_expected_entities(switches, ["Child Lock", "Display Light", "Panel Sound", "360° Airflow", "Window Detection"])
            airflow_360_switch = self.get_entity_by_key(switches, "360° Airflow")
            assert airflow_360_switch.is_on is False
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                airflow_360_switch.turn_on()
                mock_send_command.assert_called_once_with(pydreo_heater, {AIRFLOWMODE_KEY: 2})
            display_switch = self.get_entity_by_key(switches, "Display Light")
            assert display_switch.is_on is False
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                display_switch.turn_on()
                mock_send_command.assert_called_once_with(pydreo_heater, {LIGHTON_KEY: True})

            binary_sensors = binary_sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(binary_sensors, ["heating"])
            lights = light.get_entries([pydreo_heater])
            assert len(lights) == 1
            ambient_light = lights[0]
            assert ambient_light.translation_key == "ambient_light"
            assert ambient_light.supported_color_modes == {ColorMode.BRIGHTNESS}
            assert ambient_light.is_on is False
            # The fixture's rgbbri is 1.
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ambient_light.turn_on(**{ATTR_BRIGHTNESS: 1})
                mock_send_command.assert_called_once_with(pydreo_heater, {RGBON_KEY: True})
            pydreo_heater.handle_server_update({REPORTED_KEY: {RGBON_KEY: True}})
            assert ambient_light.is_on is True
            assert ambient_light.brightness == 85
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ambient_light.turn_on(**{ATTR_BRIGHTNESS: 255})
                mock_send_command.assert_called_once_with(pydreo_heater, {RGB_BRI: 3})
            pydreo_heater.handle_server_update({REPORTED_KEY: {RGB_BRI: 3}})
            assert ambient_light.brightness == 255
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ambient_light.turn_off()
                mock_send_command.assert_called_once_with(pydreo_heater, {RGBON_KEY: False})

            window_detection_switch = self.get_entity_by_key(switches, "Window Detection")
            assert window_detection_switch.is_on is False
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                window_detection_switch.turn_on()
                mock_send_command.assert_called_once_with(pydreo_heater, {WINOPENON_KEY: True})
            assert heater_ha.device_info["sw_version"] == "1.3.6"
            assert heater_ha.device_info["hw_version"] == "SC95F8615B/EU"
            heating_sensor = self.get_entity_by_key(binary_sensors, "heating")
            assert heating_sensor.is_on is False
            pydreo_heater.handle_server_update({REPORTED_KEY: {PTCON_KEY: True}})
            assert heating_sensor.is_on is True
            pydreo_heater.handle_server_update({REPORTED_KEY: {PTCON_KEY: False}})
            assert heating_sensor.is_on is False

            numbers = number.get_entries([pydreo_heater])
            self.verify_expected_entities(numbers, ["Temperature Offset"])
            offset_number = self.get_entity_by_key(numbers, "Temperature Offset")

            # Celsius: 1°C per 2°F, like the Dreo app.
            offset_number.hass = MagicMock()
            offset_number.hass.config.units.temperature_unit = UnitOfTemperature.CELSIUS
            assert offset_number.native_unit_of_measurement == UnitOfTemperature.CELSIUS
            assert (offset_number.native_min_value, offset_number.native_max_value) == (-5, 5)
            assert offset_number.native_value == 0
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                offset_number.set_native_value(-2.0)
                mock_send_command.assert_called_once_with(pydreo_heater, {TEMPOFFSET_KEY: -4})
            # The reported temperature already includes the offset; it must not be added twice.
            pydreo_heater.handle_server_update({REPORTED_KEY: {TEMPOFFSET_KEY: -4, TEMPERATURE_KEY: 66}})
            assert offset_number.native_value == -2
            assert heater_ha.current_temperature == 66

            # Fahrenheit: the device value as is.
            offset_number.hass.config.units.temperature_unit = UnitOfTemperature.FAHRENHEIT
            assert offset_number.native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT
            assert (offset_number.native_min_value, offset_number.native_max_value) == (-10, 10)
            assert offset_number.native_value == -4
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                offset_number.set_native_value(3.0)
                mock_send_command.assert_called_once_with(pydreo_heater, {TEMPOFFSET_KEY: 3})
            pydreo_heater.handle_server_update({REPORTED_KEY: {TEMPOFFSET_KEY: 0, TEMPERATURE_KEY: 70}})

            sensors = sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(sensors, [])

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H2")
                mock_send_command.assert_any_call(pydreo_heater, {MODE_KEY: DreoHeaterMode.HOTAIR})
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 2})
            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: "hotair", HTALEVEL_KEY: 2}})
            assert heater_ha.hvac_mode == HVACMode.HEAT
            assert heater_ha.preset_mode == "H2"

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.FAN_ONLY)
                mock_send_command.assert_any_call(pydreo_heater, {MODE_KEY: DreoHeaterMode.COOLAIR})
            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: "coolair"}})
            assert heater_ha.hvac_mode == HVACMode.FAN_ONLY

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_temperature(**{ATTR_TEMPERATURE: 72})
                mock_send_command.assert_called_once_with(pydreo_heater, {ECOLEVEL_KEY: 72})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.OFF)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: False})
            pydreo_heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
            assert heater_ha.hvac_mode == HVACMode.OFF

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
            assert heater_ha.translation_key == "heater"
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
            assert heater_ha.translation_key == "heater"

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

    def test_HSH010S(self):  # pylint: disable=invalid-name
        """Load DR-HSH010S oil panel heater and test HA entity."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HSH010S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater: PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == "Heater"
            assert pydreo_heater.model == "DR-HSH010S"

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.unique_id is not None
            assert heater_ha.translation_key == "heater"
            assert heater_ha.hvac_mode in [HVACMode.HEAT, HVACMode.FAN_ONLY, HVACMode.OFF]

            # HSH010S has no swing modes
            from homeassistant.components.climate import ClimateEntityFeature

            assert not (heater_ha.supported_features & ClimateEntityFeature.SWING_MODE)

            # Test HVAC mode changes
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.HEAT)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.OFF)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: False})

            # Test preset modes (H1, H2, H3)
            assert "H1" in heater_ha.preset_modes
            assert "H2" in heater_ha.preset_modes
            assert "H3" in heater_ha.preset_modes

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H1")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 1})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H3")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 3})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 3}})

            numbers = number.get_entries([pydreo_heater])
            self.verify_expected_entities(numbers, [])

            sensors = sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(sensors, [])

    def test_HSH041S(self):  # pylint: disable=invalid-name
        """Load DR-HSH041S (711S) convection heater and test HA entities (issue #928)."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HSH041S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater: PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == "Heater"
            assert pydreo_heater.model == "DR-HSH041S"
            assert pydreo_heater.series_name == "711S"

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.unique_id is not None
            assert heater_ha.hvac_mode == HVACMode.OFF  # poweron=False
            assert heater_ha.current_temperature == 74

            from homeassistant.components.climate import ClimateEntityFeature

            assert not (heater_ha.supported_features & ClimateEntityFeature.SWING_MODE)

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.HEAT)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})
            pydreo_heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

            assert {"H1", "H2", "H3"} <= set(heater_ha.preset_modes)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H3")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 3})

            # lighton=True in the diagnostics -> Display Auto Off is off (inverted, as on HSH006S).
            switches = switch.get_entries([pydreo_heater])
            display_auto_off = self.get_entity_by_key(switches, "Display Auto Off")
            assert display_auto_off is not None
            assert display_auto_off.is_on is False
            assert self.get_entity_by_key(switches, "Child Lock") is not None

    def test_HSH011S(self):  # pylint: disable=invalid-name
        """Load DR-HSH011S (OH521S) oil radiator heater and test HA entity."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HSH011S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater: PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == "Heater"
            assert pydreo_heater.model == "DR-HSH011S"
            assert pydreo_heater.series_name == "OH521S"

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.unique_id is not None
            assert heater_ha.translation_key == "heater"
            assert heater_ha.hvac_mode in [HVACMode.HEAT, HVACMode.FAN_ONLY, HVACMode.OFF]

            # HSH011S has no swing modes
            from homeassistant.components.climate import ClimateEntityFeature

            assert not (heater_ha.supported_features & ClimateEntityFeature.SWING_MODE)

            # Test HVAC mode changes
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.HEAT)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.OFF)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: False})

            # Test preset modes (H1, H2, H3)
            assert "H1" in heater_ha.preset_modes
            assert "H2" in heater_ha.preset_modes
            assert "H3" in heater_ha.preset_modes

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H1")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 1})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

            numbers = number.get_entries([pydreo_heater])
            self.verify_expected_entities(numbers, [])

            sensors = sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(sensors, [])

    def test_HSH016S(self):  # pylint: disable=invalid-name
        """Load DR-HSH016S (Tower Fan & Heater 706S) and test the combined heat/fan climate entity."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HSH016S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_heater: PyDreoHeater = self.pydreo_manager.devices[0]
            assert pydreo_heater.type == "Heater"
            assert pydreo_heater.model == "DR-HSH016S"
            assert pydreo_heater.series_name == "706S/806S"

            heater_ha = dreoheater.DreoHeaterHA(pydreo_heater)
            assert heater_ha.unique_id is not None
            assert heater_ha.translation_key == "heater"

            from homeassistant.components.climate import ClimateEntityFeature

            assert heater_ha.supported_features & ClimateEntityFeature.SWING_MODE
            assert heater_ha.supported_features & ClimateEntityFeature.FAN_MODE
            assert heater_ha.supported_features & ClimateEntityFeature.PRESET_MODE
            assert heater_ha.supported_features & ClimateEntityFeature.TARGET_TEMPERATURE
            assert sorted(heater_ha.hvac_modes) == sorted([HVACMode.HEAT, HVACMode.FAN_ONLY, HVACMode.OFF])

            # Fixture: on, fan function at speed 5 in normal mode, oscillation off
            assert heater_ha.hvac_mode == HVACMode.FAN_ONLY
            assert heater_ha.preset_mode == PRESET_NONE
            assert heater_ha.fan_modes == [str(n) for n in range(1, 13)]
            assert heater_ha.fan_mode == "5"
            assert heater_ha.swing_modes == [SWING_OFF, "30°", "60°", "90°", "120°"]
            assert heater_ha.swing_mode == SWING_OFF
            assert heater_ha.current_temperature == 66
            assert heater_ha.target_temperature == 85
            assert (heater_ha.min_temp, heater_ha.max_temp) == (41, 95)
            assert heater_ha.preset_modes == [PRESET_ECO, "H1", "H2", "H3", "H4", "H5", PRESET_NONE, "Natural", "Sleep", "Auto"]

            # Fan speed
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_fan_mode("12")
                mock_send_command.assert_any_call(pydreo_heater, {COOLLEVEL_KEY: 12})
            pydreo_heater.handle_server_update({REPORTED_KEY: {COOLLEVEL_KEY: 12}})
            assert heater_ha.fan_mode == "12"
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_fan_mode("13")
                mock_send_command.assert_not_called()

            # Fan sub-mode presets
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("Sleep")
                mock_send_command.assert_any_call(pydreo_heater, {COOLMODE_KEY: 3})
            pydreo_heater.handle_server_update({REPORTED_KEY: {COOLMODE_KEY: 3}})
            assert heater_ha.preset_mode == "Sleep"
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode(PRESET_NONE)
                mock_send_command.assert_any_call(pydreo_heater, {COOLMODE_KEY: 1})
            pydreo_heater.handle_server_update({REPORTED_KEY: {COOLMODE_KEY: 1}})
            assert heater_ha.preset_mode == PRESET_NONE

            # Switching to heat sends the function and sub-mode together, as the app does
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.HEAT)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: True})
                mock_send_command.assert_any_call(pydreo_heater, {MODE_KEY: 1, HTAMODE_KEY: 1})
            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 1}})
            # Already heating: no function command. An unknown reported function reads as heat but is replaced
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.HEAT)
                mock_send_command.assert_called_once_with(pydreo_heater, {POWERON_KEY: True})
            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 99}})
            assert heater_ha.hvac_mode == HVACMode.HEAT
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.HEAT)
                mock_send_command.assert_any_call(pydreo_heater, {MODE_KEY: 1, HTAMODE_KEY: 1})
            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 1}})
            assert heater_ha.hvac_mode == HVACMode.HEAT
            assert heater_ha.preset_mode == "H1"

            # Heat levels up to H5
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode("H5")
                mock_send_command.assert_any_call(pydreo_heater, {HTALEVEL_KEY: 5})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 5}})
            assert heater_ha.preset_mode == "H5"

            # Eco is the heat function with the eco sub-mode; thermostat in Fahrenheit
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_preset_mode(PRESET_ECO)
                mock_send_command.assert_any_call(pydreo_heater, {MODE_KEY: 1, HTAMODE_KEY: 2})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HTAMODE_KEY: 2}})
            assert heater_ha.hvac_mode == HVACMode.HEAT
            assert heater_ha.preset_mode == PRESET_ECO
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_temperature(temperature=70)
                mock_send_command.assert_any_call(pydreo_heater, {ECOLEVEL_KEY: 70})

            # Back to the fan function
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.FAN_ONLY)
                mock_send_command.assert_any_call(pydreo_heater, {MODE_KEY: 2})
            pydreo_heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 2}})
            assert heater_ha.hvac_mode == HVACMode.FAN_ONLY

            # Swing: a preset angle sets a symmetric range and turns oscillation on; off just stops it
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_swing_mode("90°")
                mock_send_command.assert_any_call(pydreo_heater, {HORIZONTAL_OSCILLATION_ANGLE_KEY: "-45,45"})
                mock_send_command.assert_any_call(pydreo_heater, {HORIZONTAL_OSCILLATION_KEY: True})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: True, HORIZONTAL_OSCILLATION_ANGLE_KEY: "-45,45"}})
            assert heater_ha.swing_mode == "90°"
            # An asymmetric range set from the app maps to the nearest preset by width
            pydreo_heater.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_ANGLE_KEY: "-30,20"}})
            assert heater_ha.swing_mode == "60°"
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_swing_mode(SWING_OFF)
                mock_send_command.assert_any_call(pydreo_heater, {HORIZONTAL_OSCILLATION_KEY: False})
            pydreo_heater.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: False}})
            assert heater_ha.swing_mode == SWING_OFF

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater_ha.set_hvac_mode(HVACMode.OFF)
                mock_send_command.assert_any_call(pydreo_heater, {POWERON_KEY: False})
            pydreo_heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
            assert heater_ha.hvac_mode == HVACMode.OFF

            # Companion entities: fixed direction + oscillation range numbers, the usual heater switches
            # plus open-window detection, and the off/on/auto display select
            numbers = number.get_entries([pydreo_heater])
            self.verify_expected_entities(numbers, ["Horizontal Angle", "Horizontal Oscillation Angle Left", "Horizontal Oscillation Angle Right"])
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                self.get_entity_by_key(numbers, "Horizontal Angle").set_native_value(-20)
                mock_send_command.assert_any_call(pydreo_heater, {HORIZONTAL_ANGLE_ADJ_KEY: -20})

            switches = switch.get_entries([pydreo_heater])
            self.verify_expected_entities(switches, ["Horizontally Oscillating", "Panel Sound", "PTC", "Child Lock", "Window Detection"])
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                self.get_entity_by_key(switches, "Window Detection").turn_on()
                mock_send_command.assert_any_call(pydreo_heater, {WINOPENON_KEY: True})

            selects = select.get_entries([pydreo_heater])
            self.verify_expected_entities(selects, ["Display Mode"])
            display = self.get_entity_by_key(selects, "Display Mode")
            assert display.options == ["off", "on", "auto"]
            assert display.current_option == "auto"
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                display.select_option("off")
                mock_send_command.assert_any_call(pydreo_heater, {LIGHTMODE_KEY: 0})

            sensors = sensor.get_entries([pydreo_heater])
            self.verify_expected_entities(sensors, [])
