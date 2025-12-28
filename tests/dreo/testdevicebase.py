"""Base class for Dreo device tests."""
from unittest.mock import MagicMock, patch
import pytest
from homeassistant.helpers.entity import Entity
from .custommocks import PyDreoDeviceMock

PATCH_BASE_PATH = 'homeassistant.helpers.entity.Entity'
PATCH_UPDATE_HA_STATE = 'homeassistant.helpers.entity.Entity.schedule_update_ha_state'

class TestDeviceBase:
    """Base class for Dreo Device Tests."""

    @pytest.fixture(autouse=True, scope="class")
    def mock_update_ha_state(self):
        """Mock the update ha state method."""
        with patch(PATCH_UPDATE_HA_STATE) as mock_method:
            mock_method.return_value = True
            yield mock_method

    def create_mock_device(self, 
                           type : str = None,
                           name: str = "Mocked Dreo Device", 
                           serial_number: str = "123456", 
                           features: dict[str, any] = None,
                           modes: list[str] = None,
                           swing_modes: list[str] = None) -> PyDreoDeviceMock:
        
        """Create a mock device."""
        pydreo_device_mock : PyDreoDeviceMock = PyDreoDeviceMock(type=type, 
                                                                 name=name, 
                                                                 serial_number=serial_number, 
                                                                 features=features,
                                                                 modes=modes,
                                                                 swing_modes=swing_modes)
        return MagicMock(return_value=pydreo_device_mock)()
   
    def verify_expected_entities(self, ha_entities: list[Entity], expected_keys: list[str]) -> None:
        """Verify the expected entities are present."""
        found_entity_keys : list[str] = []
        for ha_entity in ha_entities:
            found_entity_keys.append(ha_entity.entity_description.key)
        found_entity_keys.sort()
        assert found_entity_keys == expected_keys