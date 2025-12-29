# Contributing or Developing this Plugin

This section is very much a work in progress.

# Tests
There are three buckets of tests, please feel free to add as appropriate.
* [PyDreo Unit Tests](tests/pydreo/README.md)
    * These tests ensure that the PyDreo library can parse the JSONs correctly for each device we support.
* [Dreo Unit Tests](tests/dreo/README.md) - That do not talk to PyDreo
    * These tests ensure that the Dreo HA code correctly talks to PyDreo.  For these we mock PyDreo.
* [Dreo Integration Tests](tests/dreo/integrationtests/README.md) - That do talk to PyDreo
    * These integration tests ensure that the Dreo HA code gets what we expect from the device JSON files.

# Deploying to Home Assistant

## Quick Deployment Script

The easiest way to deploy the integration to your Home Assistant instance is using the automated deployment script:

```bash
# Basic deployment (Mac only, uses default path /Volumes/Config/custom_components/dreo/)
python3 testScripts/deploy_to_ha.py

# Deploy with DEBUG_TEST_MODE enabled (for testing with local device data)
python3 testScripts/deploy_to_ha.py --debug

# Deploy to custom path
python3 testScripts/deploy_to_ha.py --ha-path /custom/path/to/custom_components/dreo/

# Skip E2E test data generation
python3 testScripts/deploy_to_ha.py --skip-generate
```

**What the deployment script does:**
1. Optionally enables DEBUG_TEST_MODE (if `--debug` flag is used)
2. Generates E2E test data to `testScripts/temp/e2e_test_data/`
3. Copies generated data to `custom_components/dreo/e2e_test_data/`
4. Deploys files to your HA instance using rsync (Mac) or robocopy (Windows - TBD)
5. Automatically restores DEBUG_TEST_MODE to safe state (commented out)

**Platform Support:**
- **macOS**: Uses rsync with optimized parameters
- **Windows**: Placeholder for robocopy (use `--ha-path` to specify path manually)

See [testScripts/README.md](testScripts/README.md) for complete documentation.

## Manual Deployment (macOS)

If you prefer to deploy manually or need more control, you can use rsync directly:

```bash
rsync -rltvz --delete --no-perms --no-owner --inplace \
  --exclude='__pycache__' --exclude='.*' \
  custom_components/dreo/ /Volumes/Config/custom_components/dreo/
```

Replace `/Volumes/Config/` with your mounted SMB share path.

# Debug Test Mode

There is a special mode you can put the integration in that will allow you to pretend you have any device. Please note that enabling this will do the following:
* Temporarily disconnect your integration from the Dreo servers.
* All data will come from JSON files on disk.
* Unit-tests will fail to prevent accidental merge.

## Enabling Debug Test Mode

**Using the deployment script (recommended):**
```bash
python3 testScripts/deploy_to_ha.py --debug
```

**Manual method:**
In [custom_components/dreo/const_debug_test_mode.py](custom_components/dreo/const_debug_test_mode.py), uncomment the line:
```python
# DEBUG_TEST_MODE = True
```

**Important:** Always remember to disable DEBUG_TEST_MODE before committing! The deployment script handles this automatically.

## Configuration

The E2E test data files are located in `custom_components/dreo/e2e_test_data/` when deployed. This directory contains:

1. **get_devices.json** - Contains a JSON blob with a list of all devices. You can add/change devices here, just make sure to update the device count at the top.
2. **Device state files** - Named as `get_device_state_SERIALNUMBER.json`. You'll need one of these for each device in get_devices.json.
3. **Device setting files** - Named as `get_device_setting_SERIALNUMBER_SETTINGNAME.json` (optional, for devices with settings).

### Generating Test Data

E2E test data is generated from the API response files in `tests/pydreo/api_responses/`.

**Using the deployment script (recommended):**
The deployment script automatically generates test data before deploying. To skip generation:
```bash
python3 testScripts/deploy_to_ha.py --skip-generate
```

**Manual generation:**
```bash
python3 testScripts/generateE2ETestData.py
```

This script will:
- Combine all `get_devices_H*.json` and `get_devices_K*.json` files from `tests/pydreo/api_responses/` into a single `get_devices.json`
- Copy all device state files (`get_device_state_*.json`) 
- Copy all device setting files (`get_device_setting_*.json`)
- Output to `testScripts/temp/e2e_test_data/`

**Note about Git:** 
- The `custom_components/dreo/e2e_test_data/` directory is now in `.gitignore` and not committed to the repository
- Test data is generated on-the-fly during deployment
- The GitHub Action for auto-generating E2E test data has been disabled (now runs on `workflow_dispatch` only)

### Workflow

1. Add or update API response files in `tests/pydreo/api_responses/`
2. Run the deployment script with `--debug` flag
3. Test your changes in Home Assistant with the debug mode enabled
4. When satisfied, deploy without `--debug` flag for normal operation

Make sure you have Debug logging enabled in Home Assistant so you can confirm your files are loading correctly.

## Status Updates
TODO

## Getting Network Traces from Dreo App
As of a recent release, Dreo seems to have removed certificate pinning, at least for iOS. That makes all this a bunch easier.

### Setup Fiddler Classic as a Proxy
1. Use Fiddler Classic (http://www.fiddlertool.com) to get a network trace to see what the Dreo app is doing. I won't document here how to setup Fiddler as a proxy or do SSL decryption; Fiddler documentation is pretty good.

