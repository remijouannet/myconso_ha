"""Test fixtures for myconso_ha."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

import pytest
from homeassistant.core import HomeAssistant
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

from custom_components.myconso_ha.const import DOMAIN

ENTRY_ID = "abc123_entry"


@pytest.fixture
def mock_myconso_client() -> Generator[MagicMock]:
    """Return a mocked MyConsoClient."""
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

    # Support async context manager usage in config_flow
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("custom_components.myconso_ha.MyConsoClient", return_value=client),
        patch(
            "custom_components.myconso_ha.config_flow.MyConsoClient",
            return_value=client,
        ),
    ):
        yield client


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="abc123",
        entry_id=ENTRY_ID,
        unique_id="abc123",
        data={
            "token": "test_token",
            "refresh_token": "test_refresh_token",
            "housings": ["housing_1"],
        },
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_myconso_client: MagicMock,
) -> MockConfigEntry:
    """Set up the myconso_ha integration in Home Assistant."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield
