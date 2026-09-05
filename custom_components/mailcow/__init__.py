"""Mailcow Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MailcowApi
from .const import CONF_API_KEY, CONF_ORIGIN_IP, CONF_URL, DOMAIN, PLATFORMS
from .coordinator import MailcowCertificateCoordinator, MailcowOperationalCoordinator
from .history import MailcowQuarantineHistory


@dataclass
class MailcowRuntimeData:
    """Runtime data for a Mailcow config entry."""

    api: MailcowApi
    history: MailcowQuarantineHistory
    operational_coordinator: MailcowOperationalCoordinator
    certificate_coordinator: MailcowCertificateCoordinator


type MailcowConfigEntry = ConfigEntry[MailcowRuntimeData]

SERVICE_SCHEMA = vol.Schema({vol.Required("item_id"): cv.string})


async def async_setup_entry(hass: HomeAssistant, entry: MailcowConfigEntry) -> bool:
    """Set up Mailcow from a config entry."""
    api = MailcowApi(
        url=entry.data[CONF_URL],
        api_key=entry.data[CONF_API_KEY],
        origin_ip=entry.data.get(CONF_ORIGIN_IP),
        shared_session=async_get_clientsession(hass),
    )

    history = MailcowQuarantineHistory(hass, entry.entry_id)
    await history.async_load()

    operational_coordinator = MailcowOperationalCoordinator(hass, api, history)
    certificate_coordinator = MailcowCertificateCoordinator(hass, api)

    await operational_coordinator.async_config_entry_first_refresh()
    await certificate_coordinator.async_refresh()

    entry.runtime_data = MailcowRuntimeData(
        api=api,
        history=history,
        operational_coordinator=operational_coordinator,
        certificate_coordinator=certificate_coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MailcowConfigEntry) -> bool:
    """Unload Mailcow."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.api.async_close()
    return unload_ok


def _loaded_entry(hass: HomeAssistant) -> MailcowConfigEntry:
    """Return the loaded Mailcow entry used by service calls."""
    entries = [entry for entry in hass.config_entries.async_entries(DOMAIN) if entry.runtime_data]
    if not entries:
        raise ValueError("No loaded Mailcow configuration entry")
    if len(entries) > 1:
        raise ValueError("Multiple Mailcow entries are configured; service entry selection is not implemented yet")
    return entries[0]


def _async_register_services(hass: HomeAssistant) -> None:
    """Register Mailcow quarantine actions once."""
    if hass.services.has_service(DOMAIN, "view_quarantine_item"):
        return

    async def async_view(call: ServiceCall) -> ServiceResponse:
        entry = _loaded_entry(hass)
        details = await entry.runtime_data.api.async_get_quarantine_item_details(call.data["item_id"])
        return _safe_details(details)

    async def async_release(call: ServiceCall) -> None:
        entry = _loaded_entry(hass)
        item_id = call.data["item_id"]
        await entry.runtime_data.api.async_release_quarantine_item(item_id)
        await entry.runtime_data.history.async_set_status(item_id, "Released")
        await entry.runtime_data.operational_coordinator.async_request_refresh()

    async def async_delete(call: ServiceCall) -> None:
        entry = _loaded_entry(hass)
        item_id = call.data["item_id"]
        await entry.runtime_data.api.async_delete_quarantine_item(item_id)
        await entry.runtime_data.history.async_set_status(item_id, "Deleted")
        await entry.runtime_data.operational_coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        "view_quarantine_item",
        async_view,
        schema=SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(DOMAIN, "release_quarantine_item", async_release, schema=SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, "delete_quarantine_item", async_delete, schema=SERVICE_SCHEMA)


def _safe_details(details: dict[str, Any]) -> dict[str, Any]:
    """Return JSON/service-response-friendly quarantine detail data."""
    return {
        "id": details.get("id"),
        "subject": details.get("subject"),
        "header_from": details.get("header_from"),
        "recipients": details.get("recipients", []),
        "score": details.get("score"),
        "action": details.get("action"),
        "text_plain": details.get("text_plain"),
        "text_html": details.get("text_html"),
        "symbols": details.get("symbols", []),
    }
