# Test Scripts

This directory contains test scripts for manual testing and development of the PyDreo library, as well as deployment tools.

## Setup

1. Copy the example credentials file:
   ```bash
   cp testScripts/secrets/credentials.example.py testScripts/secrets/credentials.py
   ```

2. Edit `testScripts/secrets/credentials.py` and add your Dreo account credentials:
   - `USERNAME`: Your Dreo account email
   - `PASSWORD`: Your Dreo account password  
   - `AUTH_TOKEN`: (Optional) Authentication token from a previous login session

## Scripts

### deploy_to_ha.py

**New deployment script** for deploying the Dreo integration to your Home Assistant instance.

**Usage:**
```bash
# Basic deployment (Mac only, uses default path)
python3 testScripts/deploy_to_ha.py

# Deploy with DEBUG_TEST_MODE enabled (for testing with local data)
python3 testScripts/deploy_to_ha.py --debug

# Deploy to custom path
python3 testScripts/deploy_to_ha.py --ha-path /path/to/homeassistant/custom_components/dreo/

# Skip E2E test data generation
python3 testScripts/deploy_to_ha.py --skip-generate
```

**Features:**
- Detects OS (macOS or Windows)
- On Mac: Uses rsync to efficiently copy files
- On Windows: Uses robocopy (TBD - placeholder for future implementation)
- Optionally enables DEBUG_TEST_MODE for testing with local device data
- Generates E2E test data before deployment
- Excludes `__pycache__` and hidden files from deployment
- Automatically restores DEBUG_TEST_MODE to safe state after deployment

**Default paths:**
- macOS: `/Volumes/Config/custom_components/dreo/`
- Windows: TBD (use `--ha-path` to specify)

**What it does:**
1. Optionally enables DEBUG_TEST_MODE (if `--debug` flag is used)
2. Generates E2E test data to `testScripts/temp/e2e_test_data/`
3. Copies generated data to `custom_components/dreo/e2e_test_data/`
4. Deploys files to your HA instance using rsync or robocopy
5. Restores DEBUG_TEST_MODE to safe state

### generateE2ETestData.py

Generates E2E test data by combining device JSON files from the API responses.

**Note:** This is now called automatically by `deploy_to_ha.py`, but can still be run standalone.

**Usage:**
```bash
# From project root
python3 testScripts/generateE2ETestData.py
```

**Features:**
- Combines multiple `get_devices_*.json` files into a single `get_devices.json`
- Copies all device state and setting files
- Outputs to `testScripts/temp/e2e_test_data/` (not committed to git)

### test_basic.py

Basic test script demonstrating authentication and device loading.

**Usage:**
```bash
# From project root
python3 testScripts/test_basic.py
```

**Features:**
- Test authentication via username/password (with login)
- Test authentication via token (skips login)
- Display device information including names and capabilities

**Switching between authentication methods:**

Edit the `if __name__ == "__main__"` section at the bottom of the script:

```python
# Method 1: Login with username/password
dreo = test_with_login()

# Method 2: Use token directly (uncomment to test)
# dreo = test_with_token()
```

## Security

⚠️ **Important**: The `secrets/` directory contains sensitive credentials and is excluded from git via:
- `testScripts/secrets/.gitignore` (blocks everything except example file)
- Root `.gitignore` (blocks the entire secrets directory)

**Never commit actual credentials to the repository.**

Only the following files in `secrets/` are tracked by git:
- `credentials.example.py` - Template file
- `.gitignore` - Git ignore rules

All other files (especially `credentials.py`) are automatically ignored.
