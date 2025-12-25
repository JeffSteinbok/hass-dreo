"""
Test to validate that all device models have complete test data files.

This ensures that for every get_devices_*.json file, there is a corresponding
get_device_state_*_1.json file.
"""

import json
import os
from pathlib import Path
import pytest


API_RESPONSES_DIR = Path(__file__).parent / "api_responses"


def get_model_from_devices_file(file_path: Path) -> str:
    """Extract the model name from a get_devices file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if data.get("code") == 0 and "data" in data:
            devices_list = data["data"].get("list", [])
            if devices_list:
                # Get model from the file, e.g., "DR-HTF008S" -> "HTF008S"
                model = devices_list[0].get("model", "")
                if model.startswith("DR-"):
                    return model[3:]  # Remove "DR-" prefix
                return model
    return None


def get_sn_from_devices_file(file_path: Path) -> str:
    """Extract the serial number from a get_devices file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if data.get("code") == 0 and "data" in data:
            devices_list = data["data"].get("list", [])
            if devices_list:
                return devices_list[0].get("sn", "")
    return None


def get_device_id_from_devices_file(file_path: Path) -> str:
    """Extract the deviceId from a get_devices file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if data.get("code") == 0 and "data" in data:
            devices_list = data["data"].get("list", [])
            if devices_list:
                return devices_list[0].get("deviceId", "")
    return None


class TestDeviceDataCompleteness:
    """Test class to validate completeness of test data files."""

    def test_all_devices_have_state_files(self):
        """Test that every get_devices_*.json has a corresponding get_device_state_*_1.json file."""
        # Find all get_devices_*.json files
        device_files = list(API_RESPONSES_DIR.glob("get_devices_*.json"))
        
        assert len(device_files) > 0, "No get_devices_*.json files found"
        
        # Files to skip (special test cases)
        skip_files = {"get_devices_multiple_1.json"}
        
        missing_state_files = []
        
        for device_file in device_files:
            # Skip special test files
            if device_file.name in skip_files:
                continue
                
            # Extract model from filename (e.g., get_devices_HTF008S.json -> HTF008S)
            filename = device_file.stem  # get_devices_HTF008S
            model_from_filename = filename.replace("get_devices_", "")
            
            # Also check the model inside the file to ensure consistency
            model_from_content = get_model_from_devices_file(device_file)
            sn_from_content = get_sn_from_devices_file(device_file)
            
            # Construct expected state file name
            expected_state_file = API_RESPONSES_DIR / f"get_device_state_{sn_from_content}.json"
            
            if not expected_state_file.exists():
                missing_state_files.append({
                    "devices_file": device_file.name,
                    "expected_state_file": expected_state_file.name,
                    "model_from_filename": model_from_filename,
                    "model_from_content": model_from_content,
                    "sn_from_content": sn_from_content
                })
        
        if missing_state_files:
            error_message = "Missing get_device_state files:\n"
            for missing in missing_state_files:
                error_message += f"  - {missing['devices_file']} (model: {missing['sn_from_content']}) "
                error_message += f"needs {missing['expected_state_file']}\n"
            
            pytest.fail(error_message)

    def test_all_state_files_have_devices_files(self):
        """Test that every get_device_state_*_1.json has a corresponding get_devices_*.json file."""
        # Find all get_device_state_*_1.json files
        state_files = list(API_RESPONSES_DIR.glob("get_device_state_*_1.json"))
        
        assert len(state_files) > 0, "No get_device_state_*_1.json files found"
        
        orphaned_state_files = []
        
        for state_file in state_files:
            # Extract model from filename (e.g., get_device_state_HTF008S_1.json -> HTF008S)
            filename = state_file.stem  # get_device_state_HTF008S_1
            model_from_filename = filename.replace("get_device_state_", "").replace("_1", "")
            
            # Construct expected devices file name
            expected_devices_file = API_RESPONSES_DIR / f"get_devices_{model_from_filename}.json"
            
            if not expected_devices_file.exists():
                orphaned_state_files.append({
                    "state_file": state_file.name,
                    "expected_devices_file": expected_devices_file.name,
                    "model": model_from_filename
                })
        
        if orphaned_state_files:
            error_message = "Orphaned get_device_state files (no matching get_devices file):\n"
            for orphaned in orphaned_state_files:
                error_message += f"  - {orphaned['state_file']} needs {orphaned['expected_devices_file']}\n"
            
            pytest.fail(error_message)

    def test_serial_numbers_match_pattern(self):
        """Test that serial numbers in device files match the expected pattern."""
        device_files = list(API_RESPONSES_DIR.glob("get_devices_*.json"))
        
        # Files to skip (special test cases)
        skip_files = {"get_devices_multiple_1.json"}
        
        invalid_sns = []
        
        for device_file in device_files:
            # Skip special test files
            if device_file.name in skip_files:
                continue
                
            model_from_filename = device_file.stem.replace("get_devices_", "")
            sn = get_sn_from_devices_file(device_file)
            
            # Handle SNs that start with "DR-" prefix
            if sn:
                sn_check = sn
                if sn.startswith("DR-"):
                    sn_check = sn[3:]  # Remove "DR-" prefix for comparison
                
                if not sn_check.startswith(model_from_filename):
                    invalid_sns.append({
                        "file": device_file.name,
                        "model": model_from_filename,
                        "sn": sn,
                        "expected_pattern": f"{model_from_filename}_* or DR-{model_from_filename}_*"
                    })
        
        if invalid_sns:
            error_message = "Serial numbers don't match expected pattern:\n"
            for invalid in invalid_sns:
                error_message += f"  - {invalid['file']}: SN '{invalid['sn']}' "
                error_message += f"should match pattern '{invalid['expected_pattern']}'\n"
            
            pytest.fail(error_message)

    def test_no_duplicate_serial_numbers(self):
        """Test that all serial numbers are unique across all device files."""
        device_files = list(API_RESPONSES_DIR.glob("get_devices_*.json"))
        
        # Files to skip (special test cases)
        skip_files = {"get_devices_multiple_1.json"}
        
        # Dictionary to track serial numbers and which files they appear in
        sn_to_files = {}
        
        for device_file in device_files:
            # Skip special test files
            if device_file.name in skip_files:
                continue
                
            sn = get_sn_from_devices_file(device_file)
            
            if sn:
                if sn not in sn_to_files:
                    sn_to_files[sn] = []
                sn_to_files[sn].append(device_file.name)
        
        # Find duplicates
        duplicates = {sn: files for sn, files in sn_to_files.items() if len(files) > 1}
        
        if duplicates:
            error_message = "Duplicate serial numbers found:\n"
            for sn, files in duplicates.items():
                error_message += f"  - Serial number '{sn}' appears in:\n"
                for file in files:
                    error_message += f"    • {file}\n"
            
            pytest.fail(error_message)

    def test_no_duplicate_device_ids(self):
        """Test that all deviceIds are unique across all device files."""
        device_files = list(API_RESPONSES_DIR.glob("get_devices_*.json"))
        
        # Files to skip (special test cases)
        skip_files = {"get_devices_multiple_1.json"}
        
        # Dictionary to track deviceIds and which files they appear in
        device_id_to_files = {}
        
        for device_file in device_files:
            # Skip special test files
            if device_file.name in skip_files:
                continue
                
            device_id = get_device_id_from_devices_file(device_file)
            
            if device_id:
                # Skip redacted device IDs (used in test files for privacy)
                if device_id == "**REDACTED**":
                    continue
                    
                if device_id not in device_id_to_files:
                    device_id_to_files[device_id] = []
                device_id_to_files[device_id].append(device_file.name)
        
        # Find duplicates
        duplicates = {did: files for did, files in device_id_to_files.items() if len(files) > 1}
        
        if duplicates:
            error_message = "Duplicate deviceIds found:\n"
            for device_id, files in duplicates.items():
                error_message += f"  - deviceId '{device_id}' appears in:\n"
                for file in files:
                    error_message += f"    • {file}\n"
            
            pytest.fail(error_message)

    def test_device_ids_are_numeric_strings(self):
        """Test that all deviceIds are strings containing only digits."""
        device_files = list(API_RESPONSES_DIR.glob("get_devices_*.json"))
        
        # Files to skip (special test cases or files with legitimately redacted deviceIds)
        skip_files = {}
        invalid_device_ids = []
        
        for device_file in device_files:
            # Skip special test files
            if device_file.name in skip_files:
                continue
                
            device_id = get_device_id_from_devices_file(device_file)
            
            if device_id:
                # Check if deviceId is a string of digits
                if not device_id.isdigit():
                    invalid_device_ids.append({
                        "file": device_file.name,
                        "device_id": device_id,
                        "reason": "deviceId must be a string containing only digits"
                    })
        
        if invalid_device_ids:
            error_message = "Invalid deviceIds found (must be numeric strings):\n"
            for invalid in invalid_device_ids:
                error_message += f"  - {invalid['file']}: deviceId '{invalid['device_id']}' "
                error_message += f"({invalid['reason']})\n"
            
            pytest.fail(error_message)
