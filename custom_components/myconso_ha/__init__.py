import logging

from homeassistant.const import Platform

from .coordinator import MyConsoCoordinator
from myconso.api import MyConsoClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass, config_entry):
    _LOGGER.info("async_setup_entry api loaded")
    client = MyConsoClient(
        token=config_entry.data["token"],
        refresh_token=config_entry.data["refresh_token"],
    )

    coordinator = MyConsoCoordinator(hass, config_entry, client)

    await coordinator.async_config_entry_first_refresh()

    config_entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True
