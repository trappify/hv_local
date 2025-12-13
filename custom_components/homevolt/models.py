"""Shared models for Homevolt."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class HomevoltPayload:
    """Raw payload returned by the Homevolt local API."""

    status: Mapping[str, Any]
    ems: Mapping[str, Any]
    schedule: Mapping[str, Any] | None = None
    error_report: list[Mapping[str, Any]] | None = None


@dataclass(frozen=True)
class HomevoltCoordinatorData:
    """Flattened data provided by the update coordinator."""

    metrics: Mapping[str, Any] = field(default_factory=dict)
    attributes: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", dict(self.metrics))
        object.__setattr__(
            self,
            "attributes",
            {key: dict(value) for key, value in self.attributes.items()},
        )
