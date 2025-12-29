#!/usr/bin/env python3
"""Deploy Dreo integration to Home Assistant instance.

This script:
1. Optionally enables DEBUG_TEST_MODE in const_debug_test_mode.py
2. Generates E2E test data to temp directory
3. Copies the integration files to the HA instance
4. On Mac: uses rsync
5. On Windows: uses robocopy (TBD)
"""
import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
CUSTOM_COMPONENTS_SRC = PROJECT_ROOT / "custom_components" / "dreo"
CONST_DEBUG_FILE = CUSTOM_COMPONENTS_SRC / "const_debug_test_mode.py"
GENERATE_SCRIPT = SCRIPT_DIR / "generateE2ETestData.py"
TEMP_DIR = SCRIPT_DIR / "temp"
TEMP_E2E_DATA_DIR = TEMP_DIR / "e2e_test_data"
TARGET_E2E_DATA_DIR = CUSTOM_COMPONENTS_SRC / "e2e_test_data"

# HA instance path (Mac default)
DEFAULT_HA_PATH_MAC = "/Volumes/Config/custom_components/dreo/"
DEFAULT_HA_PATH_WINDOWS = None  # TBD


def enable_debug_mode():
    """Uncomment DEBUG_TEST_MODE = True in const_debug_test_mode.py."""
    print("Enabling DEBUG_TEST_MODE...")
    
    with open(CONST_DEBUG_FILE, 'r') as f:
        content = f.read()
    
    # Uncomment the line if it's commented
    modified_content = content.replace(
        "# DEBUG_TEST_MODE = True",
        "DEBUG_TEST_MODE = True"
    )
    
    with open(CONST_DEBUG_FILE, 'w') as f:
        f.write(modified_content)
    
    print("✓ DEBUG_TEST_MODE enabled")


def disable_debug_mode():
    """Comment out DEBUG_TEST_MODE = True in const_debug_test_mode.py."""
    print("Disabling DEBUG_TEST_MODE...")
    
    with open(CONST_DEBUG_FILE, 'r') as f:
        content = f.read()
    
    # Find and comment the line if it's uncommented
    lines = content.split('\n')
    modified_lines = []
    
    for line in lines:
        if line.strip() == "DEBUG_TEST_MODE = True" and not line.strip().startswith("#"):
            # Check if previous line is already a comment about uncommenting
            if modified_lines and "Uncomment to enable" in modified_lines[-1]:
                modified_lines.append("# " + line)
            else:
                modified_lines.append("# " + line)
        else:
            modified_lines.append(line)
    
    modified_content = '\n'.join(modified_lines)
    
    with open(CONST_DEBUG_FILE, 'w') as f:
        f.write(modified_content)
    
    print("✓ DEBUG_TEST_MODE disabled")


def generate_e2e_test_data():
    """Generate E2E test data to temp directory and copy to target."""
    print("\nGenerating E2E test data...")
    
    # Run the generation script (generates to testScripts/temp/e2e_test_data)
    result = subprocess.run(
        [sys.executable, str(GENERATE_SCRIPT)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error generating E2E test data: {result.stderr}")
        return False
    
    print(result.stdout)
    
    # Copy generated data to custom_components/dreo/e2e_test_data
    print(f"Copying E2E test data to {TARGET_E2E_DATA_DIR}...")
    
    if TARGET_E2E_DATA_DIR.exists():
        shutil.rmtree(TARGET_E2E_DATA_DIR)
    
    shutil.copytree(TEMP_E2E_DATA_DIR, TARGET_E2E_DATA_DIR)
    
    file_count = len(list(TARGET_E2E_DATA_DIR.glob("*.json")))
    print(f"✓ Copied {file_count} files to target directory")
    
    return True


def deploy_mac(ha_path, debug_mode):
    """Deploy to HA instance on macOS using rsync."""
    print(f"\nDeploying to {ha_path}...")
    
    # Build rsync command
    cmd = [
        "rsync",
        "-rltvz",
        "--delete",
        "--no-perms",
        "--no-owner",
        "--inplace",
        "--exclude=__pycache__",
        "--exclude=.*",
        f"{CUSTOM_COMPONENTS_SRC}/",
        ha_path
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("✓ Deployment successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during rsync: {e.stderr}")
        return False


def deploy_windows(ha_path):
    """Deploy to HA instance on Windows using robocopy."""
    print(f"\nDeploying to {ha_path}...")
    print("⚠ Windows deployment with robocopy is not yet implemented (TBD)")
    print("You can manually copy the files from:")
    print(f"  {CUSTOM_COMPONENTS_SRC}")
    print(f"To: {ha_path}")
    return False


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(
        description="Deploy Dreo integration to Home Assistant instance"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable DEBUG_TEST_MODE before deployment"
    )
    parser.add_argument(
        "--ha-path",
        type=str,
        help="Path to HA custom_components/dreo directory"
    )
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Skip E2E test data generation"
    )
    
    args = parser.parse_args()
    
    # Detect OS
    system = platform.system()
    print(f"Detected OS: {system}")
    
    # Determine HA path
    if args.ha_path:
        ha_path = args.ha_path
    elif system == "Darwin":  # macOS
        ha_path = DEFAULT_HA_PATH_MAC
    elif system == "Windows":
        ha_path = DEFAULT_HA_PATH_WINDOWS
        if not ha_path:
            print("Error: Please specify --ha-path for Windows deployment")
            return 1
    else:
        print(f"Error: Unsupported OS: {system}")
        return 1
    
    # Validate HA path exists
    if system == "Darwin" and not Path(ha_path).parent.exists():
        print(f"Error: HA path parent directory does not exist: {Path(ha_path).parent}")
        print("Make sure your HA instance is mounted/accessible")
        return 1
    
    success = True
    
    try:
        # Enable debug mode if requested
        if args.debug:
            enable_debug_mode()
        
        # Generate E2E test data
        if not args.skip_generate:
            if not generate_e2e_test_data():
                print("Warning: E2E test data generation failed")
                success = False
        
        # Deploy based on OS
        if system == "Darwin":
            if not deploy_mac(ha_path, args.debug):
                success = False
        elif system == "Windows":
            if not deploy_windows(ha_path):
                success = False
        
    finally:
        # Always disable debug mode when done (restore to safe state)
        if args.debug:
            disable_debug_mode()
    
    if success:
        print("\n✓ All deployment steps completed successfully")
        return 0
    else:
        print("\n⚠ Deployment completed with warnings or errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
