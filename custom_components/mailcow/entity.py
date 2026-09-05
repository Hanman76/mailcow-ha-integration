"""Base Mailcow entity."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from . import MailcowConfigEntry
from .const import DOMAIN


class MailcowEntity(CoordinatorEntity[DataUpdateCoordinator[Any]]):
    """Base Mailcow entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[Any],
        entry: MailcowConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        hostname = urlparse(entry.data["url"]).hostname or "mailcow"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, hostname)},
            name=hostname,
            manufacturer="mailcow",
            model="Mailcow Server",
            configuration_url=entry.data["url"],
        )
