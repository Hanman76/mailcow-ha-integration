"""Persistent quarantine history for Mailcow."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import HISTORY_STORAGE_VERSION, RECENT_QUARANTINE_LIMIT


class MailcowQuarantineHistory:
    """Keep the most recent quarantine events across Home Assistant restarts."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store = Store(
            hass,
            HISTORY_STORAGE_VERSION,
            f"mailcow.quarantine_history.{entry_id}",
        )
        self._items: list[dict[str, Any]] = []

    @property
    def items(self) -> list[dict[str, Any]]:
        return deepcopy(self._items)

    async def async_load(self) -> None:
        data = await self._store.async_load()
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            self._items = [item for item in data["items"] if isinstance(item, dict)]
            self._items = self._items[:RECENT_QUARANTINE_LIMIT]

    async def async_observe(self, quarantine: list[dict[str, Any]]) -> None:
        """Add newly observed quarantine messages without deleting old history."""
        changed = False
        known = {_identity(item) for item in self._items}
        new_items: list[dict[str, Any]] = []

        for raw in quarantine:
            item = _history_item(raw)
            identity = _identity(item)
            if identity and identity not in known:
                known.add(identity)
                new_items.append(item)

        if new_items:
            new_items.sort(key=lambda item: _sort_value(item.get("created")), reverse=True)
            self._items = (new_items + self._items)[:RECENT_QUARANTINE_LIMIT]
            changed = True

        if changed:
            await self._async_save()

    async def async_set_status(self, item_id: str, status: str) -> bool:
        """Update a known item's outcome after a successful Mailcow action."""
        changed = False
        for item in self._items:
            if str(item.get("id")) == str(item_id):
                item["status"] = status
                item["status_updated_at"] = datetime.now(UTC).isoformat()
                changed = True
                break
        if changed:
            await self._async_save()
        return changed

    async def _async_save(self) -> None:
        await self._store.async_save({"items": self._items})


def _identity(item: dict[str, Any]) -> str | None:
    value = item.get("id") or item.get("qhash")
    return str(value) if value is not None else None


def _history_item(item: dict[str, Any]) -> dict[str, Any]:
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
        "recipient": item.get("recipient") or item.get("rcpt") or item.get("username"),
        "score": item.get("score"),
        "created": item.get("created"),
        "action": item.get("action"),
        "symbols": symbols,
        "status": "Quarantined",
    }


def _sort_value(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
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
        return 0.0
