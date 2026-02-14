from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
)
from myconso.api import MyConsoClient

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL, description={"suggested_value": "test"}): str,
        vol.Required(CONF_PASSWORD, description={"suggested_value": "1234"}): str,
    }
)


class MyConsoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MyConso Integration."""

    VERSION = 1
    _input_data: dict[str, Any]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                async with MyConsoClient(
                    user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                ) as c:
                    res = await c.auth()
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if "base" not in errors:
                await self.async_set_unique_id(res["user"]["userIdentifier"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=res["user"]["userIdentifier"],
                    data={
                        "token": res["token"],
                        "refresh_token": res["refresh_token"],
                        "housing": res["housing"],
                        "housings": res["user"]["housingIds"],
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
