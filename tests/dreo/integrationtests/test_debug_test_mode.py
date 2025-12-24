"""Tests for Dreo Fans"""
# pylint: disable=used-before-assignment
import logging
import pytest
from custom_components.dreo.debug_test_mode import get_debug_test_mode_payload
from custom_components.dreo.pydreo import PyDreo

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TestDebugTestMode:
    """Test Debug Test Mode."""

    def test_load(self):
        """Test that the Debug Test Mode loads correctly."""
        payload: dict = get_debug_test_mode_payload("custom_components/dreo")
        assert payload is not None, "Payload should not be None"

    def test_pydreo(self):  # pylint: disable=invalid-name
        """Load fan and test sending commands."""
        pydreo_manager = PyDreo('EMAIL', 
                                'PASSWORD', 
                                redact=True, 
                                debug_test_mode=True, 
                                debug_test_mode_payload=get_debug_test_mode_payload("custom_components/dreo")) # pylint: disable=E0601

        pydreo_manager.login()
        pydreo_manager.load_devices()
        assert len(pydreo_manager.devices) == 22
        
        # Find tower fan by serial number
        tower_fan = next((d for d in pydreo_manager.devices if d.serial_number == "HTF005S_1"), None)
        assert tower_fan is not None, "Tower fan HTF005S_1 not found"
        assert tower_fan.model == "DR-HTF005S"
        assert tower_fan.speed_range == (1, 12)
        assert tower_fan.preset_modes == ['normal', 'natural', 'sleep', 'auto']
        assert tower_fan.oscillating is not None

        tower_fan.oscillating = True
        assert tower_fan.oscillating is True, "Fan should be oscillating after setting to True"