"""HTTP API helpers for Homevolt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import BasicAuth, ClientResponseError, ClientSession, ClientTimeout

from .models import HomevoltPayload

STATUS_ENDPOINT = "/status.json"
EMS_ENDPOINT = "/ems.json"
SCHEDULE_ENDPOINT = "/schedule.json"
ERROR_REPORT_ENDPOINT = "/error_report.json"
REQUEST_TIMEOUT = 30


class HomevoltError(Exception):
    """Base exception."""


class HomevoltConnectionError(HomevoltError):
    """Raised when the device cannot be reached."""


class HomevoltAuthError(HomevoltError):
    """Raised when authentication fails."""


@dataclass(slots=True)
class HomevoltClient:
    """Small wrapper around the Homevolt local web server."""

    session: ClientSession
    host: str
    port: int
    username: str
    password: str
    use_https: bool = True
    verify_ssl: bool = False

    @property
    def _base_url(self) -> str:
        scheme = "https" if self.use_https else "http"
        return f"{scheme}://{self.host}:{self.port}"

    @property
    def _auth(self) -> BasicAuth | None:
        if self.username:
            return BasicAuth(self.username, self.password or "")
        return None

    @property
    def _ssl(self) -> bool:
        return self.verify_ssl

    async def async_get_payload(self) -> HomevoltPayload:
        """Fetch the three major JSON endpoints."""
        status, ems = await self._async_request(STATUS_ENDPOINT), await self._async_request(EMS_ENDPOINT)
        schedule = await self._async_request(SCHEDULE_ENDPOINT, raise_on_fail=False)
        error_report = await self._async_request(ERROR_REPORT_ENDPOINT, raise_on_fail=False)
        return HomevoltPayload(
            status=status or {},
            ems=ems or {},
            schedule=schedule,
            error_report=error_report,
        )

    async def _async_request(
        self, path: str, *, raise_on_fail: bool = True
    ) -> dict[str, Any] | None:
        url = f"{self._base_url}{path}"
        timeout = ClientTimeout(total=REQUEST_TIMEOUT)
        try:
            async with self.session.get(
                url,
                auth=self._auth,
                timeout=timeout,
                ssl=self._ssl if self.use_https else False,
            ) as response:
                response.raise_for_status()
                return await response.json(content_type=None)
        except ClientResponseError as err:
            if err.status == 401:
                raise HomevoltAuthError from err
            if raise_on_fail:
                raise HomevoltConnectionError from err
        except Exception as err:  # pragma: no cover - mapped to a single error
            if raise_on_fail:
                raise HomevoltConnectionError from err
        return None
