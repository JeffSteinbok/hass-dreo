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
        assert len(pydreo_manager.devices) == 6
        fan = pydreo_manager.devices[0]
        assert fan.speed_range == (1, 5)
        assert fan.preset_modes == ['normal', 'natural', 'sleep', 'auto']
        assert fan.oscillating is False

        ac = pydreo_manager.devices[1]
        assert ac.temperature == 88

        fan.oscillating = True
        assert fan.oscillating is True, "Fan should be oscillating after setting to True"