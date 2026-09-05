"""Diagnostics support for Mailcow."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import MailcowConfigEntry
from .const import CONF_API_KEY

TO_REDACT = {CONF_API_KEY}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: MailcowConfigEntry,
) -> dict[str, Any]:
    """Return privacy-conscious diagnostics for a Mailcow config entry."""
    operational = entry.runtime_data.operational_coordinator
    certificate = entry.runtime_data.certificate_coordinator

    op = operational.data
    cert = certificate.data or {}

    return {
        "config_entry": async_redact_data(dict(entry.data), TO_REDACT),
        "operational": {
            "last_update_success": operational.last_update_success,
            "quarantine_count": len(op.quarantine) if op else None,
            "recent_quarantine_count": len(op.recent_quarantine) if op else None,
            "container_total": op.container_total if op else None,
            "container_running": op.container_running if op else None,
            "container_problems": op.container_problems if op else None,
            "containers": op.containers if op else [],
            "response_time_ms": op.response_time_ms if op else None,
            "refreshed_at": op.refreshed_at.isoformat() if op else None,
        },
        "certificate": {
            "last_update_success": certificate.last_update_success,
            "enabled": cert.get("enabled"),
            "days_remaining": cert.get("days_remaining"),
            "expires_at": cert.get("expires_at").isoformat()
            if cert.get("expires_at")
            else None,
            "valid_from": cert.get("valid_from").isoformat()
            if cert.get("valid_from")
            else None,
            "issuer": cert.get("issuer"),
            "subject": cert.get("subject"),
            "checked_at": cert.get("checked_at").isoformat()
            if cert.get("checked_at")
            else None,
        },
    }
