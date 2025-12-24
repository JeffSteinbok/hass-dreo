"""
Shared fixtures for UI tests.
"""
import pytest
from playwright.sync_api import Page
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import page objects and config
import pages.login_page as login_module
import config as config_module

LoginPage = login_module.LoginPage
HA_URL = config_module.HA_URL
HA_USERNAME = config_module.HA_USERNAME
HA_PASSWORD = config_module.HA_PASSWORD
HA_ACCESS_TOKEN = config_module.HA_ACCESS_TOKEN


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context with additional settings."""
    return {
        **browser_context_args,
        "viewport": {
            "width": 1920,
            "height": 1080,
        },
        "ignore_https_errors": True,  # For self-signed certificates
    }


@pytest.fixture(scope="function")
def logged_in_page(page: Page):
    """
    Fixture that provides a logged-in Home Assistant page.
    Use this in your tests instead of manually handling login.
    """
    print(f"\n=== Login Fixture Starting ===")
    print(f"HA_URL: {HA_URL}")
    print(f"HA_USERNAME: {HA_USERNAME}")
    print(f"HA_ACCESS_TOKEN: {'<set>' if HA_ACCESS_TOKEN else '<not set>'}")
    
    login_page = LoginPage(page, HA_URL)
    
    print("Navigating to login page...")
    login_page.navigate()
    
    if HA_ACCESS_TOKEN:
        print("Logging in with access token...")
        login_page.login_with_token(HA_ACCESS_TOKEN)
    else:
        print("Logging in with username/password...")
        login_page.login(HA_USERNAME, HA_PASSWORD)
    
    print("Checking if logged in...")
    assert login_page.is_logged_in(), "Failed to login to Home Assistant"
    
    print("=== Login Successful ===\n")
    yield page
    
    # Cleanup after test
    # page.close()  # Playwright handles this automatically
