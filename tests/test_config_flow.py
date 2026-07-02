"""Define tests for the MyConso config flow."""

from unittest.mock import MagicMock

from aiohttp import ClientResponseError, RequestInfo
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from multidict import CIMultiDict, CIMultiDictProxy
from pytest_homeassistant_custom_component.common import MockConfigEntry
from yarl import URL

from custom_components.myconso_ha.const import DOMAIN

CONFIG = {
    CONF_EMAIL: "test@test.com",
    CONF_PASSWORD: "secret",
}


def create_client_response_error(status: int):
    """Create a ClientResponseError with the given status code."""
    req_info = RequestInfo(
        url=URL("http://test"),
        method="GET",
        headers=CIMultiDictProxy(CIMultiDict()),
        real_url=URL("http://test"),
    )
    return ClientResponseError(request_info=req_info, history=(), status=status)


async def test_show_form(hass: HomeAssistant) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_create_entry(
    hass: HomeAssistant, mock_myconso_client: MagicMock
) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "abc123"
    assert result["data"]["token"] == "test_token"
    assert result["data"]["refresh_token"] == "test_refresh_token"
    assert result["data"]["housings"] == ["housing_1"]


async def test_invalid_auth(
    hass: HomeAssistant, mock_myconso_client: MagicMock
) -> None:
    """Test that errors are shown when authentication is invalid."""
    mock_myconso_client.auth.side_effect = create_client_response_error(401)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    assert result["errors"] == {"base": "invalid_auth"}


async def test_http_error(hass: HomeAssistant, mock_myconso_client: MagicMock) -> None:
    """Test that errors are shown for generic HTTP errors."""
    mock_myconso_client.auth.side_effect = create_client_response_error(500)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    assert result["errors"] == {"base": "http_error"}


async def test_unknown_error(
    hass: HomeAssistant, mock_myconso_client: MagicMock
) -> None:
    """Test that errors are shown for unexpected exceptions."""
    mock_myconso_client.auth.side_effect = RuntimeError("boom")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    assert result["errors"] == {"base": "unknown"}


async def test_duplicate_error(
    hass: HomeAssistant, mock_myconso_client: MagicMock
) -> None:
    """Test that duplicates are aborted."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="abc123",
        data={
            "token": "existing_token",
            "refresh_token": "existing_refresh",
            "housings": ["housing_1"],
        },
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth_success(
    hass: HomeAssistant, mock_myconso_client: MagicMock
) -> None:
    """Test reauthentication updates the existing entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="abc123",
        data={
            "token": "old_token",
            "refresh_token": "old_refresh",
            "housings": ["housing_1"],
        },
    )
    entry.add_to_hass(hass)
    hass.config.components.add(DOMAIN)

    entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONFIG
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    await hass.async_block_till_done()
    assert entry.data["token"] == "test_token"
    assert entry.data["refresh_token"] == "test_refresh_token"


async def test_reauth_invalid_auth(
    hass: HomeAssistant, mock_myconso_client: MagicMock
) -> None:
    """Test reauthentication with invalid credentials."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="abc123",
        data={
            "token": "old_token",
            "refresh_token": "old_refresh",
            "housings": ["housing_1"],
        },
    )
    entry.add_to_hass(hass)
    hass.config.components.add(DOMAIN)

    entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]

    mock_myconso_client.auth.side_effect = create_client_response_error(401)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONFIG
    )

    assert result["errors"] == {"base": "invalid_auth"}
