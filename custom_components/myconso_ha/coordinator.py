from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type MyConsoConfigEntry = ConfigEntry[MyConsoCoordinator]


class MyConsoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    config_entry: MyConsoConfigEntry
    housings: list[dict]
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
        self.housings = config_entry.data["housings"]

    async def _async_setup(self) -> None:
        self.counters = await self.client.get_counters()
        self.info_housings = await self.client.get_housings()

        for c in self.counters:
            meter_info = await self.client.get_meter_info(c["counter"], c["housing"])
            if meter_info:
                c.update({"location": meter_info["location"]})
        _LOGGER.debug("MyConsoCoordinator setup %s", self.counters)

    async def _async_update_data(self):
        data = []
        yesterday = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=1)
        for c in self.counters:
            indexes = await self.client.get_meter(
                counter=c["counter"],
                housing=c["housing"],
                startdate=yesterday,
                enddate=datetime.now(UTC),
            )
            filtered = [
                idx for idx in indexes["indexes"] if idx["fluidType"] == c["fluidType"]
            ]
            last_index = max(filtered, key=lambda x: x["date"])
            data.append({**c, "last_index": last_index["value"]})
        _LOGGER.debug("MyConsoCoordinator Update data %s ", data)

        await self.client.auth_refresh()

        if self.client.token != self.config_entry.data["token"]:
            _LOGGER.debug("Refresh token in config entries")
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={
                    "token": self.client.token,
                    "refresh_token": self.client.refresh_token,
                    "housings": self.client.housings,
                },
            )
        return data
