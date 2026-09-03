"""Config flow for Mailcow."""

from __future__ import annotations

import ipaddress
from typing import Any
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    MailcowAccessBlockedError,
    MailcowApi,
    MailcowAuthError,
    MailcowConnectionError,
    MailcowError,
)
from .const import CONF_API_KEY, CONF_ORIGIN_IP, CONF_URL, DOMAIN


class MailcowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mailcow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._pending: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Try normal Mailcow connectivity first."""
        errors: dict[str, str] = {}

        if user_input is not None:
            entered_url = user_input[CONF_URL].strip()
            api_key = user_input[CONF_API_KEY].strip()
            url = _normalise_url(entered_url)

            if not _valid_url(url):
                errors["base"] = "invalid_url"
            else:
                api = MailcowApi(
                    url=url,
                    api_key=api_key,
                    shared_session=async_get_clientsession(self.hass),
                )
                try:
                    await api.async_test_connection()
                except (
                    MailcowAuthError,
                    MailcowAccessBlockedError,
                    MailcowConnectionError,
                    MailcowError,
                ):
                    # A response through a CDN/reverse proxy cannot reliably tell us
                    # whether Mailcow itself rejected the key. Ask about proxying
                    # before presenting an authentication error.
                    self._pending = {
                        CONF_URL: url,
                        CONF_API_KEY: api_key,
                    }
                    return await self.async_step_proxy()
                else:
                    return await self._create_entry(url, api_key)

        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default="https://"): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                ),
                vol.Required(CONF_API_KEY): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.PASSWORD
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_proxy(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask how to proceed after the normal connection failed."""
        if not self._pending:
            return self.async_abort(reason="missing_connection_data")

        # A menu avoids exposing an internal field name such as "behind_proxy".
        return self.async_show_menu(
            step_id="proxy",
            menu_options=["origin", "connection_failed"],
            description_placeholders={"url": self._pending[CONF_URL]},
        )

    async def async_step_connection_failed(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Explain likely causes when no proxy/CDN is involved."""
        if not self._pending:
            return self.async_abort(reason="missing_connection_data")

        if user_input is not None:
            # The empty confirmation form acts as "Try again".
            return await self.async_step_user()

        return self.async_show_form(
            step_id="connection_failed",
            data_schema=vol.Schema({}),
            errors={"base": "connection_or_auth_failed"},
        )

    async def async_step_origin(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a direct Mailcow server IP."""
        if not self._pending:
            return self.async_abort(reason="missing_connection_data")

        errors: dict[str, str] = {}

        if user_input is not None:
            origin_ip = user_input[CONF_ORIGIN_IP].strip()

            try:
                ipaddress.ip_address(origin_ip)
            except ValueError:
                errors["base"] = "invalid_ip"
            else:
                api = MailcowApi(
                    url=self._pending[CONF_URL],
                    api_key=self._pending[CONF_API_KEY],
                    origin_ip=origin_ip,
                )
                try:
                    await api.async_test_connection()
                except MailcowAuthError:
                    # At this point we are talking directly to the configured
                    # Mailcow server, so a 401 can be reported as an API key error.
                    errors["base"] = "invalid_auth"
                except (
                    MailcowAccessBlockedError,
                    MailcowConnectionError,
                    MailcowError,
                ):
                    errors["base"] = "cannot_connect_origin"
                else:
                    return await self._create_entry(
                        self._pending[CONF_URL],
                        self._pending[CONF_API_KEY],
                        origin_ip,
                    )
                finally:
                    await api.async_close()

        schema = vol.Schema(
            {
                vol.Required(CONF_ORIGIN_IP): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="origin",
            data_schema=schema,
            errors=errors,
            description_placeholders={"url": self._pending[CONF_URL]},
        )

    async def _create_entry(
        self, url: str, api_key: str, origin_ip: str | None = None
    ) -> FlowResult:
        """Create a Mailcow config entry."""
        hostname = urlparse(url).hostname or url
        await self.async_set_unique_id(hostname.lower())
        self._abort_if_unique_id_configured()

        data = {
            CONF_URL: url,
            CONF_API_KEY: api_key,
        }
        if origin_ip:
            data[CONF_ORIGIN_IP] = origin_ip

        return self.async_create_entry(
            title="Mailcow",
            data=data,
        )


def _normalise_url(value: str) -> str:
    """Normalize the Mailcow address entered in the UI."""
    value = value.strip().rstrip("/")
    if value.startswith(("https://", "http://")):
        return value
    return f"https://{value}"


def _valid_url(value: str) -> bool:
    """Return whether value is a usable HTTP(S) URL."""
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.hostname)
