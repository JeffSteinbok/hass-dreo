"""Tests for the Dreo Button entity."""

# pylint: disable=E1123
from unittest.mock import MagicMock

from custom_components.dreo import button
from custom_components.dreo.pydreo.constant import DreoDeviceType

from .testdevicebase import TestDeviceBase


class TestDreoButtonHA(TestDeviceBase):
    """Test the Dreo Button entity."""

    def test_button_get_entries_filters_by_feature(self):
        """Only create nudge buttons for supported air circulators."""
        device = self.create_mock_device(
            type=DreoDeviceType.AIR_CIRCULATOR,
            name="Test Circulator",
            serial_number="AC001",
            features={
                "horizontal_angle_nudge": True,
                "vertical_angle_nudge": True,
            },
        )
        device.nudge_horizontal_left = MagicMock()
        device.nudge_horizontal_right = MagicMock()
        device.nudge_vertical_up = MagicMock()
        device.nudge_vertical_down = MagicMock()

        entities = button.get_entries([device])
        keys = [entity.entity_description.key for entity in entities]
        assert keys == ["Pan Left", "Pan Right", "Tilt Up", "Tilt Down"]

    def test_button_press_calls_device_method(self):
        """Pressing an entity should invoke the mapped nudge method."""
        device = self.create_mock_device(
            type=DreoDeviceType.AIR_CIRCULATOR,
            name="Test Circulator",
            serial_number="AC001",
            features={"horizontal_angle_nudge": True},
        )
        device.nudge_horizontal_left = MagicMock()

        entities = button.get_entries([device])
        pan_left = next(entity for entity in entities if entity.entity_description.key == "Pan Left")
        pan_left.press()

        device.nudge_horizontal_left.assert_called_once_with()
