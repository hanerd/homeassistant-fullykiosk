"""The Fully Kiosk Browser integration."""
import asyncio
import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (ATTR_ENTITY_ID, CONF_HOST, CONF_PASSWORD,
                                 CONF_PORT)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import (DataUpdateCoordinator,
                                                      UpdateFailed)

from fullykiosk import FullyKiosk

from .const import CONTROLLER, COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)


PLATFORMS = ["binary_sensor", "light", "media_player", "sensor", "switch"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Fully Kiosk Browser component."""

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Fully Kiosk Browser from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    config = entry.data
    fully = FullyKiosk(config[CONF_HOST], config[CONF_PORT], config[CONF_PASSWORD])

    async def async_update_data():
        """Fetch data from REST API."""
        data = await hass.async_add_executor_job(fully.getDeviceInfo)
        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="deviceInfo",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id][COORDINATOR] = coordinator
    hass.data[DOMAIN][entry.entry_id][CONTROLLER] = fully

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
