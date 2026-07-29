"""Tests for Dreo Chef Makers"""

# pylint: disable=used-before-assignment
import logging
from datetime import datetime, timezone
from unittest.mock import patch
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LIGHT_KEY = "ledpotkepton"
CM_MODE_KEY = "mode"
COOK_TIME_ESTIMATED_KEY = "wkestdu"
COOK_TIME_BEGIN_KEY = "wkbegin"


def _end_time(begin: int, estimated: int) -> datetime:
    """Expected cook end time as a timezone-aware UTC timestamp (wkbegin + wkestdu)."""
    return datetime.fromtimestamp(begin + estimated, tz=timezone.utc)


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
        # Device is idle (not cooking) in the fixture, so no cook end time is exposed.
        assert cm.cook_end_time is None

    def test_cook_end_time_when_cooking(self):
        """Cook end time is wkbegin + wkestdu, exposed as a timezone-aware UTC timestamp."""
        cm = self._load_chefmaker()
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "cooking", COOK_TIME_ESTIMATED_KEY: 600, COOK_TIME_BEGIN_KEY: 1000}})
        assert cm.cook_end_time == _end_time(1000, 600)

    def test_cook_end_time_when_paused(self):
        """Cook end time is still exposed while a cook is paused (ckpause)."""
        cm = self._load_chefmaker()
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "ckpause", COOK_TIME_ESTIMATED_KEY: 300, COOK_TIME_BEGIN_KEY: 2000}})
        assert cm.cook_end_time == _end_time(2000, 300)

    def test_cook_end_time_none_when_not_cooking(self):
        """Cook end time is None outside the active cooking/paused modes, even with valid fields.

        Gating on the active modes is what prevents a stale wkbegin left over from a previous cook
        from surfacing while the next cook is still configuring (see #864/#868).
        """
        cm = self._load_chefmaker()
        cm.handle_server_update({REPORTED_KEY: {COOK_TIME_ESTIMATED_KEY: 300, COOK_TIME_BEGIN_KEY: 1000}})
        for mode in ("standby", "ckcfm", "ckcomplete", "off"):
            cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: mode}})
            assert cm.cook_end_time is None, f"expected None for mode {mode}"

    def test_cook_end_time_none_when_estimated_zero(self):
        """Cook end time is None when the estimated duration is 0 (e.g. reported at power-off)."""
        cm = self._load_chefmaker()
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "cooking", COOK_TIME_ESTIMATED_KEY: 0, COOK_TIME_BEGIN_KEY: 1000}})
        assert cm.cook_end_time is None

    def test_cook_end_time_none_when_fields_absent(self):
        """Cook end time is None when the device has not reported the duration fields."""
        cm = self._load_chefmaker()
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "cooking"}})
        cm._cook_time_estimated = None  # pylint: disable=protected-access
        cm._cook_time_begin = None  # pylint: disable=protected-access
        assert cm.cook_end_time is None

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
        # Cook end time is wkbegin + wkestdu = 1000 + 1500 = 2500.
        assert cm.cook_end_time == _end_time(1000, 1500)

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

    def test_handle_server_update_cook_end_time_785(self):
        """Regression for #785: a real end time is exposed instead of a static wkcountdown.

        The device reports a static wkcountdown (300) that never counts down; the end time must be
        derived from the estimated total duration (wkestdu) and the cook start timestamp (wkbegin).
        """
        cm = self._load_chefmaker()
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "cooking", COOK_TIME_ESTIMATED_KEY: 360, COOK_TIME_BEGIN_KEY: 1000}})
        assert cm.cook_end_time == _end_time(1000, 360)

    def test_handle_server_update_cook_end_time_863(self):
        """Regression for #863: DR-KCM001S never pushes wkpdu during a cook.

        Captured from the debug log attached to issue #863 for a real 300 second cook:
          - wkestdu = 300 is reported when the cook is configured (mode ckcfm).
          - wkbegin = 1785039118 (epoch seconds) is reported ~21s later at cook start.
          - No wkpdu / wkcountdown is ever pushed during the cook.
        The end time must resolve to wkbegin + wkestdu once the cook is underway.
        """
        cm = self._load_chefmaker()
        wkbegin = 1785039118

        # Cook configured: estimate reported before wkbegin arrives, still in ckcfm -> no end time.
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "ckcfm", COOK_TIME_ESTIMATED_KEY: 300}})
        assert cm.cook_end_time is None

        # Cook starts: wkbegin arrives, then mode -> cooking.
        cm.handle_server_update({REPORTED_KEY: {COOK_TIME_BEGIN_KEY: wkbegin}})
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "cooking"}})
        assert cm.cook_end_time == _end_time(wkbegin, 300)

    def test_handle_server_update_cook_end_time_868(self):
        """Regression for #868: the end time is stable and correct without any further pushes.

        The device sent nothing between the "cooking" report and "ckcomplete" ~179s later, which
        froze the old ticking duration sensor.  A timestamp end time is written once and needs no
        further pushes; the frontend counts down on its own.  Reading the property repeatedly must
        return the same absolute end time (it does not depend on the local wall clock).
        """
        cm = self._load_chefmaker()
        wkbegin = 1785220828
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "cooking", COOK_TIME_ESTIMATED_KEY: 180, COOK_TIME_BEGIN_KEY: wkbegin}})
        expected = _end_time(wkbegin, 180)
        assert cm.cook_end_time == expected
        assert cm.cook_end_time == expected  # stable across reads, no drift

        # On completion the device reports ckcomplete then standby with wkestdu: 0.
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "ckcomplete"}})
        assert cm.cook_end_time is None
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "standby", COOK_TIME_ESTIMATED_KEY: 0}})
        assert cm.cook_end_time is None

    def test_cook_end_time_stale_wkbegin_not_exposed_during_configuring(self):
        """Regression for #864: a stale wkbegin from a previous cook must not surface an end time.

        The REST fixture (get_device_state_KCM001S_1.json) seeds wkbegin from a prior session.
        When a new cook reports wkestdu while still configuring (mode ckcfm) before pushing a fresh
        wkbegin, gating on the active cooking/paused modes keeps cook_end_time None rather than
        exposing a bogus timestamp built from the stale wkbegin.
        """
        cm = self._load_chefmaker()
        stale_begin = 1000
        cm._cook_time_begin = stale_begin  # pylint: disable=protected-access

        # New cook configured: wkestdu arrives, but wkbegin is still the stale value and mode ckcfm.
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "ckcfm", COOK_TIME_ESTIMATED_KEY: 300}})
        assert cm.cook_end_time is None

        # Once a fresh wkbegin arrives and the cook starts, the end time is correct.
        fresh_begin = 1785039118
        cm.handle_server_update({REPORTED_KEY: {COOK_TIME_BEGIN_KEY: fresh_begin, CM_MODE_KEY: "cooking"}})
        assert cm.cook_end_time == _end_time(fresh_begin, 300)

    def test_handle_server_update_mode(self):
        """Test handle_server_update processes mode, including the ckcfm configuring mode (#868)."""
        cm = self._load_chefmaker()
        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "cooking"}})
        assert cm.mode == "cooking"

        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "ckpause"}})
        assert cm.mode == "ckpause"

        cm.handle_server_update({REPORTED_KEY: {CM_MODE_KEY: "ckcfm"}})
        assert cm.mode == "ckcfm"

    def test_handle_server_update_combined(self):
        """Test handle_server_update processes multiple keys."""
        cm = self._load_chefmaker()
        cm.handle_server_update({REPORTED_KEY: {POWERON_KEY: True, LIGHT_KEY: 1, CM_MODE_KEY: "cooking", COOK_TIME_ESTIMATED_KEY: 1000, COOK_TIME_BEGIN_KEY: 1000}})
        assert cm.is_on is True
        assert cm.ledpotkepton is True
        assert cm.mode == "cooking"
        # Cook end time is wkbegin + wkestdu = 1000 + 1000 = 2000.
        assert cm.cook_end_time == _end_time(1000, 1000)
