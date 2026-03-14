"""Init tests for the Dreo integration."""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.dreo.const import DEBUG_TEST_MODE

class TestInit:
    
    def test_debug_test_mode(self):
        """Test that DEBUG_TEST_MODE is set to False."""
        assert DEBUG_TEST_MODE is False, "DEBUG_TEST_MODE should be False to merge changes."

    def test_login_failure_raises_config_entry_not_ready(self):
        """Test that a login failure raises ConfigEntryNotReady instead of returning False."""
        from custom_components.dreo import async_setup_entry

        mock_hass = MagicMock()
        mock_hass.data = {}
        mock_hass.async_add_executor_job = AsyncMock(return_value=False)
        mock_hass.config_entries = MagicMock()

        mock_entry = MagicMock()
        mock_entry.data = {"username": "test@example.com", "password": "password"}
        mock_entry.options = {}

        with pytest.raises(ConfigEntryNotReady):
            asyncio.run(async_setup_entry(mock_hass, mock_entry))

    def test_load_devices_failure_raises_config_entry_not_ready(self):
        """Test that a load_devices failure raises ConfigEntryNotReady instead of returning False."""
        from custom_components.dreo import async_setup_entry

        mock_hass = MagicMock()
        mock_hass.data = {}
        # login succeeds, load_devices fails
        mock_hass.async_add_executor_job = AsyncMock(side_effect=[True, False])
        mock_hass.config_entries = MagicMock()

        mock_entry = MagicMock()
        mock_entry.data = {"username": "test@example.com", "password": "password"}
        mock_entry.options = {}

        with pytest.raises(ConfigEntryNotReady):
            asyncio.run(async_setup_entry(mock_hass, mock_entry))