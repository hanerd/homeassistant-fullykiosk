"""Fully Kiosk Browser media_player entity."""
import json
import logging

import voluptuous as vol
from homeassistant.components.media_player import (
    DEVICE_CLASS_SPEAKER,
    SUPPORT_PLAY_MEDIA,
    MediaPlayerDevice,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import CONTROLLER, COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_FULLY_SETTING = "setting"
CONF_FULLY_SETTING_VALUE = "value"

SERVICE_SET_CONFIGURATION_STRING = "set_configuration_string"

SET_CONFIGURATION_STRING_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Required(CONF_FULLY_SETTING): cv.string,
        vol.Required(CONF_FULLY_SETTING_VALUE): cv.string,
    }
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Fully Kiosk Browser media player."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    controller = hass.data[DOMAIN][config_entry.entry_id][CONTROLLER]

    async_add_entities([FullyMediaPlayer(coordinator, controller)], False)

    async def set_configuration_string(call) -> None:
        """Call set string config handler."""
        await async_handle_set_configuration_string_service(call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CONFIGURATION_STRING,
        set_configuration_string,
        schema=SET_CONFIGURATION_STRING_SCHEMA,
    )


class FullyMediaPlayer(MediaPlayerDevice):
    def __init__(self, coordinator, controller):
        self._name = f"{coordinator.data['deviceName']} Media Player"
        self.coordinator = coordinator
        self.controller = controller
        self._unique_id = f"{coordinator.data['deviceID']}-mediaplayer"

    @property
    def name(self):
        return self._name

    @property
    def supported_features(self):
        return SUPPORT_PLAY_MEDIA

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.data["deviceID"])},
            "name": self.coordinator.data["deviceName"],
            "manufacturer": self.coordinator.data["deviceManufacturer"],
            "model": self.coordinator.data["deviceModel"],
            "sw_version": self.coordinator.data["appVersionName"],
        }

    @property
    def unique_id(self):
        return self._unique_id

    def play_media(self, media_type, media_id, **kwargs):
        self.controller.playSound(media_id)

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Fully Kiosk Browser entity."""
        await self.coordinator.async_request_refresh()

    async def async_handle_set_configuration_string_service(self, call):
        """Handle configuration string call."""
        self.controller.setConfigurationString(
            call.data[CONF_FULLY_SETTING], call.data[CONF_FULLY_SETTING_VALUE]
        )
