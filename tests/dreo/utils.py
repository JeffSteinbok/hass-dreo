"""Utility functions for the Dreo tests."""
import json
import os
from typing import Any

from custom_components.dreo.dreobasedevice import DreoBaseDeviceHA

current_path: str = os.path.dirname(os.path.realpath(__file__))


def get_device_dump(file_name: str) -> Any:
    """Get a device dump

    :param file_name: Name of the file to load
    """
    with open(os.path.join(current_path, "device_dumps", file_name), "r") as fh:
        return json.load(fh)


def create_devices_from_data(file_name: str) -> list[DreoBaseDeviceHA]:
    """Generate devices from a data dump

    :param file_name: Name of the file to load
    """
    devices = get_device_dump(file_name)
    processed = []
    for device in devices:
        processed_states = []
#        for state in device["states"]:
#            processed_states.append(HubSpaceState(**state))
        device["states"] = processed_states
        if "children" not in device:
            device["children"] = []
#        processed.append(HubSpaceDevice(**device))
    return processed

