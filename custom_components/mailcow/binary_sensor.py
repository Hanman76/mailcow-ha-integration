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
    async_add_entities(
        [MailcowApiConnectionBinarySensor(entry.runtime_data.coordinator, entry)]
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
    def is_on(self) -> bool:
        """Return true when the latest coordinator update succeeded."""
        return self.coordinator.last_update_success
