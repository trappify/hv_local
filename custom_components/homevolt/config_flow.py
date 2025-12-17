"""Config flow for Homevolt."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HomevoltAuthError, HomevoltClient, HomevoltConnectionError
from .const import (
    CONF_FULL_CAPACITY_SOC_THRESHOLD,
    CONF_USE_HTTPS,
    DEFAULT_FULL_CAPACITY_SOC_THRESHOLD,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USE_HTTPS,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)


async def _validate_connection(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Attempt to reach the Homevolt device with the provided credentials."""
    session = async_get_clientsession(hass, verify_ssl=data[CONF_VERIFY_SSL])
    client = HomevoltClient(
        session=session,
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        username=data[CONF_USERNAME],
        password=data.get(CONF_PASSWORD, ""),
        use_https=data[CONF_USE_HTTPS],
        verify_ssl=data[CONF_VERIFY_SSL],
    )
    payload = await client.async_get_payload()
    device_name = payload.status.get("device_name") or payload.status.get("hostname")
    unique_id = f"{data[CONF_HOST]}:{data[CONF_PORT]}"
    return {
        "title": device_name or f"Homevolt {data[CONF_HOST]}",
        "unique_id": unique_id,
    }


class HomevoltConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Homevolt."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                validated = await _validate_connection(self.hass, user_input)
            except HomevoltAuthError:
                errors["base"] = "invalid_auth"
            except HomevoltConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pragma: no cover - defensive
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(validated["unique_id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=validated["title"], data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): str,
                vol.Required(
                    CONF_PORT,
                    default=(user_input or {}).get(CONF_PORT, DEFAULT_PORT),
                ): vol.All(int, vol.Range(min=1, max=65535)),
                vol.Required(
                    CONF_USERNAME,
                    default=(user_input or {}).get(CONF_USERNAME, "admin"),
                ): str,
                vol.Optional(CONF_PASSWORD, default=(user_input or {}).get(CONF_PASSWORD, "")): str,
                vol.Required(
                    CONF_USE_HTTPS,
                    default=(user_input or {}).get(CONF_USE_HTTPS, DEFAULT_USE_HTTPS),
                ): bool,
                vol.Required(
                    CONF_VERIFY_SSL,
                    default=(user_input or {}).get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Return the options flow handler."""
        return HomevoltOptionsFlowHandler(config_entry)


class HomevoltOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Homevolt options."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.config_entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            CONF_SCAN_INTERVAL: self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            CONF_VERIFY_SSL: self.config_entry.options.get(
                CONF_VERIFY_SSL, self.config_entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
            ),
            CONF_FULL_CAPACITY_SOC_THRESHOLD: self.config_entry.options.get(
                CONF_FULL_CAPACITY_SOC_THRESHOLD,
                DEFAULT_FULL_CAPACITY_SOC_THRESHOLD,
            ),
        }

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=options[CONF_SCAN_INTERVAL],
                ): vol.All(int, vol.Range(min=15, max=900)),
                vol.Required(
                    CONF_VERIFY_SSL,
                    default=options[CONF_VERIFY_SSL],
                ): bool,
                vol.Required(
                    CONF_FULL_CAPACITY_SOC_THRESHOLD,
                    default=options[CONF_FULL_CAPACITY_SOC_THRESHOLD],
                ): vol.All(vol.Coerce(float), vol.Range(min=50.0, max=100.0)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
