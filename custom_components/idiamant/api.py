"""
API for iDiamant bound to HASS OAuth.
"""

import asyncio
import logging
import socket
from json import JSONDecodeError
from typing import cast

from aiohttp import ClientError, ClientSession

from homeassistant.helpers import config_entry_oauth2_flow

from .const import (
    AUTHORIZATION_HEADER,
    AUTHORIZATION_HEADER_BEARER,
    BASE_API_URL,
    DEFAULT_HEADERS,
    TIMEOUT,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class ApiError(Exception):
    """
    Class used when an API error occurred.
    """


def get_url(path: str) -> str:
    """
    Get the full Netatmo Connect API URL for the given path.

    Args:
        path (str): The path to append to the base URL (should start with a '/').

    Returns:
        str: The full Netatmo Connect API URL.
    """

    return BASE_API_URL + path


class AsyncConfigEntryNetatmoAuth:
    """
    Provide Netatmo Connect API authentication tied to an OAuth2 based config entry.
    """

    def __init__(
        self,
        websession: ClientSession,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ) -> None:
        """
        Initialize the authentication.
        """

        self.websession = websession
        self._oauth_session = oauth_session

    async def async_get_access_token(self) -> str:
        """
        Return a valid access token for Netatmo Connect API.
        """

        if not self._oauth_session.valid_token:
            await self._oauth_session.async_ensure_token_valid()

        return cast(str, self._oauth_session.token["access_token"])

    async def async_request(
        self,
        method: str,
        path: str,
        body: dict = None,
        headers: dict = None,
        timeout: int = TIMEOUT,
    ) -> dict:
        """
        Construct an API call to Netatmo Connect API.
        If any error occurs, it will be logged.

        Args:
            method (str): The method to use to call the endpoint: 'GET', 'POST', 'PATCH', 'PUT' or
                          'DELETE'.
            path (str): The path of the endpoint to call (should start with a '/').
            body (dict, optional): The data to send to the endpoint.
                                   Defaults to {}.
            headers (dict, optional): The headers of the call to the endpoint. Those will be added
                                      (or will overwrite) default header.
                                      Defaults to {}.

        Returns:
            dict: The data returned by the endpoint (if any).
        """

        try:
            access_token = await self.async_get_access_token()
        except ClientError as err:
            raise ApiError(f"Access token failure: {err}") from err

        method_to_use = method.upper()
        headers_to_use = {
            **DEFAULT_HEADERS,
            **headers,
            AUTHORIZATION_HEADER: f"{AUTHORIZATION_HEADER_BEARER} {access_token}",
        }

        url = get_url(path)

        try:
            response = None

            if method_to_use == "GET":
                response = await self.websession.get(
                    url, headers=headers_to_use, timeout=timeout
                )

            elif method_to_use == "PUT":
                response = await self.websession.put(
                    url, headers=headers_to_use, json=body, timeout=timeout
                )

            elif method_to_use == "PATCH":
                response = await self.websession.patch(
                    url, headers=headers_to_use, json=body, timeout=timeout
                )

            elif method_to_use == "POST":
                response = await self.websession.post(
                    url, headers=headers_to_use, json=body, timeout=timeout
                )

            if response is not None:
                if not response.ok:
                    _LOGGER.error("Error while calling %s: %s", path, response.status)
                    try:
                        decoded_response = await response.json()
                        raise ApiError(
                            f"{response.status} - "
                            f"{decoded_response['error']['message']} "
                            f"({decoded_response['error']['code']}) "
                            f"when accessing '{url}'",
                        )

                    except JSONDecodeError as exc:
                        raise ApiError(
                            f"{response.status} - " f"when accessing '{url}'",
                        ) from exc

                return await response.json()

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                path,
                exception,
            )

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                path,
                exception,
            )

        except (ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                path,
                exception,
            )

        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! %s", exception)

        return None
