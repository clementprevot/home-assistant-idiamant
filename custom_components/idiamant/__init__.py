"""
The iDiamant by Netatmo integration.

For more details about this integration, please refer to
https://github.com/clementprevot/home-assistant-idiamant
"""

from __future__ import annotations

from datetime import timedelta
from http import HTTPStatus
import logging

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import (
    aiohttp_client,
    config_entry_oauth2_flow,
    config_validation as cv,
)
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from . import api, config_flow
from .const import (
    AUTH,
    DATA_HOMES,
    DATA_MODULES,
    DATA_ROOMS,
    DOMAIN,
    OAUTH2_AUTHORIZE_URL,
    OAUTH2_TOKEN_URL,
    PLATFORMS,
    SCOPES,
    TYPE_SECURITY,
)

SCAN_INTERVAL = timedelta(minutes=1)

_LOGGER: logging.Logger = logging.getLogger(__package__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """
    Set up the iDiamant component.
    """

    hass.data[DOMAIN] = {
        DATA_HOMES: {},
        DATA_ROOMS: {},
        DATA_MODULES: {},
    }

    if DOMAIN not in config:
        return True

    config_flow.IDiamantFlowHandler.async_register_implementation(
        hass,
        config_entry_oauth2_flow.LocalOAuth2Implementation(
            hass,
            DOMAIN,
            config[DOMAIN][CONF_CLIENT_ID],
            config[DOMAIN][CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE_URL,
            OAUTH2_TOKEN_URL,
        ),
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up iDiamant from a config entry.
    """

    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )

    # Set unique id if non was set.
    if not entry.unique_id:
        hass.config_entries.async_update_entry(entry, unique_id=DOMAIN)

    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

    try:
        await session.async_ensure_token_valid()

    except aiohttp.ClientResponseError as ex:
        _LOGGER.debug("API error: %s (%s)", ex.code, ex.message)

        if ex.code in (
            HTTPStatus.BAD_REQUEST,
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.FORBIDDEN,
        ):
            raise ConfigEntryAuthFailed("Token not valid, trigger renewal") from ex

        raise ConfigEntryNotReady from ex

    if sorted(session.token["scope"]) != sorted(SCOPES):
        _LOGGER.debug("Scopes are invalids: %s != %s", session.token["scope"], SCOPES)

        raise ConfigEntryAuthFailed("Token scopes not valid, trigger renewal")

    hass.data[DOMAIN][entry.entry_id] = {
        AUTH: api.AsyncConfigEntryNetatmoAuth(
            aiohttp_client.async_get_clientsession(hass), session
        )
    }

    # data_handler = NetatmoDataHandler(hass, entry)
    # await data_handler.async_setup()
    # hass.data[DOMAIN][entry.entry_id][DATA_HANDLER] = data_handler

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)


async def async_config_entry_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """
    Handle signals of config entry being updated.
    """
    async_dispatcher_send(hass, f"signal-{DOMAIN}-public-update-{entry.entry_id}")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload a config entry.
    """
    data = hass.data[DOMAIN]

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and entry.entry_id in data:
        data.pop(entry.entry_id)

    return unload_ok
