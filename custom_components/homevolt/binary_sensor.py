"""Binary sensors for Homevolt problem indicators."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_USE_HTTPS, DEFAULT_NAME, DEFAULT_PORT, DEFAULT_USE_HTTPS, DOMAIN
from .coordinator import HomevoltDataUpdateCoordinator
from .models import HomevoltCoordinatorData


@dataclass(frozen=True, kw_only=True)
class HomevoltBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Homevolt binary sensor entities."""

    value_fn: Callable[[HomevoltCoordinatorData], Any]
    attr_key: str | None = None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Homevolt binary sensor entities."""
    coordinator: HomevoltDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = [
        HomevoltBinarySensor(
            coordinator=coordinator,
            entry=entry,
            entry_id=entry.entry_id,
            description=HomevoltBinarySensorEntityDescription(
                key="problem",
                name="Homevolt Problem",
                device_class=BinarySensorDeviceClass.PROBLEM,
                value_fn=lambda data: bool(
                    (data.metrics.get("warning_count") or 0)
                    + (data.metrics.get("error_count") or 0)
                ),
                attr_key="errors",
            ),
        )
    ]

    subsystems = []
    if coordinator.data:
        subsystems = list(coordinator.data.attributes.get("errors", {}).get("subsystems", {}).keys())

    for subsystem in subsystems:
        slug = _slugify_subsystem(subsystem)
        entities.append(
            HomevoltSubsystemBinarySensor(
                subsystem_name=subsystem,
                subsystem_slug=slug,
                coordinator=coordinator,
                entry=entry,
                entry_id=entry.entry_id,
                description=HomevoltBinarySensorEntityDescription(
                    key=f"subsystem_{slug}_problem",
                    name=f"Homevolt {subsystem} Problem",
                    device_class=BinarySensorDeviceClass.PROBLEM,
                    entity_category=EntityCategory.DIAGNOSTIC,
                    value_fn=lambda data, name=subsystem: bool(
                        data.metrics.get("subsystem_status", {}).get(name)
                    ),
                ),
            )
        )

    async_add_entities(entities)


class HomevoltBinarySensor(CoordinatorEntity[HomevoltDataUpdateCoordinator], BinarySensorEntity):
    """Base binary sensor backed by the shared coordinator."""

    entity_description: HomevoltBinarySensorEntityDescription

    def __init__(
        self,
        *,
        coordinator: HomevoltDataUpdateCoordinator,
        entry: ConfigEntry,
        entry_id: str,
        description: HomevoltBinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = description.name
        self._entry = entry

    @property
    def is_on(self) -> bool | None:
        """Return problem status."""
        if not self.coordinator.data:
            return None
        return bool(self.entity_description.value_fn(self.coordinator.data))

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return scoped attributes."""
        if not self.coordinator.data:
            return None

        attributes: dict[str, Any] = {}
        meta = self.coordinator.data.attributes.get("meta")
        if meta:
            attributes.update(meta)

        if self.entity_description.attr_key:
            scoped = self.coordinator.data.attributes.get(self.entity_description.attr_key)
            if scoped:
                attributes.update(scoped)

        return attributes or None

    @property
    def device_info(self) -> DeviceInfo:
        """Link the entity to the Homevolt device."""
        host = self._entry.data.get(CONF_HOST)
        port = self._entry.data.get(CONF_PORT, DEFAULT_PORT)
        use_https = self._entry.data.get(CONF_USE_HTTPS, DEFAULT_USE_HTTPS)
        configuration_url = None
        if host:
            scheme = "https" if use_https else "http"
            configuration_url = f"{scheme}://{host}:{port}"

        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.unique_id or self._entry.entry_id)},
            name=DEFAULT_NAME,
            manufacturer="Homevolt",
            model="Battery Gateway",
            configuration_url=configuration_url,
        )


class HomevoltSubsystemBinarySensor(HomevoltBinarySensor):
    """Binary sensor for a specific subsystem problem."""

    def __init__(
        self,
        *,
        subsystem_name: str,
        subsystem_slug: str,
        coordinator: HomevoltDataUpdateCoordinator,
        entry: ConfigEntry,
        entry_id: str,
        description: HomevoltBinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator=coordinator, entry=entry, entry_id=entry_id, description=description)
        self._subsystem_name = subsystem_name
        self._subsystem_slug = subsystem_slug

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return only this subsystem's active items."""
        base_attributes = super().extra_state_attributes or {}
        if not self.coordinator.data:
            return base_attributes or None

        errors = self.coordinator.data.attributes.get("errors", {})
        subsystem = errors.get("subsystems", {}).get(self._subsystem_name)
        if subsystem:
            scoped = {"active_items": subsystem.get("active_items", [])}
            base_attributes.update(scoped)
        return base_attributes or None


def _slugify_subsystem(name: str) -> str:
    """Create a stable slug for subsystem entity IDs."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
    slug = slug.strip("_")
    return slug or "unknown"
