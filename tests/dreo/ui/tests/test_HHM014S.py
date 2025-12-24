"""
UI tests for Dreo HHM014S Humidifier (HM774S).
Based on e2e test data: get_device_state_HHM014S_1.json

Model: DR-HHM014S / HM774S
Features similar to HHM001S with potential variations.
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

MODEL = "HHM014S"
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


class TestHHM014S:
    """Test cases for Dreo HHM014S Humidifier."""
    
    def test_power_toggle(self, logged_in_page: Page):
        """Test power on/off."""
        humidifier_page = DreoHumidifierPage(logged_in_page, HA_URL)
        humidifier_page.navigate_to_device(DEVICE_NAME)
        
        humidifier_page.turn_off_device(DEVICE_NAME)
        humidifier_page.turn_on_device(DEVICE_NAME)
    
    def test_target_humidity_setting(self, logged_in_page: Page):
        """Test setting target humidity levels."""
        humidifier_page = DreoHumidifierPage(logged_in_page, HA_URL)
        humidifier_page.navigate_to_device(DEVICE_NAME)
        
        humidifier_page.turn_on_device(DEVICE_NAME)
        
        # Test setting target humidity
        for target in [45, 55, 65]:
            humidifier_page.set_humidity(target)
    
    def test_mode_selection(self, logged_in_page: Page):
        """Test humidifier mode selection."""
        humidifier_page = DreoHumidifierPage(logged_in_page, HA_URL)
        humidifier_page.navigate_to_device(DEVICE_NAME)
        
        humidifier_page.turn_on_device(DEVICE_NAME)
        
        for mode in ["Manual", "Auto", "Sleep"]:
            try:
                humidifier_page.select_mode(mode)
            except Exception as e:
                pytest.fail(f"Failed to set mode {mode}: {e}")
    
    def test_all_sensors(self, logged_in_page: Page):
        """Test reading all sensor values."""
        humidifier_page = DreoHumidifierPage(logged_in_page, HA_URL)
        humidifier_page.navigate_to_device(DEVICE_NAME)
        
        # Read various sensors
        current_humidity = humidifier_page.get_current_humidity()
        target_humidity = humidifier_page.get_target_humidity()
        water_level = humidifier_page.get_water_level()
        
        # At least current humidity should be available
        assert current_humidity is not None or target_humidity is not None
