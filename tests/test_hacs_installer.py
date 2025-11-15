import io
import json
import zipfile
from pathlib import Path

import pytest

from ha_template.hacs_installer import HACSInstaller


class FakeDownloader:
    def __init__(self, archive: bytes):
        self.archive = archive
        self.requested_url = None

    def fetch(self, url: str) -> bytes:
        self.requested_url = url
        return self.archive


def build_archive() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr("__init__.py", "# hacs")
        zip_file.writestr("manifest.json", "{}")
        zip_file.writestr("api/__init__.py", "# api")
        zip_file.writestr(
            "frontend.py",
            "from homeassistant.core import HomeAssistant, callback\n\n"
            "def async_register_frontend(hass: HomeAssistant, hacs=None):\n"
            '    hass.http.register_static_path("/hacsfiles", "/tmp", cache_headers=False)\n',
        )
    return buffer.getvalue()


def test_installer_extracts_when_missing(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    downloader = FakeDownloader(build_archive())
    installer = HACSInstaller(config_dir, downloader=downloader)

    changed = installer.ensure("1.0.0")
    assert changed is True
    assert downloader.requested_url.endswith("/1.0.0/hacs.zip")
    target = config_dir / "custom_components" / "hacs" / "__init__.py"
    assert target.exists()
    patched_frontend = config_dir / "custom_components" / "hacs" / "frontend.py"
    text = patched_frontend.read_text()
    assert "_register_hacs_static" in text

    changed_again = installer.ensure("1.0.0")
    assert changed_again is False


def test_installer_fetches_latest(monkeypatch, tmp_path):
    class FakeResponse:
        def __init__(self, payload: dict):
            self.payload = payload

        def read(self):
            return json.dumps(self.payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(url):
        assert url.endswith("/releases/latest")
        return FakeResponse({"tag_name": "v9.9.9"})

    monkeypatch.setattr("ha_template.hacs_installer.request.urlopen", fake_urlopen)

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    downloader = FakeDownloader(build_archive())
    installer = HACSInstaller(config_dir, downloader=downloader)

    installer.ensure("latest")
    assert downloader.requested_url.endswith("/v9.9.9/hacs.zip")
