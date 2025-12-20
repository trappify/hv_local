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


def update_auto_max_baseline(
    *,
    current_sample: float | None,
    previous_baseline: float | None,
) -> float | None:
    """Return the highest observed full sample for auto-max baselines."""
    if current_sample is None or current_sample <= 0:
        return previous_baseline
    if previous_baseline is None or current_sample > previous_baseline:
        return float(current_sample)
    return previous_baseline


def select_baseline(
    *,
    strategy: str,
    manual_baseline: float | None,
    auto_baseline: float | None,
    module_count: int | None = None,
) -> float | None:
    """Select the baseline based on strategy, with optional per-module scaling."""
    if strategy == "manual":
        if manual_baseline is None or manual_baseline <= 0:
            return None
        if module_count:
            return manual_baseline / module_count
        return manual_baseline
    return auto_baseline


def calculate_soh(
    *,
    current_sample: float | None,
    baseline: float | None,
) -> float | None:
    """Return state-of-health percentage based on full-sample energy."""
    if current_sample is None or baseline is None:
        return None
    if current_sample < 0 or baseline <= 0:
        return None
    return round((current_sample / baseline) * 100, 1)
