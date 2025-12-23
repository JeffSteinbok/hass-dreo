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

# Debug Test Mode
There is a special mode you can put the integration in that will allow you to pretend you have any device. Please note that enabling this will do the following:
* Temporarily disconnect your integration from the Dreo servers.
* All data will come from JSON files on disk.
* Unit-tests will fail to prevent accidental merge.

## Enabling
In [custom_components/dreo/const.py](custom_components/dreo/const.py), uncomment the line:
```
# DEBUG_TEST_MODE = True
```

## Configuration
In [custom_components/dreo/e2e_test_data](custom_components/dreo/e2e_test_data), you'll find 2 types of files containing content as they would be returned from the Dreo server.

1. [custom_components/dreo/e2e_test_data/get_devices.json](get_devices.json) which contains a JSON blob containing a list of all devices. You can add/change anything in here, just make sure to update the device count at the top. For each device, you'll need a state file - see next point.
1. Device state files, named as SERIALNUMBER.json. You'll need one of these for each device.

### Generating Test Data
To generate the e2e test data files from the test API responses, run:
```bash
python testScripts/generateE2ETestData.py
```

This script will:
- Combine all `get_devices_H*.json` and `get_devices_K*.json` files from `tests/pydreo/api_responses/` into a single `get_devices.json`
- Copy all device state files (`get_device_settings_*.json`) to the e2e_test_data directory
- Update the device count automatically

Make sure you have Debug logging enabled as well so you can confirm your files are loading correctly.

Simply edit the necessary files, and copy them over to your HA server and you're good to go.

### Deploying to Home Assistant Server (macOS)
To sync Python files from your local development machine to your Home Assistant server via SMB share on macOS:

```bash
rsync -rltvz --delete --no-perms --no-owner --inplace \
  --include='*/' --include='*.py' --exclude='*' \
  --exclude='__pycache__' --exclude='.*' \
  custom_components/dreo/ /Volumes/YOUR_SHARE_NAME/custom_components/dreo/
```
Replace `/Volumes/YOUR_SHARE_NAME/` with your mounted SMB share path (typically `/Volumes/Config/` for HA config shares).

## Status Updates
TODO

## Getting Network Traces from Dreo App
As of a recent release, Dreo seems to have removed certificate pinning, at least for iOS. That makes all this a bunch easier.

### Setup Fiddler Classic as a Proxy
1. Use Fiddler Classic (http://www.fiddlertool.com) to get a network trace to see what the Dreo app is doing. I won't document here how to setup Fiddler as a proxy or do SSL decryption; Fiddler documentation is pretty good.

