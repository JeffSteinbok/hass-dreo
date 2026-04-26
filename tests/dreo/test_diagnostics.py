"""Tests for Dreo diagnostics module."""

import asyncio
from unittest.mock import MagicMock
import pytest
from homeassistant.components.diagnostics import REDACTED
from custom_components.dreo.diagnostics import _redact_values, _get_diagnostics, async_get_config_entry_diagnostics, KEYS_TO_REDACT
from custom_components.dreo.const import DOMAIN, PYDREO_MANAGER


class TestRedactValues:
    """Tests for _redact_values function."""

    def test_redact_values_simple_dict(self):
        """Test that a dict with redactable keys gets them replaced with REDACTED."""
        data = {"sn": "ABC123", "token": "secret_token", "password": "my_password"}
        result = _redact_values(data)
        assert result["sn"] == REDACTED
        assert result["token"] == REDACTED
        assert result["password"] == REDACTED

    def test_redact_values_preserves_safe_keys(self):
        """Test that non-redactable keys pass through unchanged."""
        data = {"device_name": "My Fan", "model": "DR-HTF001S", "status": "online", "temperature": 72}
        result = _redact_values(data)
        assert result["device_name"] == "My Fan"
        assert result["model"] == "DR-HTF001S"
        assert result["status"] == "online"
        assert result["temperature"] == 72

    def test_redact_values_nested_dict(self):
        """Test that nested dicts are recursively redacted."""
        data = {
            "device": {"sn": "ABC123", "name": "My Device"},
            "credentials": {"username": "user@example.com", "password": "secret"},
            "status": "active",
        }
        result = _redact_values(data)
        assert result["device"]["sn"] == REDACTED
        assert result["device"]["name"] == "My Device"
        assert result["credentials"]["username"] == REDACTED
        assert result["credentials"]["password"] == REDACTED
        assert result["status"] == "active"

    def test_redact_values_list_of_dicts(self):
        """Test that lists containing dicts are recursively redacted."""
        data = {"devices": [{"sn": "ABC123", "name": "Device 1"}, {"sn": "XYZ789", "name": "Device 2"}]}
        result = _redact_values(data)
        assert len(result["devices"]) == 2
        assert result["devices"][0]["sn"] == REDACTED
        assert result["devices"][0]["name"] == "Device 1"
        assert result["devices"][1]["sn"] == REDACTED
        assert result["devices"][1]["name"] == "Device 2"

    def test_redact_values_list_of_primitives(self):
        """Test that lists of non-dict items pass through unchanged."""
        data = {"tags": ["indoor", "outdoor", "portable"], "temperatures": [72, 75, 68], "enabled": True}
        result = _redact_values(data)
        assert result["tags"] == ["indoor", "outdoor", "portable"]
        assert result["temperatures"] == [72, 75, 68]
        assert result["enabled"] is True

    def test_redact_values_non_dict_input(self):
        """Test that non-dict input is returned as-is."""
        # String
        assert _redact_values("test_string") == "test_string"
        # Integer
        assert _redact_values(42) == 42
        # List
        assert _redact_values([1, 2, 3]) == [1, 2, 3]
        # None
        assert _redact_values(None) is None

    def test_redact_values_all_keys(self):
        """Test that EVERY key in KEYS_TO_REDACT is actually redacted."""
        # Create a dict with all keys that should be redacted
        data = {key: f"value_{key}" for key in KEYS_TO_REDACT}
        result = _redact_values(data)

        # Verify all keys are redacted
        for key in KEYS_TO_REDACT:
            assert result[key] == REDACTED, f"Key '{key}' was not redacted"

    def test_redact_values_empty_dict(self):
        """Test that empty dict returns empty dict."""
        data = {}
        result = _redact_values(data)
        assert result == {}
        assert isinstance(result, dict)

    def test_redact_values_deeply_nested(self):
        """Test that multiple levels of nesting are all redacted."""
        data = {
            "level1": {
                "level2": {"level3": {"sn": "ABC123", "token": "secret_token", "safe_value": "visible"}, "wifi_ssid": "MyNetwork"},
                "password": "secret",
            },
            "normal_key": "normal_value",
        }
        result = _redact_values(data)
        assert result["level1"]["level2"]["level3"]["sn"] == REDACTED
        assert result["level1"]["level2"]["level3"]["token"] == REDACTED
        assert result["level1"]["level2"]["level3"]["safe_value"] == "visible"
        assert result["level1"]["level2"]["wifi_ssid"] == REDACTED
        assert result["level1"]["password"] == REDACTED
        assert result["normal_key"] == "normal_value"

    def test_redact_values_mixed_list(self):
        """Test list with mix of dicts and primitives."""
        data = {"mixed_list": [{"sn": "ABC123", "name": "Device"}, "plain_string", 42, {"token": "secret", "id": 123}]}
        result = _redact_values(data)
        assert result["mixed_list"][0]["sn"] == REDACTED
        assert result["mixed_list"][0]["name"] == "Device"
        assert result["mixed_list"][1] == "plain_string"
        assert result["mixed_list"][2] == 42
        assert result["mixed_list"][3]["token"] == REDACTED
        assert result["mixed_list"][3]["id"] == 123


class TestGetDiagnostics:
    """Tests for _get_diagnostics function."""

    def test_get_diagnostics_structure(self):
        """Test that _get_diagnostics returns correct structure with device_count and devices."""
        # Create mock PyDreo manager
        mock_manager = MagicMock()

        # Create mock devices
        mock_device1 = MagicMock()
        mock_device1.__dict__ = {"sn": "ABC123", "name": "Device 1", "model": "DR-HTF001S"}

        mock_device2 = MagicMock()
        mock_device2.__dict__ = {"sn": "XYZ789", "name": "Device 2", "model": "DR-HTF002S"}

        mock_manager.devices = [mock_device1, mock_device2]
        mock_manager.raw_response = {"devices": [{"sn": "ABC123", "name": "Device 1"}, {"sn": "XYZ789", "name": "Device 2"}]}

        result = _get_diagnostics(mock_manager)

        # Verify structure
        assert DOMAIN in result
        assert "device_count" in result[DOMAIN]
        assert "raw_devicelist" in result[DOMAIN]
        assert "devices" in result

        # Verify device count
        assert result[DOMAIN]["device_count"] == 2

        # Verify devices list
        assert len(result["devices"]) == 2

        # Verify redaction occurred
        assert result[DOMAIN]["raw_devicelist"]["devices"][0]["sn"] == REDACTED
        assert result[DOMAIN]["raw_devicelist"]["devices"][0]["name"] == "Device 1"
        assert result["devices"][0]["sn"] == REDACTED
        assert result["devices"][0]["name"] == "Device 1"

    def test_get_diagnostics_no_devices(self):
        """Test that empty device list returns count 0."""
        # Create mock PyDreo manager with no devices
        mock_manager = MagicMock()
        mock_manager.devices = []
        mock_manager.raw_response = {"devices": []}

        result = _get_diagnostics(mock_manager)

        # Verify device count is 0
        assert result[DOMAIN]["device_count"] == 0

        # Verify empty devices list
        assert result["devices"] == []
        assert isinstance(result["devices"], list)

    def test_get_diagnostics_preserves_safe_data(self):
        """Test that safe data is preserved while sensitive data is redacted."""
        mock_manager = MagicMock()

        mock_device = MagicMock()
        mock_device.__dict__ = {"sn": "ABC123", "productId": "12345", "name": "My Fan", "model": "DR-HTF001S", "temperature": 72, "fan_speed": 5}

        mock_manager.devices = [mock_device]
        mock_manager.raw_response = {"username": "user@example.com", "token": "secret_token", "device_count": 1}

        result = _get_diagnostics(mock_manager)

        # Verify sensitive data is redacted
        assert result[DOMAIN]["raw_devicelist"]["username"] == REDACTED
        assert result[DOMAIN]["raw_devicelist"]["token"] == REDACTED
        assert result["devices"][0]["sn"] == REDACTED
        assert result["devices"][0]["productId"] == REDACTED

        # Verify safe data is preserved
        assert result[DOMAIN]["raw_devicelist"]["device_count"] == 1
        assert result["devices"][0]["name"] == "My Fan"
        assert result["devices"][0]["model"] == "DR-HTF001S"
        assert result["devices"][0]["temperature"] == 72
        assert result["devices"][0]["fan_speed"] == 5


class TestAsyncGetConfigEntryDiagnostics:
    """Tests for async_get_config_entry_diagnostics function."""

    def test_async_get_config_entry_diagnostics(self):
        """Test that entry point retrieves manager from hass.data and calls _get_diagnostics."""
        # Create mock hass
        mock_hass = MagicMock()

        # Create mock PyDreo manager
        mock_manager = MagicMock()
        mock_device = MagicMock()
        mock_device.__dict__ = {"sn": "ABC123", "name": "Test Device"}
        mock_manager.devices = [mock_device]
        mock_manager.raw_response = {"devices": [{"sn": "ABC123"}]}

        # Set up hass.data
        mock_hass.data = {DOMAIN: {PYDREO_MANAGER: mock_manager}}

        # Create mock config entry
        mock_entry = MagicMock()

        # Call the async function
        result = asyncio.run(async_get_config_entry_diagnostics(mock_hass, mock_entry))

        # Verify result structure
        assert DOMAIN in result
        assert "devices" in result
        assert result[DOMAIN]["device_count"] == 1
        assert result["devices"][0]["sn"] == REDACTED
        assert result["devices"][0]["name"] == "Test Device"

    def test_async_get_config_entry_diagnostics_multiple_devices(self):
        """Test async diagnostics with multiple devices."""
        mock_hass = MagicMock()
        mock_manager = MagicMock()

        # Create multiple mock devices
        devices = []
        for i in range(3):
            mock_device = MagicMock()
            mock_device.__dict__ = {"sn": f"SN{i}", "name": f"Device {i}", "token": f"token_{i}"}
            devices.append(mock_device)

        mock_manager.devices = devices
        mock_manager.raw_response = {"username": "test@example.com", "devices": [{"sn": f"SN{i}"} for i in range(3)]}

        mock_hass.data = {DOMAIN: {PYDREO_MANAGER: mock_manager}}

        mock_entry = MagicMock()

        result = asyncio.run(async_get_config_entry_diagnostics(mock_hass, mock_entry))

        # Verify device count
        assert result[DOMAIN]["device_count"] == 3

        # Verify all devices are present and redacted
        assert len(result["devices"]) == 3
        for i in range(3):
            assert result["devices"][i]["sn"] == REDACTED
            assert result["devices"][i]["token"] == REDACTED
            assert result["devices"][i]["name"] == f"Device {i}"

        # Verify raw_devicelist is redacted
        assert result[DOMAIN]["raw_devicelist"]["username"] == REDACTED
