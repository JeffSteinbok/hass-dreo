"""Tests for the PyDreo class."""

import logging
import pytest
from unittest.mock import patch, MagicMock

from .imports import *  # pylint: disable=W0401,W0614
from .testbase import TestBase, PATCH_SEND_COMMAND


class TestPyDreoApiServerRegion:
    """Test api_server_region property."""

    def test_na_region_returns_us(self):
        """Test NA auth region returns US API region."""
        pydreo = PyDreo("user", "pass", redact=False)
        pydreo.auth_region = DREO_AUTH_REGION_NA
        assert pydreo.api_server_region == DREO_API_REGION_US

    def test_eu_region_returns_eu(self):
        """Test EU auth region returns EU API region."""
        pydreo = PyDreo("user", "pass", redact=False)
        pydreo.auth_region = DREO_AUTH_REGION_EU
        assert pydreo.api_server_region == DREO_API_REGION_EU

    def test_invalid_region_raises_value_error(self):
        """Test invalid region raises ValueError."""
        pydreo = PyDreo("user", "pass", redact=False)
        pydreo.auth_region = "INVALID"
        with pytest.raises(ValueError, match="Invalid Auth Region"):
            _ = pydreo.api_server_region


class TestPyDreoRedact:
    """Test redact property setter."""

    def test_set_redact_true(self):
        """Test setting redact=True sets Helpers.shouldredact=True."""
        pydreo = PyDreo("user", "pass", redact=False)
        pydreo.redact = True
        assert Helpers.shouldredact is True
        assert pydreo.redact is True

    def test_set_redact_false(self):
        """Test setting redact=False sets Helpers.shouldredact=False."""
        pydreo = PyDreo("user", "pass", redact=True)
        pydreo.redact = False
        assert Helpers.shouldredact is False
        assert pydreo.redact is False


class TestPyDreoAddDevTest:
    """Test add_dev_test method."""

    def test_no_cid_returns_true(self):
        """Test device without cid key always returns True."""
        pydreo = PyDreo("user", "pass", redact=False)
        assert pydreo.add_dev_test({"deviceId": "123"}) is True

    def test_duplicate_device_returns_false(self):
        """Test duplicate device with matching deviceId returns False."""
        pydreo = PyDreo("user", "pass", redact=False)
        mock_dev = MagicMock()
        mock_dev.deviceId = "123"
        pydreo._dev_list = {"fans": [mock_dev]}
        new_dev = {"cid": "some_cid", "deviceid": "123"}
        assert pydreo.add_dev_test(new_dev) is False

    def test_non_duplicate_with_cid_returns_true(self):
        """Test device with cid but no matching deviceId returns True."""
        pydreo = PyDreo("user", "pass", redact=False)
        mock_dev = MagicMock()
        mock_dev.deviceId = "456"
        pydreo._dev_list = {"fans": [mock_dev]}
        new_dev = {"cid": "some_cid", "deviceid": "999"}
        assert pydreo.add_dev_test(new_dev) is True


class TestPyDreoSetDevId:
    """Test set_dev_id static method."""

    def test_filters_devices_without_device_id(self):
        """Test devices without deviceId are filtered out."""
        devices = [
            {"deviceId": "123", "name": "fan1"},
            {"name": "fan2"},
            {"deviceId": "456", "name": "fan3"},
        ]
        result = PyDreo.set_dev_id(devices)
        assert len(result) == 2
        assert result[0]["deviceId"] == "123"
        assert result[1]["deviceId"] == "456"

    def test_empty_list(self):
        """Test empty list returns empty."""
        assert PyDreo.set_dev_id([]) == []

    def test_all_have_device_id(self):
        """Test all devices with deviceId are kept."""
        devices = [{"deviceId": "1"}, {"deviceId": "2"}]
        assert len(PyDreo.set_dev_id(devices)) == 2


class TestPyDreoProcessDevices(TestBase):
    """Test _process_devices method."""

    @pytest.fixture(autouse=True, scope="function")
    def setup(self, caplog):
        """Override setup to use get_devices_all.json."""
        self._get_devices_file_name = "get_devices_all.json"
        self.mock_api_call = patch("custom_components.dreo.pydreo.PyDreo.call_dreo_api")
        self.caplog = caplog
        self.mock_api = self.mock_api_call.start()
        self.mock_api.side_effect = self.call_dreo_api
        self.mock_api.create_autospect()
        self.mock_api.return_value.ok = True
        self.pydreo_manager = PyDreo("EMAIL", "PASSWORD", redact=True)
        self.pydreo_manager.enabled = True
        self.pydreo_manager.token = "sample_tk"
        self.pydreo_manager.account_id = "sample_id"
        caplog.set_level(logging.DEBUG)
        yield
        self.mock_api_call.stop()

    def test_empty_device_list_returns_false(self):
        """Test empty device list returns False."""
        result = self.pydreo_manager._process_devices([])
        assert result is False

    def test_devices_without_device_id_filtered(self):
        """Test devices without deviceId are filtered and result is False."""
        result = self.pydreo_manager._process_devices([{"name": "no_id"}])
        assert result is False

    def test_unknown_model_creates_unknown_device(self):
        """Test unknown model creates PyDreoUnknownDevice."""
        devices = [
            {
                "deviceId": "test123",
                "sn": "SN123",
                "deviceName": "Unknown Device",
                "model": "UNKNOWN-MODEL-XYZ",
            }
        ]
        result = self.pydreo_manager._process_devices(devices)
        assert result is True
        assert len(self.pydreo_manager.devices) == 1
        assert isinstance(self.pydreo_manager.devices[0], PyDreoUnknownDevice)

    def test_known_model_prefix_match(self):
        """Test known model prefix creates correct device type."""
        devices = [
            {
                "deviceId": "test123",
                "sn": "SN123",
                "deviceName": "Tower Fan",
                "model": "DR-HTF001S",
            }
        ]
        result = self.pydreo_manager._process_devices(devices)
        assert result is True
        assert len(self.pydreo_manager.devices) == 1
        assert isinstance(self.pydreo_manager.devices[0], PyDreoTowerFan)


class TestPyDreoLoadDevices(TestBase):
    """Test load_devices method."""

    def test_not_enabled_returns_false(self):
        """Test load_devices returns False when not enabled."""
        self.pydreo_manager.enabled = False
        result = self.pydreo_manager.load_devices()
        assert result is False

    def test_debug_test_mode_payload(self):
        """Test load_devices with debug_test_mode payload."""
        payload = {
            "get_devices": {
                "code": 0,
                "data": {
                    "list": [
                        {
                            "deviceId": "test123",
                            "sn": "SN_DEBUG",
                            "deviceName": "Debug Fan",
                            "model": "DR-HTF001S",
                        }
                    ]
                },
            },
            "SN_DEBUG": {
                "code": 0,
                "data": {
                    "mixed": {
                        "poweron": True,
                        "windlevel": 1,
                    }
                },
            },
        }
        self.pydreo_manager.debug_test_mode = True
        self.pydreo_manager.debug_test_mode_payload = payload
        result = self.pydreo_manager.load_devices()
        assert result is True
        assert len(self.pydreo_manager.devices) == 1

    def test_empty_data_key_in_response(self, caplog):
        """Test load_devices with missing data key in response."""
        self.mock_api.side_effect = None
        self.mock_api.return_value = ({"code": 0}, 200)
        result = self.pydreo_manager.load_devices()
        assert result is False
        assert "Device list in response not found" in caplog.text

    def test_failed_api_response(self, caplog):
        """Test load_devices with failed API response."""
        self.mock_api.side_effect = None
        self.mock_api.return_value = (None, 500)
        result = self.pydreo_manager.load_devices()
        assert result is False
        assert "Error retrieving device list" in caplog.text


class TestPyDreoLogin:
    """Test login method."""

    def test_debug_test_mode_login(self):
        """Test login in debug test mode."""
        pydreo = PyDreo("user", "pass", redact=False, debug_test_mode=True, debug_test_mode_payload={})
        result = pydreo.login()
        assert result is True
        assert pydreo.enabled is True

    def test_token_login_with_region(self):
        """Test token login with region suffix."""
        pydreo = PyDreo("user", "pass", redact=False, token="mytoken:EU")
        result = pydreo.login()
        assert result is True
        assert pydreo.enabled is True
        assert pydreo.token == "mytoken"
        assert pydreo.auth_region == "EU"

    def test_token_login_without_region(self):
        """Test token login without region suffix."""
        pydreo = PyDreo("user", "pass", redact=False, token="simpletoken")
        result = pydreo.login()
        assert result is True
        assert pydreo.token == "simpletoken"

    def test_empty_username(self, caplog):
        """Test login with empty username."""
        caplog.set_level(logging.DEBUG)
        pydreo = PyDreo("", "pass", redact=False)
        result = pydreo.login()
        assert result is False
        assert "Username invalid" in caplog.text

    def test_empty_password(self, caplog):
        """Test login with empty password."""
        caplog.set_level(logging.DEBUG)
        pydreo = PyDreo("user", "", redact=False)
        result = pydreo.login()
        assert result is False
        assert "Password invalid" in caplog.text

    @patch("custom_components.dreo.pydreo.PyDreo.call_dreo_api")
    def test_no_response_from_api(self, mock_api, caplog):
        """Test login with no response from API."""
        caplog.set_level(logging.DEBUG)
        mock_api.return_value = (None, 500)
        pydreo = PyDreo("user", "pass", redact=False)
        result = pydreo.login()
        assert result is False
        assert "No response from Dreo API" in caplog.text

    @patch("custom_components.dreo.pydreo.PyDreo.call_dreo_api")
    def test_failed_auth_non_zero_code(self, mock_api, caplog):
        """Test login with non-zero code in response."""
        caplog.set_level(logging.DEBUG)
        mock_api.return_value = ({"code": 1, "msg": "Invalid credentials"}, 200)
        pydreo = PyDreo("user", "pass", redact=False)
        result = pydreo.login()
        assert result is False
        assert "Authentication failed" in caplog.text


class TestPyDreoSendCommand:
    """Test send_command method."""

    def test_debug_test_mode_simulates_ack(self):
        """Test send_command in debug test mode simulates ack via _transport_consume_message."""
        pydreo = PyDreo("user", "pass", redact=False, debug_test_mode=True, debug_test_mode_payload={})
        mock_device = MagicMock()
        mock_device.serial_number = "SN_TEST"
        mock_device.name = "Test Device"

        # Register device so message routing works
        pydreo._device_list_by_sn["SN_TEST"] = mock_device

        params = {"poweron": True}
        pydreo.send_command(mock_device, params)

        # Verify the device received the update
        mock_device.handle_server_update_base.assert_called_once()
        call_args = mock_device.handle_server_update_base.call_args[0][0]
        assert call_args["devicesn"] == "SN_TEST"
        assert call_args["method"] == "control-report"
        assert call_args["reported"] == {"poweron": True}


class TestPyDreoTransportConsumeMessage:
    """Test _transport_consume_message method."""

    def test_known_device_sn_routes_to_device(self):
        """Test message with known SN routes to the device."""
        pydreo = PyDreo("user", "pass", redact=False)
        mock_device = MagicMock()
        pydreo._device_list_by_sn["SN123"] = mock_device

        message = {"devicesn": "SN123", "method": "report", "reported": {"poweron": True}}
        pydreo._transport_consume_message(message)

        mock_device.handle_server_update_base.assert_called_once_with(message)

    def test_unknown_device_sn_logs_debug(self, caplog):
        """Test message with unknown SN logs debug message."""
        caplog.set_level(logging.DEBUG)
        pydreo = PyDreo("user", "pass", redact=False)

        message = {"devicesn": "UNKNOWN_SN", "method": "report", "reported": {}}
        pydreo._transport_consume_message(message)

        assert "unknown or unsupported device" in caplog.text


class TestPyDreoHandleCommandAck:
    """Test _handle_command_ack method."""

    def test_none_device_sn_returns_early(self):
        """Test None device_sn returns without doing anything."""
        pydreo = PyDreo("user", "pass", redact=False)
        pydreo._pending_command_device = "SN123"
        pydreo._handle_command_ack(None, "control-report", {})
        assert pydreo._ack_received is False

    def test_wrong_method_name_returns_early(self):
        """Test non-matching method name returns without signaling."""
        pydreo = PyDreo("user", "pass", redact=False)
        pydreo._pending_command_device = "SN123"
        pydreo._handle_command_ack("SN123", "wrong-method", {})
        assert pydreo._ack_received is False

    def test_matching_device_and_params_signals_ack(self):
        """Test matching device and params signals ack."""
        pydreo = PyDreo("user", "pass", redact=False)
        pydreo._pending_command_device = "SN123"
        pydreo._pending_command_params = {"poweron": True}
        pydreo._ack_received = False

        pydreo._handle_command_ack("SN123", "control-report", {"poweron": True})
        assert pydreo._ack_received is True

    def test_non_matching_params_still_signals_ack(self):
        """Test non-matching reported params still signals ack (device match is sufficient)."""
        pydreo = PyDreo("user", "pass", redact=False)
        pydreo._pending_command_device = "SN123"
        pydreo._pending_command_params = {"poweron": True}
        pydreo._ack_received = False

        pydreo._handle_command_ack("SN123", "control-report", {"windlevel": 3})
        assert pydreo._ack_received is True

    def test_no_params_to_match_falls_back(self):
        """Test no pending params falls back to device match and signals ack."""
        pydreo = PyDreo("user", "pass", redact=False)
        pydreo._pending_command_device = "SN123"
        pydreo._pending_command_params = None
        pydreo._ack_received = False

        pydreo._handle_command_ack("SN123", "control-report", None)
        assert pydreo._ack_received is True

    def test_different_pending_device_ignored(self):
        """Test ack for different device is ignored."""
        pydreo = PyDreo("user", "pass", redact=False)
        pydreo._pending_command_device = "SN_OTHER"
        pydreo._pending_command_params = {"poweron": True}
        pydreo._ack_received = False

        pydreo._handle_command_ack("SN123", "control-report", {"poweron": True})
        assert pydreo._ack_received is False
