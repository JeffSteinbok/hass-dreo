"""Tests for Dreo Chef Makers"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LIGHT_KEY = "ledpotkepton"
CM_MODE_KEY = "mode"
COOK_TIME_ESTIMATED_KEY = "wkestdu"
COOK_TIME_BEGIN_KEY = "wkbegin"

# Patch target for time.time() inside the chefmaker module so cook-time math is deterministic.
PATCH_TIME = "custom_components.dreo.pydreo.pydreochefmaker.time.time"


class TestPyDreoChefMaker(TestBase):
    """Test PyDreoChefMaker class."""

    def _load_chefmaker(self):
        """Helper to load KCM001S ChefMaker device."""
        self.get_devices_file_name = "get_devices_KCM001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        return self.pydreo_manager.devices[0]

    def test_KCM001S(self):  # pylint: disable=invalid-name
        """Load ChefMaker and test sending commands."""

        self.get_devices_file_name = "get_devices_KCM001S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        chef_maker = self.pydreo_manager.devices[0]
        assert chef_maker.is_feature_supported("is_on") is True

    def test_update_state_power_and_mode(self):
        """Test update_state processes power, LED, and mode from REST state."""
        cm = self._load_chefmaker()
        # After load_devices, update_state should have been called
        assert cm.is_on is False  # from device state file
        assert cm.mode == "standby" or cm.mode == "off"
        assert cm.cook_time_remaining is not None

    def test_update_state_cook_time_remaining(self):
        """Remaining cook time is derived from estimated (wkestdu) minus elapsed time since wkbegin."""
        cm = self._load_chefmaker()
        state = {
            COOK_TIME_ESTIMATED_KEY: {"state": 600},
            COOK_TIME_BEGIN_KEY: {"state": 1000},
        }
        cm.update_state(state)
        # 120 seconds have elapsed since the cook began: 600 - 120 = 480 remaining.
        with patch(PATCH_TIME, return_value=1120):
            assert cm.cook_time_remaining == 480

    def test_cook_time_remaining_clamped_to_zero(self):
        """Remaining cook time never goes negative when the cook has run past its estimate."""
        cm = self._load_chefmaker()
        cm.update_state({
            COOK_TIME_ESTIMATED_KEY: {"state": 300},
            COOK_TIME_BEGIN_KEY: {"state": 1000},
        })
        # 360 seconds elapsed against a 300 second estimate -> clamped to 0.
        with patch(PATCH_TIME, return_value=1360):
            assert cm.cook_time_remaining == 0

    def test_cook_time_remaining_none_when_fields_absent(self):
        """Remaining cook time is None when the device does not report the duration fields."""
        cm = self._load_chefmaker()
        cm._cook_time_estimated = None  # pylint: disable=protected-access
        cm._cook_time_begin = None  # pylint: disable=protected-access
        assert cm.cook_time_remaining is None

    def test_update_state_led(self):
        """Test update_state processes LED state from REST."""
        cm = self._load_chefmaker()
        assert cm.ledpotkepton is False  # ledpotkepton = 0 in state file

    def test_update_state_mode_when_on(self):
        """Test update_state reads mode from state when device is on."""
        cm = self._load_chefmaker()
        # Simulate state with poweron=true and mode=cooking
        state = {
            POWERON_KEY: {"state": True},
            LIGHT_KEY: {"state": 1},
            CM_MODE_KEY: {"state": "cooking"},
            COOK_TIME_ESTIMATED_KEY: {"state": 1500},
            COOK_TIME_BEGIN_KEY: {"state": 1000},
        }
        cm.update_state(state)
        assert cm.is_on is True
        assert cm.mode == "cooking"
        # 300 seconds elapsed since the cook began: 1500 - 300 = 1200 remaining.
        with patch(PATCH_TIME, return_value=1300):
            assert cm.cook_time_remaining == 1200

    def test_update_state_mode_when_off(self):
        """Test update_state sets mode from power state when device is off."""
        cm = self._load_chefmaker()
        state = {
            POWERON_KEY: {"state": False},
            LIGHT_KEY: {"state": 0},
            CM_MODE_KEY: {"state": "standby"},
        }
        cm.update_state(state)
        assert cm.is_on is False
        assert cm.mode == "off"  # set_mode_from_is_on overrides

    def test_is_on_setter_sends_command(self):
        """Test is_on setter sends power command and updates mode."""
        cm = self._load_chefmaker()
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            cm.is_on = True
            mock_send_command.assert_called_once_with(cm, {POWERON_KEY: True})
        assert cm.mode == "standby"

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            cm.is_on = False
            mock_send_command.assert_called_once_with(cm, {POWERON_KEY: False})
        assert cm.mode == "off"

    def test_ledpotkepton_setter_sends_command(self):
        """Test LED setter sends command when value changes."""
        cm = self._load_chefmaker()
        # Initially ledpotkepton is 0 (off)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            cm.ledpotkepton = True
            mock_send_command.assert_called_once_with(cm, {LIGHT_KEY: 1})
        assert cm.ledpotkepton is True

    def test_ledpotkepton_setter_noop(self):
        """Test LED setter skips command when value hasn't changed."""
        cm = self._load_chefmaker()
        # Currently off (0), set to False (new_value=0, same)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            cm.ledpotkepton = False
            mock_send_command.assert_not_called()

    def test_ledpotkepton_setter_noop_already_on(self):
        """Test LED setter skips when already on and set to True."""
        cm = self._load_chefmaker()
        cm._ledpotkepton = 1  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            cm.ledpotkepton = True
            mock_send_command.assert_not_called()

    def test_mode_property(self):
        """Test mode property returns stored mode."""
        cm = self._load_chefmaker()
        cm.mode = "cooking"
        assert cm.mode == "cooking"
        cm.mode = None
        assert cm.mode is None

    def test_handle_server_update_poweron(self):
        """Test handle_server_update processes poweron."""
        cm = self._load_chefmaker()
        cm.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert cm.is_on is True
        assert cm.mode == "standby"

        cm.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
        assert cm.is_on is False
        assert cm.mode == "off"

    def test_handle_server_update_ledpotkepton(self):
        """Test handle_server_update processes ledpotkepton."""
        cm = self._load_chefmaker()
        cm.handle_server_update({REPORTED_KEY: {LIGHT_KEY: 1}})
        assert cm.ledpotkepton is True

        cm.handle_server_update({REPORTED_KEY: {LIGHT_KEY: 0}})
        assert cm.ledpotkepton is False

    def test_handle_server_update_cook_time_remaining_785(self):
        """Regression for #785: remaining time counts down instead of showing a static value.

        The device reports a static wkcountdown (300) that never counts down; remaining must be
        derived from the estimated total duration (wkestdu) and the cook start timestamp (wkbegin)
        instead.
        """
        cm = self._load_chefmaker()
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "cooking", COOK_TIME_ESTIMATED_KEY: 360, COOK_TIME_BEGIN_KEY: 1000}})
        # Just after the cook begins the full estimate remains.
        with patch(PATCH_TIME, return_value=1000):
            assert cm.cook_time_remaining == 360

        # As real time advances the remaining value must decrease.
        with patch(PATCH_TIME, return_value=1090):
            assert cm.cook_time_remaining == 270

    def test_handle_server_update_cook_time_remaining_863(self):
        """Regression for #863: DR-KCM001S never pushes wkpdu during a cook.

        Captured from the debug log attached to issue #863 for a real 300 second cook:
          - wkestdu = 300 is reported when the cook is configured.
          - wkbegin = 1785039118 (epoch seconds) is reported ~21s later at cook start.
          - No wkpdu / wkcountdown is ever pushed during the cook.
        With the old wkestdu - wkpdu logic the sensor stayed pinned at 300; deriving from wkbegin
        makes it count down and reach 0 by completion (device hit ckcomplete ~298.6s later).
        """
        cm = self._load_chefmaker()
        wkbegin = 1785039118

        # Cook configured: estimate reported before wkbegin arrives.
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "ckcfm", COOK_TIME_ESTIMATED_KEY: 300}})
        # Cook starts: wkbegin arrives, then mode -> cooking.
        cm.handle_server_update({REPORTED_KEY: {COOK_TIME_BEGIN_KEY: wkbegin}})
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "cooking"}})

        # At cook start the full duration remains.
        with patch(PATCH_TIME, return_value=wkbegin):
            assert cm.cook_time_remaining == 300

        # Midway through the cook it has counted down.
        with patch(PATCH_TIME, return_value=wkbegin + 120):
            assert cm.cook_time_remaining == 180

        # By the time the device reports ckcomplete (~300s later) it has reached 0.
        with patch(PATCH_TIME, return_value=wkbegin + 300):
            assert cm.cook_time_remaining == 0

        # On power-off the device reports wkestdu: 0, which also yields 0.
        cm.handle_server_update({REPORTED_KEY: {COOK_TIME_ESTIMATED_KEY: 0}})
        with patch(PATCH_TIME, return_value=wkbegin + 400):
            assert cm.cook_time_remaining == 0

    def test_handle_server_update_mode(self):
        """Test handle_server_update processes mode."""
        cm = self._load_chefmaker()
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "cooking"}})
        assert cm.mode == "cooking"

        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "ckpause"}})
        assert cm.mode == "ckpause"

    def test_handle_server_update_combined(self):
        """Test handle_server_update processes multiple keys."""
        cm = self._load_chefmaker()
        cm.handle_server_update({REPORTED_KEY: {POWERON_KEY: True, LIGHT_KEY: 1, CM_MODE_KEY: "cooking", COOK_TIME_ESTIMATED_KEY: 1000, COOK_TIME_BEGIN_KEY: 1000}})
        assert cm.is_on is True
        assert cm.ledpotkepton is True
        assert cm.mode == "cooking"
        # 100 seconds elapsed since the cook began: 1000 - 100 = 900 remaining.
        with patch(PATCH_TIME, return_value=1100):
            assert cm.cook_time_remaining == 900
