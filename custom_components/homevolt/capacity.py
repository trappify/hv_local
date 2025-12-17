"""Helpers for estimating battery capacity over time."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def is_full(soc: float | None, threshold: float) -> bool:
    """Return True when SOC is at/above the configured full threshold."""
    if soc is None:
        return False
    return soc >= threshold


def sample_when_full(
    *,
    current_value: float | None,
    soc: float | None,
    threshold: float,
    previous_value: float | None,
) -> float | None:
    """Return the latest value only when SOC is full; otherwise return the previous."""
    if current_value is None:
        return previous_value
    if is_full(soc, threshold):
        return current_value
    return previous_value


def sample_total_when_full(
    *,
    modules: Sequence[Mapping[str, Any]],
    threshold: float,
    previous_value: float | None,
) -> float | None:
    """Return summed module energy when all modules are full; otherwise keep previous."""
    if not modules:
        return previous_value

    module_socs: list[float] = []
    module_energy: list[float] = []

    for module in modules:
        soc = module.get("soc")
        energy = module.get("energy_available")
        if not isinstance(soc, (int, float)) or not isinstance(energy, (int, float)):
            return previous_value
        module_socs.append(float(soc))
        module_energy.append(float(energy))

    if not all(is_full(soc, threshold) for soc in module_socs):
        return previous_value

    return round(sum(module_energy), 2)
