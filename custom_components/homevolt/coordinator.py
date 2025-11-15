"""Data update coordinator for Homevolt."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import HomevoltAuthError, HomevoltClient, HomevoltConnectionError
from .const import CONF_USE_HTTPS, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DEFAULT_USE_HTTPS, DOMAIN
from .models import HomevoltCoordinatorData
from .processor import summarize

LOGGER = logging.getLogger(__name__)


class HomevoltDataUpdateCoordinator(DataUpdateCoordinator[HomevoltCoordinatorData]):
    """Keep Homevolt data up to date."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self._scan_interval = timedelta(
            seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )

        verify_ssl = entry.options.get(
            CONF_VERIFY_SSL,
            entry.data.get(CONF_VERIFY_SSL, False),
        )

        session = async_get_clientsession(hass, verify_ssl=verify_ssl)

        self.client = HomevoltClient(
            session=session,
            host=entry.data[CONF_HOST],
            port=entry.data.get(CONF_PORT, DEFAULT_PORT),
            username=entry.data.get(CONF_USERNAME, "admin"),
            password=entry.data.get(CONF_PASSWORD, ""),
            use_https=entry.data.get(CONF_USE_HTTPS, DEFAULT_USE_HTTPS),
            verify_ssl=verify_ssl,
        )

        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN} coordinator",
            update_interval=self._scan_interval,
        )

    async def _async_update_data(self) -> HomevoltCoordinatorData:
        """Fetch and process data from the device."""
        try:
            payload = await self.client.async_get_payload()
        except HomevoltAuthError as err:
            raise UpdateFailed("Authentication failed") from err
        except HomevoltConnectionError as err:
            raise UpdateFailed("Unable to reach Homevolt") from err

        return summarize(payload, dt_util.utcnow())
