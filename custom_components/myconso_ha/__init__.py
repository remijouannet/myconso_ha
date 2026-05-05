import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from myconso.api import MyConsoClient

from .coordinator import MyConsoCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the MyConso integration from a configuration entry."""
    client = MyConsoClient(
        token=config_entry.data["token"],
        refresh_token=config_entry.data["refresh_token"],
    )

    # Validate credentials before setting up platforms
    try:
        await client.get_housings()
    except aiohttp.ClientResponseError as exc:
        if exc.status == aiohttp.web.HTTPUnauthorized.status_code:
            raise ConfigEntryAuthFailed from exc
        raise ConfigEntryNotReady from exc
    except aiohttp.ClientError as exc:
        raise ConfigEntryNotReady from exc
    except Exception as exc:
        _LOGGER.exception("Unexpected exception during setup")
        raise ConfigEntryNotReady from exc

    coordinator = MyConsoCoordinator(hass, config_entry, client)

    await coordinator.async_config_entry_first_refresh()

    config_entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a MyConso configuration entry and clean up resources."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
