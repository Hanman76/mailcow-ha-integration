"""Binary sensors for Mailcow."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MailcowConfigEntry
from .entity import MailcowEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MailcowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Mailcow binary sensors."""
    coordinator = entry.runtime_data.operational_coordinator
    async_add_entities(
        [
            MailcowApiConnectionBinarySensor(coordinator, entry),
            MailcowContainerHealthBinarySensor(coordinator, entry),
        ]
    )


class MailcowApiConnectionBinarySensor(MailcowEntity, BinarySensorEntity):
    """Mailcow API connectivity."""

    _attr_translation_key = "api_connection"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:server-network"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_api_connection"

    @property
    def available(self) -> bool:
        """Keep this entity visible so failure is shown as disconnected."""
        return True

    @property
    def is_on(self) -> bool:
        """Return true when the latest operational refresh succeeded."""
        return self.coordinator.last_update_success


class MailcowContainerHealthBinarySensor(MailcowEntity, BinarySensorEntity):
    """Indicate whether Mailcow containers appear healthy."""

    _attr_translation_key = "container_health"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:docker"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_container_health"

    @property
    def is_on(self) -> bool:
        """Problem is on when one or more containers are not healthy."""
        return self.coordinator.data.container_problems > 0

    @property
    def extra_state_attributes(self) -> dict:
        """Expose container summary and normalized status list."""
        data = self.coordinator.data
        return {
            "total": data.container_total,
            "running": data.container_running,
            "problems": data.container_problems,
            "containers": data.containers,
        }
