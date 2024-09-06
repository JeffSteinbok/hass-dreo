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
    