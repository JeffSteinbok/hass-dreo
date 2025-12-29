#!/usr/bin/env python3
"""Generate E2E test data by combining device JSON files."""
import json
import os
import shutil
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
API_RESPONSES_DIR = PROJECT_ROOT / "tests" / "pydreo" / "api_responses"
E2E_TEST_DATA_DIR = SCRIPT_DIR / "temp" / "e2e_test_data"

def main():
    """Generate E2E test data."""
    # Ensure output directory exists
    E2E_TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all get_devices files starting with H or K
    device_files = []
    for pattern in ["get_devices_H*.json", "get_devices_K*.json"]:
        device_files.extend(API_RESPONSES_DIR.glob(pattern))
    
    device_files.sort()
    
    print(f"Found {len(device_files)} device files to combine:")
    for file in device_files:
        print(f"  - {file.name}")
    
    # Combine all devices into a single list
    combined_devices = []
    
    for file_path in device_files:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Extract the device list from each file
        if 'data' in data and 'list' in data['data']:
            devices = data['data']['list']
            combined_devices.extend(devices)
            print(f"Added {len(devices)} device(s) from {file_path.name}")
    
    # Create the combined get_devices.json structure
    combined_data = {
        "code": 0,
        "msg": "OK",
        "data": {
            "currentPage": 1,
            "pageSize": 100,
            "totalNum": len(combined_devices),
            "totalPage": 1,
            "familyRooms": None,
            "list": combined_devices
        }
    }
    
    # Write combined file
    output_file = E2E_TEST_DATA_DIR / "get_devices.json"
    with open(output_file, 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print(f"\n✓ Created {output_file} with {len(combined_devices)} devices")
    
    # Clean existing state files in destination
    existing_state_files = list(E2E_TEST_DATA_DIR.glob("get_device_state_*.json"))
    if existing_state_files:
        print(f"\nCleaning {len(existing_state_files)} existing state files:")
        for file_path in existing_state_files:
            file_path.unlink()
            print(f"  ✓ Deleted {file_path.name}")
    
    # Copy all get_device_state files
    state_files = list(API_RESPONSES_DIR.glob("get_device_state_*.json"))
    state_files.sort()
    
    print(f"\nCopying {len(state_files)} state files:")
    for file_path in state_files:
        dest_path = E2E_TEST_DATA_DIR / file_path.name
        shutil.copy2(file_path, dest_path)
        print(f"  ✓ Copied {file_path.name}")

    # Copy all get_device_settings files
    setting_files = list(API_RESPONSES_DIR.glob("get_device_setting_*.json"))
    setting_files.sort()
    
    print(f"\nCopying {len(setting_files)} settings files:")
    for file_path in setting_files:
        dest_path = E2E_TEST_DATA_DIR / file_path.name
        shutil.copy2(file_path, dest_path)
        print(f"  ✓ Copied {file_path.name}")
    
    print(f"\n✓ Done! Generated E2E test data in {E2E_TEST_DATA_DIR}")
    print(f"  - 1 combined get_devices.json file")
    print(f"  - {len(state_files)} get_device_state files")
    print(f"  - {len(setting_files)} get_device_setting files")

if __name__ == "__main__":
    main()
