"""Data coordinators for Mailcow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from time import monotonic
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
from .history import MailcowQuarantineHistory

from .const import (
    CERTIFICATE_SCAN_INTERVAL,
    DOMAIN,
    OPERATIONAL_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class MailcowOperationalData:
    """Fast-changing Mailcow data."""

    quarantine: list[dict[str, Any]]
    recent_quarantine: list[dict[str, Any]]
    containers: list[dict[str, Any]]
    host: dict[str, Any]
    container_total: int
    container_running: int
    container_problems: int
    response_time_ms: int
    refreshed_at: datetime


class MailcowOperationalCoordinator(DataUpdateCoordinator[MailcowOperationalData]):
    """Poll operational Mailcow data every minute."""

    def __init__(self, hass: HomeAssistant, api: MailcowApi, history: MailcowQuarantineHistory) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_operational",
            update_interval=OPERATIONAL_SCAN_INTERVAL,
            always_update=False,
        )
        self.api = api
        self.history = history

    async def _async_update_data(self) -> MailcowOperationalData:
        started = monotonic()
        try:
            containers_raw = await self.api.async_get_containers()
            quarantine = await self.api.async_get_quarantine()
            host = await self.api.async_get_host_status()

            containers = _normalize_containers(containers_raw)
            await self.history.async_observe(quarantine)
            recent = self.history.items
            running = sum(1 for item in containers if item["healthy"])
            problems = sum(1 for item in containers if not item["healthy"])

            return MailcowOperationalData(
                quarantine=quarantine,
                recent_quarantine=recent,
                containers=containers,
                host=host,
                container_total=len(containers),
                container_running=running,
                container_problems=problems,
                response_time_ms=round((monotonic() - started) * 1000),
                refreshed_at=datetime.now(UTC),
            )
        except MailcowAuthError as err:
            raise ConfigEntryAuthFailed("Mailcow API authentication failed") from err
        except (MailcowConnectionError, MailcowError) as err:
            raise UpdateFailed(f"Error communicating with Mailcow: {err}") from err


class MailcowCertificateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll the Mailcow TLS certificate every 12 hours."""

    def __init__(self, hass: HomeAssistant, api: MailcowApi) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_certificate",
            update_interval=CERTIFICATE_SCAN_INTERVAL,
            always_update=False,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.api.async_get_certificate()
            data["checked_at"] = datetime.now(UTC)
            return data
        except (MailcowConnectionError, MailcowError) as err:
            raise UpdateFailed(f"Error checking Mailcow TLS certificate: {err}") from err


def _normalize_containers(data: Any) -> list[dict[str, Any]]:
    """Normalize common Mailcow container-status response shapes."""
    raw_items: list[Any]

    if isinstance(data, list):
        raw_items = data
    elif isinstance(data, dict):
        for key in ("containers", "data", "result"):
            value = data.get(key)
            if isinstance(value, list):
                raw_items = value
                break
        else:
            # Some APIs return a mapping keyed by container name.
            raw_items = [
                {"name": key, **value} if isinstance(value, dict) else {"name": key, "state": value}
                for key, value in data.items()
            ]
    else:
        raw_items = []

    normalized: list[dict[str, Any]] = []
    for raw in raw_items:
        if isinstance(raw, str):
            item = {"name": raw, "state": "unknown"}
        elif isinstance(raw, dict):
            item = raw
        else:
            continue

        name = (
            item.get("name")
            or item.get("container")
            or item.get("container_name")
            or item.get("service")
            or "unknown"
        )
        state = str(
            item.get("state")
            or item.get("status")
            or item.get("State")
            or item.get("Status")
            or "unknown"
        )
        health = str(
            item.get("health")
            or item.get("Health")
            or item.get("health_status")
            or ""
        )

        state_l = state.lower()
        health_l = health.lower()
        healthy = (
            state_l in {"running", "up", "healthy"}
            or state_l.startswith("up ")
            or "running" in state_l
        )
        if health_l:
            healthy = healthy and health_l not in {"unhealthy", "starting", "failed", "error"}

        normalized.append(
            {
                "name": str(name),
                "state": state,
                "health": health or None,
                "healthy": healthy,
            }
        )

    normalized.sort(key=lambda item: item["name"].lower())
    return normalized


def _recent_quarantine(
    quarantine: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    """Return a normalized, newest-first quarantine preview."""
    normalized = [_normalize_quarantine_item(item) for item in quarantine]
    normalized.sort(
        key=lambda item: _timestamp_sort_value(item.get("created")),
        reverse=True,
    )
    return normalized[:limit]


def _normalize_quarantine_item(item: dict[str, Any]) -> dict[str, Any]:
    """Keep useful quarantine fields stable for frontend consumers."""
    symbols = item.get("symbols", item.get("rspamd_symbols"))
    if isinstance(symbols, str):
        symbols = [part.strip() for part in symbols.split(",") if part.strip()]
    elif isinstance(symbols, dict):
        symbols = list(symbols.keys())
    elif not isinstance(symbols, list):
        symbols = []

    return {
        "id": item.get("id"),
        "qhash": item.get("qhash"),
        "subject": item.get("subject"),
        "sender": item.get("sender"),
        "recipient": (
            item.get("recipient")
            or item.get("rcpt")
            or item.get("username")
        ),
        "score": item.get("score"),
        "created": item.get("created"),
        "action": item.get("action"),
        "symbols": symbols,
    }


def _timestamp_sort_value(value: Any) -> float:
    """Convert common Mailcow timestamp forms to a sortable value."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return 0.0

    try:
        return float(text)
    except ValueError:
        pass

    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.timestamp()
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=UTC).timestamp()
        except ValueError:
            continue

    return 0.0
