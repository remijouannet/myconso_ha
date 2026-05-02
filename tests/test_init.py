"""Tests for the MyConso integration initialization."""

from unittest.mock import MagicMock

import aiohttp
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.myconso_ha.const import DOMAIN
from tests import init_integration
from tests.conftest import create_client_response_error


async def test_setup_entry(hass: HomeAssistant, mock_myconso_client: MagicMock) -> None:
    """Test successful setup of a config entry."""
    entry = await init_integration(hass)

    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data is not None
    assert entry.runtime_data.client is mock_myconso_client


async def test_setup_entry_auth_failed(
    hass: HomeAssistant, mock_myconso_client: MagicMock
) -> None:
    """Test setup aborts with ConfigEntryAuthFailed on 401."""
    mock_myconso_client.get_housings.side_effect = create_client_response_error(401)

    entry = MockConfigEntry(
        domain=DOMAIN,
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

    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_setup_entry_not_ready(
    hass: HomeAssistant, mock_myconso_client: MagicMock
) -> None:
    """Test setup retries with ConfigEntryNotReady on connection error."""

    mock_myconso_client.get_housings.side_effect = aiohttp.ClientConnectionError(
        "Connection refused"
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
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

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_entry_unexpected_error(
    hass: HomeAssistant, mock_myconso_client: MagicMock
) -> None:
    """Test setup retries with ConfigEntryNotReady on unexpected error."""
    mock_myconso_client.get_housings.side_effect = RuntimeError("boom")

    entry = MockConfigEntry(
        domain=DOMAIN,
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

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant, mock_myconso_client: MagicMock
) -> None:
    """Test unloading a config entry."""
    entry = await init_integration(hass)

    assert entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
