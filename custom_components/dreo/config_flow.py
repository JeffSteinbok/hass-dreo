"""Config (and Options) flow for Dreo integration."""
import logging
from typing import Any, Dict
from collections import OrderedDict
import voluptuous as vol

from .haimports import * # pylint: disable=W0401,W0614
from .const import (
    DOMAIN,
    CONF_AUTO_RECONNECT
)
from .pydreo import PyDreo

_LOGGER = logging.getLogger("dreo")

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_AUTO_RECONNECT): bool
    }
)

class OptionsFlowHandler(OptionsFlow):
    """Handles options flow for the component.
    
    Note: This class follows Home Assistant 2025.12 best practices:
    - Does not explicitly set self.config_entry (provided by parent class)
    - Access config_entry via self.config_entry property
    - No constructor arguments needed
    """

    async def async_step_init(self, user_input: Dict[str, Any] | None = None) -> ConfigFlowResult:
        """Manage the options for the custom component."""
        
        _LOGGER.debug("Options Flow Step Init")
        if user_input is not None:
            _LOGGER.debug("UserInput is not none")
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init", 
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )

class DreoFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Dreo Custom config flow."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1

    def __init__(self) -> None:
        """Instantiate config flow."""
        self._username = None
        self._password = None
        self.data_schema = OrderedDict()
        self.data_schema[vol.Required(CONF_USERNAME)] = str
        self.data_schema[vol.Required(CONF_PASSWORD)] = str

    @callback
    def _show_form(self, errors=None):
        """Show form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(self.data_schema),
            errors=errors if errors else {},
        )

    async def async_step_user(self, user_input=None):
        """Handle a flow start."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if not user_input:
            return self._show_form()

        self._username = user_input[CONF_USERNAME]
        self._password = user_input[CONF_PASSWORD]

        pydreo_manager = PyDreo(self._username, self._password, "us")
        login = await self.hass.async_add_executor_job(pydreo_manager.login)
        if not login:
            return self._show_form(errors={"base": "invalid_auth"})

        return self.async_create_entry(
            title=self._username,
            data={CONF_USERNAME: self._username, CONF_PASSWORD: self._password},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowHandler:
        """Get the options flow for this handler.
        
        Note: Following Home Assistant 2025.12 pattern:
        - Returns OptionsFlowHandler() without passing config_entry
        - config_entry is automatically provided by Home Assistant
        """
        return OptionsFlowHandler()

