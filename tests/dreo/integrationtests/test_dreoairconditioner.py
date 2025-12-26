"""Integration Tests for Dreo Ceiling Fans"""
# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import number, sensor, dreoairconditioner
from homeassistant.components.climate import HVACMode
from  .imports import * # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_SCHEDULE_UPDATE_HA_STATE= f'{PATCH_BASE_PATH}.schedule_update_ha_state'

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
            assert pydreo_ac.type == 'Air Conditioner'

            numbers = number.get_entries([pydreo_ac])
            self.verify_expected_entities(numbers, ["Target Humidity"])

            sensors = sensor.get_entries([pydreo_ac])
            self.verify_expected_entities(sensors, ['Humidity', 'Target temp reached', 'Use since cleaning'])

    def test_HAC006S(self):  # pylint: disable=invalid-name
        """Load air conditioner and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):

            self.get_devices_file_name = "get_devices_HAC006S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_ac = self.pydreo_manager.devices[0]
            assert pydreo_ac.type == 'Air Conditioner'

            numbers = number.get_entries([pydreo_ac])
            self.verify_expected_entities(numbers, ["Target Humidity"])

            sensors = sensor.get_entries([pydreo_ac])
            self.verify_expected_entities(sensors, ["Humidity", "Use since cleaning", "Target temp reached"])

    def test_HAC006S_hvac_modes(self):  # pylint: disable=invalid-name
        """Test that HVAC modes are properly exposed for DR-HAC006S."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HAC006S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_ac = self.pydreo_manager.devices[0]
            assert pydreo_ac.type == 'Air Conditioner'

            # Create the HA climate entity
            ac_ha = dreoairconditioner.DreoAirConditionerHA(pydreo_ac)
            
            # Verify that hvac_modes contains only valid HVACMode values
            assert ac_ha.hvac_modes is not None
            assert isinstance(ac_ha.hvac_modes, list)
            assert len(ac_ha.hvac_modes) > 0
            
            # All HVAC modes should be proper HVACMode enum values
            valid_hvac_modes = [HVACMode.OFF, HVACMode.COOL, HVACMode.DRY, HVACMode.FAN_ONLY, 
                               HVACMode.HEAT, HVACMode.AUTO, HVACMode.HEAT_COOL]
            for mode in ac_ha.hvac_modes:
                assert mode in valid_hvac_modes, f"Invalid HVAC mode: {mode}"
            
            # Check that we have the expected modes for an air conditioner
            assert HVACMode.COOL in ac_ha.hvac_modes
            assert HVACMode.DRY in ac_ha.hvac_modes
            assert HVACMode.FAN_ONLY in ac_ha.hvac_modes
            assert HVACMode.OFF in ac_ha.hvac_modes
            
            # These modes should NOT be present for an AC (they're heater modes)
            assert "coolair" not in ac_ha.hvac_modes
            assert "hotair" not in ac_ha.hvac_modes
            assert "eco" not in ac_ha.hvac_modes

