"""
The iDiamant data handler.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
import logging
from time import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from . import api, SCAN_INTERVAL
from .const import (
    AUTH,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


# GATEWAY_DATA_CLASS_NAME = "AsyncGatewayData"
SHUTTER_DATA_CLASS_NAME = "AsyncShutterData"

DATA_CLASSES = {
    # GATEWAY_DATA_CLASS_NAME: None,
    SHUTTER_DATA_CLASS_NAME: None,
}

DEFAULT_INTERVALS = {
    # GATEWAY_DATA_CLASS_NAME: 600,
    SHUTTER_DATA_CLASS_NAME: 60,
}


@dataclass
class IDiamantDevice:
    """
    iDiamant device class.
    """

    data_handler: IDiamantDataHandler
    parent_id: str
    state_class_name: str


@dataclass
class IDiamantDataClass:
    """
    Class for keeping track of iDiamant data class metadata.
    """

    name: str
    interval: int
    next_scan: float
    subscriptions: list[CALLBACK_TYPE | None]


class IDiamantDataHandler:
    """
    Manages the iDiamant data handling.
    """

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self.hass = hass
        self.config_entry = config_entry
        self._auth = hass.data[DOMAIN][config_entry.entry_id][AUTH]
        self.data_classes: dict = {}
        self.data: dict = {}
        self._queue: deque = deque()

    async def async_setup(self) -> None:
        """
        Set up the iDiamant data handler.
        """

        async_track_time_interval(self.hass, self.async_update, SCAN_INTERVAL)

        await asyncio.gather(
            *[
                self.register_data_class(data_class, data_class, None)
                for data_class in (
                    GATEWAY_DATA_CLASS_NAME,
                    SHUTTER_DATA_CLASS_NAME,
                )
            ]
        )

    async def async_update(self) -> None:
        """
        Update device.
        """

        for data_class in self._queue:
            if data_class.next_scan > time():
                continue

            if data_class_name := data_class.name:
                self.data_classes[data_class_name].next_scan = (
                    time() + data_class.interval
                )

                await self.async_fetch_data(data_class_name)

        self._queue.rotate(1)

    @callback
    def async_force_update(self, data_class_entry: str) -> None:
        """
        Prioritize data retrieval for given data class entry.
        """

        self.data_classes[data_class_entry].next_scan = time()
        self._queue.rotate(-(self._queue.index(self.data_classes[data_class_entry])))

    async def async_fetch_data(self, data_class_entry: str) -> None:
        """
        Fetch data and notify.
        """

        if self.data[data_class_entry] is None:
            return

        try:
            await self.data[data_class_entry].async_update()

        except api.ApiError as err:
            _LOGGER.debug(err)

        except asyncio.TimeoutError as err:
            _LOGGER.debug(err)

            return

        for update_callback in self.data_classes[data_class_entry].subscriptions:
            if update_callback:
                update_callback()

    async def register_data_class(
        self,
        data_class_name: str,
        data_class_entry: str,
        update_callback: CALLBACK_TYPE | None,
        **kwargs: Any,
    ) -> None:
        """
        Register data class.
        """

        if data_class_entry in self.data_classes:
            if update_callback not in self.data_classes[data_class_entry].subscriptions:
                self.data_classes[data_class_entry].subscriptions.append(
                    update_callback
                )

            return

        self.data_classes[data_class_entry] = IDiamantDataClass(
            name=data_class_entry,
            interval=DEFAULT_INTERVALS[data_class_name],
            next_scan=time() + DEFAULT_INTERVALS[data_class_name],
            subscriptions=[update_callback],
        )

        self.data[data_class_entry] = DATA_CLASSES[data_class_name](
            self._auth, **kwargs
        )

        try:
            await self.async_fetch_data(data_class_entry)

        except KeyError:
            self.data_classes.pop(data_class_entry)

            raise

        self._queue.append(self.data_classes[data_class_entry])

        _LOGGER.debug("Data class %s added", data_class_entry)

    async def unregister_data_class(
        self, data_class_entry: str, update_callback: CALLBACK_TYPE | None
    ) -> None:
        """
        Unregister data class.
        """

        self.data_classes[data_class_entry].subscriptions.remove(update_callback)

        if not self.data_classes[data_class_entry].subscriptions:
            self._queue.remove(self.data_classes[data_class_entry])
            self.data_classes.pop(data_class_entry)
            self.data.pop(data_class_entry)

            _LOGGER.debug("Data class %s removed", data_class_entry)
