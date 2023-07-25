"""Include all HA imports here."""

# Single file for all HA imports so that we can include this in all
# other files, and disable linting in one specific place.

# This is pretty ugly all things considered, but seems less ugly than 
# ignoring specific lines all over the place

# pyright: reportMissingImports =false
# pylint: disable=all

import voluptuous as vol
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_REGION, Platform

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send

from homeassistant.core import HomeAssistant

from homeassistant.components.diagnostics import REDACTED 
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.typing import StateType

from homeassistant.helpers.entity import (
    DeviceInfo,
    Entity 
)

from homeassistant.core import callback #type:ignore

from homeassistant.util.percentage import (
    int_states_in_range,
    percentage_to_ranged_value,
    ranged_value_to_percentage,
) 

from homeassistant.components.fan import (
    FanEntity, 
    FanEntityFeature
)

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from homeassistant.const import (
    TEMPERATURE,
    UnitOfTemperature 
)
