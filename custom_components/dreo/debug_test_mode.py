"""Support for Dreo Debug Test Mode."""
import json
import logging

from .const import (
    LOGGER,
    DEBUG_TEST_MODE_DIRECTORY_NAME,
    DEBUG_TEST_MODE_DEVICES_FILE_NAME
)

_LOGGER = logging.getLogger(LOGGER)


def get_debug_test_mode_payload(base_dir: str) -> dict:
    """Get the debug test mode payload from the file."""

    debug_test_mode_payload: dict = {}

    _LOGGER.debug("DEBUG_TEST_MODE: get_debug_test_mode_payload called")
    get_devices_payload = load_test_file(base_dir, DEBUG_TEST_MODE_DEVICES_FILE_NAME)
    if get_devices_payload is None: 
        _LOGGER.error("DEBUG_TEST_MODE: Failed to load devices payload from file.")
        return None 
    debug_test_mode_payload["get_devices"] = get_devices_payload
    _LOGGER.debug("DEBUG_TEST_MODE: GetDevices Payload: %s", get_devices_payload)

    # Iterate over all devices and verify uniqueness of serial number and device id
    seen_serial_numbers = set()
    seen_device_ids = set()

    data = get_devices_payload.get("data", None)
    if data is None:
        _LOGGER.error("DEBUG_TEST_MODE: No data found in get_devices payload")
        return None
    
    for device in data.get("list", []):
        serial_number = device.get("sn")
        device_id = device.get("deviceId")

        if not serial_number:
            _LOGGER.error("DEBUG_TEST_MODE: Device missing serial number")
            continue

        if not device_id:
            _LOGGER.error("DEBUG_TEST_MODE: Device missing device id")
            continue                

        if serial_number in seen_serial_numbers:
            _LOGGER.error("DEBUG_TEST_MODE: Duplicate serial number found: %s", serial_number)
            continue

        if device_id in seen_device_ids:
            _LOGGER.error("DEBUG_TEST_MODE: Duplicate device id found: %s", device_id)
            continue

        seen_serial_numbers.add(serial_number)
        seen_device_ids.add(device_id)

        # Load a file specific to the serial number
        device_state : dict = load_test_file(base_dir, serial_number + ".json")
        if device_state is None:
            _LOGGER.error("DEBUG_TEST_MODE: Failed to load device state for serial number %s", serial_number)
            continue
        _LOGGER.debug("Loaded data for serial number %s: %s", serial_number, device_state)
        debug_test_mode_payload[serial_number] = device_state

    return debug_test_mode_payload

def load_test_file(base_dir, filename: str) -> dict:
    """Load a JSON response from a file in the debug test mode directory."""
    
    returned_data: dict = None

    _LOGGER.debug("DEBUG_TEST_MODE: Attempting to load response from file: %s", filename)
    full_path = f"{base_dir}/{DEBUG_TEST_MODE_DIRECTORY_NAME}/{filename}"
    try:
        with open(full_path, 'r', encoding="utf-8") as file:
            _LOGGER.debug("DEBUG_TEST_MODE: Successfully loaded file: %s", full_path)
            returned_data = json.load(file)
    except FileNotFoundError:
        _LOGGER.error("DEBUG_TEST_MODE: File not found: %s", full_path)
    except json.JSONDecodeError as e:
        _LOGGER.error("DEBUG_TEST_MODE: Error decoding JSON for file %s: %s", full_path, e)

    return returned_data
