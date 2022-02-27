"""
Config flow for iDiamant.
"""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow

from .const import (
    DOMAIN,
    SCOPES,
)


class IDiamantFlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """
    Config flow to handle Netatmo Connect API OAuth2 authentication.
    """

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """
        Return the logger.
        """

        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> dict:
        """
        Extra data that needs to be appended to the authorize url.
        """

        return {"scope": " ".join(SCOPES)}

    async def async_step_user(self, user_input: dict = None) -> FlowResult:
        """
        Handle a flow start.
        """

        await self.async_set_unique_id(DOMAIN)

        if (
            self.source != config_entries.SOURCE_REAUTH
            and self._async_current_entries()
        ):
            return self.async_abort(reason="single_instance_allowed")

        return await super().async_step_user(user_input)

    async def async_step_reauth(self) -> FlowResult:
        """
        Perform reauth upon an API authentication error.
        """

        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict = None) -> FlowResult:
        """
        Dialog that informs the user that reauth is required.
        """

        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
            )

        return await self.async_step_user()

    async def async_oauth_create_entry(self, data: dict) -> FlowResult:
        """
        Create an oauth config entry or update existing entry for reauth.
        """

        existing_entry = await self.async_set_unique_id(DOMAIN)
        if existing_entry:
            self.hass.config_entries.async_update_entry(existing_entry, data=data)
            await self.hass.config_entries.async_reload(existing_entry.entry_id)

            return self.async_abort(reason="reauth_successful")

        return await super().async_oauth_create_entry(data)
