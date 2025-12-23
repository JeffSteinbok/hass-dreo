# Test Scripts

This directory contains test scripts for manual testing and development of the PyDreo library.

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
