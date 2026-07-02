"""Tests for the MyConso integration initialization."""

from unittest.mock import MagicMock

import aiohttp
from aiohttp import ClientResponseError, RequestInfo
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from multidict import CIMultiDict, CIMultiDictProxy
from pytest_homeassistant_custom_component.common import MockConfigEntry
from yarl import URL

from custom_components.myconso_ha.const import DOMAIN


def create_client_response_error(status: int):
    """Create a ClientResponseError with the given status code."""
    req_info = RequestInfo(
        url=URL("http://test"),
        method="GET",
        headers=CIMultiDictProxy(CIMultiDict()),
        real_url=URL("http://test"),
    )
    return ClientResponseError(request_info=req_info, history=(), status=status)


async def test_setup_entry(
    init_integration: MockConfigEntry, mock_myconso_client: MagicMock
) -> None:
    """Test successful setup of a config entry."""
    entry = init_integration

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
    assert await hass.config_entries.async_setup(entry.entry_id) is False
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
    assert await hass.config_entries.async_setup(entry.entry_id) is False
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
    assert await hass.config_entries.async_setup(entry.entry_id) is False
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Test unloading a config entry."""
    entry = init_integration

    assert entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
