# Dreo Home Assistant UI Testing

This directory contains end-to-end UI tests for the Dreo Home Assistant integration using [Playwright](https://playwright.dev/).

## Overview

The UI test suite allows you to test the Dreo integration against a real Home Assistant instance. Tests interact with the Home Assistant web interface to verify that device controls, sensors, and other features work correctly from the user's perspective.

**Key Feature:** Tests are organized by **device model** (e.g., HAF001S, HHM001S) and map directly to the e2e test data files, making it easy to verify specific device functionality.

## Directory Structure

```
tests/dreo/ui/
├── README.md                 # This file
├── playwright.config.js      # Playwright configuration
├── package.json             # Node.js dependencies
├── config/                  # Configuration files
│   ├── __init__.py
│   ├── test_config.example.py  # Example configuration (copy and modify)
│   └── .gitignore           # Prevents committing sensitive data
├── pages/                   # Page Object Model classes
│   ├── __init__.py
│   ├── base_page.py        # Base page class
│   ├── login_page.py       # Login page object
│   └── device_page.py      # Device control page objects
└── tests/                   # Test files (organized by model)
    ├── __init__.py
    ├── conftest.py         # Pytest fixtures
    ├── test_HAF001S.py     # Tower Fan DR-HTF001S tests
    ├── test_HHM001S.py     # Humidifier DR-HHM001S tests
    ├── test_HHM014S.py     # Humidifier DR-HHM014S tests
    └── ...                 # Additional model-specific tests
```

## Prerequisites

1. **Node.js and npm** - Required for Playwright
   ```bash
   # macOS
   brew install node
   
   # Ubuntu/Debian
   sudo apt install nodejs npm
   ```

2. **Python 3.9+** - For running Python-based tests

3. **Running Home Assistant instance** with the Dreo integration installed and configured

4. **Dreo devices** added to your Home Assistant instance

## Installation

### 1. Install Node.js Dependencies

From the `tests/dreo/ui` directory:

```bash
npm install
```

### 2. Install Playwright Browsers

```bash
npx playwright install chromium
```

For other browsers:
```bash
npx playwright install  # Installs all browsers
```

### 3. Configure Test Settings

Copy the example configuration file:

```bash
cp config/test_config.example.py config/test_config.py
```

Edit `config/test_config.py` with your Home Assistant details:

```python
# Home Assistant URL
HA_URL = "http://192.168.1.100:8123"  # Your HA URL

# Option 1: Username and password
HA_USERNAME = "your-username"
HA_PASSWORD = "your-password"

# Option 2: Long-lived access token (recommended)
HA_ACCESS_TOKEN = "your-long-lived-token"
```

**Then** edit `config/models.py` to map models to your actual device names:

```python
# Map device models to your actual device names in Home Assistant
MODEL_DEVICES = {
    # Only configure the models you have - set others to None
    "HAF001S": "Living Room Tower Fan",       # DR-HTF001S
    "HHM001S": "Master Bedroom Humidifier",   # DR-HHM001S
    "HHM014S": "Kids Room Humidifier",        # DR-HHM014S
    "HSH003S": None,                          # Don't have this model
    # ... configure as needed
}
```

**Important:** 
- Never commit `test_config.py` - it's already in `.gitignore`
- `models.py` can be committed and shared (no sensitive data)
- Only tests for configured models (non-None values) will run
- Tests for unconfigured models are automatically skipped

### 4. Create a Long-Lived Access Token (Recommended)

Using an access token is more secure than username/password:

1. Log into Home Assistant
2. Click your profile (bottom left)
3. Scroll to "Security" section
4. Click "Create Token" under "Long-Lived Access Tokens"
5. Give it a name (e.g., "UI Tests")
6. Copy the token and add it to `test_config.py`

## Running Tests

### Run All Tests

```bash
# From tests/dreo/ui directory
npx playwright test
```

### Run Specific Test File

```bash
# Test a specific model
npx playwright test tests/test_HAF001S.py
npx playwright test tests/test_HHM001S.py
```

### Run in Headed Mode (See Browser)

```bash
npx playwright test --headed
```

### Run in Debug Mode

```bash
npx playwright test --debug
```

### Run Specific Test

```bash
# Run a specific test by name
npx playwright test -g "test_power_toggle"

# Run all tests for a specific model
npx playwright test -g "TestHAF001S"
```

### View Test Report

```bash
npx playwright show-report
```

## Using Environment Variables

You can override configuration values using environment variables:

```bash
# Set HA URL
export HA_URL="http://192.168.1.100:8123"

# Run tests
npx playwright test
```

Or inline:

```bash
HA_URL="http://homeassistant.local:8123" npx playwright test
```

## Writing Tests

### Test Organization

Tests are organized by **device model** matching the e2e test data:

- `test_HAF001S.py` - Tower Fan DR-HTF001S (based on `get_device_state_HAF001S_1.json`)
- `test_HHM001S.py` - Humidifier DR-HHM001S (based on `get_device_state_HHM001S_1.json`)
- `test_HHM014S.py` - Humidifier DR-HHM014S (based on `get_device_state_HHM014S_1.json`)
- etc.

### Test Structure

Each model test file includes:
1. **E2E data reference** in the docstring
2. **Feature list** from the e2e data
3. **Model configuration check** - tests are skipped if model not configured
4. **Test methods** for each feature

Example:

```python
"""
UI tests for Dreo HAF001S Tower Fan.
Based on e2e test data: get_device_state_HAF001S_1.json

Model: DR-HTF001S
Features from e2e data:
- Power on/off (poweron)
- Wind level 1-4 (windlevel)
- Mode: Normal, Natural, Sleep, Auto
- Oscillation (shakehorizon)
- Temperature sensor
"""

MODEL = "HAF001S"
DEVICE_NAME = MODEL_DEVICES.get(MODEL)

# Skip if not configured
pytestmark = pytest.mark.skipif(
    DEVICE_NAME is None,
    reason=f"Model {MODEL} not configured"
)

class TestHAF001S:
    def test_power_toggle(self, logged_in_page: Page):
        """Test power on/off."""
        fan_page = DreoFanPage(logged_in_page, HA_URL)
        fan_page.navigate_to_device(DEVICE_NAME)
        
        fan_page.turn_off_device(DEVICE_NAME)
        fan_page.turn_on_device(DEVICE_NAME)
```

### Adding Tests for New Models

1. **Check e2e data**: Look at `custom_components/dreo/e2e_test_data/get_device_state_<MODEL>_1.json`
2. **Create test file**: `tests/test_<MODEL>.py`
3. **Document features**: List features from e2e data in docstring
4. **Write tests**: One test per feature
5. **Configure model**: Add to `MODEL_DEVICES` in `test_config.py`

### Using Fixtures

The `logged_in_page` fixture automatically logs you into Home Assistant:

```python
def test_something(logged_in_page: Page):
    # Page is already logged in
    device_page = DevicePage(logged_in_page, HA_URL)
    # ... rest of test
```

### Page Objects

Page objects abstract the UI interactions:

- **`LoginPage`** - Handles login
- **`DevicePage`** - Base class for device interactions
- **`DreoFanPage`** - Fan-specific actions
- **`DreoHumidifierPage`** - Humidifier-specific actions
- **`DreoHeaterPage`** - Heater-specific actions

## Test Data

Tests are mapped 1:1 with e2e test data files in `custom_components/dreo/e2e_test_data/`:

| Model | File | Device Type | Test File |
|-------|------|-------------|-----------|
| HAF001S | get_device_state_HAF001S_1.json | Tower Fan | test_HAF001S.py |
| HAF004S | get_device_state_HAF004S_1.json | Tower Fan | test_HAF004S.py |
| HTF005S | get_device_state_HTF005S_1.json | Tower Fan | test_HTF005S.py |
| HHM001S | get_device_state_HHM001S_1.json | Humidifier | test_HHM001S.py |
| HHM014S | get_device_state_HHM014S_1.json | Humidifier | test_HHM014S.py |
| HSH003S | get_device_state_HSH003S_1.json | Heater | test_HSH003S.py |
| WH714S | get_device_state_WH714S_1.json | Heater | test_WH714S.py |
| ... | ... | ... | ... |

Each test file:
1. References the specific e2e data file in its docstring
2. Documents the features available from that data
3. Tests those specific features against a real device
4. Is automatically skipped if the model isn't configured

This makes it easy to:
- **Verify new models**: Add e2e data → create test file → configure device → run tests
- **Test specific features**: Each test method corresponds to a feature in the e2e data
- **Maintain tests**: When e2e data changes, update the corresponding test file

## Troubleshooting

### Login Fails

- Verify `HA_URL` is correct and accessible
- Check username/password or access token
- Ensure Home Assistant is running
- Try accessing the URL in a browser first

### Device Not Found

- Verify device name in `MODEL_DEVICES` matches exactly (case-sensitive)
- Check the model key matches the e2e test data file name (e.g., HAF001S for get_device_state_HAF001S_1.json)
- Ensure device is configured and online in Home Assistant
- Device should be connected and responding

### Timeout Errors

- Increase timeout in `playwright.config.js`:
  ```javascript
  use: {
    actionTimeout: 30000,  // 30 seconds
    navigationTimeout: 60000,  // 60 seconds
  }
  ```

### Tests Pass Locally but Fail in CI

- Use headless mode in CI: `npx playwright test --reporter=list`
- Ensure Home Assistant is accessible from CI environment
- Consider using a dedicated test instance

### Certificate Errors (HTTPS)

If using HTTPS with self-signed certificates, the config already ignores HTTPS errors. If you need more control:

```python
# In conftest.py, modify browser_context_args fixture
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "ignore_https_errors": True,
    }
```

## Best Practices

1. **Use Page Objects** - Keep selectors and actions in page classes
2. **Add Waits** - Let elements load before interacting
3. **Test One Thing** - Each test should verify one behavior
4. **Clean Up** - Reset device state if needed between tests
5. **Use Fixtures** - Share common setup code
6. **Descriptive Names** - Test names should describe what they test
7. **Reference E2E Data** - Document which e2e data file the test is based on
8. **Model-Specific Tests** - Create separate test files per model
9. **Auto-Skip** - Use `pytestmark` to skip tests for unconfigured models
10. **Feature Comments** - Reference e2e data keys in test comments (e.g., `# E2E: poweron`)

## CI/CD Integration

### GitHub Actions Example

```yaml
name: UI Tests

on: [push, pull_request]

jobs:
  ui-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        working-directory: tests/dreo/ui
        run: |
          npm ci
          npx playwright install chromium
      
      - name: Run tests
        working-directory: tests/dreo/ui
        env:
          HA_URL: ${{ secrets.HA_URL }}
          HA_ACCESS_TOKEN: ${{ secrets.HA_ACCESS_TOKEN }}
        run: npx playwright test
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: tests/dreo/ui/playwright-report/
```

## Further Reading

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Python](https://playwright.dev/python/)
- [Page Object Model Pattern](https://playwright.dev/docs/pom)
- [Home Assistant Frontend](https://www.home-assistant.io/developers/frontend/)

## CoAdd model to `models.py`** with `None` as default value
3. **Create model test file** in `tests/` (e.g., `test_HAF004S.py`)
4. **Document features** from e2e data in file docstring
5. **Add page objects** for new device types if needed in `pages/`
6. **Configure your test device** in `models.py` locally
7. **Test locally** with your actual device before submitting
8. **Update this README** if adding new testing patterns or page objects
9. **Commit `models.py`** but NOT `test_config.py`
3. **Document features** from e2e data in file docstring
4. **Add page objects** for new device types if needed in `pages/`
5. **Update MODEL_DEVICES** in `test_config.example.py` with the new model
6. **Test locally** with your actual device before submitting
7. **Update this README** if adding new testing patterns or page objects

### Test File Template

```python
"""
UI tests for Dreo <MODEL> <Device Type>.
Based on e2e test data: get_device_state_<MODEL>_1.json

Model: DR-<MODEL>
Features from e2e data:
- Feature 1 (e2e_key_1)
- Feature 2 (e2e_key_2)
"""
import pytest
from playwright.sync_api import Page
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pages.login_page import LoginPage
from pages.device_page import DreoDevicePage
from config import HA_URL, HA_USERNAME, HA_PASSWORD, HA_ACCESS_TOKEN, MODEL_DEVICES

MODEL = "<MODEL>"
DEVICE_NAME = MODEL_DEVICES.get(MODEL)

@pytest.fixture(scope="function")
def logged_in_page(page: Page):
    login_page = LoginPage(page, HA_URL)
    login_page.navigate()
    
    if HA_ACCESS_TOKEN:
        login_page.login_with_token(HA_ACCESS_TOKEN)
    else:
        login_page.login(HA_USERNAME, HA_PASSWORD)
    
    assert login_page.is_logged_in()
    yield page

pytestmark = pytest.mark.skipif(
    DEVICE_NAME is None,
    reason=f"Model {MODEL} not configured"
)

class Test<MODEL>:
    def test_feature(self, logged_in_page: Page):
        # Your test here
        pass
```

## Support

For issues with:
- **Playwright**: Check [Playwright Docs](https://playwright.dev/)
- **Dreo Integration**: Open an issue on [GitHub](https://github.com/JeffSteinbok/hass-dreo/issues)
- **Home Assistant**: See [HA Community](https://community.home-assistant.io/)
