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
    was_full: bool,
) -> tuple[float | None, bool]:
    """Return the latest value once per full cycle and updated full state."""
    if soc is None:
        return previous_value, was_full

    if not is_full(soc, threshold):
        return previous_value, False

    if was_full:
        return previous_value, True

    if current_value is None:
        return previous_value, False

    return current_value, True


def sample_total_when_full(
    *,
    modules: Sequence[Mapping[str, Any]],
    threshold: float,
    previous_value: float | None,
    was_full: bool,
) -> tuple[float | None, bool]:
    """Return summed module energy once per full cycle and updated full state."""
    if not modules:
        return previous_value, False

    module_socs: list[float] = []
    module_energy: list[float] = []

    for module in modules:
        soc = module.get("soc")
        energy = module.get("energy_available")
        if not isinstance(soc, (int, float)) or not isinstance(energy, (int, float)):
            return previous_value, was_full
        module_socs.append(float(soc))
        module_energy.append(float(energy))

    if not all(is_full(soc, threshold) for soc in module_socs):
        return previous_value, False

    if was_full:
        return previous_value, True

    return round(sum(module_energy), 2), True
