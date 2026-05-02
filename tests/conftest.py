"""Test fixtures for myconso_ha."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import RequestInfo
from multidict import CIMultiDict, CIMultiDictProxy
from myconso.models.auth import Auth
from myconso.models.counter import Counter
from myconso.models.housings import Housings
from myconso.models.meter import Meter
from myconso.models.meter_info import MeterInfo
from pytest_homeassistant_custom_component.common import (
    load_json_value_fixture,
)
from yarl import URL


def create_client_response_error(status: int) -> aiohttp.ClientResponseError:
    """Create a ClientResponseError with the given status code."""
    req_info = RequestInfo(
        url=URL("http://test"),
        method="GET",
        headers=CIMultiDictProxy(CIMultiDict()),
        real_url=URL("http://test"),
    )
    return aiohttp.ClientResponseError(request_info=req_info, history=(), status=status)


@pytest.fixture
def mock_myconso_client() -> Generator[MagicMock]:
    """Return a mocked MyConsoClient."""
    auth = Auth.model_validate(load_json_value_fixture("auth.json"))
    counters = Counter.model_validate(load_json_value_fixture("counters.json"))
    housings = Housings.model_validate(load_json_value_fixture("housings.json"))
    meter_info = MeterInfo.model_validate(load_json_value_fixture("meter_info.json"))
    meter = Meter.model_validate(load_json_value_fixture("meter.json"))

    client = MagicMock()
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


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield
