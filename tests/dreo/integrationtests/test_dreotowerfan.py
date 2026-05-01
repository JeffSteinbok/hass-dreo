"""Tests for Dreo Fans"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from custom_components.dreo import fan, switch, sensor
from .imports import *  # pylint: disable=W0401,W0614
from .integrationtestbase import IntegrationTestBase, PATCH_SEND_COMMAND

PATCH_BASE_PATH = "homeassistant.helpers.entity.Entity"
PATCH_SCHEDULE_UPDATE_HA_STATE = f"{PATCH_BASE_PATH}.schedule_update_ha_state"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TestDreoTowerFan(IntegrationTestBase):
    """Test PyDreoFan class."""

    def test_HTF005S(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HTF005S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan = self.pydreo_manager.devices[0]

        # Test initial state values
        assert fan.speed_range == (1, 12)
        assert fan.preset_modes == ["normal", "natural", "sleep", "auto"]
        assert fan.oscillating is True
        assert fan.model == "DR-HTF005S"
        assert fan.serial_number is not None
        assert fan.is_on is not None
        assert fan.is_on is True

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        # Test all preset modes
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "natural"
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 2}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 3}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "auto"
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 4}})

        with pytest.raises(ValueError):
            fan.preset_mode = "not_a_mode"

        # Test speed commands at various levels
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 3
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 3}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 6
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 6})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 6}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 12
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 12})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 12}})

        # Test speed boundaries
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 13

        # Test oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = False
            mock_send_command.assert_called_once_with(fan, {SHAKEHORIZON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {SHAKEHORIZON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            mock_send_command.assert_called_once_with(fan, {SHAKEHORIZON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {SHAKEHORIZON_KEY: True}})

    def test_HTF018S(self):  # pylint: disable=invalid-name
        """Load HTF018S fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HTF018S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan = self.pydreo_manager.devices[0]

        # Test initial state values - speed_range and preset_modes come from SUPPORTED_DEVICES
        # since controlsConf only has a template reference
        assert fan.speed_range == (1, 9)
        assert fan.preset_modes == ["normal", "natural", "sleep", "auto"]
        assert fan.model == "DR-HTF018S"
        assert fan.serial_number is not None
        assert fan.is_on is True
        assert fan.oscillating is False

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

        # Test all preset modes
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "natural"
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 2}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 3}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "auto"
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 4}})

        with pytest.raises(ValueError):
            fan.preset_mode = "not_a_mode"

        # Test speed commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 5
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 5})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 5}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 9
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 9})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 9}})

        # Test speed boundaries
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 10

        # Test oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            mock_send_command.assert_called_once_with(fan, {SHAKEHORIZON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {SHAKEHORIZON_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = False
            mock_send_command.assert_called_once_with(fan, {SHAKEHORIZON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {SHAKEHORIZON_KEY: False}})

    def test_HTF024S(self):  # pylint: disable=invalid-name
        """Load HTF024S fan and test sending commands."""

        self.get_devices_file_name = "get_devices_HTF024S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan = self.pydreo_manager.devices[0]

        # Test initial state values - speed_range and preset_modes come from SUPPORTED_DEVICES
        # since controlsConf only has a template reference
        assert fan.speed_range == (1, 9)
        assert fan.preset_modes == ["normal", "natural", "sleep", "auto"]
        assert fan.model == "DR-HTF024S"
        assert fan.serial_number is not None
        assert fan.is_on is True
        assert fan.oscillating is False

        # Test power commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = False
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

        # Test all preset modes
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "natural"
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 2})
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 2}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "sleep"
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 3})
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 3}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "auto"
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 4})
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 4}})

        with pytest.raises(ValueError):
            fan.preset_mode = "not_a_mode"

        # Test speed commands
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 5
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 5})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 5}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 9
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 9})
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 9}})

        # Test speed boundaries
        with pytest.raises(ValueError):
            fan.fan_speed = 0

        with pytest.raises(ValueError):
            fan.fan_speed = 10

        # Test oscillation
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = True
            mock_send_command.assert_called_once_with(fan, {SHAKEHORIZON_KEY: True})
        fan.handle_server_update({REPORTED_KEY: {SHAKEHORIZON_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.oscillating = False
            mock_send_command.assert_called_once_with(fan, {SHAKEHORIZON_KEY: False})
        fan.handle_server_update({REPORTED_KEY: {SHAKEHORIZON_KEY: False}})

    def test_HTF007S(self):  # pylint: disable=invalid-name
        """Load HTF007S tower fan and test HA entity."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HTF007S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_fan = self.pydreo_manager.devices[0]
            assert pydreo_fan.model == "DR-HTF007S"
            assert pydreo_fan.speed_range == (1, 4)
            assert pydreo_fan.preset_modes == ["normal", "natural", "sleep", "auto"]

            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert ha_fan.speed_count == 4
            assert ha_fan.unique_id is not None
            assert ha_fan.name is not None
            assert ha_fan.preset_modes == ["normal", "natural", "sleep", "auto"]

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: True})
            pydreo_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: False})
            pydreo_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

            # Test max speed (fan off, so turn_on fires too)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)
                mock_send_command.assert_any_call(pydreo_fan, {WINDLEVEL_KEY: 4})

            switches = switch.get_entries([pydreo_fan])
            self.verify_expected_entities(switches, ["Display Auto Off", "Panel Sound"])
            sensors = sensor.get_entries([pydreo_fan])
            self.verify_expected_entities(sensors, ["Temperature"])

    def test_HTF008S(self):  # pylint: disable=invalid-name
        """Load HTF008S tower fan and test HA entity."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HTF008S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_fan = self.pydreo_manager.devices[0]
            assert pydreo_fan.model == "DR-HTF008S"

            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert ha_fan.unique_id is not None
            assert ha_fan.name is not None

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: True})
            pydreo_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: False})
            pydreo_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

            switches = switch.get_entries([pydreo_fan])
            self.verify_expected_entities(switches, ["Display Auto Off", "Panel Sound"])
            sensors = sensor.get_entries([pydreo_fan])
            self.verify_expected_entities(sensors, ["Temperature"])

    def test_HTF009S(self):  # pylint: disable=invalid-name
        """Load HTF009S tower fan and test HA entity."""
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HTF009S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_fan = self.pydreo_manager.devices[0]
            assert pydreo_fan.model == "DR-HTF009S"
            assert pydreo_fan.speed_range == (1, 9)
            assert pydreo_fan.preset_modes == ["normal", "natural", "sleep", "auto"]

            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert ha_fan.speed_count == 9
            assert ha_fan.unique_id is not None
            assert ha_fan.name is not None
            assert ha_fan.preset_modes == ["normal", "natural", "sleep", "auto"]

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: True})
            pydreo_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: False})
            pydreo_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

            # Test max speed (fan off, so turn_on fires too)
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_percentage(100)
                mock_send_command.assert_any_call(pydreo_fan, {WINDLEVEL_KEY: 9})

            switches = switch.get_entries([pydreo_fan])
            self.verify_expected_entities(switches, ["Display Auto Off", "Panel Sound"])
            sensors = sensor.get_entries([pydreo_fan])
            self.verify_expected_entities(sensors, ["Temperature"])

    def test_HTF010S(self):  # pylint: disable=invalid-name
        """Load HTF010S tower fan and test HA entity.

        HTF010S differs from HTF005S: uses WIND_MODE_KEY for preset modes and
        OSCON_KEY for oscillation.
        """
        with patch(PATCH_SCHEDULE_UPDATE_HA_STATE):
            self.get_devices_file_name = "get_devices_HTF010S.json"
            self.pydreo_manager.load_devices()
            assert len(self.pydreo_manager.devices) == 1

            pydreo_fan = self.pydreo_manager.devices[0]
            assert pydreo_fan.model == "DR-HTF010S"
            assert pydreo_fan.speed_range == (1, 12)
            assert pydreo_fan.preset_modes == ["normal", "natural", "sleep", "auto"]

            ha_fan = fan.DreoFanHA(pydreo_fan)
            assert ha_fan.speed_count == 12
            assert ha_fan.unique_id is not None
            assert ha_fan.name is not None
            assert ha_fan.preset_modes == ["normal", "natural", "sleep", "auto"]

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_on()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: True})
            pydreo_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.turn_off()
                mock_send_command.assert_called_once_with(pydreo_fan, {POWERON_KEY: False})
            pydreo_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

            # Test preset mode (HTF010S uses WIND_MODE_KEY, not WINDTYPE_KEY)
            pydreo_fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ha_fan.set_preset_mode("natural")
                mock_send_command.assert_called_once_with(pydreo_fan, {WIND_MODE_KEY: 2})
            pydreo_fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 2}})

            switches = switch.get_entries([pydreo_fan])
            self.verify_expected_entities(switches, ["Panel Sound"])
            sensors = sensor.get_entries([pydreo_fan])
            self.verify_expected_entities(sensors, ["Temperature", "pm25"])
