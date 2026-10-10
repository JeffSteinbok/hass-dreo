"""Tests for Dreo Heaters"""

# pylint: disable=used-before-assignment
import logging
from unittest.mock import patch, call
import pytest
from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HEATER_EXHAUSTIVE_MODELS = [
    "get_devices_HSH003S.json",
    "get_devices_HSH004S.json",
    "get_devices_HSH006S.json",
    "get_devices_HSH009S.json",
    "get_devices_HSH010S.json",
    "get_devices_HSH011.json",
    "get_devices_HSH011S.json",
    "get_devices_HSH016S.json",
    "get_devices_HSH034S.json",
    "get_devices_HSH040S.json",
    "get_devices_HSH041S.json",
    "get_devices_WH714S.json",
]


class TestPyDreoHeater(TestBase):
    """Test PyDreoHeater class."""

    def _exercise_all_settable_properties(self, heater: PyDreoHeater):
        """Exercise all writable heater properties that are supported by a model."""
        _ = heater.poweron
        _ = heater.htalevel_range
        _ = heater.modes
        _ = heater.devon
        _ = heater.htalevel
        _ = heater.ecolevel_range
        _ = heater.ecolevel
        _ = heater.mode
        _ = heater.temperature
        _ = heater.temperature_offset
        _ = heater.temperature_units
        _ = heater.oscon
        _ = heater.oscangle
        _ = heater.oscmode
        _ = heater.ptcon
        _ = heater.display_auto_off
        _ = heater.ctlstatus
        _ = heater.childlockon
        _ = heater.panel_sound
        _ = heater.coolmode
        _ = heater.coollevel
        _ = heater.coollevel_range
        _ = heater.horizontally_oscillating
        _ = heater.horizontal_osc_angle_left
        _ = heater.horizontal_osc_angle_right
        _ = heater.horizontal_angle
        _ = heater.lightmode
        _ = heater.window_detection

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = not bool(heater.poweron)
            mock_send_command.assert_called_once()

        if heater.htalevel is not None and heater.htalevel_range is not None:
            low, high = heater.htalevel_range
            new_heat_level = low if heater.htalevel != low else high
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.htalevel = new_heat_level
                mock_send_command.assert_called_once()

        different_mode = next((mode for mode in heater.modes if mode != heater.mode), None)
        if different_mode is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.mode = different_mode
                mock_send_command.assert_called_once()

        if heater.ecolevel is not None:
            eco_low, eco_high = heater.ecolevel_range
            new_eco = eco_low if heater.ecolevel != eco_low else eco_high
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.ecolevel = new_eco
                mock_send_command.assert_called_once()

        if heater.devon is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.devon = not bool(heater.devon)
                mock_send_command.assert_called_once()

        if heater.oscon is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.oscon = not bool(heater.oscon)
                mock_send_command.assert_called_once()

        if heater.oscangle is not None:
            new_oscangle = 90 if heater.oscangle != 90 else 120
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.oscangle = new_oscangle
                mock_send_command.assert_called_once()

        if heater.oscmode is not None:
            new_oscmode = 1 if heater.oscmode != 1 else 0
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.oscmode = new_oscmode
                mock_send_command.assert_called_once()

        if heater.ptcon is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.ptcon = not bool(heater.ptcon)
                mock_send_command.assert_called_once()

        if heater.display_auto_off is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.display_auto_off = not bool(heater.display_auto_off)
                mock_send_command.assert_called_once()

        if heater.display_light is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.display_light = not bool(heater.display_light)
                mock_send_command.assert_called_once()

        if heater.ctlstatus is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.ctlstatus = not bool(heater.ctlstatus)
                mock_send_command.assert_called_once()

        if heater.childlockon is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.childlockon = not bool(heater.childlockon)
                mock_send_command.assert_called_once()

        if heater.panel_sound is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.panel_sound = not bool(heater.panel_sound)
                mock_send_command.assert_called_once()

        if heater.coolmode is not None:
            new_coolmode = DreoHeaterFanMode.NORMAL if heater.coolmode != DreoHeaterFanMode.NORMAL else DreoHeaterFanMode.AUTO
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.coolmode = new_coolmode
                mock_send_command.assert_called_once()

        if heater.coollevel is not None and heater.coollevel_range is not None:
            low, high = heater.coollevel_range
            new_coollevel = low if heater.coollevel != low else high
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.coollevel = new_coollevel
                mock_send_command.assert_called_once()

        if heater.horizontally_oscillating is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.horizontally_oscillating = not bool(heater.horizontally_oscillating)
                mock_send_command.assert_called_once()

        if heater.horizontal_angle is not None:
            new_angle = 0 if heater.horizontal_angle != 0 else 30
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.horizontal_angle = new_angle
                mock_send_command.assert_called_once()

        if heater.lightmode is not None:
            new_lightmode = 0 if heater.lightmode != 0 else 2
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.lightmode = new_lightmode
                mock_send_command.assert_called_once()

        if heater.window_detection is not None:
            with patch(PATCH_SEND_COMMAND) as mock_send_command:
                heater.window_detection = not bool(heater.window_detection)
                mock_send_command.assert_called_once()

    def test_HSH009S(self):  # pylint: disable=invalid-name
        """Load heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF])
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"

    def test_HSH011(self):  # pylint: disable=invalid-name
        """Load DR-HSH011 oil radiator heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH011.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH011"
        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"

    def test_HSH010S(self):  # pylint: disable=invalid-name
        """Load oil radiator heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH010S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"

    def test_WH714S(self):  # pylint: disable=invalid-name
        """Load WH714S heater and test sending commands."""

        self.get_devices_file_name = "get_devices_WH714S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH034S"
        assert heater.series_name == "WH714S"
        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"

    def test_HSH041S(self):  # pylint: disable=invalid-name
        """Load HSH041S (711S) convection heater from its issue #928 diagnostics."""
        self.get_devices_file_name = "get_devices_HSH041S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH041S"
        assert heater.series_name == "711S"
        assert heater.htalevel_range == (1, 3)
        assert heater.poweron is False
        assert heater.mode == DreoHeaterMode.ECO
        assert heater.ecolevel == 68
        assert heater.htalevel == 1
        assert heater.temperature == 74
        assert heater.childlockon is False

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = True
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: True})
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: True}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 3
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 3})], True)

    def test_HSH011S(self):  # pylint: disable=invalid-name
        """Load HSH011S (OH521S) oil radiator heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH011S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH011S"
        # Reports rgbon, but its ambient light has not been checked on a real unit.
        assert heater.rgblevel is None
        assert heater.series_name == "OH521S"
        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF])

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 1
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 1})], True)
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1}})

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"

    def test_HSH040S(self):  # pylint: disable=invalid-name
        """Load HSH040S (720S) heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH040S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert isinstance(heater, PyDreoHeater)
        assert heater.model == "DR-HSH040S"
        assert heater.series_name == "720S"
        assert heater.htalevel_range == (1, 3)
        assert heater.ecolevel_range == (41, 95)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF])
        assert heater.device_definition.swing_modes is None

        assert heater.poweron is True
        assert heater.mode == DreoHeaterMode.ECO
        assert heater.ecolevel == 68
        assert heater.temperature == 70
        assert heater.temperature_units == TemperatureUnit.FAHRENHEIT
        assert heater.oscon is None
        assert heater.oscangle is None
        assert heater.oscmode is None

        # PTC only reports whether the heating element is engaged; it cannot be set.
        assert heater.ptcon is None
        assert heater.heating is False
        heater.handle_server_update({REPORTED_KEY: {PTCON_KEY: True}})
        assert heater.heating is True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ptcon = False
            mock_send_command.assert_not_called()

        # airflowmode: 1 = direct heat (front only), 2 = 360° airflow (checked on a real unit).
        assert heater.airflow_360 is False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.airflow_360 = True
            mock_send_command.assert_called_once_with(heater, {AIRFLOWMODE_KEY: 2})
        heater.handle_server_update({REPORTED_KEY: {AIRFLOWMODE_KEY: 2}})
        assert heater.airflow_360 is True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.airflow_360 = False
            mock_send_command.assert_called_once_with(heater, {AIRFLOWMODE_KEY: 1})

        # tempoffset is a -10..+10°F calibration, and the reported temperature already includes it
        # (checked on a real unit: +3°C in the app -> 6, +2°F -> 2, temperature moved by the same amount).
        assert heater.temperature_offset_range == (-10, 10)
        assert heater.temperature_offset == 0
        heater.handle_server_update({REPORTED_KEY: {TEMPOFFSET_KEY: 6, TEMPERATURE_KEY: 76}})
        assert heater.temperature_offset == 6
        assert heater.temperature == 76
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.temperature_offset = -10
            mock_send_command.assert_called_once_with(heater, {TEMPOFFSET_KEY: -10})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.temperature_offset = 11
            mock_send_command.assert_not_called()

        assert heater.mcu_firmware_version == "1.3.6"

        # rgbon turns the ambient light on and off, rgbbri is its 1-3 brightness (checked on a real unit).
        assert heater.rgblevel == 0
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.rgblevel = 2
            mock_send_command.assert_has_calls([call(heater, {RGB_BRI: 2}), call(heater, {RGBON_KEY: True})])
        heater.handle_server_update({REPORTED_KEY: {RGBON_KEY: True, RGB_BRI: 2}})
        assert heater.rgblevel == 2
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.rgblevel = 0
            mock_send_command.assert_called_once_with(heater, {RGBON_KEY: False})
        assert heater.window_detection is False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.window_detection = True
            mock_send_command.assert_called_once_with(heater, {WINOPENON_KEY: True})
        heater.handle_server_update({REPORTED_KEY: {WINOPENON_KEY: True}})
        assert heater.window_detection is True

        # lighton is not inverted on this model: True means the display is on (checked on a real unit).
        assert heater.display_light is False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.display_light = True
            mock_send_command.assert_called_once_with(heater, {LIGHTON_KEY: True})
        heater.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: True}})
        assert heater.display_light is True
        # lighton is owned by display_light here, so the inverted Display Auto Off is not exposed.
        assert heater.display_auto_off is None
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.display_auto_off = True
            mock_send_command.assert_not_called()

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.mode = DreoHeaterMode.HOTAIR
            mock_send_command.assert_called_once_with(heater, {MODE_KEY: DreoHeaterMode.HOTAIR})
        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: "hotair"}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 3
            mock_send_command.assert_called_once_with(heater, {HTALEVEL_KEY: 3})
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 3}})
        assert heater.htalevel == 3

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ecolevel = 72
            mock_send_command.assert_called_once_with(heater, {ECOLEVEL_KEY: 72})

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"

    def test_HSH004S(self):  # pylint: disable=invalid-name
        """Load HSH004S (Atom One S) heater and test sending commands."""

        self.get_devices_file_name = "get_devices_HSH004S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH004S"
        assert heater.series_name == "Atom One S"
        assert heater.htalevel_range == (1, 3)
        assert sorted(heater.modes) == sorted([DreoHeaterMode.COOLAIR, DreoHeaterMode.HOTAIR, DreoHeaterMode.ECO, DreoHeaterMode.OFF])

        # Test temperature offset is applied to temperature reading
        assert heater.temperature_offset == 2
        assert heater.temperature == 66  # raw 64 + offset 2

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = False
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: False})
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 2
            mock_send_command.assert_has_calls([call(heater, {HTALEVEL_KEY: 2})], True)
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 2}})

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"

    def test_HSH004S_temperature_offset_update(self):  # pylint: disable=invalid-name
        """Test that temperature offset from server updates is applied to temperature."""

        self.get_devices_file_name = "get_devices_HSH004S.json"
        self.pydreo_manager.load_devices()
        heater = self.pydreo_manager.devices[0]

        # Initial state: raw temp 64, offset 2 -> calibrated 66
        assert heater.temperature == 66

        # Simulate a WebSocket update with new temperature and offset
        heater.handle_server_update({REPORTED_KEY: {TEMPERATURE_KEY: 70, TEMPOFFSET_KEY: -3}})
        assert heater.temperature_offset == -3
        assert heater.temperature == 67  # raw 70 + offset -3

    def test_HSH009S_power_cycle_stale_state(self):  # pylint: disable=invalid-name
        """Test that poweron command is sent even when cached state is stale after power cycle."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        # Simulate device power cycle scenario:
        # 1. Device is physically OFF (power cycled)
        # 2. Cloud sends stale WebSocket state with poweron: true
        # 3. User calls poweron = True
        # 4. Command should be sent even though cached state shows ON

        # Simulate stale WebSocket update reporting device is ON (but it's actually OFF)
        message = {"method": "control-report", "devicesn": "HSH009S_1", "reported": {"poweron": True}}
        heater.handle_server_update(message)
        assert heater.poweron is True  # Cached state shows ON

        # User calls poweron = True - command should be sent despite cached state being ON
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = True  # Attempt to turn on
            # Command MUST be sent even though cached state matches
            mock_send_command.assert_called_once_with(heater, {POWERON_KEY: True})

    def test_HSH009S_handle_server_update_all_fields(self):  # pylint: disable=invalid-name
        """Test that handle_server_update correctly updates all device state fields."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        # temperature
        heater.handle_server_update({REPORTED_KEY: {TEMPERATURE_KEY: 70}})
        assert heater.temperature == 70

        # mode (string for heater)
        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: DreoHeaterMode.HOTAIR}})
        assert heater.mode == DreoHeaterMode.HOTAIR

        # oscon
        heater.handle_server_update({REPORTED_KEY: {OSCON_KEY: True}})
        assert heater.oscon is True

        # oscangle
        heater.handle_server_update({REPORTED_KEY: {OSCANGLE_KEY: 90}})
        assert heater.oscangle == 90

        # muteon
        heater.handle_server_update({REPORTED_KEY: {MUTEON_KEY: False}})
        assert heater._mute_on is False

        # ptcon (PTC on implies device on)
        heater._is_on = False
        heater.handle_server_update({REPORTED_KEY: {PTCON_KEY: True}})
        assert heater.ptcon is True
        assert heater.poweron is True  # inferred from PTC turning on

        # ptcon off does not force device off
        heater.handle_server_update({REPORTED_KEY: {PTCON_KEY: False}})
        assert heater.ptcon is False

        # lighton (inverted: lighton=False means display auto-off is enabled)
        heater.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: False}})
        assert heater._light_on is False
        assert heater.display_auto_off is True
        heater.handle_server_update({REPORTED_KEY: {LIGHTON_KEY: True}})
        assert heater.display_auto_off is False

        # ecolevel (target temperature)
        heater.handle_server_update({REPORTED_KEY: {ECOLEVEL_KEY: 75}})
        assert heater.ecolevel == 75

        # childlockon
        heater.handle_server_update({REPORTED_KEY: {CHILDLOCKON_KEY: True}})
        assert heater.childlockon is True

        # tempoffset
        heater.handle_server_update({REPORTED_KEY: {TEMPOFFSET_KEY: 2}})
        assert heater._tempoffset == 2

    def test_HSH009S_setters_send_commands(self):  # pylint: disable=invalid-name
        """Test that heater setters send the correct commands."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        # oscon setter
        heater._oscon = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.oscon = True
            mock_send_command.assert_called_once_with(heater, {OSCON_KEY: True})

        # Duplicate value -- no command
        heater._oscon = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.oscon = True
            mock_send_command.assert_not_called()

        # oscangle setter
        heater._oscangle = 120
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.oscangle = 90
            mock_send_command.assert_called_once_with(heater, {OSCANGLE_KEY: 90})

        # Duplicate value -- no command
        heater._oscangle = 90
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.oscangle = 90
            mock_send_command.assert_not_called()

        # panel_sound setter (inverts mute)
        heater._mute_on = True  # currently muted (sound off)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.panel_sound = True  # turn sound on -> muteon=False
            mock_send_command.assert_called_once_with(heater, {MUTEON_KEY: False})

        # Duplicate value -- no command
        heater._mute_on = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.panel_sound = True  # sound already on (muteon=False)
            mock_send_command.assert_not_called()

        # ptcon setter
        heater._ptc_on = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ptcon = True
            mock_send_command.assert_called_once_with(heater, {PTCON_KEY: True})

        # Duplicate value -- no command
        heater._ptc_on = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ptcon = True
            mock_send_command.assert_not_called()

        # childlockon setter
        heater._childlockon = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.childlockon = True
            mock_send_command.assert_called_once_with(heater, {CHILDLOCKON_KEY: True})

        # Duplicate value -- no command
        heater._childlockon = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.childlockon = True
            mock_send_command.assert_not_called()

    def test_HSH009S_ecolevel_setter(self):  # pylint: disable=invalid-name
        """Test ecolevel setter sends correct command."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ecolevel = 68
            mock_send_command.assert_called_once_with(heater, {ECOLEVEL_KEY: 68})

        # Duplicate value -- no command
        heater._ecolevel = 68
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ecolevel = 68
            mock_send_command.assert_not_called()

    def test_HSH009S_devon_setter(self):  # pylint: disable=invalid-name
        """Test devon setter sends correct command."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        heater._dev_on = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.devon = True
            mock_send_command.assert_called_once_with(heater, {DEVON_KEY: True})

        # Duplicate value -- no command
        heater._dev_on = True
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.devon = True
            mock_send_command.assert_not_called()

    def test_HSH009S_display_auto_off_setter(self):  # pylint: disable=invalid-name
        """Test display_auto_off setter sends the inverted lighton command."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        # Manually set _light_on to a non-None value to enable the setter
        # (HSH009S state may not have a lighton field; we simulate a device that supports it)
        heater._light_on = True  # auto-off is ON
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.display_auto_off = True  # enable display auto-off -> send LIGHTON_KEY: False
            mock_send_command.assert_called_once_with(heater, {LIGHTON_KEY: False})

        # Duplicate value -- no command (_light_on=False -> display_auto_off is already True)
        heater._light_on = False
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.display_auto_off = True
            mock_send_command.assert_not_called()

    def test_HSH009S_poweron_mode_preserved_on_poweroff(self):  # pylint: disable=invalid-name
        """Test that a poweron=False WebSocket update does NOT reset the mode.

        The hvac_mode property already returns HVACMode.OFF when the device is
        powered off, regardless of the stored mode value.  Resetting _mode to OFF
        on every power-off event caused hvac_mode to show OFF even after the
        device powered back on, when the power-on ACK didn't include the mode.
        """
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        heater._mode = DreoHeaterMode.HOTAIR
        heater.handle_server_update({REPORTED_KEY: {POWERON_KEY: False}})
        assert heater.poweron is False
        # Mode must NOT be reset to OFF — it must keep the last active mode so
        # that hvac_mode correctly shows HEAT when the device powers back on.
        assert heater.mode == DreoHeaterMode.HOTAIR, (
            "handle_server_update with poweron=False must preserve the last "
            "active mode instead of resetting it to 'off'"
        )

    def test_HSH009S_htalevel_range_validation(self):  # pylint: disable=invalid-name
        """Test that htalevel rejects values outside the valid range."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        # Range is (1, 3) for HSH009S
        assert heater.htalevel_range == (1, 3)

        # Value below range should be rejected (no command sent)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 0
            mock_send_command.assert_not_called()

        # Value above range should be rejected (no command sent)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 4
            mock_send_command.assert_not_called()

        # Value within range should be accepted
        heater._htalevel = None  # reset to avoid duplicate check
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 2
            mock_send_command.assert_called_once_with(heater, {HTALEVEL_KEY: 2})

    def test_HSH009S_ecolevel_range_validation(self):  # pylint: disable=invalid-name
        """Test that ecolevel rejects values outside the valid range."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater = self.pydreo_manager.devices[0]

        eco_range = heater.ecolevel_range

        # Value below range should be rejected
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ecolevel = eco_range[0] - 1
            mock_send_command.assert_not_called()

        # Value above range should be rejected
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ecolevel = eco_range[1] + 1
            mock_send_command.assert_not_called()

        # Boundary values should be accepted
        heater._ecolevel = None
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.ecolevel = eco_range[0]
            mock_send_command.assert_called_once_with(heater, {ECOLEVEL_KEY: eco_range[0]})

    def test_HSH009S_timer_parsing_safe(self):  # pylint: disable=invalid-name
        """Test that timer parsing handles None and missing 'du' gracefully."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        heater = self.pydreo_manager.devices[0]

        # Timer with valid dict
        heater.update_state({TIMERON_KEY: {"state": {"du": 120}}, TIMEROFF_KEY: {"state": {"du": 60}}})
        assert heater._timer_on == 120
        assert heater._timer_off == 60

        # Timer with None value in state
        heater.update_state({TIMERON_KEY: {"state": None}, TIMEROFF_KEY: {"state": None}})
        assert heater._timer_on is None
        assert heater._timer_off is None

        # Timer key absent from state entirely
        heater.update_state({})
        assert heater._timer_on is None
        assert heater._timer_off is None

        # Timer with dict missing 'du' key
        heater.update_state({TIMERON_KEY: {"state": {"other": 1}}, TIMEROFF_KEY: {"state": {"other": 2}}})
        assert heater._timer_on is None
        assert heater._timer_off is None

    @pytest.mark.parametrize("devices_file", ["get_devices_HSH003S.json", "get_devices_HSH034S.json"])
    def test_additional_heater_models(self, devices_file: str):  # pylint: disable=invalid-name
        """Load additional heater models and test core command paths."""
        self.get_devices_file_name = devices_file
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater: PyDreoHeater = self.pydreo_manager.devices[0]

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.poweron = not bool(heater.poweron)
            mock_send_command.assert_called_once()

        low, high = heater.htalevel_range
        new_heat_level = low if heater.htalevel != low else high
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = new_heat_level
            mock_send_command.assert_called_once()

        for mode in heater.modes:
            if mode != heater.mode:
                with patch(PATCH_SEND_COMMAND) as mock_send_command:
                    heater.mode = mode
                    mock_send_command.assert_called_once()
                break

    def test_HSH016S(self):  # pylint: disable=invalid-name
        """Load the DR-HSH016S tower fan/heater combo and check the function/sub-mode translation.

        Key values were captured from the Dreo app driving a real device: mode 1 = heat, 2 = fan;
        htamode 1 = power heat, 2 = eco; coolmode 1-4 = normal/natural/sleep/auto; hoscangle is a
        "left,right" range and hangleadj the fixed direction while not oscillating.
        """

        self.get_devices_file_name = "get_devices_HSH016S.json"
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) == 1
        heater: PyDreoHeater = self.pydreo_manager.devices[0]

        assert heater.model == "DR-HSH016S"
        assert heater.series_name == "706S/806S"
        assert heater.is_fan_heater is True
        assert heater.htalevel_range == (1, 5)
        assert heater.coollevel_range == (1, 12)
        assert heater.ecolevel_range == (41, 95)

        # Fixture: on, fan function (mode 2), normal mode at speed 5, oscillation off pointing at 45 degrees
        assert heater.poweron is True
        assert heater.mode == DreoHeaterMode.COOLAIR
        assert heater.coolmode == DreoHeaterFanMode.NORMAL
        assert heater.coollevel == 5
        assert heater.htalevel == 1
        assert heater.ecolevel == 85
        assert heater.horizontally_oscillating is False
        assert (heater.horizontal_osc_angle_left, heater.horizontal_osc_angle_right) == (-30, 20)
        assert heater.horizontal_angle == 45
        assert heater.lightmode == 2
        assert heater.window_detection is False
        assert heater.temperature == 66
        assert heater.temperature_units == TemperatureUnit.FAHRENHEIT

        # Mode changes are sent as the function integer plus, for heat, the sub-mode - in one command
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.mode = DreoHeaterMode.HOTAIR
            mock_send_command.assert_called_once_with(heater, {MODE_KEY: 1, HTAMODE_KEY: 1})
        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 1}})
        assert heater.mode == DreoHeaterMode.HOTAIR

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.mode = DreoHeaterMode.ECO
            mock_send_command.assert_called_once_with(heater, {MODE_KEY: 1, HTAMODE_KEY: 2})
        heater.handle_server_update({REPORTED_KEY: {HTAMODE_KEY: 2}})
        assert heater.mode == DreoHeaterMode.ECO

        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.mode = DreoHeaterMode.COOLAIR
            mock_send_command.assert_called_once_with(heater, {MODE_KEY: 2})
        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 2}})
        assert heater.mode == DreoHeaterMode.COOLAIR
        # The heat sub-mode is remembered while in the fan function
        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 1}})
        assert heater.mode == DreoHeaterMode.ECO
        heater.handle_server_update({REPORTED_KEY: {HTALEVEL_KEY: 1, HTAMODE_KEY: 1}})
        assert heater.mode == DreoHeaterMode.HOTAIR

        # Heat levels H1-H5
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 5
            mock_send_command.assert_called_once_with(heater, {HTALEVEL_KEY: 5})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.htalevel = 6
            mock_send_command.assert_not_called()

        # Fan sub-modes and speed
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.coolmode = DreoHeaterFanMode.SLEEP
            mock_send_command.assert_called_once_with(heater, {COOLMODE_KEY: 3})
        heater.handle_server_update({REPORTED_KEY: {COOLMODE_KEY: 3}})
        assert heater.coolmode == DreoHeaterFanMode.SLEEP
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.coollevel = 12
            mock_send_command.assert_called_once_with(heater, {COOLLEVEL_KEY: 12})
        heater.handle_server_update({REPORTED_KEY: {COOLLEVEL_KEY: 12}})
        assert heater.coollevel == 12
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.coollevel = 13
            mock_send_command.assert_not_called()

        # Horizontal oscillation: on/off, "left,right" range, fixed direction
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.horizontally_oscillating = True
            mock_send_command.assert_called_once_with(heater, {HORIZONTAL_OSCILLATION_KEY: True})
        heater.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_KEY: True}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.set_horizontal_oscillation_range(-60, 60)
            mock_send_command.assert_called_once_with(heater, {HORIZONTAL_OSCILLATION_ANGLE_KEY: "-60,60"})
        heater.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_ANGLE_KEY: "-60,60"}})
        assert (heater.horizontal_osc_angle_left, heater.horizontal_osc_angle_right) == (-60, 60)
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.horizontal_osc_angle_right = 20
            mock_send_command.assert_called_once_with(heater, {HORIZONTAL_OSCILLATION_ANGLE_KEY: "-60,20"})
        # Both bounds share one key: a left change made before the right one is reported must not be lost
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.horizontal_osc_angle_left = -45
            heater.horizontal_osc_angle_right = 45
            mock_send_command.assert_has_calls(
                [
                    call(heater, {HORIZONTAL_OSCILLATION_ANGLE_KEY: "-45,20"}),
                    call(heater, {HORIZONTAL_OSCILLATION_ANGLE_KEY: "-45,45"}),
                ]
            )
        heater.handle_server_update({REPORTED_KEY: {HORIZONTAL_OSCILLATION_ANGLE_KEY: "-45,45"}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.set_horizontal_oscillation_range(30, 10)
            mock_send_command.assert_not_called()
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.horizontal_angle = -20
            mock_send_command.assert_called_once_with(heater, {HORIZONTAL_ANGLE_ADJ_KEY: -20})
        heater.handle_server_update({REPORTED_KEY: {HORIZONTAL_ANGLE_ADJ_KEY: -20}})
        assert heater.horizontal_angle == -20

        # Display mode and open-window detection
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.lightmode = 0
            mock_send_command.assert_called_once_with(heater, {LIGHTMODE_KEY: 0})
        heater.handle_server_update({REPORTED_KEY: {LIGHTMODE_KEY: 0}})
        assert heater.lightmode == 0
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.window_detection = True
            mock_send_command.assert_called_once_with(heater, {WINOPENON_KEY: True})
        heater.handle_server_update({REPORTED_KEY: {WINOPENON_KEY: True}})
        assert heater.window_detection is True

        # "off" is not a function: it must never be sent as power heat
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.mode = DreoHeaterMode.OFF
            mock_send_command.assert_not_called()

        # Unknown function or heat sub-mode values are kept but do not leave the mode undefined:
        # they read as power heat whatever the previous state was
        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 1, HTAMODE_KEY: 2}})
        assert heater.mode == DreoHeaterMode.ECO
        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 99}})
        assert heater.mode == DreoHeaterMode.HOTAIR
        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 2}})
        assert heater.mode == DreoHeaterMode.COOLAIR
        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 1, HTAMODE_KEY: 99}})
        assert heater.mode == DreoHeaterMode.HOTAIR
        heater.handle_server_update({REPORTED_KEY: {HTAMODE_KEY: 2}})
        assert heater.mode == DreoHeaterMode.ECO

        # The combo is identified by its model, so a state without a function still uses the integer protocol
        heater.update_state({})
        assert heater.is_fan_heater
        assert heater.mode == DreoHeaterMode.HOTAIR
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.mode = DreoHeaterMode.ECO
            mock_send_command.assert_called_once_with(heater, {MODE_KEY: 1, HTAMODE_KEY: 2})

        # Requesting power heat while the device reports an unknown function or heat sub-mode must still
        # send the command even though the fallback already reads as power heat
        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 99, HTAMODE_KEY: 1}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.mode = DreoHeaterMode.HOTAIR
            mock_send_command.assert_called_once_with(heater, {MODE_KEY: 1, HTAMODE_KEY: 1})
        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 1, HTAMODE_KEY: 99}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.mode = DreoHeaterMode.HOTAIR
            mock_send_command.assert_called_once_with(heater, {MODE_KEY: 1, HTAMODE_KEY: 1})
        heater.handle_server_update({REPORTED_KEY: {MODE_KEY: 1, HTAMODE_KEY: 1}})
        with patch(PATCH_SEND_COMMAND) as mock_send_command:
            heater.mode = DreoHeaterMode.HOTAIR
            mock_send_command.assert_not_called()

        with pytest.raises(ValueError):
            heater.mode = "not_a_mode"
        with pytest.raises(ValueError):
            heater.coolmode = 9

    def test_HSH009S_has_no_fan_function(self):  # pylint: disable=invalid-name
        """A conventional heater must not grow the tower fan/heater combo features."""
        self.get_devices_file_name = "get_devices_HSH009S.json"
        self.pydreo_manager.load_devices()
        heater: PyDreoHeater = self.pydreo_manager.devices[0]
        assert heater.is_fan_heater is False
        assert heater.coolmode is None
        assert heater.coollevel is None
        assert heater.horizontally_oscillating is None
        assert heater.horizontal_angle is None
        assert heater.lightmode is None
        with pytest.raises(ValueError):
            heater.coolmode = DreoHeaterFanMode.AUTO
        with pytest.raises(ValueError):
            heater.coollevel = 3

    @pytest.mark.parametrize("devices_file", HEATER_EXHAUSTIVE_MODELS)
    def test_all_settable_properties_for_each_model(self, devices_file: str):
        """Exercise all writable properties for each heater model fixture in this file."""
        self.get_devices_file_name = devices_file
        self.pydreo_manager.load_devices()
        assert len(self.pydreo_manager.devices) >= 1
        for device in self.pydreo_manager.devices:
            heater: PyDreoHeater = device
            self._exercise_all_settable_properties(heater)
