"""Integration Tests for Dreo Ceiling Fans"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import number, sensor
from custom_components.dreo import dreoairconditioner
from custom_components.dreo.pydreo.constant import DreoACFanMode
from homeassistant.components.climate import FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH
from .imports import *  # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase, PATCH_SEND_COMMAND

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_SCHEDULE_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestDreoAirConditioner(IntegrationTestBase):
    """Test Dreo Ceiling Fan class and PyDreo together."""

    def test_HAC005S(self):  # pylint: disable=invalid-name
        """Load air conditioner and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HAC005S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_ac = self.pydreo_manager.devices[0]
            assert pydreo_ac.type == "Air Conditioner"

            numbers = number.get_entries([pydreo_ac])
            self.verify_expected_entities(numbers, ["Target Humidity"])

            sensors = sensor.get_entries([pydreo_ac])
            self.verify_expected_entities(sensors, ["Humidity", "Target temp reached", "Use since cleaning"])

            # Test fan_modes returns strings (regression test for DreoACFanMode enum bug)
            ac_ha = dreoairconditioner.DreoAirConditionerHA(pydreo_ac)
            assert ac_ha.fan_modes is not None
            for mode in ac_ha.fan_modes:
                assert isinstance(mode, str), f"fan_modes must contain strings, got {type(mode)}: {mode!r}"
            assert FAN_AUTO in ac_ha.fan_modes
            assert FAN_LOW in ac_ha.fan_modes
            assert FAN_MEDIUM in ac_ha.fan_modes
            assert FAN_HIGH in ac_ha.fan_modes

    def test_HAC006S(self):  # pylint: disable=invalid-name
        """Load air conditioner and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HAC006S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_ac = self.pydreo_manager.devices[0]
            assert pydreo_ac.type == "Air Conditioner"

            numbers = number.get_entries([pydreo_ac])
            self.verify_expected_entities(numbers, ["Target Humidity"])

            sensors = sensor.get_entries([pydreo_ac])
            self.verify_expected_entities(sensors, ["Humidity", "Use since cleaning", "Target temp reached"])

            # Test climate entity - fan_modes must be strings (regression for DreoACFanMode enum bug)
            ac_ha = dreoairconditioner.DreoAirConditionerHA(pydreo_ac)
            assert ac_ha.fan_modes is not None
            for mode in ac_ha.fan_modes:
                assert isinstance(mode, str), f"fan_modes must contain strings, got {type(mode)}: {mode!r}"
            assert FAN_AUTO in ac_ha.fan_modes
            assert FAN_LOW in ac_ha.fan_modes
            assert FAN_MEDIUM in ac_ha.fan_modes
            assert FAN_HIGH in ac_ha.fan_modes

            # Test set_fan_mode round-trip
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ac_ha.set_fan_mode(FAN_LOW)
                mock_send_command.assert_called_once_with(pydreo_ac, {WINDLEVEL_KEY: DreoACFanMode.LOW})
            pydreo_ac.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: DreoACFanMode.LOW}})
            assert ac_ha.fan_mode == FAN_LOW
