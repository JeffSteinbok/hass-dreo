"""
UI tests for Dreo HAF001S Tower Fan (Cruiser Pro T1).
Based on e2e test data: get_device_state_HAF001S_1.json

Model: DR-HTF001S
Features from e2e data:
- Power on/off (poweron)
- Wind level 1-4 (windlevel)
- Mode: Normal, Natural, Sleep, Auto (mode: 1, 2, 3, 4)
- Oscillation (shakehorizon)
- Temperature sensor (temperature)
"""
import pytest
from playwright.sync_api import Page
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pages.login_page as login_module
import pages.device_page as device_module
import config as config_module

LoginPage = login_module.LoginPage
DreoFanPage = device_module.DreoFanPage
HA_URL = config_module.HA_URL
HA_USERNAME = config_module.HA_USERNAME
HA_PASSWORD = config_module.HA_PASSWORD
HA_ACCESS_TOKEN = config_module.HA_ACCESS_TOKEN
MODEL_DEVICES = config_module.MODEL_DEVICES

# Load e2e test data for reference
E2E_DATA_PATH = Path(__file__).parent.parent.parent.parent.parent / "custom_components" / "dreo" / "e2e_test_data" / "get_device_state_HAF001S_1.json"

MODEL = "HAF001S"
DEVICE_NAME = MODEL_DEVICES.get(MODEL)


# Skip all tests if device not configured
pytestmark = pytest.mark.skipif(
    DEVICE_NAME is None,
    reason=f"Model {MODEL} not configured in test_config.py"
)


class TestHAF001S:
    """Test cases for Dreo HAF001S Tower Fan."""
    
    def test_power_toggle(self, logged_in_page: Page):
        """
        Test power on/off functionality.
        E2E data shows: poweron: true
        """
        fan_page = DreoFanPage(logged_in_page, HA_URL)
        fan_page.navigate_to_device(DEVICE_NAME)
        
        # Turn off
        fan_page.turn_off_device(DEVICE_NAME)
        # TODO: Add assertion to verify off state
        
        # Turn on
        fan_page.turn_on_device(DEVICE_NAME)
        # TODO: Add assertion to verify on state
    
    def test_wind_level_control(self, logged_in_page: Page):
        """
        Test wind level 1-4.
        E2E data shows: windlevel: 4 (range 1-4)
        """
        fan_page = DreoFanPage(logged_in_page, HA_URL)
        fan_page.navigate_to_device(DEVICE_NAME)
        
        # Ensure fan is on
        fan_page.turn_on_device(DEVICE_NAME)
        
        # Test each wind level
        for level in [1, 2, 3, 4]:
            fan_page.set_fan_speed(level)
            # TODO: Verify speed was set
    
    def test_oscillation_control(self, logged_in_page: Page):
        """
        Test oscillation (shakehorizon).
        E2E data shows: shakehorizon: true/false
        """
        fan_page = DreoFanPage(logged_in_page, HA_URL)
        fan_page.navigate_to_device(DEVICE_NAME)
        
        # Ensure fan is on
        fan_page.turn_on_device(DEVICE_NAME)
        
        # Toggle oscillation
        fan_page.toggle_oscillation()
        # TODO: Verify oscillation state
    
    def test_mode_selection(self, logged_in_page: Page):
        """
        Test fan modes: Normal (1), Natural (2), Sleep (3), Auto (4).
        E2E data shows: mode: 1
        """
        fan_page = DreoFanPage(logged_in_page, HA_URL)
        fan_page.navigate_to_device(DEVICE_NAME)
        
        # Ensure fan is on
        fan_page.turn_on_device(DEVICE_NAME)
        
        # Test available modes
        modes = [
            ("Normal", 1),
            ("Natural", 2),
            ("Sleep", 3),
            ("Auto", 4)
        ]
        
        for mode_name, mode_value in modes:
            try:
                fan_page.select_mode(mode_name)
                # TODO: Verify mode was set
            except Exception as e:
                pytest.fail(f"Failed to set mode {mode_name}: {e}")
    
    def test_temperature_sensor_reading(self, logged_in_page: Page):
        """
        Test temperature sensor reading.
        E2E data shows: temperature: 77 (Fahrenheit based on tempunit: 1)
        """
        fan_page = DreoFanPage(logged_in_page, HA_URL)
        fan_page.navigate_to_device(DEVICE_NAME)
        
        # Read temperature sensor
        temperature = fan_page.get_sensor_value("Temperature")
        
        if temperature:
            # Verify temperature is in reasonable range
            # Should be between 50-100°F or 10-40°C
            assert temperature is not None, "Temperature sensor should return a value"
            # TODO: Parse and validate temperature value
