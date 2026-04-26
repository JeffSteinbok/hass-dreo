"""Tests for the Dreo config flow."""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from collections import OrderedDict

from custom_components.dreo.config_flow import DreoFlowHandler, OptionsFlowHandler, OPTIONS_SCHEMA


class TestDreoFlowHandler:
    """Tests for DreoFlowHandler."""

    def test_flow_handler_init(self):
        """Test that __init__ sets up data_schema with username and password."""
        flow = DreoFlowHandler()

        assert flow._username is None
        assert flow._password is None
        assert isinstance(flow.data_schema, OrderedDict)
        assert len(flow.data_schema) == 2

        # Check that username and password fields are in the schema
        keys = list(flow.data_schema.keys())
        assert any("username" in str(key) for key in keys)
        assert any("password" in str(key) for key in keys)

    def test_show_form_no_errors(self):
        """Test _show_form with no errors returns form with empty errors dict."""
        flow = DreoFlowHandler()
        flow.async_show_form = MagicMock(return_value="form_result")

        result = flow._show_form()

        assert result == "form_result"
        flow.async_show_form.assert_called_once()
        call_kwargs = flow.async_show_form.call_args[1]
        assert call_kwargs["step_id"] == "user"
        assert call_kwargs["errors"] == {}
        # Verify data_schema is present (type depends on voluptuous version)
        assert "data_schema" in call_kwargs

    def test_show_form_with_errors(self):
        """Test _show_form with errors passes them through."""
        flow = DreoFlowHandler()
        flow.async_show_form = MagicMock(return_value="form_result")

        errors = {"base": "invalid_auth"}
        result = flow._show_form(errors=errors)

        assert result == "form_result"
        flow.async_show_form.assert_called_once()
        call_kwargs = flow.async_show_form.call_args[1]
        assert call_kwargs["step_id"] == "user"
        assert call_kwargs["errors"] == errors

    def test_async_step_user_no_input(self):
        """Test async_step_user with no input shows form."""
        flow = DreoFlowHandler()
        flow._show_form = MagicMock(return_value="form_result")
        flow._async_current_entries = MagicMock(return_value=[])

        result = asyncio.run(flow.async_step_user(user_input=None))

        assert result == "form_result"
        flow._show_form.assert_called_once_with()

    def test_async_step_user_existing_entry(self):
        """Test async_step_user with existing entry returns single_instance_allowed abort."""
        flow = DreoFlowHandler()
        flow._async_current_entries = MagicMock(return_value=[{"some": "entry"}])
        flow.async_abort = MagicMock(return_value="abort_result")

        result = asyncio.run(flow.async_step_user(user_input={}))

        assert result == "abort_result"
        flow.async_abort.assert_called_once_with(reason="single_instance_allowed")

    def test_async_step_user_login_success(self):
        """Test async_step_user with valid credentials creates entry with username title."""
        flow = DreoFlowHandler()
        flow._async_current_entries = MagicMock(return_value=[])
        flow.async_create_entry = MagicMock(return_value="entry_result")

        mock_hass = MagicMock()
        mock_hass.async_add_executor_job = AsyncMock(return_value=True)
        flow.hass = mock_hass

        user_input = {"username": "test@example.com", "password": "testpass123"}

        with patch("custom_components.dreo.config_flow.PyDreo") as mock_pydreo:
            mock_manager = MagicMock()
            mock_pydreo.return_value = mock_manager

            result = asyncio.run(flow.async_step_user(user_input=user_input))

        assert result == "entry_result"
        assert flow._username == "test@example.com"
        assert flow._password == "testpass123"

        # Verify PyDreo was instantiated correctly
        mock_pydreo.assert_called_once_with("test@example.com", "testpass123", "us")

        # Verify login was called
        mock_hass.async_add_executor_job.assert_called_once_with(mock_manager.login)

        # Verify entry was created
        flow.async_create_entry.assert_called_once_with(title="test@example.com", data={"username": "test@example.com", "password": "testpass123"})

    def test_async_step_user_login_failure(self):
        """Test async_step_user with failed login shows form with invalid_auth error."""
        flow = DreoFlowHandler()
        flow._async_current_entries = MagicMock(return_value=[])
        flow._show_form = MagicMock(return_value="form_with_error")

        mock_hass = MagicMock()
        mock_hass.async_add_executor_job = AsyncMock(return_value=False)
        flow.hass = mock_hass

        user_input = {"username": "test@example.com", "password": "wrongpassword"}

        with patch("custom_components.dreo.config_flow.PyDreo") as mock_pydreo:
            mock_manager = MagicMock()
            mock_pydreo.return_value = mock_manager

            result = asyncio.run(flow.async_step_user(user_input=user_input))

        assert result == "form_with_error"
        assert flow._username == "test@example.com"
        assert flow._password == "wrongpassword"

        # Verify PyDreo was instantiated
        mock_pydreo.assert_called_once_with("test@example.com", "wrongpassword", "us")

        # Verify login was attempted
        mock_hass.async_add_executor_job.assert_called_once_with(mock_manager.login)

        # Verify error form was shown
        flow._show_form.assert_called_once_with(errors={"base": "invalid_auth"})

    def test_async_get_options_flow(self):
        """Test async_get_options_flow returns OptionsFlowHandler instance."""
        mock_config_entry = MagicMock()

        result = DreoFlowHandler.async_get_options_flow(mock_config_entry)

        assert isinstance(result, OptionsFlowHandler)


class TestOptionsFlowHandler:
    """Tests for OptionsFlowHandler."""

    def test_options_flow_no_input(self):
        """Test async_step_init with no input shows form with current options."""
        flow = OptionsFlowHandler()
        flow.async_show_form = MagicMock(return_value="form_result")
        flow.add_suggested_values_to_schema = MagicMock(return_value="schema_with_values")

        mock_config_entry = MagicMock()
        mock_config_entry.options = {"auto_reconnect": True}

        # Mock the config_entry property
        with patch.object(type(flow), "config_entry", new_callable=lambda: property(lambda self: mock_config_entry)):
            result = asyncio.run(flow.async_step_init(user_input=None))

        assert result == "form_result"
        flow.async_show_form.assert_called_once_with(step_id="init", data_schema="schema_with_values")
        flow.add_suggested_values_to_schema.assert_called_once_with(OPTIONS_SCHEMA, {"auto_reconnect": True})

    def test_options_flow_with_input(self):
        """Test async_step_init with input creates entry with provided data."""
        flow = OptionsFlowHandler()
        flow.async_create_entry = MagicMock(return_value="entry_result")

        mock_config_entry = MagicMock()
        mock_config_entry.options = {"auto_reconnect": True}

        # Mock the config_entry property
        with patch.object(type(flow), "config_entry", new_callable=lambda: property(lambda self: mock_config_entry)):
            user_input = {"auto_reconnect": False}
            result = asyncio.run(flow.async_step_init(user_input=user_input))

        assert result == "entry_result"
        flow.async_create_entry.assert_called_once_with(data={"auto_reconnect": False})

    def test_options_schema_structure(self):
        """Test that OPTIONS_SCHEMA has the correct structure."""
        # Verify OPTIONS_SCHEMA exists and has expected structure
        assert OPTIONS_SCHEMA is not None

        # Verify the schema contains auto_reconnect as a required boolean
        schema_dict = OPTIONS_SCHEMA.schema
        assert len(schema_dict) == 1

        # Check that auto_reconnect key exists and is required
        keys = list(schema_dict.keys())
        assert any("auto_reconnect" in str(key) for key in keys)

        # Check that it's a boolean type
        for key, value in schema_dict.items():
            if "auto_reconnect" in str(key):
                assert value is bool
