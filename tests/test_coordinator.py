"""Tests for the MyConso coordinator."""

from unittest.mock import AsyncMock, MagicMock, create_autospec

import aiohttp
import pytest
from aiohttp import RequestInfo
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from multidict import CIMultiDict, CIMultiDictProxy
from myconso.api import MyConsoClient
from myconso.models.auth import Auth
from myconso.models.counter import Counter
from myconso.models.housings import Housings
from myconso.models.meter import Meter
from myconso.models.meter_info import MeterInfo
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    load_json_value_fixture,
)
from yarl import URL

from custom_components.myconso_ha.const import DOMAIN
from custom_components.myconso_ha.coordinator import MyConsoCoordinator


def create_client_response_error(status: int):
    """Create a ClientResponseError with the given status code."""
    req_info = RequestInfo(
        url=URL("http://test"),
        method="GET",
        headers=CIMultiDictProxy(CIMultiDict()),
        real_url=URL("http://test"),
    )
    return aiohttp.ClientResponseError(request_info=req_info, history=(), status=status)


@pytest.fixture
def mock_myconso_client_spec() -> MagicMock:
    """Return a mocked MyConsoClient with spec."""
    auth = Auth.model_validate(load_json_value_fixture("auth.json"))
    counters = Counter.model_validate(load_json_value_fixture("counters.json"))
    housings = Housings.model_validate(load_json_value_fixture("housings.json"))
    meter_info = MeterInfo.model_validate(load_json_value_fixture("meter_info.json"))
    meter = Meter.model_validate(load_json_value_fixture("meter.json"))

    client = create_autospec(MyConsoClient)
    client.token = auth.token
    client.refresh_token = auth.refresh_token
    client.housings = auth.user.housingIds

    client.auth = AsyncMock(return_value=auth)
    client.auth_refresh = AsyncMock(return_value=auth)
    client.get_counters = AsyncMock(return_value=counters)
    client.get_housings = AsyncMock(return_value=housings)
    client.get_meter_info = AsyncMock(return_value=meter_info)
    client.get_meter = AsyncMock(return_value=meter)

    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    return client


async def test_coordinator_update_success(
    hass: HomeAssistant, mock_myconso_client_spec: MagicMock
) -> None:
    """Test successful coordinator update produces CounterState data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )
    coordinator = MyConsoCoordinator(hass, entry, mock_myconso_client_spec)
    await coordinator._async_setup()

    data = await coordinator._async_update_data()

    assert len(data) == 1
    assert data[0].housing == "housing_1"
    assert data[0].counter == "counter_1"
    assert data[0].fluid_type == "heating"
    assert data[0].last_index == 1500.5  # noqa: PLR2004


async def test_coordinator_auth_failure(
    hass: HomeAssistant, mock_myconso_client_spec: MagicMock
) -> None:
    """Test ConfigEntryAuthFailed is raised on 401 during update."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )
    coordinator = MyConsoCoordinator(hass, entry, mock_myconso_client_spec)
    await coordinator._async_setup()

    mock_myconso_client_spec.get_meter.side_effect = create_client_response_error(401)

    with pytest.raises(ConfigEntryAuthFailed, match="Authentication failed"):
        await coordinator._async_update_data()


async def test_coordinator_http_error(
    hass: HomeAssistant, mock_myconso_client_spec: MagicMock
) -> None:
    """Test UpdateFailed is raised on generic HTTP error during update."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )
    coordinator = MyConsoCoordinator(hass, entry, mock_myconso_client_spec)
    await coordinator._async_setup()

    mock_myconso_client_spec.get_meter.side_effect = create_client_response_error(503)

    with pytest.raises(UpdateFailed, match="HTTP error 503"):
        await coordinator._async_update_data()


async def test_coordinator_connection_error(
    hass: HomeAssistant, mock_myconso_client_spec: MagicMock
) -> None:
    """Test UpdateFailed is raised on aiohttp ClientError during update."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )
    coordinator = MyConsoCoordinator(hass, entry, mock_myconso_client_spec)
    await coordinator._async_setup()

    mock_myconso_client_spec.get_meter.side_effect = aiohttp.ClientConnectionError(
        "Connection refused"
    )

    with pytest.raises(UpdateFailed, match="Connection error"):
        await coordinator._async_update_data()


async def test_coordinator_unexpected_error(
    hass: HomeAssistant, mock_myconso_client_spec: MagicMock
) -> None:
    """Test UpdateFailed is raised on unexpected exceptions during update."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )
    coordinator = MyConsoCoordinator(hass, entry, mock_myconso_client_spec)
    await coordinator._async_setup()

    mock_myconso_client_spec.get_meter.side_effect = RuntimeError("boom")

    with pytest.raises(UpdateFailed, match="Unexpected error"):
        await coordinator._async_update_data()


async def test_coordinator_setup(
    hass: HomeAssistant, mock_myconso_client_spec: MagicMock
) -> None:
    """Test that _async_setup populates internal state."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )
    coordinator = MyConsoCoordinator(hass, entry, mock_myconso_client_spec)
    await coordinator._async_setup()

    assert len(coordinator.counters) == 2  # noqa: PLR2004
    assert coordinator.info_housings.totalItems == 1
    assert coordinator.counter_locations == {
        "housing_1": {
            "counter_1": "Kitchen",
            "counter_2": "Kitchen",
        }
    }
