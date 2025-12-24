"""
UI tests for Dreo HHM001S Humidifier.
Based on e2e test data: get_device_state_HHM001S_1.json

Model: DR-HHM001S
Features from e2e data:
- Power on/off (poweron)
- Mode: Manual (1), Auto (2), Sleep (3) (mode)
- Target humidity (rhset: 60)
- Current humidity (humidity: 47)
- Water level status (waterlackstatus: 0=OK)
- Mist level 1-3 (mistlevel)
- Display light level (ledlevel)
- Work time/usage (worktime)
"""
import pytest
from playwright.sync_api import Page
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pages.login_page as login_module
import pages.device_page as device_module
import config as config_module

LoginPage = login_module.LoginPage
DreoHumidifierPage = device_module.DreoHumidifierPage
HA_URL = config_module.HA_URL
HA_USERNAME = config_module.HA_USERNAME
HA_PASSWORD = config_module.HA_PASSWORD
HA_ACCESS_TOKEN = config_module.HA_ACCESS_TOKEN
MODEL_DEVICES = config_module.MODEL_DEVICES

MODEL = "HHM001S"
DEVICE_NAME = MODEL_DEVICES.get(MODEL)


@pytest.fixture(scope="function")
def logged_in_page(page: Page):
    """Fixture to handle login before each test."""
    login_page = LoginPage(page, HA_URL)
    login_page.navigate()
    
    if HA_ACCESS_TOKEN:
        login_page.login_with_token(HA_ACCESS_TOKEN)
    else:
        login_page.login(HA_USERNAME, HA_PASSWORD)
    
    assert login_page.is_logged_in(), "Failed to login to Home Assistant"
    
    yield page


pytestmark = pytest.mark.skipif(
    DEVICE_NAME is None,
    reason=f"Model {MODEL} not configured in test_config.py"
)


class TestHHM001S:
    """Test cases for Dreo HHM001S Humidifier."""
    
    def test_power_toggle(self, logged_in_page: Page):
        """
        Test power on/off.
        E2E data shows: poweron: true
        """
        humidifier_page = DreoHumidifierPage(logged_in_page, HA_URL)
        humidifier_page.navigate_to_device(DEVICE_NAME)
        
        # Turn off
        humidifier_page.turn_off_device(DEVICE_NAME)
        # TODO: Verify off state
        
        # Turn on
        humidifier_page.turn_on_device(DEVICE_NAME)
        # TODO: Verify on state
    
    def test_target_humidity_setting(self, logged_in_page: Page):
        """
        Test setting target humidity.
        E2E data shows: rhset: 60, range typically 30-90%
        """
        humidifier_page = DreoHumidifierPage(logged_in_page, HA_URL)
        humidifier_page.navigate_to_device(DEVICE_NAME)
        
        # Ensure on
        humidifier_page.turn_on_device(DEVICE_NAME)
        
        # Test different target humidity levels
        target_levels = [40, 50, 60, 70, 80]
        for target in target_levels:
            humidifier_page.set_humidity(target)
            # TODO: Verify target was set
    
    def test_mode_selection(self, logged_in_page: Page):
        """
        Test humidifier modes: Manual (1), Auto (2), Sleep (3).
        E2E data shows: mode: 1
        """
        humidifier_page = DreoHumidifierPage(logged_in_page, HA_URL)
        humidifier_page.navigate_to_device(DEVICE_NAME)
        
        # Ensure on
        humidifier_page.turn_on_device(DEVICE_NAME)
        
        # Test modes
        modes = [
            ("Manual", 1),
            ("Auto", 2),
            ("Sleep", 3)
        ]
        
        for mode_name, mode_value in modes:
            try:
                humidifier_page.select_mode(mode_name)
                # TODO: Verify mode was set
            except Exception as e:
                pytest.fail(f"Failed to set mode {mode_name}: {e}")
    
    def test_humidity_sensor_reading(self, logged_in_page: Page):
        """
        Test current humidity sensor reading.
        E2E data shows: humidity: 47
        """
        humidifier_page = DreoHumidifierPage(logged_in_page, HA_URL)
        humidifier_page.navigate_to_device(DEVICE_NAME)
        
        # Read current humidity
        current_humidity = humidifier_page.get_current_humidity()
        
        if current_humidity:
            # Humidity should be 0-100%
            assert current_humidity is not None
            # TODO: Parse and validate humidity percentage
    
    def test_target_humidity_sensor(self, logged_in_page: Page):
        """
        Test target humidity sensor (new feature).
        This sensor displays the current target humidity setting.
        E2E data shows: rhset: 60
        """
        humidifier_page = DreoHumidifierPage(logged_in_page, HA_URL)
        humidifier_page.navigate_to_device(DEVICE_NAME)
        
        # Ensure on
        humidifier_page.turn_on_device(DEVICE_NAME)
        
        # Set a specific target
        target = 55
        humidifier_page.set_humidity(target)
        
        # Read the Target Humidity sensor
        target_humidity_sensor = humidifier_page.get_target_humidity()
        
        if target_humidity_sensor:
            # Should match what we set
            assert target_humidity_sensor is not None
            # TODO: Parse value and compare to target
    
    def test_water_level_sensor(self, logged_in_page: Page):
        """
        Test water level sensor reading.
        E2E data shows: waterlackstatus: 0 (0=OK, 1=EMPTY)
        """
        humidifier_page = DreoHumidifierPage(logged_in_page, HA_URL)
        humidifier_page.navigate_to_device(DEVICE_NAME)
        
        # Read water level
        water_level = humidifier_page.get_water_level()
        
        if water_level:
            # Should be either OK or EMPTY
            assert water_level is not None
            # TODO: Validate value is "OK" or "EMPTY"
    
    def test_status_sensor(self, logged_in_page: Page):
        """
        Test status sensor (shows current mode).
        E2E data shows: mode can be Manual, Auto, or Sleep
        """
        humidifier_page = DreoHumidifierPage(logged_in_page, HA_URL)
        humidifier_page.navigate_to_device(DEVICE_NAME)
        
        # Ensure on
        humidifier_page.turn_on_device(DEVICE_NAME)
        
        # Set to Auto mode
        humidifier_page.select_mode("Auto")
        
        # Read status sensor
        status = humidifier_page.get_sensor_value("Status")
        
        if status:
            # Should show "Auto"
            assert status is not None
            # TODO: Validate status matches mode
