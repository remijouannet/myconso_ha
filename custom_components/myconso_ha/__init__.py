import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from myconso.api import MyConsoClient

from .coordinator import MyConsoCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    client = MyConsoClient(
        token=config_entry.data["token"],
        refresh_token=config_entry.data["refresh_token"],
    )

    coordinator = MyConsoCoordinator(hass, config_entry, client)

    await coordinator.async_config_entry_first_refresh()

    config_entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload the config entry and platforms."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
