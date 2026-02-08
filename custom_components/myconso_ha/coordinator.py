from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

type MyConsoConfigEntry = ConfigEntry[MyConsoCoordinator]

UPDATE_INTERVAL = timedelta(minutes=30)

class MyConsoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    config_entry: MyConsoConfigEntry
    housing: str
    counters: list[dict]

    def __init__(self, hass, config_entry, client) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self.housing = config_entry.data["housing"]

    async def _async_setup(self) -> None:
        self.counters = await self.client.get_counters()
        self.info_housing = await self.client.get_housing()

        for c in self.counters:
            meter_info = await self.client.get_meter_info(c['counter'])
            if meter_info:
                c.update({"location": meter_info["location"]})
        _LOGGER.debug("_async_setup %s", self.counters)

    async def _async_update_data(self):
        _LOGGER.debug("_async_update_data 1 %s", self.counters)
        data = []
        for counter in self.counters:
            indexes = await self.client.get_meter(counter["counter"])
            filtered = [idx for idx in indexes['indexes'] if idx["fluidType"] == counter["fluidType"]]
            last_index = max(filtered, key=lambda x: x["date"])
            data.append({**counter, "last_index": last_index["value"]})
        _LOGGER.debug("_async_update_data 2 %s ", data)

        await self.client.auth_refresh()

        if self.client.token != self.config_entry.data['token']:
            _LOGGER.debug("_async_update_data 3 update token")
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={
                    'token': self.client.token,
                    'refresh_token': self.client.refresh_token,
                    'housing': self.client._housing,
                },
            )
        return data
