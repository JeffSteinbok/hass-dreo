#!/usr/bin/env python3
"""
Basic test script for PyDreo functionality.

This script demonstrates:
1. Authentication via username/password (with login)
2. Authentication via token (skips login)
3. Loading and displaying device information
"""

import sys
import logging
from pathlib import Path

# Add the project root to sys.path for proper imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from custom_components.dreo.pydreo import PyStoneboxDreo

# Import credentials from secrets directory
# Add secrets directory to path
secrets_path = Path(__file__).parent / "secrets"
sys.path.insert(0, str(secrets_path))

try:
    import credentials
    USERNAME = credentials.USERNAME
    PASSWORD = credentials.PASSWORD
    AUTH_TOKEN = credentials.AUTH_TOKEN
except ImportError:
    print("ERROR: Could not import credentials.")
    print("Please copy testScripts/secrets/credentials.example.py to")
    print("testScripts/secrets/credentials.py and fill in your credentials.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def test_with_login():
    """Test authentication using username/password with login."""
    print("\n" + "="*60)
    print("Testing with username/password (requires login)")
    print("="*60)
    
    dreo = PyStoneboxDreo(username=USERNAME, password=PASSWORD)
    dreo.redact = False
    dreo.login()
    
    print(f"Token from login: {dreo.token}")
    print(f"Cloud client authenticated: {dreo._cloud_client.is_authenticated}")
    
    dreo.load_devices()
    
    if dreo.devices:
        print(f"\nFound {len(dreo.devices)} device(s):")
        for i, device in enumerate(dreo.devices):
            device_type = getattr(device, 'device_type', getattr(device, 'device_name', 'Unknown'))
            print(f"  [{i}] {device.name} ({device_type})")
            if hasattr(device, 'speed_range'):
                print(f"      Speed Range: {device.speed_range}")
    else:
        print("\nNo devices found")
    
    return dreo


def test_with_token():
    """Test authentication using token (skips login)."""
    print("\n" + "="*60)
    print("Testing with token (skips login)")
    print("="*60)
    
    dreo = PyStoneboxDreo(token=AUTH_TOKEN)
    dreo.redact = False
    
    print(f"Token: {dreo.token}")
    print(f"Cloud client authenticated: {dreo._cloud_client.is_authenticated}")
    
    dreo.load_devices()
    
    if dreo.devices:
        print(f"\nFound {len(dreo.devices)} device(s):")
        for i, device in enumerate(dreo.devices):
            device_type = getattr(device, 'device_type', getattr(device, 'device_name', 'Unknown'))
            print(f"  [{i}] {device.name} ({device_type})")
            if hasattr(device, 'speed_range'):
                print(f"      Speed Range: {device.speed_range}")
    else:
        print("\nNo devices found")
    
    return dreo


if __name__ == "__main__":
    # Choose which method to test:
    
    # Method 1: Login with username/password
    dreo = test_with_login()
    
    # Method 2: Use token directly (uncomment to test)
    # dreo = test_with_token()
    
    # Additional testing can be done here with the dreo instance
    # Example: dreo.devices[0].is_on = True
