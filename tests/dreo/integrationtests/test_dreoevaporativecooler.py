"""Integration Tests for Dreo Evaporative Coolers"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from custom_components.dreo import fan
from custom_components.dreo import light
from custom_components.dreo import number
from custom_components.dreo import select
from custom_components.dreo import sensor
from custom_components.dreo import switch
from .imports import *  # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_SCHEDULE_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestDreoEvaporativeCoolers(IntegrationTestBase):
    """Test Dreo Evaporative Coolers Fan class and PyDreo together."""

    def test_HEC002S(self):  # pylint: disable=invalid-name
        """Load air conditioner and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HEC002S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_ec = self.pydreo_manager.devices[0]
            assert pydreo_ec.type == "Evaporative Cooler"
            assert pydreo_ec.model == "DR-HEC002S"

            ha_fan = fan.DreoFanHA(pydreo_ec)
            assert ha_fan.is_on is False
            assert ha_fan.speed_count == 4
            assert ha_fan.unique_id is not None
            assert ha_fan.name is not None

            # Verify speed range
            assert pydreo_ec.speed_range == (1, 4)

            # Test percentage calculation when off
            if ha_fan.is_on:
                assert ha_fan.percentage >= 0 and ha_fan.percentage <= 100

            # Check preset modes if available
            if hasattr(pydreo_ec, "preset_modes") and pydreo_ec.preset_modes:
                assert len(pydreo_ec.preset_modes) > 0

            numbers = number.get_entries([pydreo_ec])
            self.verify_expected_entities(numbers, ["Target Humidity"])

            sensors = sensor.get_entries([pydreo_ec])
            self.verify_expected_entities(sensors, ["Temperature", "Humidity", "Use since cleaning"])

    def test_HEC006S(self):  # pylint: disable=invalid-name
        """Load HEC006S (TurboCool Misting Fan 516S) and test sending commands."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HEC006S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_ec = self.pydreo_manager.devices[0]
            assert pydreo_ec.type == "Evaporative Cooler"
            assert pydreo_ec.model == "DR-HEC006S"

            ha_fan = fan.DreoFanHA(pydreo_ec)
            assert ha_fan.is_on is True
            assert ha_fan.speed_count == 6
            assert ha_fan.unique_id is not None
            assert ha_fan.name is not None

            # Verify speed range
            assert pydreo_ec.speed_range == (1, 6)

            # Test percentage calculation when on
            assert ha_fan.percentage >= 0 and ha_fan.percentage <= 100

            # Check preset modes
            assert pydreo_ec.preset_modes == ["Normal", "Turbo"]
            assert len(pydreo_ec.preset_modes) == 2

            numbers = number.get_entries([pydreo_ec])
            self.verify_expected_entities(numbers, ["Fog Level", "Horizontal Angle", "Target Humidity"])

            sensors = sensor.get_entries([pydreo_ec])
            self.verify_expected_entities(sensors, ["Temperature", "Humidity", "Use since cleaning"])

            switches = switch.get_entries([pydreo_ec])
            self.verify_expected_entities(switches, ["Child Lock", "Display Light", "Humidify", "Misting", "Panel Sound"])

            lights = light.get_entries([pydreo_ec])
            self.verify_expected_entities(lights, ["Ambient Light"])

            selects = select.get_entries([pydreo_ec])
            self.verify_expected_entities(selects, ["Ambient Light Mode"])
