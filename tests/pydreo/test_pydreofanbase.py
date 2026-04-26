"""Tests for PyDreoFanBase - base class for all Dreo fans."""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch
import pytest
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND
from custom_components.dreo.pydreo.pydreofanbase import PyDreoFanBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

PATCH_BASE_PATH = "custom_components.dreo.pydreo"
PATCH_SET_SETTING = f"{PATCH_BASE_PATH}.PyDreo.set_device_setting"


class TestPyDreoFanBase(TestBase):
    """Test PyDreoFanBase class using a tower fan (HTF005S) as concrete implementation."""

    def _load_htf005s(self):
        """Helper to load HTF005S fan device."""
        self.get_devices_file_name = "get_devices_HTF005S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        return self.pydreo_manager.devices[0]

    def _load_htf010s(self):
        """Helper to load HTF010S fan device (uses WIND_MODE_KEY)."""
        self.get_devices_file_name = "get_devices_HTF010S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        return self.pydreo_manager.devices[0]

    # --- fan_speed setter no-op ---
    def test_fan_speed_noop_when_unchanged(self):
        """Test fan_speed setter skips command when value hasn't changed."""
        fan = self._load_htf005s()
        # Set initial speed via websocket
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 5}})
        assert fan.fan_speed == 5

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.fan_speed = 5  # same value
            mock_send_command.assert_not_called()

    # --- preset_mode setter with unsupported mode ---
    def test_preset_mode_unsupported_raises_value_error(self):
        """Test preset_mode setter raises ValueError for invalid mode."""
        fan = self._load_htf005s()
        with pytest.raises(ValueError, match="not in the acceptable list"):
            fan.preset_mode = "turbo_mode"

    def test_preset_mode_noop_when_unchanged(self):
        """Test preset_mode setter skips command when value hasn't changed."""
        fan = self._load_htf005s()
        # Set wind_type to 'normal' (value 1) via websocket
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 1}})
        assert fan.preset_mode == "normal"

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "normal"  # same value
            mock_send_command.assert_not_called()

    def test_preset_mode_none_when_no_modes(self):
        """Test preset_mode returns None when _preset_modes is None."""
        fan = self._load_htf005s()
        fan._preset_modes = None  # pylint: disable=protected-access
        assert fan.preset_mode is None

    def test_preset_mode_setter_raises_when_no_modes(self):
        """Test preset_mode setter raises NotImplementedError when modes not supported."""
        fan = self._load_htf005s()
        fan._preset_modes = None  # pylint: disable=protected-access
        with pytest.raises(NotImplementedError, match="doesn't support modes"):
            fan.preset_mode = "normal"

    def test_preset_mode_setter_raises_when_no_wind_type_or_mode(self):
        """Test preset_mode setter raises when neither wind_type nor wind_mode is set."""
        fan = self._load_htf005s()
        fan._wind_type = None  # pylint: disable=protected-access
        fan._wind_mode = None  # pylint: disable=protected-access
        with pytest.raises(NotImplementedError, match="doesn't support"):
            fan.preset_mode = "normal"

    def test_preset_mode_uses_wind_mode_key(self):
        """Test preset_mode setter uses WIND_MODE_KEY when wind_mode is set."""
        fan = self._load_htf010s()
        # HTF010S uses WIND_MODE_KEY
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 1}})
        assert fan.preset_mode == "normal"

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.preset_mode = "natural"
            mock_send_command.assert_called_once_with(fan, {WIND_MODE_KEY: 2})

    # --- temperature and temperature_offset properties ---
    def test_temperature_property(self):
        """Test temperature property returns raw temperature."""
        fan = self._load_htf005s()
        fan.handle_server_update({REPORTED_KEY: {TEMPERATURE_KEY: 72}})
        assert fan.temperature is not None

    def test_temperature_with_offset(self):
        """Test temperature property adds offset when available."""
        fan = self._load_htf005s()
        # HTF005S has temperature_offset support (loaded from settings file)
        fan.handle_server_update({REPORTED_KEY: {TEMPERATURE_KEY: 72}})
        assert fan.temperature_offset is not None
        expected = 72 + fan.temperature_offset
        assert fan.temperature == expected

    def test_temperature_none(self):
        """Test temperature returns None when no temperature data."""
        fan = self._load_htf005s()
        fan._temperature = None  # pylint: disable=protected-access
        assert fan.temperature is None

    def test_temperature_offset_property(self):
        """Test temperature_offset returns stored value."""
        fan = self._load_htf005s()
        assert fan.temperature_offset is not None

    def test_temperature_offset_setter(self):
        """Test temperature_offset setter calls _set_setting."""
        fan = self._load_htf005s()
        with patch(PATCH_SET_SETTING) as mock_set_setting:
            fan.temperature_offset = 3
            mock_set_setting.assert_called_once()

    def test_temperature_offset_setter_raises_when_unsupported(self):
        """Test temperature_offset setter raises NotImplementedError when not supported."""
        fan = self._load_htf005s()
        fan._temperature_offset = None  # pylint: disable=protected-access
        with pytest.raises(NotImplementedError, match="doesn't support"):
            fan.temperature_offset = 3

    def test_temperature_units_fahrenheit(self):
        """Test temperature_units returns FAHRENHEIT for temps > 50."""
        fan = self._load_htf005s()
        fan._temperature = 72  # pylint: disable=protected-access
        assert fan.temperature_units == TemperatureUnit.FAHRENHEIT

    def test_temperature_units_celsius(self):
        """Test temperature_units returns CELSIUS for temps <= 50."""
        fan = self._load_htf005s()
        fan._temperature = 25  # pylint: disable=protected-access
        assert fan.temperature_units == TemperatureUnit.CELSIUS

    def test_temperature_units_none_temp(self):
        """Test temperature_units returns CELSIUS when temperature is None."""
        fan = self._load_htf005s()
        fan._temperature = None  # pylint: disable=protected-access
        assert fan.temperature_units == TemperatureUnit.CELSIUS

    # --- is_on / poweron ---
    def test_is_on_property(self):
        """Test is_on returns current power state."""
        fan = self._load_htf005s()
        assert fan.is_on is not None

    def test_is_on_setter_sends_command(self):
        """Test is_on setter sends power command."""
        fan = self._load_htf005s()
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_called_once_with(fan, {POWERON_KEY: True})

    def test_is_on_setter_power_on_key_none(self):
        """Test is_on setter returns early when _power_on_key is None."""
        fan = self._load_htf005s()
        fan._power_on_key = None  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.is_on = True
            mock_send_command.assert_not_called()

    # --- parse_speed_range edge cases ---
    def test_parse_speed_range_no_controls_conf(self):
        """Test parse_speed_range returns None with no controlsConf."""
        fan = self._load_htf005s()
        result = fan.parse_speed_range({})
        assert result is None

    def test_parse_speed_range_controls_conf_no_extras_no_control(self):
        """Test parse_speed_range returns None when controlsConf has no relevant nodes."""
        fan = self._load_htf005s()
        result = fan.parse_speed_range({"controlsConf": {}})
        assert result is None

    def test_parse_speed_range_from_control_node_no_speed_type(self):
        """Test parse_speed_range_from_control_node returns None when no Speed type found."""
        fan = self._load_htf005s()
        control_node = [{"type": "Mode", "items": []}]
        result = fan.parse_speed_range_from_control_node(control_node)
        assert result is None

    def test_parse_speed_range_from_control_node_insufficient_items(self):
        """Test parse_speed_range_from_control_node warns when items < 2."""
        fan = self._load_htf005s()
        control_node = [{"type": "Speed", "items": [{"value": 1}]}]
        result = fan.parse_speed_range_from_control_node(control_node)
        assert result is None

    def test_parse_speed_range_from_control_node_no_items(self):
        """Test parse_speed_range_from_control_node handles missing items key."""
        fan = self._load_htf005s()
        control_node = [{"type": "Speed"}]
        result = fan.parse_speed_range_from_control_node(control_node)
        assert result is None

    def test_parse_speed_range_from_control_node_valid(self):
        """Test parse_speed_range_from_control_node returns tuple from valid items."""
        fan = self._load_htf005s()
        control_node = [{"type": "Speed", "items": [{"value": 1}, {"value": 12}]}]
        result = fan.parse_speed_range_from_control_node(control_node)
        assert result == (1, 12)

    def test_parse_speed_range_extraconfigs_control(self):
        """Test parse_speed_range via extraConfigs/control path."""
        fan = self._load_htf005s()
        details = {"controlsConf": {"extraConfigs": [{"key": "control", "value": [{"type": "Speed", "items": [{"value": 1}, {"value": 8}]}]}]}}
        result = fan.parse_speed_range(details)
        assert result == (1, 8)

    def test_parse_speed_range_extraconfigs_no_match(self):
        """Test parse_speed_range falls through extraConfigs when key != control."""
        fan = self._load_htf005s()
        details = {"controlsConf": {"extraConfigs": [{"key": "other", "value": []}]}}
        result = fan.parse_speed_range(details)
        assert result is None

    def test_parse_speed_range_control_node_path(self):
        """Test parse_speed_range via controlsConf/control path."""
        fan = self._load_htf005s()
        details = {"controlsConf": {"control": [{"type": "Speed", "items": [{"value": 1}, {"value": 6}]}]}}
        result = fan.parse_speed_range(details)
        assert result == (1, 6)

    # --- handle_server_update for various keys ---
    def test_handle_server_update_windlevel(self):
        """Test handle_server_update processes windlevel."""
        fan = self._load_htf005s()
        fan.handle_server_update({REPORTED_KEY: {WINDLEVEL_KEY: 7}})
        assert fan.fan_speed == 7

    def test_handle_server_update_temperature(self):
        """Test handle_server_update processes temperature."""
        fan = self._load_htf005s()
        fan.handle_server_update({REPORTED_KEY: {TEMPERATURE_KEY: 68}})
        assert fan._temperature == 68  # pylint: disable=protected-access

    def test_handle_server_update_ledalwayson(self):
        """Test handle_server_update processes ledalwayson."""
        fan = self._load_htf005s()
        fan.handle_server_update({REPORTED_KEY: {LEDALWAYSON_KEY: True}})
        assert fan._led_always_on is True  # pylint: disable=protected-access

    def test_handle_server_update_voiceon(self):
        """Test handle_server_update processes voiceon."""
        fan = self._load_htf005s()
        fan.handle_server_update({REPORTED_KEY: {VOICEON_KEY: False}})
        assert fan._voice_on is False  # pylint: disable=protected-access

    def test_handle_server_update_wind_mode(self):
        """Test handle_server_update processes wind mode."""
        fan = self._load_htf010s()
        fan.handle_server_update({REPORTED_KEY: {WIND_MODE_KEY: 3}})
        assert fan._wind_mode == 3  # pylint: disable=protected-access

    def test_handle_server_update_windtype(self):
        """Test handle_server_update processes windtype."""
        fan = self._load_htf005s()
        fan.handle_server_update({REPORTED_KEY: {WINDTYPE_KEY: 2}})
        assert fan._wind_type == 2  # pylint: disable=protected-access

    def test_handle_server_update_lightsensoron(self):
        """Test handle_server_update processes lightsensoron."""
        fan = self._load_htf005s()
        fan._light_sensor_on = False  # pylint: disable=protected-access
        fan.handle_server_update({REPORTED_KEY: {LIGHTSENSORON_KEY: True}})
        assert fan._light_sensor_on is True  # pylint: disable=protected-access

    def test_handle_server_update_muteon(self):
        """Test handle_server_update processes muteon."""
        fan = self._load_htf005s()
        fan._mute_on = False  # pylint: disable=protected-access
        fan.handle_server_update({REPORTED_KEY: {MUTEON_KEY: True}})
        assert fan._mute_on is True  # pylint: disable=protected-access

    def test_handle_server_update_pm25(self):
        """Test handle_server_update processes pm25."""
        fan = self._load_htf010s()
        fan.handle_server_update({REPORTED_KEY: {PM25_KEY: 15}})
        assert fan._pm25 == 15  # pylint: disable=protected-access

    def test_handle_server_update_poweron(self):
        """Test handle_server_update processes power state."""
        fan = self._load_htf005s()
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
        assert fan.is_on is False
        fan.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})
        assert fan.is_on is True

    # --- display_auto_off ---
    def test_display_auto_off_property(self):
        """Test display_auto_off returns inverse of _led_always_on."""
        fan = self._load_htf005s()
        fan._led_always_on = True  # pylint: disable=protected-access
        assert fan.display_auto_off is False
        fan._led_always_on = False  # pylint: disable=protected-access
        assert fan.display_auto_off is True

    def test_display_auto_off_none(self):
        """Test display_auto_off returns None when not supported."""
        fan = self._load_htf005s()
        fan._led_always_on = None  # pylint: disable=protected-access
        assert fan.display_auto_off is None

    def test_display_auto_off_setter_noop(self):
        """Test display_auto_off setter skips command when unchanged."""
        fan = self._load_htf005s()
        fan._led_always_on = True  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.display_auto_off = False  # not value = True, same as current
            mock_send_command.assert_not_called()

    def test_display_auto_off_setter_sends_command(self):
        """Test display_auto_off setter sends ledalwayson command."""
        fan = self._load_htf005s()
        fan._led_always_on = True  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.display_auto_off = True  # not value = False, different
            mock_send_command.assert_called_once_with(fan, {LEDALWAYSON_KEY: False})

    def test_display_auto_off_setter_raises_unsupported(self):
        """Test display_auto_off setter raises when not supported."""
        fan = self._load_htf005s()
        fan._led_always_on = None  # pylint: disable=protected-access
        with pytest.raises(NotImplementedError):
            fan.display_auto_off = True

    # --- adaptive_brightness ---
    def test_adaptive_brightness_property(self):
        """Test adaptive_brightness returns _light_sensor_on value."""
        fan = self._load_htf005s()
        fan._light_sensor_on = True  # pylint: disable=protected-access
        assert fan.adaptive_brightness is True

    def test_adaptive_brightness_none(self):
        """Test adaptive_brightness returns None when not supported."""
        fan = self._load_htf005s()
        fan._light_sensor_on = None  # pylint: disable=protected-access
        assert fan.adaptive_brightness is None

    def test_adaptive_brightness_setter_noop(self):
        """Test adaptive_brightness setter skips when unchanged."""
        fan = self._load_htf005s()
        fan._light_sensor_on = True  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.adaptive_brightness = True
            mock_send_command.assert_not_called()

    def test_adaptive_brightness_setter_sends_command(self):
        """Test adaptive_brightness setter sends command."""
        fan = self._load_htf005s()
        fan._light_sensor_on = False  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.adaptive_brightness = True
            mock_send_command.assert_called_once_with(fan, {LIGHTSENSORON_KEY: True})

    def test_adaptive_brightness_setter_raises_unsupported(self):
        """Test adaptive_brightness setter raises when not supported."""
        fan = self._load_htf005s()
        fan._light_sensor_on = None  # pylint: disable=protected-access
        with pytest.raises(NotImplementedError):
            fan.adaptive_brightness = True

    # --- panel_sound ---
    def test_panel_sound_voice_on(self):
        """Test panel_sound returns _voice_on when set."""
        fan = self._load_htf005s()
        fan._voice_on = True  # pylint: disable=protected-access
        assert fan.panel_sound is True

    def test_panel_sound_mute_on(self):
        """Test panel_sound returns inverse of _mute_on when _voice_on is None."""
        fan = self._load_htf005s()
        fan._voice_on = None  # pylint: disable=protected-access
        fan._mute_on = True  # pylint: disable=protected-access
        assert fan.panel_sound is False

    def test_panel_sound_none(self):
        """Test panel_sound returns None when neither voice nor mute supported."""
        fan = self._load_htf005s()
        fan._voice_on = None  # pylint: disable=protected-access
        fan._mute_on = None  # pylint: disable=protected-access
        assert fan.panel_sound is None

    def test_panel_sound_setter_voice_noop(self):
        """Test panel_sound setter skips when voice_on already matches."""
        fan = self._load_htf005s()
        fan._voice_on = True  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.panel_sound = True
            mock_send_command.assert_not_called()

    def test_panel_sound_setter_voice_sends(self):
        """Test panel_sound setter sends voiceon command."""
        fan = self._load_htf005s()
        fan._voice_on = False  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.panel_sound = True
            mock_send_command.assert_called_once_with(fan, {VOICEON_KEY: True})

    def test_panel_sound_setter_mute_noop(self):
        """Test panel_sound setter skips when mute_on already matches."""
        fan = self._load_htf005s()
        fan._voice_on = None  # pylint: disable=protected-access
        fan._mute_on = False  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.panel_sound = True  # not value = False, same as _mute_on
            mock_send_command.assert_not_called()

    def test_panel_sound_setter_mute_sends(self):
        """Test panel_sound setter sends muteon command."""
        fan = self._load_htf005s()
        fan._voice_on = None  # pylint: disable=protected-access
        fan._mute_on = True  # pylint: disable=protected-access
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.panel_sound = True  # not value = False, different from _mute_on=True
            mock_send_command.assert_called_once_with(fan, {MUTEON_KEY: False})

    def test_panel_sound_setter_raises_unsupported(self):
        """Test panel_sound setter raises when not supported."""
        fan = self._load_htf005s()
        fan._voice_on = None  # pylint: disable=protected-access
        fan._mute_on = None  # pylint: disable=protected-access
        with pytest.raises(NotImplementedError):
            fan.panel_sound = True

    # --- pm25 ---
    def test_pm25_property(self):
        """Test pm25 returns stored value."""
        fan = self._load_htf010s()
        assert fan.pm25 is not None

    def test_pm25_none(self):
        """Test pm25 returns None when not set."""
        fan = self._load_htf005s()
        fan._pm25 = None  # pylint: disable=protected-access
        assert fan.pm25 is None

    def test_pm25_setter_noop(self):
        """Test pm25 setter skips when unchanged."""
        fan = self._load_htf010s()
        current_pm25 = fan.pm25
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.pm25 = current_pm25
            mock_send_command.assert_not_called()

    def test_pm25_setter_sends(self):
        """Test pm25 setter sends command."""
        fan = self._load_htf010s()
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            fan.pm25 = 99
            mock_send_command.assert_called_once_with(fan, {PM25_KEY: 99})

    def test_pm25_setter_raises_unsupported(self):
        """Test pm25 setter raises when not supported."""
        fan = self._load_htf005s()
        fan._pm25 = None  # pylint: disable=protected-access
        with pytest.raises(NotImplementedError):
            fan.pm25 = 10

    # --- update_state with FANON_KEY fallback ---
    def test_update_state_fanon_fallback(self):
        """Test update_state uses FANON_KEY when POWERON_KEY is absent."""
        fan = self._load_htf005s()
        state = {
            FANON_KEY: {"state": True},
            WINDLEVEL_KEY: {"state": 5},
        }
        fan.update_state(state)
        assert fan.is_on is True
        assert fan._power_on_key == FANON_KEY  # pylint: disable=protected-access

    def test_update_state_no_power_key_defaults_poweron(self):
        """Test update_state defaults _power_on_key to POWERON_KEY when neither key present."""
        fan = self._load_htf005s()
        fan._power_on_key = None  # pylint: disable=protected-access
        state = {
            WINDLEVEL_KEY: {"state": 3},
        }
        fan.update_state(state)
        assert fan._power_on_key == POWERON_KEY  # pylint: disable=protected-access

    def test_preset_mode_returns_none_when_mode_values_none(self):
        """Test preset_mode returns None when both _wind_mode and _wind_type are None."""
        fan = self._load_htf005s()
        fan._wind_mode = None  # pylint: disable=protected-access
        fan._wind_type = None  # pylint: disable=protected-access
        assert fan.preset_mode is None

    def test_preset_modes_property_none(self):
        """Test preset_modes returns None when _preset_modes is None."""
        fan = self._load_htf005s()
        fan._preset_modes = None  # pylint: disable=protected-access
        assert fan.preset_modes is None

    # --- parse_preset_modes raises NotImplementedError ---
    def test_parse_preset_modes_raises(self):
        """Test parse_preset_modes raises NotImplementedError (must be overridden)."""
        fan = self._load_htf005s()
        with pytest.raises(NotImplementedError):
            PyDreoFanBase.parse_preset_modes(fan, {})

    # --- preset_mode returns None for unrecognized numeric value ---
    def test_preset_mode_returns_none_for_unknown_value(self):
        """Test preset_mode returns None when name lookup yields no match."""
        fan = self._load_htf005s()
        fan._wind_type = 999  # pylint: disable=protected-access
        assert fan.preset_mode is None

    # --- oscillating property/setter raise NotImplementedError ---
    def test_oscillating_property_raises(self):
        """Test oscillating property raises NotImplementedError on base class."""
        fan = self._load_htf005s()
        with pytest.raises(NotImplementedError):
            PyDreoFanBase.oscillating.fget(fan)

    def test_oscillating_setter_raises(self):
        """Test oscillating setter raises NotImplementedError on base class."""
        fan = self._load_htf005s()
        with pytest.raises(NotImplementedError):
            PyDreoFanBase.oscillating.fset(fan, True)

    # --- update_state with no fan speed ---
    def test_update_state_no_fan_speed(self):
        """Test update_state logs error when fan speed is missing from state."""
        fan = self._load_htf005s()
        state = {
            POWERON_KEY: {"state": True},
        }
        fan.update_state(state)
        assert fan.is_on is True
