"""Data coordinator for Mailcow."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    MailcowApi,
    MailcowAuthError,
    MailcowConnectionError,
    MailcowError,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class MailcowData:
    """Data shared by Mailcow entities."""

    quarantine: list[dict[str, Any]]
    certificate: dict[str, Any]


class MailcowCoordinator(DataUpdateCoordinator[MailcowData]):
    """Coordinate Mailcow API polling."""

    def __init__(self, hass: HomeAssistant, api: MailcowApi) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            always_update=False,
        )
        self.api = api

    async def _async_update_data(self) -> MailcowData:
        try:
            quarantine = await self.api.async_get_quarantine()
            certificate = await self.api.async_get_certificate()
            return MailcowData(
                quarantine=quarantine,
                certificate=certificate,
            )
        except MailcowAuthError as err:
            raise ConfigEntryAuthFailed("Mailcow API authentication failed") from err
        except (MailcowConnectionError, MailcowError) as err:
            raise UpdateFailed(f"Error communicating with Mailcow: {err}") from err
