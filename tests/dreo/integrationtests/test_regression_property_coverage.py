"""Regression-focused integration coverage across all model fixtures."""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from homeassistant.components.climate import HVACMode

from custom_components.dreo import fan
from custom_components.dreo import humidifier
from custom_components.dreo import dreoheater
from custom_components.dreo import dreoairconditioner

from .integrationtestbase import IntegrationTestBase, PATCH_SEND_COMMAND

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_SCHEDULE_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

INTEGRATION_EXHAUSTIVE_MODEL_FIXTURES = [
    "get_devices_HAC005S.json",
    "get_devices_HAC006S.json",
    "get_devices_HAF001S.json",
    "get_devices_HAF003S.json",
    "get_devices_HAF004S.json",
    "get_devices_HAF004S_2REVS.json",
    "get_devices_HAF008S.json",
    "get_devices_HCF001S.json",
    "get_devices_HCF002S.json",
    "get_devices_HCF003S.json",
    "get_devices_HHM001S.json",
    "get_devices_HHM003S.json",
    "get_devices_HHM006S.json",
    "get_devices_HHM014S.json",
    "get_devices_HHM015S.json",
    "get_devices_HPF002S.json",
    "get_devices_HPF005S.json",
    "get_devices_HPF007S.json",
    "get_devices_HPF008S.json",
    "get_devices_HPF015S.json",
    "get_devices_HPF020S.json",
    "get_devices_HPF025S.json",
    "get_devices_HSH003S.json",
    "get_devices_HSH004S.json",
    "get_devices_HSH009S.json",
    "get_devices_HSH010S.json",
    "get_devices_HSH011.json",
    "get_devices_HSH011S.json",
    "get_devices_HSH034S.json",
    "get_devices_WH714S.json",
]


class TestRegressionPropertyCoverage(IntegrationTestBase):
    """Exercise integration-layer properties and command paths for every model fixture."""

    def _exercise_fan_like_entities(self, pydreo_device):
        ha_fan = fan.DreoFanHA(pydreo_device)
        _ = ha_fan.is_on
        _ = ha_fan.speed_count
        _ = ha_fan.percentage
        _ = ha_fan.preset_mode
        _ = ha_fan.preset_modes
        _ = ha_fan.supported_features
        _ = ha_fan.unique_id
        _ = ha_fan.name

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            if ha_fan.is_on:
                ha_fan.turn_off()
            else:
                ha_fan.turn_on()
            assert mock_send_command.call_count >= 1

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            target_percentage = 25 if ha_fan.percentage != 25 else 75
            ha_fan.set_percentage(target_percentage)
            assert mock_send_command.call_count >= 1

        if ha_fan.preset_modes:
            target_mode = next((mode for mode in ha_fan.preset_modes if mode != ha_fan.preset_mode), None)
            if target_mode is not None:
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    ha_fan.set_preset_mode(target_mode)
                    assert mock_send_command.call_count >= 1

    def _exercise_ac_entities(self, pydreo_device):
        ac = dreoairconditioner.DreoAirConditionerHA(pydreo_device)
        _ = ac.hvac_mode
        _ = ac.hvac_modes
        _ = ac.fan_mode
        _ = ac.fan_modes
        _ = ac.current_temperature
        _ = ac.target_temperature
        _ = ac.current_humidity
        _ = ac.target_humidity
        _ = ac.unique_id
        # The AC entity name is derived from translation_key + has_entity_name, so
        # reading .name requires an entity platform (unavailable in this unit test).
        # Exercise the naming attributes that drive it instead.
        _ = ac.translation_key
        _ = ac.has_entity_name

        if ac.fan_modes:
            target_mode = next((mode for mode in ac.fan_modes if mode != ac.fan_mode), None)
            if target_mode is not None:
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    ac.set_fan_mode(target_mode)
                    assert mock_send_command.call_count >= 1

    def _exercise_heater_entities(self, pydreo_device):
        heater = dreoheater.DreoHeaterHA(pydreo_device)
        _ = heater.hvac_mode
        _ = heater.hvac_modes
        _ = heater.preset_mode
        _ = heater.preset_modes
        _ = heater.current_temperature
        _ = heater.target_temperature
        _ = heater.min_temp
        _ = heater.max_temp
        _ = heater.unique_id
        # The heater entity name is derived from translation_key + has_entity_name, so
        # reading .name requires an entity platform (unavailable in this unit test).
        # Exercise the naming attributes that drive it instead.
        _ = heater.translation_key
        _ = heater.has_entity_name
        _ = heater.is_on

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.set_hvac_mode(HVACMode.OFF if heater.is_on else HVACMode.HEAT)
            assert mock_send_command.call_count >= 1

        if heater.preset_modes:
            target_mode = next((mode for mode in heater.preset_modes if mode != heater.preset_mode), None)
            if target_mode is not None:
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    heater.set_preset_mode(target_mode)
                    assert mock_send_command.call_count >= 1

    def _exercise_humidifier_entities(self, pydreo_device):
        ha_humidifier = humidifier.DreoHumidifierHA(pydreo_device)
        _ = ha_humidifier.is_on
        _ = ha_humidifier.current_humidity
        _ = ha_humidifier.target_humidity
        _ = ha_humidifier.available_modes
        _ = ha_humidifier.mode
        _ = ha_humidifier.supported_features
        _ = ha_humidifier.unique_id
        _ = ha_humidifier.name

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            if ha_humidifier.is_on:
                ha_humidifier.turn_off()
            else:
                ha_humidifier.turn_on()
            assert mock_send_command.call_count >= 1

        if ha_humidifier.available_modes:
            target_mode = next((mode for mode in ha_humidifier.available_modes if mode != ha_humidifier.mode), None)
            if target_mode is not None:
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    ha_humidifier.set_mode(target_mode)
                    assert mock_send_command.call_count >= 1

        if ha_humidifier.target_humidity is not None:
            new_target_humidity = ha_humidifier.target_humidity + 1 if ha_humidifier.target_humidity < 90 else ha_humidifier.target_humidity - 1
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_humidifier.set_humidity(new_target_humidity)
                assert mock_send_command.call_count >= 1

    @pytest.mark.parametrize("devices_file", INTEGRATION_EXHAUSTIVE_MODEL_FIXTURES)
    def test_integration_property_and_command_regression_coverage(self, devices_file: str):
        """Exercise HA integration properties and command paths for every model fixture."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = devices_file
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) >= 1

            for device in self.pydreo_manager.devices:
                device_type = device.type.value if hasattr(device.type, "value") else device.type

                if device_type in ("Air Circulator", "Ceiling Fan"):
                    self._exercise_fan_like_entities(device)
                elif device_type == "Air Conditioner":
                    self._exercise_ac_entities(device)
                elif device_type == "Heater":
                    self._exercise_heater_entities(device)
                elif device_type == "Humidifier":
                    self._exercise_humidifier_entities(device)
