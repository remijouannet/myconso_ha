from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import override

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from myconso.api import MyConsoClient
from myconso.models import Housings
from myconso.models.counter import CounterItem

from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type MyConsoConfigEntry = ConfigEntry[MyConsoCoordinator]


@dataclass
class CounterState:
    """Represents counter state with housing, counter ID, fluid type, and last index."""

    housing: str
    counter: str
    fluid_type: str
    last_index: float


class MyConsoCoordinator(DataUpdateCoordinator[list[CounterState]]):
    """Coordinates data updates from the MyConso API and manages counter state."""

    config_entry: MyConsoConfigEntry
    housings: list[str]
    counters: list[CounterItem]
    info_housings: Housings
    counter_locations: dict[str, dict[str, str | None]]

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, client: MyConsoClient
    ) -> None:
        """Initialize coordinator with HA instance, config entry, and MyConso client."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client: MyConsoClient = client
        self.housings = config_entry.data["housings"]
        self._unavailable_logged: bool = False

    @override
    async def _async_setup(self) -> None:
        """Set up initial data structures and fetch metadata from MyConso."""
        self.counters = (await self.client.get_counters()).root
        self.info_housings = await self.client.get_housings()

        self.counter_locations = {}
        for c in self.counters:
            meter_info = await self.client.get_meter_info(c.counter, c.housing)
            if meter_info:
                if c.housing not in self.counter_locations:
                    self.counter_locations[c.housing] = {}
                self.counter_locations[c.housing][c.counter] = meter_info.location
        _LOGGER.debug("MyConsoCoordinator setup %s", self.counters)

    @override
    async def _async_update_data(self) -> list[CounterState]:
        """Fetch latest counter data from MyConso API and handle errors."""
        try:
            data = await self._fetch_data()
        except aiohttp.ClientResponseError as exc:
            if exc.status == HTTPStatus.UNAUTHORIZED.value:
                raise ConfigEntryAuthFailed("Authentication failed") from exc
            raise UpdateFailed(f"HTTP error {exc.status}") from exc
        except aiohttp.ClientError as exc:
            raise UpdateFailed(f"Connection error: {exc}") from exc
        except Exception as exc:
            _LOGGER.exception("Unexpected exception during update")
            raise UpdateFailed(f"Unexpected error: {exc}") from exc

        # Log once when back online
        if self._unavailable_logged:
            _LOGGER.info("MyConso is back online")
            self._unavailable_logged = False

        if self.client.token != self.config_entry.data["token"]:
            _LOGGER.debug("Refresh token in config entries")
            self.hass.config_entries.async_update_entry(
                entry=self.config_entry,
                data={
                    "token": self.client.token,
                    "refresh_token": self.client.refresh_token,
                    "housings": self.client.housings,
                },
            )
        return data

    async def _fetch_data(self) -> list[CounterState]:
        """Retrieve counter readings for the last 7 days from MyConso API."""
        data: list[CounterState] = []
        last_7_days = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=7)
        now = datetime.now(UTC)
        for c in self.counters:
            meter = await self.client.get_meter(
                counter=c.counter,
                housing=c.housing,
                startdate=last_7_days,
                enddate=now,
            )
            if meter is None:
                continue
            filtered = [idx for idx in meter.indexes if idx.fluidType == c.fluidType]
            if filtered:
                last_index = max(filtered, key=lambda x: x.date)
                data.append(
                    CounterState(
                        housing=c.housing,
                        counter=c.counter,
                        fluid_type=c.fluidType,
                        last_index=last_index.value,
                    )
                )
        _LOGGER.debug("MyConsoCoordinator Update data %s ", data)
        return data
