"""Homevolt integration entry points."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .const import DOMAIN, PLATFORMS

if TYPE_CHECKING:  # pragma: no cover - runtime imports handled lazily
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType
else:
    ConfigEntry = Any
    HomeAssistant = Any
    ConfigType = Any


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Homevolt from YAML (no-op placeholder)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Homevolt from a config entry."""
    from .coordinator import HomevoltDataUpdateCoordinator

    coordinator = HomevoltDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Homevolt config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
