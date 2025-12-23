# GitHub Copilot Instructions for hass-dreo

This document provides guidance for GitHub Copilot when working with the Dreo Smart Device Integration for Home Assistant.

## Project Overview

This is an unofficial Home Assistant custom integration for Dreo brand smart devices (fans, heaters, air conditioners, humidifiers, dehumidifiers, and cookers). The integration communicates with Dreo's cloud API and WebSocket service to control devices.

## Repository Structure

- `custom_components/dreo/` - Main integration code
  - `pydreo/` - Python library for Dreo API communication (embedded)
  - Device-specific files: `dreofan.py`, `dreoheater.py`, `dreohumidifier.py`, etc.
  - `dreobasedevice.py` - Base class for all Dreo devices
  - `config_flow.py` - Configuration flow for Home Assistant
  - `haimports.py` - Home Assistant imports (helps with IDE support)
- `tests/` - Test suite with three levels:
  - `tests/pydreo/` - Unit tests for the PyDreo library
  - `tests/dreo/` - Unit tests for HA integration (mock PyDreo)
  - `tests/dreo/integrationtests/` - Integration tests (use real device JSON)
- `.github/workflows/` - CI/CD workflows

## Coding Standards

### Python Style

- **Python Version**: Target Python 3.13 (as per CI configuration)
- **Line Length**: Maximum 150 characters (configured in pylintrc)
- **Linting**: Use pylint with the provided `pylintrc` configuration
- **Imports**: Follow Home Assistant conventions:
  - Use `from .haimports import *` for HA-specific imports
  - Place third-party imports at the top
  - Use `# pylint: disable=C0415` for conditional imports

### Code Conventions

- Use type hints where appropriate
- Add docstrings for public classes and methods
- Follow Home Assistant's async patterns (use `async def` for async operations)
- Use `_LOGGER.debug()`, `_LOGGER.info()`, `_LOGGER.warning()`, `_LOGGER.error()` for logging
- Device classes should inherit from `DreoBaseDevice`

### Naming Conventions

- Class names: PascalCase (e.g., `DreoFanHA`, `PyDreoFan`)
- Method names: snake_case (e.g., `async_setup_entry`, `handle_coordinator_update`)
- Constants: UPPER_SNAKE_CASE (e.g., `DOMAIN`, `PYDREO_MANAGER`)
- Private methods: prefix with underscore (e.g., `_update_state`)

## Testing

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt
pip install -r requirements.test.txt

# Run all tests
pytest

# Run specific test file
pytest tests/dreo/test_fan.py

# Run with coverage
pytest --cov=custom_components/dreo
```

### Linting

```bash
# Run pylint (errors only, as in CI)
pylint --recursive=yes --reports=yes --disable=W,C,R .

# Run pylint with full checks
pylint --recursive=yes custom_components/dreo
```

### Test Structure

- **Unit tests** should mock external dependencies
- **Integration tests** use JSON files from `e2e_test_data/` directory
- New device support requires corresponding test coverage
- Follow existing test patterns in the repository

## Home Assistant Integration Patterns

### Device Types

The integration supports multiple device types, each mapped to Home Assistant platforms:
- **Fans** → `fan` platform
- **Heaters** → `climate` platform
- **Humidifiers/Dehumidifiers** → `humidifier` platform
- **Lights** (device displays) → `light` platform
- **Switches** (device features) → `switch` platform
- **Sensors** (temperature, humidity) → `sensor` platform
- **Numbers** (adjustable values) → `number` platform

### Adding New Device Support

1. Check device model prefix (e.g., `DR-HTF` for tower fans)
2. Add device type mapping in PyDreo library
3. Create or extend device class (e.g., `PyDreoTowerFan`)
4. Add Home Assistant entity wrapper (e.g., `DreoFanHA`)
5. Add test coverage with device JSON in `e2e_test_data/`
6. Update README.md with supported model

### Configuration Flow

- Users configure via Home Assistant UI (Settings → Devices & Services)
- Credentials are stored in Home Assistant's config entry
- No `configuration.yaml` entries required

## Debug Test Mode

The integration includes a special debug mode for testing without live devices:

- Located in `debug_test_mode.py` and `const_debug_test_mode.py`
- **DO NOT enable in production code** (causes unit test failures)
- Uses JSON files from `custom_components/dreo/e2e_test_data/`
- To enable: Uncomment `DEBUG_TEST_MODE = True` in `custom_components/dreo/const.py`
- See `contributing.md` for detailed usage instructions and configuration

## Common Tasks

### Adding a New Device Model

1. Obtain device JSON from user (via diagnostics or debug logs)
2. Identify device type and capabilities
3. Add device model mapping in the PyDreo library (check existing device files in `custom_components/dreo/pydreo/` for the appropriate location)
4. Create/update device class if needed
5. Add test JSON to `custom_components/dreo/e2e_test_data/`
6. Write integration test in `tests/dreo/integrationtests/`
7. Update README.md with the new supported model

### Fixing a Bug

1. Add test that reproduces the bug
2. Fix the issue with minimal changes
3. Ensure all tests pass
4. Run pylint to check for issues
5. Update relevant documentation if needed

### Updating Dependencies

- `requirements.txt` - Runtime dependencies (minimal)
- `requirements.test.txt` - Test-only dependencies
- `custom_components/dreo/manifest.json` - HA integration manifest
- Test after dependency updates

## CI/CD Workflows

- **CI Validation** (`ci.yaml`) - Runs on PRs and pushes to main/beta
  - Executes pytest suite
  - Runs pylint (errors only)
- **HACS Validation** (`hacs_validate.yaml`) - Validates HACS compatibility
- **Hassfest** (`hassfest.yaml`) - Validates Home Assistant integration
- **Release** (`release.yaml`) - Automated release process

## Important Notes

### Security

- Never commit credentials or API keys
- Use Home Assistant's config entry for sensitive data
- Redact sensitive information in debug logs

### WebSocket Connection

- Integration maintains a WebSocket connection to Dreo servers
- Auto-reconnect is configurable via integration options
- Handle connection failures gracefully

### Device Updates

- Devices send state updates via WebSocket
- Use Home Assistant's coordinator pattern for state management
- Throttle frequent updates to avoid performance issues

### Documentation

- Keep README.md updated with supported devices
- Add inline comments for complex logic
- Update RELEASE.md for version changes

## Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [PyDreo Library](custom_components/dreo/pydreo/) (embedded in this repo)
- [Contributing Guide](contributing.md)
- [GitHub Issues](https://github.com/JeffSteinbok/hass-dreo/issues)

## Best Practices for Copilot

- Focus on minimal, surgical changes
- Follow existing patterns in the codebase
- Run tests after changes
- Check pylint before committing
- Update documentation when adding features
- Use existing device classes as templates for new devices
- Test with debug mode when possible before requesting user testing
