"""Automates installing HACS into the config directory."""

from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Protocol
from urllib import request


class Downloader(Protocol):
    """Abstraction to make downloading testable."""

    def fetch(self, url: str) -> bytes:  # pragma: no cover - interface contract
        ...


class HttpDownloader:
    """Downloads bytes over HTTP."""

    def fetch(self, url: str) -> bytes:
        with request.urlopen(url) as response:  # type: ignore[arg-type]
            return response.read()


@dataclass
class HACSInstaller:
    """Install HACS from a GitHub release archive if missing."""

    config_dir: Path
    downloader: Downloader = HttpDownloader()
    releases_api_url: str = "https://api.github.com/repos/hacs/integration/releases/latest"

    def ensure(self, version: str) -> bool:
        hacs_dir = self.config_dir / "custom_components" / "hacs"
        if hacs_dir.exists() and any(hacs_dir.iterdir()):
            return False

        target_version = self._resolve_version(version)
        archive_bytes = self.downloader.fetch(self._release_url(target_version))
        self._extract_hacs(archive_bytes, hacs_dir)
        (self.config_dir / "www" / "community").mkdir(parents=True, exist_ok=True)
        return True

    def _resolve_version(self, version: str | None) -> str:
        if not version or version.lower() == "latest":
            with request.urlopen(self.releases_api_url) as response:  # type: ignore[arg-type]
                payload = json.loads(response.read())
                resolved = payload.get("tag_name")
                if not resolved:
                    raise RuntimeError("Unable to determine latest HACS release")
                return resolved
        return version

    def _release_url(self, version: str) -> str:
        return f"https://github.com/hacs/integration/releases/download/{version}/hacs.zip"

    def _extract_hacs(self, archive_bytes: bytes, target_dir: Path) -> None:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
            zf.extractall(target_dir)
        self._apply_frontend_patch(target_dir)

    def _apply_frontend_patch(self, target_dir: Path) -> None:
        frontend_file = target_dir / "frontend.py"
        if not frontend_file.exists():
            return
        text = frontend_file.read_text()
        if "_register_hacs_static" in text:
            return
        helper = """

def _register_hacs_static(hass: HomeAssistant, url_path: str, path: str, cache_headers: bool = False) -> None:
    register = getattr(hass.http, "register_static_path", None)
    if register:
        register(url_path, path, cache_headers=cache_headers)
        return
    hass.http.async_register_static_paths([(url_path, path, cache_headers)])
"""
        if "if TYPE_CHECKING:" in text:
            text = text.replace("if TYPE_CHECKING:", helper + "\nif TYPE_CHECKING:", 1)
        else:
            text = text + helper
        text = text.replace("hass.http.register_static_path(", "_register_hacs_static(hass, ")
        frontend_file.write_text(text)
