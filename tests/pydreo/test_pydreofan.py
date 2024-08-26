# pylint: disable=used-before-assignment
import logging
from typing import TYPE_CHECKING
from unittest.mock import patch
import pytest
import os

if TYPE_CHECKING:
    from  .imports import * # pylint: disable=W0401,W0614
    from . import call_json
    from .testbase import TestBase
else:
    from imports import * # pylint: disable=W0401,W0614
    import call_json
    from testbase import TestBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LOGIN_RESPONSE = call_json.LOGIN_RET_BODY


class TestPyDreoFan(TestBase):
    """Test PyDreoFan class."""
    def test_tower_load_and_send_commands(self):
        """Load fan and test sending commands."""
       
        self.getDevicesFileName = "get_devices_HTF008S.json"
        self.manager.load_devices()
        assert len(self.manager.fans) == 1
        fan = self.manager.fans[0]
        assert fan.speed_range == (1, 5)
        assert fan.preset_modes == ['normal', 'natural', 'sleep', 'auto']
        
        with patch('pydreo.PyDreo.send_command') as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})

        with patch('pydreo.PyDreo.send_command') as mock_send_command:
            fan.preset_mode = 'normal'
            mock_send_command.assert_called_once_with(fan, {WINDTYPE_KEY: 1})

        with pytest.raises(ValueError):
            fan.preset_mode = 'not_a_mode'

        with patch('pydreo.PyDreo.send_command') as mock_send_command:
            fan.fan_speed = 3
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 3})

        with pytest.raises(ValueError):
            fan.fan_speed = 10

    def test_circulator_load_and_send_commands(self):
        """Load circulator fan and test sending commands."""
        self.getDevicesFileName = "get_devices_HAF004S.json"
        self.manager.load_devices()

        assert len(self.manager.fans) == 1

        fan = self.manager.fans[0]

        assert fan.speed_range == (1, 9)
        assert fan.preset_modes == ['normal', 'natural', 'sleep', 'auto', 'turbo']
        
        with patch('pydreo.PyDreo.send_command') as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})

        with patch('pydreo.PyDreo.send_command') as mock_send_command:
            fan.preset_mode = 'normal'
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 1})

        with pytest.raises(ValueError):
            fan.preset_mode = 'not_a_mode'

        with patch('pydreo.PyDreo.send_command') as mock_send_command:
            fan.fan_speed = 3
            mock_send_command.assert_called_once_with(fan, {WINDLEVEL_KEY: 3})

        with pytest.raises(ValueError):
            fan.fan_speed = 10

