"""Include all HA imports here."""

# Single file for all HA imports so that we can include this in all
# other files, and disable linting in one specific place.

# This is pretty ugly all things considered, but seems less ugly than 
# ignoring specific lines all over the place

# pylint: disable=unused-import, wildcard-import, unused-wildcard-import

import voluptuous as vol
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_REGION, Platform

from homeassistant import config_entries, core

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send

from homeassistant.components.diagnostics import REDACTED 
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_registry import async_entries_for_config_entry
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from homeassistant.helpers.entity import (
    DeviceInfo,
    Entity,
    EntityDescription
)

from homeassistant.util.percentage import (
    int_states_in_range,
    percentage_to_ranged_value,
    ranged_value_to_percentage
) 

from homeassistant.components.fan import (
    FanEntity, 
    FanEntityFeature
)

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    ClimateEntityDescription,
    FAN_ON,
    FAN_OFF
)

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass
)

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription
)

from homeassistant.components.light import (
    LightEntity,
    LightEntityFeature,
    ColorMode,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_BRIGHTNESS
)

from homeassistant.util.color import (
    value_to_brightness,
    brightness_to_value
)

from homeassistant.const import (
    TEMPERATURE,
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    STATE_OFF,
    STATE_ON,
    UnitOfTemperature)

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    PRESET_NONE,
    PRESET_ECO,
    SWING_OFF,
    SWING_ON,
    SWING_VERTICAL,
    SWING_HORIZONTAL,
    SWING_BOTH,
    HVACAction,
    HVACMode,
)

from homeassistant.helpers import entity_platform
