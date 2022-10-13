"""Config flow for elvia integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    COST_PERIOD,
    DOMAIN,
    INCLUDE_PRODUCTION_TO_GRID,
    MAX_HOURS,
    METER,
    METER_READING,
    TOKEN,
)
from elvia.elvia import ElviaApi

_LOGGER = logging.getLogger(__name__)

data_types: dict[str, int] = {"Max Hours": 0, "Meter Values": 1}

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(TOKEN): cv.string,
        vol.Optional(INCLUDE_PRODUCTION_TO_GRID, default=False): cv.boolean,
        vol.Optional(COST_PERIOD, default=True): cv.boolean,
        vol.Optional(MAX_HOURS, default=True): cv.boolean,
        vol.Optional(METER_READING, default=False): cv.boolean,
    }
)


# pylint: disable=fixme
async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    result = await ElviaApi(data[TOKEN]).get_meters()

    if result.status_code == 401:
        raise InvalidAuthenticationToken
    if result.status_code == 403:
        raise RequestForbidden
    if result.status_code != 200:
        raise Exception("Something, something went wrong...")

    return {"title": "elvia", "token": data[TOKEN], METER: result}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for elvia."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
            return self.async_create_entry(title=info["title"], data=user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuthenticationToken:
            errors["base"] = "invalid_auth"
        except RequestForbidden:
            errors["base"] = "forbidden_call"
        except asyncio.TimeoutError:
            errors["base"] = "timeout"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class InvalidAuthenticationToken(HomeAssistantError):
    """Error to indicate that the TOKEN is invalid or not available."""


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class RequestForbidden(HomeAssistantError):
    """Error to indicate there is a permission issue."""
