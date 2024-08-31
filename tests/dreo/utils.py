import asyncio
import json
import os
from typing import Any

from hubspace_async import HubSpaceConnection, HubSpaceDevice, HubSpaceState

from custom_components.hubspace import anonomyize_data

current_path: str = os.path.dirname(os.path.realpath(__file__))


def get_device_dump(file_name: str) -> Any:
    """Get a device dump

    :param file_name: Name of the file to load
    """
    with open(os.path.join(current_path, "device_dumps", file_name), "r") as fh:
        return json.load(fh)


def create_devices_from_data(file_name: str) -> list[HubSpaceDevice]:
    """Generate devices from a data dump

    :param file_name: Name of the file to load
    """
    devices = get_device_dump(file_name)
    processed = []
    for device in devices:
        processed_states = []
        for state in device["states"]:
            processed_states.append(HubSpaceState(**state))
        device["states"] = processed_states
        if "children" not in device:
            device["children"] = []
        processed.append(HubSpaceDevice(**device))
    return processed


def convert_hs_raw(data):
    """Used for converting old data-dumps to new data dumps"""
    loop = asyncio.get_event_loop()
    conn = HubSpaceConnection(None, None)
    loop.run_until_complete(conn._process_api_results(data))
    devs = loop.run_until_complete(anonomyize_data.generate_anon_data(conn))
    with open("converted.json", "w") as fh:
        json.dump(devs, fh, indent=4)
    return devs