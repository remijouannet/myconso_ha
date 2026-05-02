"""Tests for the MyConso coordinator."""

from unittest.mock import MagicMock

import aiohttp
import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.myconso_ha.coordinator import MyConsoCoordinator
from tests.conftest import create_client_response_error


async def test_coordinator_update_success(hass, mock_myconso_client: MagicMock) -> None:
    """Test successful coordinator update produces CounterState data."""
    entry = MockConfigEntry(
        domain="myconso_ha",
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )
    coordinator = MyConsoCoordinator(hass, entry, mock_myconso_client)
    await coordinator._async_setup()

    data = await coordinator._async_update_data()

    assert len(data) == 1
    assert data[0].housing == "housing_1"
    assert data[0].counter == "counter_1"
    assert data[0].fluid_type == "heating"
    assert data[0].last_index == 1500.5  # noqa: PLR2004


async def test_coordinator_auth_failure(hass, mock_myconso_client: MagicMock) -> None:
    """Test UpdateFailed is raised on 401 during update."""
    entry = MockConfigEntry(
        domain="myconso_ha",
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )
    coordinator = MyConsoCoordinator(hass, entry, mock_myconso_client)
    await coordinator._async_setup()

    mock_myconso_client.get_meter.side_effect = create_client_response_error(401)

    with pytest.raises(UpdateFailed, match="Authentication failed"):
        await coordinator._async_update_data()


async def test_coordinator_http_error(hass, mock_myconso_client: MagicMock) -> None:
    """Test UpdateFailed is raised on generic HTTP error during update."""
    entry = MockConfigEntry(
        domain="myconso_ha",
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )
    coordinator = MyConsoCoordinator(hass, entry, mock_myconso_client)
    await coordinator._async_setup()

    mock_myconso_client.get_meter.side_effect = create_client_response_error(503)

    with pytest.raises(UpdateFailed, match="HTTP error 503"):
        await coordinator._async_update_data()


async def test_coordinator_connection_error(
    hass, mock_myconso_client: MagicMock
) -> None:
    """Test UpdateFailed is raised on aiohttp ClientError during update."""
    entry = MockConfigEntry(
        domain="myconso_ha",
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )
    coordinator = MyConsoCoordinator(hass, entry, mock_myconso_client)
    await coordinator._async_setup()

    mock_myconso_client.get_meter.side_effect = aiohttp.ClientConnectionError(
        "Connection refused"
    )

    with pytest.raises(UpdateFailed, match="Connection error"):
        await coordinator._async_update_data()


async def test_coordinator_unexpected_error(
    hass, mock_myconso_client: MagicMock
) -> None:
    """Test UpdateFailed is raised on unexpected exceptions during update."""
    entry = MockConfigEntry(
        domain="myconso_ha",
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )
    coordinator = MyConsoCoordinator(hass, entry, mock_myconso_client)
    await coordinator._async_setup()

    mock_myconso_client.get_meter.side_effect = RuntimeError("boom")

    with pytest.raises(UpdateFailed, match="Unexpected error"):
        await coordinator._async_update_data()


async def test_coordinator_setup(hass, mock_myconso_client: MagicMock) -> None:
    """Test that _async_setup populates internal state."""
    entry = MockConfigEntry(
        domain="myconso_ha",
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )
    coordinator = MyConsoCoordinator(hass, entry, mock_myconso_client)
    await coordinator._async_setup()

    assert len(coordinator.counters) == 2  # noqa: PLR2004
    assert coordinator.info_housings.totalItems == 1
    assert coordinator.counter_locations == {
        "housing_1_counter_1": "Kitchen",
        "housing_1_counter_2": "Kitchen",
    }
