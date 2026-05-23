"""Focused tests for device fixtures that lacked direct functional coverage."""
from unittest.mock import patch

import pytest

from .imports import *  # pylint: disable=W0401,W0614
from .testbase import PATCH_SEND_COMMAND, TestBase


def _pick_alternative(current_value, values):
    """Return a value from values that differs from current_value."""
    for value in values or []:
        if value != current_value:
            return value
    return None


def _assert_command_sent(mock_send_command, device):
    """Assert a single command call was made for the provided device."""
    mock_send_command.assert_called_once()
    call_args = mock_send_command.call_args[0]
    assert call_args[0] is device
    assert isinstance(call_args[1], dict)
    assert len(call_args[1]) >= 1


class TestUncoveredDeviceModels(TestBase):
    """Add functional command coverage for previously uncovered device fixtures."""

    @pytest.mark.parametrize(
        "devices_file,expected_count",
        [
            ("get_devices_HPF005S.json", 1),
            ("get_devices_HPF007S.json", 1),
            ("get_devices_HPF020S.json", 1),
            ("get_devices_HAF003S.json", 2),
            ("get_devices_HAF004S_2REVS.json", 2),
        ],
    )
    def test_air_circulator_models(self, devices_file: str, expected_count: int):  # pylint: disable=invalid-name
        """Test uncovered air circulator models exercise core controls."""
        self.get_devices_file_name = devices_file
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == expected_count

        for fan in self.pydreo_manager.devices:
            assert isinstance(fan, PyDreoAirCirculator)

            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.is_on = not bool(fan.is_on)
                _assert_command_sent(mock_send_command, fan)

            low, high = fan.speed_range
            target_speed = low if fan.fan_speed != low else high
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.fan_speed = target_speed
                _assert_command_sent(mock_send_command, fan)

            target_mode = _pick_alternative(fan.preset_mode, fan.preset_modes)
            if target_mode is not None:
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    fan.preset_mode = target_mode
                    _assert_command_sent(mock_send_command, fan)

    def test_hac005s_air_conditioner(self):  # pylint: disable=invalid-name
        """Test uncovered HAC005S model exercises core AC controls."""
        self.get_devices_file_name = "get_devices_HAC005S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        ac: PyDreoAC = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            ac.poweron = not bool(ac.poweron)
            _assert_command_sent(mock_send_command, ac)

        target_mode = _pick_alternative(ac.mode, ac.modes)
        if target_mode is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ac.mode = target_mode
                _assert_command_sent(mock_send_command, ac)

        if ac.target_humidity is not None:
            target_humidity = ac.target_humidity + 1
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                ac.target_humidity = target_humidity
                _assert_command_sent(mock_send_command, ac)

    def test_hcf003s_ceiling_fan(self):  # pylint: disable=invalid-name
        """Test uncovered HCF003S model exercises fan and light controls."""
        self.get_devices_file_name = "get_devices_HCF003S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        fan: PyDreoCeilingFan = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = not bool(fan.is_on)
            _assert_command_sent(mock_send_command, fan)

        low, high = fan.speed_range
        target_speed = low if fan.fan_speed != low else high
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = target_speed
            _assert_command_sent(mock_send_command, fan)

        target_mode = _pick_alternative(fan.preset_mode, fan.preset_modes)
        if target_mode is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.preset_mode = target_mode
                _assert_command_sent(mock_send_command, fan)

        if fan.light_on is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                fan.light_on = not fan.light_on
                _assert_command_sent(mock_send_command, fan)

    def test_hhm006s_humidifier(self):  # pylint: disable=invalid-name
        """Test uncovered HHM006S model exercises humidifier controls."""
        self.get_devices_file_name = "get_devices_HHM006S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        humidifier: PyDreoHumidifier = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.is_on = not bool(humidifier.is_on)
            _assert_command_sent(mock_send_command, humidifier)

        min_humidity, max_humidity = humidifier.target_humidity_range
        target_humidity = min_humidity if humidifier.target_humidity != min_humidity else max_humidity
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            humidifier.target_humidity = target_humidity
            _assert_command_sent(mock_send_command, humidifier)

        if humidifier.modes:
            target_mode = _pick_alternative(humidifier.mode, humidifier.modes)
            if target_mode is not None:
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    humidifier.mode = target_mode
                    _assert_command_sent(mock_send_command, humidifier)

        if humidifier.mist_level is not None:
            target_mist_level = 1 if humidifier.mist_level != 1 else 2
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                humidifier.mist_level = target_mist_level
                _assert_command_sent(mock_send_command, humidifier)

    @pytest.mark.parametrize("devices_file", ["get_devices_HSH003S.json", "get_devices_HSH034S.json"])
    def test_heater_models(self, devices_file: str):
        """Test uncovered heater models exercise core heater controls."""
        self.get_devices_file_name = devices_file
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater: PyDreoHeater = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = not bool(heater.poweron)
            _assert_command_sent(mock_send_command, heater)

        low, high = heater.htalevel_range
        target_heat_level = low if heater.htalevel != low else high
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = target_heat_level
            _assert_command_sent(mock_send_command, heater)

        target_mode = _pick_alternative(heater.mode, heater.modes)
        if target_mode is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.mode = target_mode
                _assert_command_sent(mock_send_command, heater)
