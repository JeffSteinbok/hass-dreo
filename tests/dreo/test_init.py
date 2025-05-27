"""Init tests for the Dreo integration."""

from custom_components.dreo.const import DEBUG_TEST_MODE

class TestInit:
    
    def test_debug_test_mode(self):
        """Test that DEBUG_TEST_MODE is set to False."""
        assert DEBUG_TEST_MODE is False, "DEBUG_TEST_MODE should be False to merge changes."