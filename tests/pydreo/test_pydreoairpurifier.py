"""Tests for Dreo Fans"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestPyDreoAirPurifier(TestBase):
    """Test TestPyDreoAirPurifier class."""

    def test_HAP002S(self):  # pylint: disable=invalid-name
        """Test DR-HAP002S Air Purifier (Macro Pro S)."""

        self.get_devices_file_name = "get_devices_HAP002S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP002S"
        assert air_purifier.series_name == "Macro Pro S"
        assert air_purifier.speed_range == (1, 18)
        assert air_purifier.preset_modes == ["manual"]

    def test_HAP003S(self):  # pylint: disable=invalid-name
        """Test DR-HAP003S Air Purifier (Macro Max S) — original revision ("meidi" MCU).

        The original hardware revision uses "auto" as both the command and the state value.
        Setting preset_mode to "auto" must send the unchanged "auto" string.
        """

        self.get_devices_file_name = "get_devices_HAP003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP003S"
        assert air_purifier.series_name == "Macro Max S"
        assert air_purifier.speed_range == (1, 18)
        assert air_purifier.preset_modes == ["auto", "manual", "sleep", "turbo"]
        # Original revision must NOT have the auto-silent remap flag set
        assert air_purifier._auto_mode_uses_auto_silent is False  # pylint: disable=protected-access

        # Setting auto on the original revision must send "auto" unchanged
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "sleep"  # move away from current mode first
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "sleep"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "auto"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "auto"})

    def test_HAP003S_2(self):  # pylint: disable=invalid-name
        """Test DR-HAP003S Air Purifier (Macro Max S/AS) — newer "midea" MCU revision.

        This hardware revision rejects the plain "auto" mode command.  The device requires
        "auto-silent" to be sent.  The _auto_mode_uses_auto_silent flag must be set by the
        MCU override, and preset_mode="auto" must translate to command value "auto-silent".
        State updates reporting "auto-silent" must still resolve to preset_mode "auto".
        """

        self.get_devices_file_name = "get_devices_HAP003S_2.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP003S"
        assert air_purifier.series_name == "Macro Max S/AS"
        assert air_purifier.speed_range == (1, 18)
        assert air_purifier.preset_modes == ["auto", "manual", "sleep", "turbo"]
        # Newer "midea" MCU revision must have the auto-silent remap flag set
        assert air_purifier._auto_mode_uses_auto_silent is True  # pylint: disable=protected-access

        # Setting auto on the new revision must send "auto-silent"
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "sleep"  # move away from current mode first
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "sleep"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "auto"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "auto-silent"})

        # Other modes must remain unchanged
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto-silent"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "sleep"})

        # State updates with "auto-silent" must resolve to preset_mode "auto"
        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto-silent"}})
        assert air_purifier.preset_mode == "auto"

    def test_HAP005S(self):  # pylint: disable=invalid-name
        """Test DR-HAP005S Air Purifier (Macro AP505S)."""

        self.get_devices_file_name = "get_devices_HAP005S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        air_purifier = self.pydreo_manager.devices[0]
        assert air_purifier.model == "DR-HAP005S"
        assert air_purifier.series_name == "Macro AP505S"
        assert air_purifier.speed_range == (1, 4)
        assert air_purifier.preset_modes == ["manual"]

    def test_air_purifier_preset_mode_variant_mapping(self):
        """Mode variants like auto-regular should still map to the base preset mode."""
        self.get_devices_file_name = "get_devices_HAP003S.json"
        self.pydreo_manager.load_devices()
        air_purifier = self.pydreo_manager.devices[0]

        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "auto-regular"}})
        assert air_purifier.preset_mode == "auto"

        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "sleep-regular"}})
        assert air_purifier.preset_mode == "sleep"

        air_purifier.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: "manual"}})
        assert air_purifier.preset_mode == "manual"

    def test_air_purifier_set_preset_mode_uses_mode_key(self):
        """Air purifier preset mode changes should send the mode command."""
        self.get_devices_file_name = "get_devices_HAP003S.json"
        self.pydreo_manager.load_devices()
        air_purifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            air_purifier.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(air_purifier, {WIND_MODE_KEY: "sleep"})

