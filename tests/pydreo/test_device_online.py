"""Tests for applying `device-online` WebSocket messages as device state.

When a device (re)connects to the Dreo cloud - e.g. after a mains outage - the
cloud pushes a `device-online` message whose `reported` dict is the device's
full state snapshot. Air circulators come back from a power loss with
poweron=False, and that message is the only notification of it.
"""

# pylint: disable=used-before-assignment
import glob
import logging
import os
from unittest.mock import MagicMock, patch
import pytest
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND, API_REPONSE_BASE_PATH

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Captured from a DR-HPF015S reconnecting after being unplugged for ~45 s
# (identifiers and network details removed).
HPF015S_DEVICE_ONLINE_REPORTED = {
    "wifi_rssi": -49,
    "poweron": False,
    "scheid": 0,
    "cruiseconf": "90,75,-10,-75",
    "timeron": {"du": 0, "ts": 1790605509},
    "matter_state": 4,
    "fixedconf": "-5,0",
    "scheon": False,
    "mode": 4,
    "mcuon": True,
    "network_latency": 0,
    "module_hardware_model": "X1",
    "mcu_firmware_version": "0.5.0",
    "oscmode": 0,
    "temperature": 86,
    "alignon": True,
    "muteon": False,
    "lighton": False,
}

DEVICE_LIST_FILES = sorted(os.path.basename(path) for path in glob.glob(f"{API_REPONSE_BASE_PATH}get_devices_*.json"))


class TestDeviceOnline(TestBase):
    """device-online carries real device state and must be applied."""

    def _device_online(self, device, reported: dict) -> dict:
        return {
            "method": "device-online",
            "devicesn": device.serial_number,
            "timestamp": 1790605510674,
            "reported": reported,
        }

    def test_device_online_after_power_loss_turns_stale_fan_off(self):
        """Stale ON + device-online(poweron=False) -> OFF, callbacks fire, turn_on sends."""
        self.get_devices_file_name = "get_devices_HPF015S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]

        # HA last saw the fan running before the outage.
        self.pydreo_manager._transport_consume_message({"method": "report", "devicesn": fan.serial_number, "reported": {POWERON_KEY: True}})
        assert fan.is_on is True

        callback = MagicMock()
        fan.add_attr_callback(callback)

        # Power comes back: the fan boots OFF and reports its full state.
        self.pydreo_manager._transport_consume_message(self._device_online(fan, HPF015S_DEVICE_ONLINE_REPORTED))

        assert fan.is_on is False
        callback.assert_called_once()
        # The rest of the snapshot is applied too.
        assert fan.fixed_conf_reported == "-5,0"
        assert fan.temperature == 86
        assert fan.preset_mode == "auto"

        # With the real state known, turn_on is no longer swallowed by the
        # same-value guard in the is_on setter.
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})

    def test_device_online_does_not_ack_pending_command(self):
        """device-online is state, not a command acknowledgement."""
        self.get_devices_file_name = "get_devices_HPF015S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]

        self.pydreo_manager._reserve_command_slot(fan.serial_number, {POWERON_KEY: True})
        try:
            self.pydreo_manager._transport_consume_message(self._device_online(fan, HPF015S_DEVICE_ONLINE_REPORTED))
            assert self.pydreo_manager._ack_received is False
        finally:
            self.pydreo_manager._release_command_slot()

    def test_device_offline_marks_disconnected(self):
        """device-offline (no reported state) marks the device disconnected and notifies (issue #937)."""
        self.get_devices_file_name = "get_devices_HPF015S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        power_before = fan.is_on

        callback = MagicMock()
        fan.add_attr_callback(callback)

        self.pydreo_manager._transport_consume_message({"method": "device-offline", "devicesn": fan.serial_number, "timestamp": 1791452054262})

        assert fan.connected is False
        assert fan.is_on == power_before
        callback.assert_called_once()

    def test_device_online_after_offline_marks_connected(self):
        """device-online brings a device marked offline back, even if the snapshot lacks "connected"."""
        self.get_devices_file_name = "get_devices_HPF015S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]

        self.pydreo_manager._transport_consume_message({"method": "device-offline", "devicesn": fan.serial_number})
        assert fan.connected is False

        callback = MagicMock()
        fan.add_attr_callback(callback)
        self.pydreo_manager._transport_consume_message(self._device_online(fan, HPF015S_DEVICE_ONLINE_REPORTED))

        assert fan.connected is True
        callback.assert_called_once()

    def test_control_reply_is_still_not_applied(self):
        """Adding device-online must not re-open the door for control-reply."""
        self.get_devices_file_name = "get_devices_HPF015S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]
        assert fan.is_on is False

        self.pydreo_manager._transport_consume_message({"method": "control-reply", "devicesn": fan.serial_number, "reported": {POWERON_KEY: True}})
        assert fan.is_on is False

    def test_device_online_ceiling_fan_gate_closed(self):
        """A ceiling fan snapshot with the power gate closed reads OFF, retaining load values."""
        self.install_manual_scheduler()
        self.get_devices_file_name = "get_devices_HCF002S.json"
        self.pydreo_manager.load_devices()
        fan = self.pydreo_manager.devices[0]

        # Stale: fan motor and light were on before the outage.
        self.pydreo_manager._transport_consume_message(
            {"method": "report", "devicesn": fan.serial_number, "reported": {POWERON_KEY: True, FANON_KEY: True, LIGHTON_KEY: True}}
        )
        assert fan.is_on is True
        assert fan.light_on is True

        self.pydreo_manager._transport_consume_message(
            self._device_online(fan, {POWERON_KEY: False, FANON_KEY: True, LIGHTON_KEY: True, WINDLEVEL_KEY: 3})
        )

        assert fan.poweron is False
        assert fan.is_on is False
        assert fan.light_on is False
        # Load keys are retained behind the closed gate (hardware behavior).
        assert fan.gate_diagnostics()[FANON_KEY] is True
        assert fan.fan_speed == 3

    @pytest.mark.parametrize("devices_file", DEVICE_LIST_FILES)
    def test_full_snapshot_is_processed_for_every_device(self, devices_file):
        """Every device class digests a full-state device-online without side effects.

        Feeds each fixture's own REST state back as a device-online snapshot: the
        message must be applied without errors, notify listeners exactly once,
        leave the power state consistent with REST, and never send a command.
        """
        self.install_manual_scheduler()
        self.get_devices_file_name = devices_file
        self.pydreo_manager.load_devices()

        for device in self.pydreo_manager.devices:
            mixed = ((device.raw_state or {}).get("data") or {}).get("mixed") or {}
            reported = {key: (value["state"] if isinstance(value, dict) and "state" in value else value) for key, value in mixed.items()}
            power_before = getattr(device, "is_on", None)
            callback = MagicMock()
            device.add_attr_callback(callback)

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                self.pydreo_manager._transport_consume_message(self._device_online(device, reported))
                mock_send_command.assert_not_called()

            callback.assert_called_once()
            assert getattr(device, "is_on", None) == power_before
