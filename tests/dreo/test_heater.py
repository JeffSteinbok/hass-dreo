"""Tests for the Dreo Ceiling heater HA class."""
from unittest.mock import MagicMock

from custom_components.dreo import climate
from custom_components.dreo import switch
from custom_components.dreo import number
from custom_components.dreo import light
from custom_components.dreo import sensor
from .testdevicebase import TestDeviceBase
from .custommocks import PyDreoDeviceMock

from homeassistant.components.climate import (
    HVACMode
)

from custom_components.dreo.pydreo.constant import (
    SPEED_RANGE,
    HEATER_MODE_COOLAIR,
    HEATER_MODE_HOTAIR,
    HEATER_MODE_ECO,
    HEATER_MODE_OFF,
    HEAT_RANGE,
    ECOLEVEL_RANGE,
    SPEED_RANGE,
    TEMP_RANGE,
    TARGET_TEMP_RANGE,
    TARGET_TEMP_RANGE_ECO,
    HeaterOscillationAngles,
    HUMIDITY_RANGE,
    SWING_ON,
    SWING_OFF,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    PRESET_NONE,
    PRESET_ECO,
    DreoDeviceType
)

class TestDreoHeaterHA(TestDeviceBase):
    """Test the Dreo Ceiling heater HA class."""

    def test_ceiling_heater_simple(self, mock_update_ha_state: MagicMock):
        """Test the Dreo Ceiling heater HA class."""
        
        mocked_pydreo_heater : PyDreoDeviceMock = self.create_mock_device(name="Test Heater", 
                                                                            serial_number="123456", 
                                                                            features= { "poweron" : True,
                                                                                        "temperature" : 75,
                                                                                        "device_ranges": {HEAT_RANGE: (1, 3), ECOLEVEL_RANGE: (41, 95)},
                                                                                        "htalevel": 2,
                                                                                        "hvac_mode": HVACMode.OFF,
                                                                                        "hvac_modes" : [
                                                                                            HEATER_MODE_COOLAIR,
                                                                                            HEATER_MODE_HOTAIR,
                                                                                            HEATER_MODE_ECO,
                                                                                            HEATER_MODE_OFF,
                                                                                        ],
                                                                                        "swing_modes" : [
                                                                                            HeaterOscillationAngles.OSC,
                                                                                            HeaterOscillationAngles.SIXTY,
                                                                                            HeaterOscillationAngles.NINETY,
                                                                                            HeaterOscillationAngles.ONE_TWENTY]})
        
        test_heater = climate.DreoHeaterHA(mocked_pydreo_heater)
        assert test_heater.is_on is True
