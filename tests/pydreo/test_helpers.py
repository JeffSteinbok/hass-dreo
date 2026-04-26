"""Test helpers for PyDreo."""
import time
from unittest.mock import patch, MagicMock
import requests
from  .imports import Helpers

class TestHelpers:
    """Test Helpers class."""
    def test_value_from_name(self):
        """Test value_from_name() method."""
        name_value_collection = [("on", True), ("off", False)]
        assert Helpers.value_from_name(name_value_collection, "on") is True # pylint: disable=E0601
        assert Helpers.value_from_name(name_value_collection, "off") is False
        assert Helpers.value_from_name(name_value_collection, "oxx") is None

    def test_name_from_value(self):
        """Test name_from_value() method."""
        name_value_collection = [("on", True), ("off", False)]
        assert Helpers.name_from_value(name_value_collection, False) == "off" # pylint: disable=E0601
        assert Helpers.name_from_value(name_value_collection, True) == "on"
        assert Helpers.name_from_value(name_value_collection, "oxx") is None

    def test_get_name_list(self):
        """Test get_name_list() method."""
        name_value_collection = [("on", True), ("off", False)]
        assert Helpers.get_name_list(name_value_collection)[0] == "on" # pylint: disable=E0601
        assert Helpers.get_name_list(name_value_collection)[1] == "off"

    def test_value_from_name_with_integers(self):
        """Test value_from_name() with integer values."""
        name_value_collection = [("low", 1), ("medium", 2), ("high", 3)]
        assert Helpers.value_from_name(name_value_collection, "low") == 1
        assert Helpers.value_from_name(name_value_collection, "medium") == 2
        assert Helpers.value_from_name(name_value_collection, "high") == 3
        assert Helpers.value_from_name(name_value_collection, "invalid") is None

    def test_value_from_name_empty_collection(self):
        """Test value_from_name() with empty collection."""
        assert Helpers.value_from_name([], "anything") is None

    def test_value_from_name_case_sensitivity(self):
        """Test value_from_name() is case sensitive."""
        name_value_collection = [("On", True), ("OFF", False)]
        assert Helpers.value_from_name(name_value_collection, "On") is True
        assert Helpers.value_from_name(name_value_collection, "on") is None
        assert Helpers.value_from_name(name_value_collection, "OFF") is False
        assert Helpers.value_from_name(name_value_collection, "off") is None

    def test_name_from_value_with_integers(self):
        """Test name_from_value() with integer values."""
        name_value_collection = [("low", 1), ("medium", 2), ("high", 3)]
        assert Helpers.name_from_value(name_value_collection, 1) == "low"
        assert Helpers.name_from_value(name_value_collection, 2) == "medium"
        assert Helpers.name_from_value(name_value_collection, 3) == "high"
        assert Helpers.name_from_value(name_value_collection, 999) is None

    def test_name_from_value_with_strings(self):
        """Test name_from_value() with string values."""
        name_value_collection = [("mode1", "normal"), ("mode2", "sleep"), ("mode3", "auto")]
        assert Helpers.name_from_value(name_value_collection, "normal") == "mode1"
        assert Helpers.name_from_value(name_value_collection, "sleep") == "mode2"
        assert Helpers.name_from_value(name_value_collection, "auto") == "mode3"

    def test_name_from_value_empty_collection(self):
        """Test name_from_value() with empty collection."""
        assert Helpers.name_from_value([], "anything") is None

    def test_name_from_value_duplicate_values(self):
        """Test name_from_value() with duplicate values returns first match."""
        name_value_collection = [("first", 1), ("second", 1), ("third", 2)]
        assert Helpers.name_from_value(name_value_collection, 1) == "first"

    def test_get_name_list_multiple_items(self):
        """Test get_name_list() with multiple items."""
        name_value_collection = [("low", 1), ("medium", 2), ("high", 3), ("turbo", 4)]
        names = Helpers.get_name_list(name_value_collection)
        assert len(names) == 4
        assert names == ["low", "medium", "high", "turbo"]

    def test_get_name_list_empty_collection(self):
        """Test get_name_list() with empty collection."""
        names = Helpers.get_name_list([])
        assert len(names) == 0
        assert names == []

    def test_get_name_list_preserves_order(self):
        """Test get_name_list() preserves order."""
        name_value_collection = [("zebra", 1), ("apple", 2), ("monkey", 3)]
        names = Helpers.get_name_list(name_value_collection)
        assert names == ["zebra", "apple", "monkey"]

    def test_value_from_name_with_none_value(self):
        """Test value_from_name() can return None as a valid value."""
        name_value_collection = [("none_mode", None), ("some_mode", 1)]
        assert Helpers.value_from_name(name_value_collection, "none_mode") is None
        assert Helpers.value_from_name(name_value_collection, "some_mode") == 1

    def test_name_from_value_with_zero(self):
        """Test name_from_value() with zero as a value."""
        name_value_collection = [("off", 0), ("on", 1)]
        assert Helpers.name_from_value(name_value_collection, 0) == "off"
        assert Helpers.name_from_value(name_value_collection, 1) == "on"

    def test_realistic_preset_modes(self):
        """Test with realistic preset modes from actual devices."""
        preset_modes = [("normal", 1), ("natural", 2), ("sleep", 3), ("auto", 4), ("turbo", 5)]
        
        # Test value_from_name
        assert Helpers.value_from_name(preset_modes, "normal") == 1
        assert Helpers.value_from_name(preset_modes, "turbo") == 5
        assert Helpers.value_from_name(preset_modes, "invalid") is None
        
        # Test name_from_value
        assert Helpers.name_from_value(preset_modes, 1) == "normal"
        assert Helpers.name_from_value(preset_modes, 5) == "turbo"
        assert Helpers.name_from_value(preset_modes, 99) is None
        
        # Test get_name_list
        names = Helpers.get_name_list(preset_modes)
        assert len(names) == 5
        assert "normal" in names
        assert "turbo" in names

    def test_realistic_hvac_modes(self):
        """Test with realistic HVAC modes."""
        hvac_modes = [("off", 0), ("cool", 1), ("heat", 2), ("fan", 3), ("auto", 4)]
        
        assert Helpers.value_from_name(hvac_modes, "cool") == 1
        assert Helpers.value_from_name(hvac_modes, "heat") == 2
        assert Helpers.name_from_value(hvac_modes, 0) == "off"
        assert Helpers.name_from_value(hvac_modes, 4) == "auto"
        
        names = Helpers.get_name_list(hvac_modes)
        assert len(names) == 5
        assert names[0] == "off"
        assert names[-1] == "auto"

    def test_hash_password_simple(self):
        """Test hash_password() with simple password."""
        hashed = Helpers.hash_password("simple123")
        assert hashed == "ee2da41de9eb269679017db7613bc778"
        assert len(hashed) == 32  # MD5 produces 32-character hex string

    def test_hash_password_with_special_characters(self):
        """Test hash_password() with passwords containing special characters."""
        # Test common special characters that might appear in passwords
        test_cases = [
            ("Test@Pass123", "653207b624fb1980f4348606dbe9c115"),
            ("P@ssw0rd!", "8a24367a1f46c141048752f2d5bbd14b"),
            ("user&pass", "c1c852bf3981df03b989a6f466af9d62"),
            ("test=value", "84fb50487551d2e89da17080d0ebde85"),
            ("test?query", "4a4882479489d59e6a3226a61128d535"),
            ("test#hash", "656ce5d715c16b0d96d45b93d21a360e"),
            ("test+plus", "875f0982fdc91507d3686b9820d5a2b5"),
            ("test%percent", "71770b09d686ad7ee626dc52b882f4e1"),
            ("test/slash", "7827c077e17fe24f53637576418ef205"),
        ]
        for password, expected_hash in test_cases:
            hashed = Helpers.hash_password(password)
            assert hashed == expected_hash, f"Failed for password: {password}"
            assert len(hashed) == 32

    def test_hash_password_with_quotes_and_backslashes(self):
        """Test hash_password() with quotes and backslashes."""
        # These are particularly problematic for JSON encoding
        test_cases = [
            'pass"word',  # double quote
            "pass'word",  # single quote
            "pass\\word",  # backslash
            'pass"\\\'word',  # mixed quotes and backslash
        ]
        for password in test_cases:
            hashed = Helpers.hash_password(password)
            assert isinstance(hashed, str)
            assert len(hashed) == 32
            # Verify it's a valid hex string
            int(hashed, 16)  # Should not raise ValueError

    def test_hash_password_with_unicode(self):
        """Test hash_password() with Unicode characters."""
        test_cases = [
            "пароль123",  # Cyrillic
            "密码123",  # Chinese
            "パスワード123",  # Japanese
            "🔒secure123",  # Emoji
            "café@123",  # Accented characters
        ]
        for password in test_cases:
            hashed = Helpers.hash_password(password)
            assert isinstance(hashed, str)
            assert len(hashed) == 32
            # Verify it's a valid hex string
            int(hashed, 16)  # Should not raise ValueError

    def test_hash_password_empty_string(self):
        """Test hash_password() with empty string."""
        hashed = Helpers.hash_password("")
        assert hashed == "d41d8cd98f00b204e9800998ecf8427e"  # MD5 of empty string
        assert len(hashed) == 32

    def test_hash_password_consistency(self):
        """Test that hash_password() produces consistent results."""
        password = "TestPass@123"
        hash1 = Helpers.hash_password(password)
        hash2 = Helpers.hash_password(password)
        assert hash1 == hash2

    def test_calculate_hex(self):
        """Test calculate_hex() with valid hex string."""
        result = Helpers.calculate_hex("1A:2B")
        expected = (0x1A + 0x2B) / 8192
        assert result == expected

    def test_calculate_hex_zero(self):
        """Test calculate_hex() with zero values."""
        result = Helpers.calculate_hex("00:00")
        assert result == 0.0

    def test_redactor_with_redact_enabled(self):
        """Test redactor redacts sensitive values when shouldredact=True."""
        original = Helpers.shouldredact
        try:
            Helpers.shouldredact = True
            test_str = '{"token": "secret123", "password": "mypass", "email": "user@example.com"}'
            result = Helpers.redactor(test_str)
            assert "secret123" not in result
            assert "mypass" not in result
            assert "user@example.com" not in result
            assert "##_REDACTED_##" in result
        finally:
            Helpers.shouldredact = original

    def test_redactor_with_redact_disabled(self):
        """Test redactor returns string unchanged when shouldredact=False."""
        original = Helpers.shouldredact
        try:
            Helpers.shouldredact = False
            test_str = '{"token": "secret123", "password": "mypass"}'
            result = Helpers.redactor(test_str)
            assert result == test_str
        finally:
            Helpers.shouldredact = original

    @patch('custom_components.dreo.pydreo.helpers.requests.get')
    def test_call_api_get(self, mock_get):
        """Test call_api with GET method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"code": 0}'
        mock_response.json.return_value = {"code": 0}
        mock_get.return_value = mock_response

        response, status = Helpers.call_api("https://api.test.com", "/path", "get", {}, {})
        assert status == 200
        assert response == {"code": 0}
        mock_get.assert_called_once()

    @patch('custom_components.dreo.pydreo.helpers.requests.post')
    def test_call_api_post(self, mock_post):
        """Test call_api with POST method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"code": 0}'
        mock_response.json.return_value = {"code": 0}
        mock_post.return_value = mock_response

        response, status = Helpers.call_api("https://api.test.com", "/path", "post", {"key": "val"}, {})
        assert status == 200
        assert response == {"code": 0}

    @patch('custom_components.dreo.pydreo.helpers.requests.put')
    def test_call_api_put(self, mock_put):
        """Test call_api with PUT method."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"code": 0}'
        mock_response.json.return_value = {"code": 0}
        mock_put.return_value = mock_response

        response, status = Helpers.call_api("https://api.test.com", "/path", "put", {"key": "val"}, {})
        assert status == 200
        assert response == {"code": 0}

    @patch('custom_components.dreo.pydreo.helpers.requests.get')
    def test_call_api_request_exception(self, mock_get):
        """Test call_api handles request exceptions."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        response, status = Helpers.call_api("https://api.test.com", "/path", "get", {}, {})
        assert response is None
        assert status is None

    @patch('custom_components.dreo.pydreo.helpers.requests.get')
    def test_call_api_non_200_status(self, mock_get):
        """Test call_api handles non-200 status code."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        response, status = Helpers.call_api("https://api.test.com", "/path", "get", {}, {})
        assert response is None
        assert status is None  # status_code is only set for 200 responses

    def test_code_check_none_input(self):
        """Test code_check with None input."""
        assert Helpers.code_check(None) is False

    def test_code_check_non_dict(self):
        """Test code_check with non-dict input."""
        assert Helpers.code_check("not a dict") is False

    def test_code_check_non_zero_code(self):
        """Test code_check with non-zero code."""
        assert Helpers.code_check({"code": 1}) is False

    def test_code_check_zero_code(self):
        """Test code_check with zero code."""
        assert Helpers.code_check({"code": 0}) is True

    def test_api_timestamp(self):
        """Test api_timestamp returns string of millisecond timestamp."""
        before = int(time.time() * 1000)
        result = Helpers.api_timestamp()
        after = int(time.time() * 1000)
        assert isinstance(result, str)
        ts = int(result)
        assert before <= ts <= after

    def test_req_headers_without_token(self):
        """Test req_headers without token."""
        manager = MagicMock()
        manager.token = None
        headers = Helpers.req_headers(manager)
        assert "authorization" not in headers
        assert headers["content-type"] == "application/json; charset=UTF-8"

    def test_req_headers_with_token(self):
        """Test req_headers with token."""
        manager = MagicMock()
        manager.token = "test_token"
        headers = Helpers.req_headers(manager)
        assert headers["authorization"] == "Bearer test_token"

    def test_req_body_login(self):
        """Test req_body for login type."""
        manager = MagicMock()
        manager.username = "user@test.com"
        manager.password = "pass123"
        body = Helpers.req_body(manager, "login")
        assert body["email"] == "user@test.com"
        assert body["grant_type"] == "email-password"
        assert "password" in body
        assert "client_id" in body

    def test_req_body_devicelist(self):
        """Test req_body for devicelist type."""
        manager = MagicMock()
        body = Helpers.req_body(manager, "devicelist")
        assert body["method"] == "devices"
        assert body["pageNo"] == "1"
        assert body["pageSize"] == "100"

    def test_req_body_unknown_type(self):
        """Test req_body for unknown type returns empty dict."""
        manager = MagicMock()
        body = Helpers.req_body(manager, "unknown_type")
        assert body == {}
