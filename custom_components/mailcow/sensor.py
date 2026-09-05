"""Sensors for Mailcow."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import PERCENTAGE, UnitOfTime
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
    operational = entry.runtime_data.operational_coordinator
    certificate = entry.runtime_data.certificate_coordinator

    async_add_entities(
        [
            MailcowQuarantineCountSensor(operational, entry),
            MailcowRecentQuarantineSensor(operational, entry),
            MailcowContainersRunningSensor(operational, entry),
            MailcowApiResponseTimeSensor(operational, entry),
            MailcowUptimeSensor(operational, entry),
            MailcowCpuLoadSensor(operational, entry),
            MailcowMemoryUsageSensor(operational, entry),
            MailcowCertificateSensor(certificate, entry),
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

    @property
    def extra_state_attributes(self) -> dict:
        # Preserve compatibility with existing Lovelace quarantine cards.
        return {"messages": self.coordinator.data.quarantine}


class MailcowRecentQuarantineSensor(MailcowEntity, SensorEntity):
    """Structured preview of recent quarantine entries."""

    _attr_translation_key = "recent_quarantine"
    _attr_icon = "mdi:email-outline"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_recent_quarantine"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.recent_quarantine)

    @property
    def extra_state_attributes(self) -> dict:
        return {"messages": self.coordinator.data.recent_quarantine}


class MailcowContainersRunningSensor(MailcowEntity, SensorEntity):
    """Count Mailcow containers reported as healthy/running."""

    _attr_translation_key = "containers_running"
    _attr_icon = "mdi:docker"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_containers_running"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.container_running

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data
        return {
            "total": data.container_total,
            "problems": data.container_problems,
        }


class MailcowApiResponseTimeSensor(MailcowEntity, SensorEntity):
    """Time for the operational Mailcow API refresh."""

    _attr_translation_key = "api_response_time"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS
    _attr_icon = "mdi:timer-outline"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_api_response_time"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.response_time_ms

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "last_successful_refresh": self.coordinator.data.refreshed_at.isoformat()
        }


class MailcowUptimeSensor(MailcowEntity, SensorEntity):
    """Mailcow host uptime in seconds."""

    _attr_translation_key = "uptime"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_uptime"

    @property
    def native_value(self) -> int | None:
        value = self.coordinator.data.host.get("uptime")
        if value is None:
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None


class MailcowCpuLoadSensor(MailcowEntity, SensorEntity):
    """Mailcow host CPU usage."""

    _attr_translation_key = "cpu_load"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = "measurement"
    _attr_icon = "mdi:cpu-64-bit"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_cpu_load"

    @property
    def native_value(self) -> float | None:
        cpu = self.coordinator.data.host.get("cpu", {})
        if not isinstance(cpu, dict):
            return None
        try:
            return float(cpu.get("usage"))
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict:
        cpu = self.coordinator.data.host.get("cpu", {})
        return {"cores": cpu.get("cores")} if isinstance(cpu, dict) else {}


class MailcowMemoryUsageSensor(MailcowEntity, SensorEntity):
    """Mailcow host memory usage."""

    _attr_translation_key = "memory_usage"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = "measurement"
    _attr_icon = "mdi:memory"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_memory_usage"

    @property
    def native_value(self) -> float | None:
        memory = self.coordinator.data.host.get("memory", {})
        if not isinstance(memory, dict):
            return None
        try:
            return float(memory.get("usage"))
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict:
        memory = self.coordinator.data.host.get("memory", {})
        if not isinstance(memory, dict):
            return {}
        total = memory.get("total")
        try:
            total_bytes = int(float(total))
            total_gb = round(total_bytes / 1073741824, 1)
        except (TypeError, ValueError):
            total_bytes = None
            total_gb = None
        return {"total_bytes": total_bytes, "total_gb": total_gb}


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
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("days_remaining")

    @property
    def extra_state_attributes(self) -> dict:
        cert = self.coordinator.data or {}
        expires_at = cert.get("expires_at")
        valid_from = cert.get("valid_from")
        checked_at = cert.get("checked_at")
        return {
            "enabled": cert.get("enabled"),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "valid_from": valid_from.isoformat() if valid_from else None,
            "issuer": cert.get("issuer"),
            "subject": cert.get("subject"),
            "checked_at": checked_at.isoformat() if checked_at else None,
        }
