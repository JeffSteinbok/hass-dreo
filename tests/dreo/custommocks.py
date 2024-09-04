"""Custom mocks for Dreo tests."""
from unittest.mock import MagicMock

class PyDreoDeviceMock(MagicMock):
    """Mock for PyDreoDevice."""

    def __init__(self, 
                 name: str = "Mocked Dreo Device", 
                 serial_number : str = "123456",
                 features : dict[str, any] = None) -> None:
         super().__init__()
         self.name = name
         self.serial_number = serial_number
         self._supported_features : list[str] = []
         if (features is not None):
            self.set_features(features)

    def set_feature(self, feature_name : str, value : any):
        """Set a feature on the mock."""
        setattr(self, feature_name, value)
        if (value is not None) and (feature_name not in self._supported_features):
            self._supported_features.append(feature_name)
    
    def set_features(self, features : dict[str, any]):
        """Set multiple features on the mock."""
        for feature_name, value in features.items():
            self.set_feature(feature_name, value)

    def is_feature_supported(self, feature_name : str) -> bool:
        """Check if a feature is supported."""
        return feature_name in self._supported_features
    
class TestBase:
    """Base class for all device tests."""

  