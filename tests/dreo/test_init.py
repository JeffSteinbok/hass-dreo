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

    def test_successful_setup_with_fan(self):
        """Test successful setup with a TOWER_FAN device."""
        from custom_components.dreo import async_setup_entry
        from custom_components.dreo.pydreo.constant import DreoDeviceType
        from homeassistant.const import Platform

        mock_hass = MagicMock()
        mock_hass.data = {}
        mock_hass.async_add_executor_job = AsyncMock(side_effect=[True, True])  # login, load_devices
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.data = {"username": "test@example.com", "password": "password"}
        mock_entry.options = {}
        mock_entry.add_update_listener = MagicMock(return_value=MagicMock())
        mock_entry.async_on_unload = MagicMock()

        # Create mock device
        mock_device = MagicMock()
        mock_device.type = DreoDeviceType.TOWER_FAN

        # Mock PyDreo
        mock_pydreo = MagicMock()
        mock_pydreo.devices = [mock_device]
        mock_pydreo.start_transport = MagicMock()
        mock_pydreo.auto_reconnect = True

        with patch('custom_components.dreo.pydreo.PyDreo', return_value=mock_pydreo):
            result = asyncio.run(async_setup_entry(mock_hass, mock_entry))

        assert result is True
        assert "dreo" in mock_hass.data
        assert "pydreo_manager" in mock_hass.data["dreo"]
        assert "platforms" in mock_hass.data["dreo"]
        
        platforms = mock_hass.data["dreo"]["platforms"]
        assert Platform.FAN in platforms
        assert Platform.SENSOR in platforms
        assert Platform.SWITCH in platforms
        assert Platform.NUMBER in platforms
        
        mock_pydreo.start_transport.assert_called_once()
        mock_hass.config_entries.async_forward_entry_setups.assert_called_once()

    def test_successful_setup_with_heater(self):
        """Test successful setup with a HEATER device."""
        from custom_components.dreo import async_setup_entry
        from custom_components.dreo.pydreo.constant import DreoDeviceType
        from homeassistant.const import Platform

        mock_hass = MagicMock()
        mock_hass.data = {}
        mock_hass.async_add_executor_job = AsyncMock(side_effect=[True, True])
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.data = {"username": "test@example.com", "password": "password"}
        mock_entry.options = {}
        mock_entry.add_update_listener = MagicMock(return_value=MagicMock())
        mock_entry.async_on_unload = MagicMock()

        mock_device = MagicMock()
        mock_device.type = DreoDeviceType.HEATER

        mock_pydreo = MagicMock()
        mock_pydreo.devices = [mock_device]
        mock_pydreo.start_transport = MagicMock()
        mock_pydreo.auto_reconnect = True

        with patch('custom_components.dreo.pydreo.PyDreo', return_value=mock_pydreo):
            result = asyncio.run(async_setup_entry(mock_hass, mock_entry))

        assert result is True
        platforms = mock_hass.data["dreo"]["platforms"]
        assert Platform.CLIMATE in platforms
        assert Platform.SENSOR in platforms
        assert Platform.SWITCH in platforms
        assert Platform.NUMBER in platforms

    def test_successful_setup_with_ceiling_fan(self):
        """Test successful setup with a CEILING_FAN device."""
        from custom_components.dreo import async_setup_entry
        from custom_components.dreo.pydreo.constant import DreoDeviceType
        from homeassistant.const import Platform

        mock_hass = MagicMock()
        mock_hass.data = {}
        mock_hass.async_add_executor_job = AsyncMock(side_effect=[True, True])
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.data = {"username": "test@example.com", "password": "password"}
        mock_entry.options = {}
        mock_entry.add_update_listener = MagicMock(return_value=MagicMock())
        mock_entry.async_on_unload = MagicMock()

        mock_device = MagicMock()
        mock_device.type = DreoDeviceType.CEILING_FAN

        mock_pydreo = MagicMock()
        mock_pydreo.devices = [mock_device]
        mock_pydreo.start_transport = MagicMock()
        mock_pydreo.auto_reconnect = True

        with patch('custom_components.dreo.pydreo.PyDreo', return_value=mock_pydreo):
            result = asyncio.run(async_setup_entry(mock_hass, mock_entry))

        assert result is True
        platforms = mock_hass.data["dreo"]["platforms"]
        assert Platform.FAN in platforms
        assert Platform.LIGHT in platforms
        assert Platform.SENSOR in platforms
        assert Platform.SWITCH in platforms
        assert Platform.NUMBER in platforms

    def test_successful_setup_with_air_circulator(self):
        """Test successful setup with an AIR_CIRCULATOR device includes LIGHT platform."""
        from custom_components.dreo import async_setup_entry
        from custom_components.dreo.pydreo.constant import DreoDeviceType
        from homeassistant.const import Platform

        mock_hass = MagicMock()
        mock_hass.data = {}
        mock_hass.async_add_executor_job = AsyncMock(side_effect=[True, True])
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.data = {"username": "test@example.com", "password": "password"}
        mock_entry.options = {}
        mock_entry.add_update_listener = MagicMock(return_value=MagicMock())
        mock_entry.async_on_unload = MagicMock()

        mock_device = MagicMock()
        mock_device.type = DreoDeviceType.AIR_CIRCULATOR

        mock_pydreo = MagicMock()
        mock_pydreo.devices = [mock_device]
        mock_pydreo.start_transport = MagicMock()
        mock_pydreo.auto_reconnect = True

        with patch('custom_components.dreo.pydreo.PyDreo', return_value=mock_pydreo):
            result = asyncio.run(async_setup_entry(mock_hass, mock_entry))

        assert result is True
        platforms = mock_hass.data["dreo"]["platforms"]
        assert Platform.FAN in platforms
        assert Platform.LIGHT in platforms
        assert Platform.SENSOR in platforms
        assert Platform.SWITCH in platforms
        assert Platform.NUMBER in platforms

    def test_successful_setup_with_humidifier(self):
        """Test successful setup with a HUMIDIFIER device."""
        from custom_components.dreo import async_setup_entry
        from custom_components.dreo.pydreo.constant import DreoDeviceType
        from homeassistant.const import Platform

        mock_hass = MagicMock()
        mock_hass.data = {}
        mock_hass.async_add_executor_job = AsyncMock(side_effect=[True, True])
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.data = {"username": "test@example.com", "password": "password"}
        mock_entry.options = {}
        mock_entry.add_update_listener = MagicMock(return_value=MagicMock())
        mock_entry.async_on_unload = MagicMock()

        mock_device = MagicMock()
        mock_device.type = DreoDeviceType.HUMIDIFIER

        mock_pydreo = MagicMock()
        mock_pydreo.devices = [mock_device]
        mock_pydreo.start_transport = MagicMock()
        mock_pydreo.auto_reconnect = True

        with patch('custom_components.dreo.pydreo.PyDreo', return_value=mock_pydreo):
            result = asyncio.run(async_setup_entry(mock_hass, mock_entry))

        assert result is True
        platforms = mock_hass.data["dreo"]["platforms"]
        assert Platform.HUMIDIFIER in platforms
        assert Platform.SENSOR in platforms
        assert Platform.SWITCH in platforms
        assert Platform.NUMBER in platforms

    def test_successful_setup_with_dehumidifier(self):
        """Test successful setup with a DEHUMIDIFIER device."""
        from custom_components.dreo import async_setup_entry
        from custom_components.dreo.pydreo.constant import DreoDeviceType
        from homeassistant.const import Platform

        mock_hass = MagicMock()
        mock_hass.data = {}
        mock_hass.async_add_executor_job = AsyncMock(side_effect=[True, True])
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.data = {"username": "test@example.com", "password": "password"}
        mock_entry.options = {}
        mock_entry.add_update_listener = MagicMock(return_value=MagicMock())
        mock_entry.async_on_unload = MagicMock()

        mock_device = MagicMock()
        mock_device.type = DreoDeviceType.DEHUMIDIFIER

        mock_pydreo = MagicMock()
        mock_pydreo.devices = [mock_device]
        mock_pydreo.start_transport = MagicMock()
        mock_pydreo.auto_reconnect = True

        with patch('custom_components.dreo.pydreo.PyDreo', return_value=mock_pydreo):
            result = asyncio.run(async_setup_entry(mock_hass, mock_entry))

        assert result is True
        platforms = mock_hass.data["dreo"]["platforms"]
        assert Platform.HUMIDIFIER in platforms
        assert Platform.FAN in platforms
        assert Platform.SENSOR in platforms
        assert Platform.SWITCH in platforms
        assert Platform.NUMBER in platforms

    def test_successful_setup_with_chef_maker(self):
        """Test successful setup with a CHEF_MAKER device."""
        from custom_components.dreo import async_setup_entry
        from custom_components.dreo.pydreo.constant import DreoDeviceType
        from homeassistant.const import Platform

        mock_hass = MagicMock()
        mock_hass.data = {}
        mock_hass.async_add_executor_job = AsyncMock(side_effect=[True, True])
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.data = {"username": "test@example.com", "password": "password"}
        mock_entry.options = {}
        mock_entry.add_update_listener = MagicMock(return_value=MagicMock())
        mock_entry.async_on_unload = MagicMock()

        mock_device = MagicMock()
        mock_device.type = DreoDeviceType.CHEF_MAKER

        mock_pydreo = MagicMock()
        mock_pydreo.devices = [mock_device]
        mock_pydreo.start_transport = MagicMock()
        mock_pydreo.auto_reconnect = True

        with patch('custom_components.dreo.pydreo.PyDreo', return_value=mock_pydreo):
            result = asyncio.run(async_setup_entry(mock_hass, mock_entry))

        assert result is True
        platforms = mock_hass.data["dreo"]["platforms"]
        assert Platform.SENSOR in platforms
        assert Platform.SWITCH in platforms
        assert Platform.NUMBER in platforms
        # Should NOT have FAN or CLIMATE
        assert Platform.FAN not in platforms
        assert Platform.CLIMATE not in platforms

    def test_successful_setup_with_evaporative_cooler(self):
        """Test successful setup with an EVAPORATIVE_COOLER device."""
        from custom_components.dreo import async_setup_entry
        from custom_components.dreo.pydreo.constant import DreoDeviceType
        from homeassistant.const import Platform

        mock_hass = MagicMock()
        mock_hass.data = {}
        mock_hass.async_add_executor_job = AsyncMock(side_effect=[True, True])
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.data = {"username": "test@example.com", "password": "password"}
        mock_entry.options = {}
        mock_entry.add_update_listener = MagicMock(return_value=MagicMock())
        mock_entry.async_on_unload = MagicMock()

        mock_device = MagicMock()
        mock_device.type = DreoDeviceType.EVAPORATIVE_COOLER

        mock_pydreo = MagicMock()
        mock_pydreo.devices = [mock_device]
        mock_pydreo.start_transport = MagicMock()
        mock_pydreo.auto_reconnect = True

        with patch('custom_components.dreo.pydreo.PyDreo', return_value=mock_pydreo):
            result = asyncio.run(async_setup_entry(mock_hass, mock_entry))

        assert result is True
        platforms = mock_hass.data["dreo"]["platforms"]
        assert Platform.FAN in platforms
        assert Platform.SENSOR in platforms
        assert Platform.SWITCH in platforms
        assert Platform.NUMBER in platforms

    def test_auto_reconnect_default_true(self):
        """Test that auto_reconnect defaults to True when not specified in options."""
        from custom_components.dreo import async_setup_entry
        from custom_components.dreo.pydreo.constant import DreoDeviceType

        mock_hass = MagicMock()
        mock_hass.data = {}
        mock_hass.async_add_executor_job = AsyncMock(side_effect=[True, True])
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.data = {"username": "test@example.com", "password": "password"}
        mock_entry.options = {}  # No auto_reconnect specified
        mock_entry.add_update_listener = MagicMock(return_value=MagicMock())
        mock_entry.async_on_unload = MagicMock()

        mock_device = MagicMock()
        mock_device.type = DreoDeviceType.TOWER_FAN

        mock_pydreo = MagicMock()
        mock_pydreo.devices = [mock_device]
        mock_pydreo.start_transport = MagicMock()

        with patch('custom_components.dreo.pydreo.PyDreo', return_value=mock_pydreo):
            result = asyncio.run(async_setup_entry(mock_hass, mock_entry))

        assert result is True
        assert mock_pydreo.auto_reconnect is True

    def test_auto_reconnect_from_options(self):
        """Test that auto_reconnect is set from options when specified."""
        from custom_components.dreo import async_setup_entry
        from custom_components.dreo.pydreo.constant import DreoDeviceType

        mock_hass = MagicMock()
        mock_hass.data = {}
        mock_hass.async_add_executor_job = AsyncMock(side_effect=[True, True])
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_forward_entry_setups = AsyncMock()

        mock_entry = MagicMock()
        mock_entry.data = {"username": "test@example.com", "password": "password"}
        mock_entry.options = {"auto_reconnect": False}  # Explicitly set to False
        mock_entry.add_update_listener = MagicMock(return_value=MagicMock())
        mock_entry.async_on_unload = MagicMock()

        mock_device = MagicMock()
        mock_device.type = DreoDeviceType.TOWER_FAN

        mock_pydreo = MagicMock()
        mock_pydreo.devices = [mock_device]
        mock_pydreo.start_transport = MagicMock()

        with patch('custom_components.dreo.pydreo.PyDreo', return_value=mock_pydreo):
            result = asyncio.run(async_setup_entry(mock_hass, mock_entry))

        assert result is True
        assert mock_pydreo.auto_reconnect is False

    def test_unload_entry(self):
        """Test async_unload_entry."""
        from custom_components.dreo import async_unload_entry
        from homeassistant.const import Platform

        mock_hass = MagicMock()
        mock_pydreo = MagicMock()
        mock_pydreo.stop_transport = MagicMock()
        
        mock_hass.data = {
            "dreo": {
                "pydreo_manager": mock_pydreo,
                "platforms": {Platform.FAN, Platform.SENSOR}
            }
        }
        mock_hass.config_entries = MagicMock()
        mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        mock_entry = MagicMock()

        result = asyncio.run(async_unload_entry(mock_hass, mock_entry))

        assert result is True
        mock_pydreo.stop_transport.assert_called_once()
        assert "dreo" not in mock_hass.data
        mock_hass.config_entries.async_unload_platforms.assert_called_once()

    def test_remove_config_entry_device(self):
        """Test async_remove_config_entry_device always returns True."""
        from custom_components.dreo import async_remove_config_entry_device

        mock_hass = MagicMock()
        mock_entry = MagicMock()
        mock_device = MagicMock()

        result = asyncio.run(async_remove_config_entry_device(mock_hass, mock_entry, mock_device))

        assert result is True
