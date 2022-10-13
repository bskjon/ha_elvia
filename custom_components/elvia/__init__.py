"""The elvia integration."""
from __future__ import annotations

import asyncio
import logging

# from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType


from .const import COST_PERIOD, MAX_HOURS, METER, METER_READING, TOKEN, DATA_HASS_CONFIG
from elvia.elvia import ElviaApi

PLATFORMS: list[Platform] = [Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)



async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Elvia component."""

    hass.data[DATA_HASS_CONFIG] = config
    return True


# pylint: disable=fixme
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up elvia from a config entry."""

    hass.data[TOKEN] = entry.data[TOKEN]
    hass.data[MAX_HOURS] = entry.data[MAX_HOURS]
    hass.data[METER_READING] = entry.data[METER_READING]
    hass.data[COST_PERIOD] = entry.data[COST_PERIOD]

    try:
        result = await ElviaApi(entry.data[TOKEN]).get_meters()
        hass.data[METER] = result
    except asyncio.TimeoutError as err:
        _LOGGER.error("Connection timed out while contacting Elvia. Please try again later. %s", err)
        return False

    # IF NEEDED: entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _close))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    return unload_ok

# https://dev.to/adafycheng/write-custom-component-for-home-assistant-4fce
