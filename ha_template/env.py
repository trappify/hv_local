"""Helpers for .env files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict


@dataclass
class EnvManager:
    """Simple .env reader/writer with minimal parsing."""

    path: Path
    _data: Dict[str, str] = field(default_factory=dict, init=False)
    _loaded: bool = field(default=False, init=False)

    def _parse(self, raw: str) -> Dict[str, str]:
        data: Dict[str, str] = {}
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            data[key.strip()] = value.strip()
        return data

    def load(self) -> Dict[str, str]:
        if self._loaded:
            return self._data
        if self.path.exists():
            self._data = self._parse(self.path.read_text())
        else:
            self._data = {}
        self._loaded = True
        return self._data

    def save(self) -> None:
        lines = [f"{key}={value}" for key, value in self._data.items()]
        self.path.write_text("\n".join(lines) + ("\n" if lines else ""))

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.load().get(key, default)

    def set(self, key: str, value: str) -> None:
        data = self.load()
        data[key] = value
        self._data = data
        self.save()

    def ensure(self, key: str, factory: Callable[[], str]) -> str:
        data = self.load()
        value = data.get(key)
        if not value or value.lower() == "auto":
            value = factory()
            data[key] = value
            self._data = data
            self.save()
        return value

    def update_from(self, other: Dict[str, str]) -> None:
        data = self.load()
        data.update(other)
        self._data = data
        self.save()
