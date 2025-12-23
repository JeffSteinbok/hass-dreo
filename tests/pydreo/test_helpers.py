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
    