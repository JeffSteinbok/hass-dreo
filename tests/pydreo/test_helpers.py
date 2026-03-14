"""Test helpers for PyDreo."""
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
        assert Helpers.name_from_value(name_value_collection, False) is "off" # pylint: disable=E0601
        assert Helpers.name_from_value(name_value_collection, True) is "on"
        assert Helpers.name_from_value(name_value_collection, "oxx") is None

    def test_get_name_list(self):
        """Test get_name_list() method."""
        name_value_collection = [("on", True), ("off", False)]
        assert Helpers.get_name_list(name_value_collection)[0] is "on" # pylint: disable=E0601
        assert Helpers.get_name_list(name_value_collection)[1] is "off"

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
    