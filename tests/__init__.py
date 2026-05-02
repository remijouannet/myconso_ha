"""Tests for the myconso_ha integration."""

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def init_integration(hass: HomeAssistant) -> MockConfigEntry:
    """Set up the myconso_ha integration in Home Assistant."""
    entry = MockConfigEntry(
        domain="myconso_ha",
        title="abc123",
        entry_id="abc123_entry",
        unique_id="abc123",
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
