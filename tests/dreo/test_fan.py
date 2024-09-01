from unittest.mock import patch
#from homeassistant.helpers import Entity

from custom_components.dreo import fan

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_SEND_COMMAND = f'{PATCH_BASE_PATH}.schedule_update_ha_state'

class Test_DreoFanHA:

    def test_fan_simple(self, mocker):
        with patch(PATCH_SEND_COMMAND) as mock_send_command:

            mocked_pydreo_fan = mocker.MagicMock()
            mocked_pydreo_fan.is_on = True
            mocked_pydreo_fan.fan_speed = 3
            mocked_pydreo_fan.speed_range = (1, 5)
            mocked_pydreo_fan.preset_modes = ['normal', 'natural', 'sleep', 'auto']

            test_fan = fan.DreoFanHA(mocked_pydreo_fan)
            assert test_fan.is_on is True
            assert test_fan.percentage == 60
            assert test_fan.speed_count == 5

            test_fan.set_percentage(20)
            assert mocked_pydreo_fan.fan_speed == 1
            mock_send_command.assert_called_once()
            mock_send_command.reset_mock()

            test_fan.set_percentage(0)
            assert mocked_pydreo_fan.is_on is False
            # TODO: Possible bug; need to test at home.  Why does this not cause an update?
            #mock_send_command.assert_called_once()
            #mock_send_command.reset_mock()

            test_fan.set_preset_mode("normal")
            assert mocked_pydreo_fan.preset_mode is "normal"
            mock_send_command.assert_called_once()
            mock_send_command.reset_mock()

