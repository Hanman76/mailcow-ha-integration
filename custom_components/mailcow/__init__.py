"""Mailcow Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MailcowApi
from .const import CONF_API_KEY, CONF_ORIGIN_IP, CONF_URL, PLATFORMS
from .coordinator import MailcowCoordinator


@dataclass
class MailcowRuntimeData:
    """Runtime data for a Mailcow config entry."""

    api: MailcowApi
    coordinator: MailcowCoordinator


type MailcowConfigEntry = ConfigEntry[MailcowRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: MailcowConfigEntry) -> bool:
    """Set up Mailcow from a config entry."""
    api = MailcowApi(
        url=entry.data[CONF_URL],
        api_key=entry.data[CONF_API_KEY],
        origin_ip=entry.data.get(CONF_ORIGIN_IP),
        shared_session=async_get_clientsession(hass),
    )

    coordinator = MailcowCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = MailcowRuntimeData(api=api, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MailcowConfigEntry) -> bool:
    """Unload Mailcow."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.api.async_close()
    return unload_ok
