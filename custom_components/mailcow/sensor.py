"""Sensors for Mailcow."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MailcowConfigEntry
from .entity import MailcowEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MailcowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Mailcow sensors."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            MailcowQuarantineCountSensor(coordinator, entry),
            MailcowCertificateSensor(coordinator, entry),
        ]
    )


class MailcowQuarantineCountSensor(MailcowEntity, SensorEntity):
    """Number of messages currently in quarantine."""

    _attr_translation_key = "quarantine_count"
    _attr_icon = "mdi:email-alert-outline"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_quarantine_count"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.quarantine)


class MailcowCertificateSensor(MailcowEntity, SensorEntity):
    """Days remaining on the Mailcow TLS certificate."""

    _attr_translation_key = "certificate"
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_icon = "mdi:certificate"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_certificate"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.certificate.get("days_remaining")

    @property
    def extra_state_attributes(self) -> dict:
        cert = self.coordinator.data.certificate
        expires_at = cert.get("expires_at")
        valid_from = cert.get("valid_from")
        return {
            "enabled": cert.get("enabled"),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "valid_from": valid_from.isoformat() if valid_from else None,
            "issuer": cert.get("issuer"),
            "subject": cert.get("subject"),
        }
