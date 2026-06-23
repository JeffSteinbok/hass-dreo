"""Tests for Dreo Humidifiers"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HUMIDIFIER_EXHAUSTIVE_MODELS = [
    "get_devices_HHM001S.json",
    "get_devices_HHM003S.json",
    "get_devices_HHM006S.json",
    "get_devices_HHM014S.json",
    "get_devices_HHM015S.json",
]


class TestPyDreoHumidifier(TestBase):
    """Test PyDreoHumidifier class."""

    def _exercise_all_settable_properties(self, humidifier: PyDreoHumidifier):
        """Exercise all writable humidifier properties that are supported by a model."""
        _ = humidifier.is_on
        _ = humidifier.modes
        _ = humidifier.target_humidity_range
        _ = humidifier.humidity
        _ = humidifier.target_humidity
        _ = humidifier.sleep_target_humidity
        _ = humidifier.fog_level
        _ = humidifier.panel_sound
        _ = humidifier.mode
        _ = humidifier.wrong
        _ = humidifier.water_level
        _ = humidifier.worktime
        _ = humidifier.display_light
        _ = humidifier.foglevel
        _ = humidifier.mist_level
        _ = humidifier.rgblevel
        _ = humidifier.ambient_light
        _ = humidifier.rgbmode
        _ = humidifier.rgbcolor
        _ = humidifier.rgbth
        _ = humidifier.rgbth_low
        _ = humidifier.rgbth_high
        _ = humidifier.scheon
        _ = humidifier.filtertime
        _ = humidifier.filteron
        _ = humidifier.suspend

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.is_on = not bool(humidifier.is_on)
            mock_send_command.assert_called_once()

        min_humidity, max_humidity = humidifier.target_humidity_range
        new_target_humidity = min_humidity if humidifier.target_humidity != min_humidity else max_humidity
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.target_humidity = new_target_humidity
            mock_send_command.assert_called_once()

        if humidifier.sleep_target_humidity is not None:
            new_sleep_target = 40 if humidifier.sleep_target_humidity != 40 else 45
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.sleep_target_humidity = new_sleep_target
                mock_send_command.assert_called_once()

        if humidifier.fog_level is not None:
            new_fog_level = 1 if humidifier.fog_level != 1 else 2
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.fog_level = new_fog_level
                mock_send_command.assert_called_once()

        if humidifier.panel_sound is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.panel_sound = not bool(humidifier.panel_sound)
                mock_send_command.assert_called_once()

        if humidifier.modes:
            for mode in humidifier.modes:
                if mode != humidifier.mode:
                    with patch(PATCH_SEND_COMMAND) as mock_send_command:
                        humidifier.mode = mode
                        mock_send_command.assert_called_once()
                    break

        if humidifier.display_light is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.display_light = not humidifier.display_light
                mock_send_command.assert_called_once()

        if humidifier.mist_level is not None:
            new_mist_level = 1 if humidifier.mist_level != 1 else 2
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.mist_level = new_mist_level
                mock_send_command.assert_called_once()

        if humidifier.rgblevel is not None:
            new_rgblevel = 0 if int(humidifier.rgblevel) != 0 else 2
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.rgblevel = new_rgblevel
                mock_send_command.assert_called_once()

        if humidifier.ambient_light is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.ambient_light = not humidifier.ambient_light
                mock_send_command.assert_called_once()

        if humidifier.rgbmode is not None:
            new_rgbmode = 1 if humidifier.rgbmode != 1 else 0
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.rgbmode = new_rgbmode
                mock_send_command.assert_called_once()

        if humidifier.rgbcolor is not None:
            new_rgbcolor = 16711680 if humidifier.rgbcolor != 16711680 else 255
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.rgbcolor = new_rgbcolor
                mock_send_command.assert_called_once()

        if humidifier.rgbth_low is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.rgbth_low = humidifier.rgbth_low + 1
                mock_send_command.assert_called_once()

        if humidifier.rgbth_high is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.rgbth_high = humidifier.rgbth_high + 1
                mock_send_command.assert_called_once()

        if humidifier.scheon is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.scheon = not bool(humidifier.scheon)
                mock_send_command.assert_called_once()

    def test_HHM001S(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.modes == ["normal", "auto", "sleep"]
        assert humidifier.is_feature_supported("is_on") is True
        assert humidifier.is_feature_supported("humidity") is True
        assert humidifier.is_feature_supported("target_humidity") is True
        assert humidifier.humidity == 47
        assert humidifier.target_humidity == 60

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.mode = "normal"
            mock_send_command.assert_called_once_with(humidifier, {MODE_KEY: 0})
        humidifier.handle_server_update({REPORTED_KEY: {MODE_KEY: 0}})

    def test_HHM001S_websocket_updates(self):  # pylint: disable=invalid-name
        """Test that humidity values are updated from websocket messages."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        # Initial values
        assert humidifier.humidity == 47
        assert humidifier.target_humidity == 60

        # Simulate websocket update for humidity
        message = {"method": "control-report", "devicesn": "HHM001S_1", "reported": {"rh": 55}}
        humidifier.handle_server_update(message)
        assert humidifier.humidity == 55

        # Simulate websocket update for target_humidity
        message = {"method": "control-report", "devicesn": "HHM001S_1", "reported": {"rhautolevel": 70}}
        humidifier.handle_server_update(message)
        assert humidifier.target_humidity == 70

    def test_HHM001S_water_level_property(self):  # pylint: disable=invalid-name
        """Test that water_level property works correctly."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        # Check that water_level is accessible and returns the expected value
        assert humidifier.is_feature_supported("water_level") is True
        assert humidifier.water_level == "Ok"

    def test_HHM003S(self):  # pylint: disable=invalid-name
        """Load HHM003S (HM713S/813S) and test humidity properties."""

        self.get_devices_file_name = "get_devices_HHM003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.model == "DR-HHM003S"
        assert humidifier.series_name == "HM713S/813S"
        assert humidifier.modes == ["normal", "auto", "sleep"]
        assert humidifier.is_feature_supported("is_on") is True
        assert humidifier.is_feature_supported("humidity") is True
        assert humidifier.is_feature_supported("target_humidity") is True
        assert humidifier.is_feature_supported("worktime") is True
        assert humidifier.humidity == 40
        assert humidifier.target_humidity == 50
        assert humidifier.worktime == 10

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.mode = "normal"
            mock_send_command.assert_called_once_with(humidifier, {MODE_KEY: 0})
        humidifier.handle_server_update({REPORTED_KEY: {MODE_KEY: 0}})

    def test_HHM014S(self):  # pylint: disable=invalid-name
        """Load HHM014S (HM774S) and test mode properties."""

        self.get_devices_file_name = "get_devices_HHM014S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.model == "DR-HHM014S"
        assert humidifier.series_name == "HM774S"
        assert humidifier.modes == ["normal", "auto", "sleep"]
        assert humidifier.is_feature_supported("is_on") is True
        assert humidifier.is_feature_supported("humidity") is True
        assert humidifier.is_feature_supported("target_humidity") is True
        assert humidifier.humidity == 52
        assert humidifier.target_humidity == 55
        assert humidifier.mode == "auto"

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.mode = "normal"
            mock_send_command.assert_called_once_with(humidifier, {MODE_KEY: 0})
        humidifier.handle_server_update({REPORTED_KEY: {MODE_KEY: 2}})
        assert humidifier.mode == "sleep"



    def test_HHM003S_websocket_updates(self):  # pylint: disable=invalid-name
        """Test that humidity values are updated from websocket messages for HHM003S."""
        self.get_devices_file_name = "get_devices_HHM003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        # Initial values
        assert humidifier.humidity == 40
        assert humidifier.target_humidity == 50

        # Simulate websocket update for humidity
        message = {"method": "control-report", "devicesn": "HHM003S_1", "reported": {"rh": 65}}
        humidifier.handle_server_update(message)
        assert humidifier.humidity == 65

        # Simulate websocket update for target_humidity
        message = {"method": "control-report", "devicesn": "HHM003S_1", "reported": {"rhautolevel": 75}}
        humidifier.handle_server_update(message)
        assert humidifier.target_humidity == 75

        # Simulate websocket update for worktime
        message = {"method": "control-report", "devicesn": "HHM003S_1", "reported": {"worktime": 50}}
        humidifier.handle_server_update(message)
        assert humidifier.worktime == 50

    def test_HHM003S_water_level_property(self):  # pylint: disable=invalid-name
        """Test that water_level property works correctly for HHM003S."""
        self.get_devices_file_name = "get_devices_HHM003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        # Check that water_level is accessible and returns the expected value
        assert humidifier.is_feature_supported("water_level") is True
        assert humidifier.water_level == "Ok"

    def test_HHM015S(self):  # pylint: disable=invalid-name
        """Load HHM015S (HM755S) and test humidity properties."""

        self.get_devices_file_name = "get_devices_HHM015S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.model == "DR-HHM015S"
        assert humidifier.series_name == "HM755S"
        assert humidifier.is_feature_supported("is_on") is True
        assert humidifier.is_feature_supported("humidity") is True
        assert humidifier.is_feature_supported("target_humidity") is True
        assert humidifier.is_on is False
        assert humidifier.humidity == 31
        assert humidifier.target_humidity == 60
        # HHM015S has no modes configured - modes should return None, not an empty list or error
        assert humidifier.modes is None
        assert humidifier.mode is None

    def test_HHM015S_websocket_updates(self):  # pylint: disable=invalid-name
        """Test that humidity values are updated from websocket messages for HHM015S."""
        self.get_devices_file_name = "get_devices_HHM015S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        # Initial values
        assert humidifier.humidity == 31
        assert humidifier.target_humidity == 60

        # Simulate websocket update for humidity
        message = {"method": "control-report", "devicesn": "HHM015S_1", "reported": {"rh": 45}}
        humidifier.handle_server_update(message)
        assert humidifier.humidity == 45

        # Simulate websocket update for target_humidity
        message = {"method": "control-report", "devicesn": "HHM015S_1", "reported": {"rhautolevel": 65}}
        humidifier.handle_server_update(message)
        assert humidifier.target_humidity == 65

    def test_HHM015S_water_level_property(self):  # pylint: disable=invalid-name
        """Test that water_level property works correctly for HHM015S."""
        self.get_devices_file_name = "get_devices_HHM015S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        # Check that water_level is accessible and returns the expected value
        assert humidifier.is_feature_supported("water_level") is True
        assert humidifier.water_level == "Ok"

    def test_HHM001S_power_cycle_stale_state(self):  # pylint: disable=invalid-name
        """Test that turn_on command is sent even when cached state is stale after power cycle."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        # Simulate device power cycle scenario:
        # 1. Device is physically OFF (power cycled)
        # 2. Cloud sends stale WebSocket state with poweron: true
        # 3. User calls turn_on
        # 4. Command should be sent even though cached state shows ON

        # Simulate stale WebSocket update reporting device is ON (but it's actually OFF)
        message = {"method": "control-report", "devicesn": "HHM001S_1", "reported": {"poweron": True}}
        humidifier.handle_server_update(message)
        assert humidifier.is_on is True  # Cached state shows ON

        # User calls turn_on - command should be sent despite cached state being ON
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.is_on = True  # Attempt to turn on
            # Command MUST be sent even though cached state matches
            mock_send_command.assert_called_once_with(humidifier, {POWERON_KEY: True})

    def test_HHM003S_power_cycle_stale_state(self):  # pylint: disable=invalid-name
        """Test that turn_on command is sent even when cached state is stale for HHM003S."""
        self.get_devices_file_name = "get_devices_HHM003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        # Simulate stale WebSocket update reporting device is ON
        message = {"method": "control-report", "devicesn": "HHM003S_1", "reported": {"poweron": True}}
        humidifier.handle_server_update(message)
        assert humidifier.is_on is True

        # Command should be sent even when cached state matches
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.is_on = True
            mock_send_command.assert_called_once_with(humidifier, {POWERON_KEY: True})

    # --- target_humidity setter ---

    def test_target_humidity_setter_sends_command(self):
        """Test target_humidity setter sends command when value changes."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.target_humidity == 60
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.target_humidity = 70
            mock_send_command.assert_called_once_with(humidifier, {TARGET_AUTO_HUMIDITY_KEY: 70})
        assert humidifier.target_humidity == 70

    def test_target_humidity_setter_noop(self):
        """Test target_humidity setter skips command when value unchanged."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.target_humidity = 60  # same as initial
            mock_send_command.assert_not_called()

    # --- panel_sound property and setter ---

    def test_panel_sound_property(self):
        """Test panel_sound returns inverse of mute_on."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        # _mute_on loaded from state
        assert humidifier.panel_sound is not None

    def test_panel_sound_none(self):
        """Test panel_sound returns None when mute_on is None."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        humidifier._mute_on = None  # pylint: disable=protected-access
        assert humidifier.panel_sound is None

    def test_panel_sound_setter_sends_command(self):
        """Test panel_sound setter sends muteon command."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        humidifier._mute_on = True  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.panel_sound = True  # not value = False, different from _mute_on=True
            mock_send_command.assert_called_once_with(humidifier, {MUTEON_KEY: False})

    def test_panel_sound_setter_noop(self):
        """Test panel_sound setter skips when already matching."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        humidifier._mute_on = False  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.panel_sound = True  # not value = False, same as _mute_on
            mock_send_command.assert_not_called()

    # --- mode property with name resolution ---

    def test_mode_property_resolves_name(self):
        """Test mode property resolves numeric mode to string name."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        # Set mode to a known numeric value
        humidifier._mode = 1  # pylint: disable=protected-access
        assert humidifier.mode == "auto"

    def test_mode_property_returns_none_for_unknown(self):
        """Test mode property returns None for unrecognized numeric value."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        humidifier._mode = 999  # pylint: disable=protected-access
        assert humidifier.mode is None

    # --- mode setter ---

    def test_mode_setter_noop(self):
        """Test mode setter skips command when value unchanged."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        # Set mode via websocket first
        humidifier.handle_server_update({REPORTED_KEY: {MODE_KEY: 0}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.mode = "normal"  # value 0, same as current
            mock_send_command.assert_not_called()

    def test_mode_setter_raises_for_invalid(self):
        """Test mode setter raises ValueError for invalid mode name."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        import pytest

        with pytest.raises(ValueError, match="not in the acceptable list"):
            humidifier.mode = "turbo"

    def test_mode_setter_raises_when_no_modes(self):
        """Test mode setter raises NotImplementedError when modes not supported."""
        self.get_devices_file_name = "get_devices_HHM015S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        import pytest

        with pytest.raises(NotImplementedError, match="doesn't support modes"):
            humidifier.mode = "normal"

    # --- wrong property ---

    def test_wrong_property(self):
        """Test wrong property returns water level status."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.wrong == "Ok"

    # --- rgblevel property ---

    def test_rgblevel_property(self):
        """Test rgblevel property returns RGB level status."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.rgblevel is not None

    # --- scheon property and setter ---

    def test_scheon_property(self):
        """Test scheon property returns schedule state."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.scheon is not None

    def test_scheon_setter_sends_command(self):
        """Test scheon setter sends command when value changes."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        humidifier._scheon = False  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.scheon = True
            mock_send_command.assert_called_once_with(humidifier, {SCHEDULE_ENABLE: True})

    def test_scheon_setter_noop(self):
        """Test scheon setter skips command when value unchanged."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        humidifier._scheon = True  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.scheon = True
            mock_send_command.assert_not_called()

    # --- handle_server_update for additional keys ---

    def test_handle_server_update_water_level(self):
        """Test handle_server_update processes water level status."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        humidifier.handle_server_update({REPORTED_KEY: {"wrong": 1}})
        assert humidifier.wrong == "Empty"
        assert humidifier.water_level == "Empty"

    def test_handle_server_update_rgblevel(self):
        """Test handle_server_update processes rgblevel."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        humidifier.handle_server_update({REPORTED_KEY: {"rgblevel": 2}})
        assert humidifier.rgblevel == 2

    def test_handle_server_update_scheon(self):
        """Test handle_server_update processes scheon."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        humidifier.handle_server_update({REPORTED_KEY: {SCHEDULE_ENABLE: True}})
        assert humidifier.scheon is True

    def test_handle_server_update_muteon(self):
        """Test handle_server_update processes muteon."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        humidifier.handle_server_update({REPORTED_KEY: {MUTEON_KEY: False}})
        assert humidifier._mute_on is False  # pylint: disable=protected-access

    def test_HHM006S(self):  # pylint: disable=invalid-name
        """Load HHM006S and test core humidifier command paths."""
        self.get_devices_file_name = "get_devices_HHM006S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.is_on = not bool(humidifier.is_on)
            mock_send_command.assert_called_once()

        min_humidity, max_humidity = humidifier.target_humidity_range
        new_target_humidity = min_humidity if humidifier.target_humidity != min_humidity else max_humidity
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.target_humidity = new_target_humidity
            mock_send_command.assert_called_once()

        if humidifier.modes:
            for mode in humidifier.modes:
                if mode != humidifier.mode:
                    with patch(PATCH_SEND_COMMAND) as mock_send_command:
                        humidifier.mode = mode
                        mock_send_command.assert_called_once()
                    break

        if humidifier.mist_level is not None:
            target_mist_level = 1 if humidifier.mist_level != 1 else 2
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.mist_level = target_mist_level
                mock_send_command.assert_called_once()

    @pytest.mark.parametrize("devices_file", HUMIDIFIER_EXHAUSTIVE_MODELS)
    def test_all_settable_properties_for_each_model(self, devices_file: str):
        """Exercise all writable properties for each humidifier model fixture in this file."""
        self.get_devices_file_name = devices_file
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) >= 1
        for device in self.pydreo_manager.devices:
            humidifier: PyDreoHumidifier = device
            self._exercise_all_settable_properties(humidifier)
            
    # --- filtertime, filteron, suspend properties ---

    def test_filtertime_property(self):
        """Test filtertime property returns filter life remaining."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.is_feature_supported("filtertime") is True
        assert humidifier.filtertime is not None

    def test_filteron_property(self):
        """Test filteron property returns filter active state."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.is_feature_supported("filteron") is True
        assert humidifier.filteron is not None

    def test_suspend_property(self):
        """Test suspend property returns target humidity reached state."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.is_feature_supported("suspend") is True
        assert humidifier.suspend is not None

    def test_handle_server_update_filtertime(self):
        """Test handle_server_update processes filtertime."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        humidifier.handle_server_update({REPORTED_KEY: {"filtertime": 50}})
        assert humidifier.filtertime == 50

    def test_handle_server_update_filteron(self):
        """Test handle_server_update processes filteron."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        humidifier.handle_server_update({REPORTED_KEY: {"filteron": True}})
        assert humidifier.filteron is True

    def test_handle_server_update_suspend(self):
        """Test handle_server_update processes suspend (target humidity reached)."""
        self.get_devices_file_name = "get_devices_HHM001S.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        humidifier.handle_server_update({REPORTED_KEY: {"suspend": True}})
        assert humidifier.suspend is True
        humidifier.handle_server_update({REPORTED_KEY: {"suspend": False}})
        assert humidifier.suspend is False

    # --- Newer firmware (atm* keys) ---

    def test_HHM015S_atm_firmware(self):  # pylint: disable=invalid-name
        """Load HHM015S (ATM firmware) and verify atm* properties are populated."""
        self.get_devices_file_name = "get_devices_HHM015S_atm.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]
        assert humidifier.model == "DR-HHM015S"

        # ATM properties must be populated from the state fixture.
        assert humidifier.atm_on is True
        assert humidifier.atm_mode == "Breath"
        assert humidifier.atm_color == 16711680  # red
        assert humidifier.atm_brightness == 128

        # Legacy rgb* properties are absent for newer firmware.
        assert humidifier.rgblevel is None
        assert humidifier.rgbmode is None
        assert humidifier.rgbcolor is None

        # ambient_light should transparently delegate to atm_on.
        assert humidifier.ambient_light is True

    def test_HHM015S_atm_ambient_light_setter(self):  # pylint: disable=invalid-name
        """Test ambient_light setter routes to ambient_switch for newer firmware."""
        self.get_devices_file_name = "get_devices_HHM015S_atm.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        # Turn off via ambient_light — should send ambient_switch=False.
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.ambient_light = False
            mock_send_command.assert_called_once_with(humidifier, {AMBIENT_SWITCH_KEY: False})

        humidifier.handle_server_update({REPORTED_KEY: {AMBIENT_SWITCH_KEY: False}})
        assert humidifier.atm_on is False
        assert humidifier.ambient_light is False

        # Turn on — should send ambient_switch=True.
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.ambient_light = True
            mock_send_command.assert_called_once_with(humidifier, {AMBIENT_SWITCH_KEY: True})

    def test_HHM015S_atm_on_setter(self):  # pylint: disable=invalid-name
        """Test atm_on property setter sends the ambient_switch command."""
        self.get_devices_file_name = "get_devices_HHM015S_atm.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.atm_on = False
            mock_send_command.assert_called_once_with(humidifier, {AMBIENT_SWITCH_KEY: False})

        # Idempotent — no command if value unchanged.
        humidifier.handle_server_update({REPORTED_KEY: {AMBIENT_SWITCH_KEY: False}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.atm_on = False
            mock_send_command.assert_not_called()

    def test_HHM015S_atm_color_setter(self):  # pylint: disable=invalid-name
        """Test atm_color property setter sends the atmcolor command."""
        self.get_devices_file_name = "get_devices_HHM015S_atm.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        new_color = 255  # blue = 0x0000FF
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.atm_color = new_color
            mock_send_command.assert_called_once_with(humidifier, {ATMCOLOR_KEY: new_color})

    def test_HHM015S_atm_mode_setter(self):  # pylint: disable=invalid-name
        """Test atm_mode property setter sends the atmmode command."""
        self.get_devices_file_name = "get_devices_HHM015S_atm.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.atm_mode = "Circle"
            mock_send_command.assert_called_once_with(humidifier, {ATMMODE_KEY: "Circle"})

        # Idempotent.
        humidifier.handle_server_update({REPORTED_KEY: {ATMMODE_KEY: "Circle"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.atm_mode = "Circle"
            mock_send_command.assert_not_called()

    def test_HHM015S_atm_brightness_setter(self):  # pylint: disable=invalid-name
        """Test atm_brightness property setter sends the atmbri command."""
        self.get_devices_file_name = "get_devices_HHM015S_atm.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.atm_brightness = 200
            mock_send_command.assert_called_once_with(humidifier, {ATMBRI_KEY: 200})

    def test_HHM015S_atm_handle_server_updates(self):  # pylint: disable=invalid-name
        """Test WebSocket updates for atm* keys are reflected in atm* properties."""
        self.get_devices_file_name = "get_devices_HHM015S_atm.json"
        self.pydreo_manager.load_devices()
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        humidifier.handle_server_update({REPORTED_KEY: {AMBIENT_SWITCH_KEY: False}})
        assert humidifier.atm_on is False

        humidifier.handle_server_update({REPORTED_KEY: {ATMMODE_KEY: "Circle"}})
        assert humidifier.atm_mode == "Circle"

        humidifier.handle_server_update({REPORTED_KEY: {ATMCOLOR_KEY: 65280}})
        assert humidifier.atm_color == 65280

        humidifier.handle_server_update({REPORTED_KEY: {ATMBRI_KEY: 64}})
        assert humidifier.atm_brightness == 64
