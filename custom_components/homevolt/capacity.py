"""Helpers for estimating battery capacity over time."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

DEFAULT_KALMAN_PROCESS_VARIANCE = 0.0025
DEFAULT_KALMAN_MEASUREMENT_VARIANCE = 0.04
DEFAULT_TEMPERATURE_BAND = (15.0, 30.0)
DEFAULT_TEMPERATURE_SCALE = 0.1
DEFAULT_TEMPERATURE_MAX_FACTOR = 5.0


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


def temperature_variance(
    temperature_c: float | None,
    *,
    base_variance: float = DEFAULT_KALMAN_MEASUREMENT_VARIANCE,
    band: tuple[float, float] = DEFAULT_TEMPERATURE_BAND,
    scale_per_degree: float = DEFAULT_TEMPERATURE_SCALE,
    max_factor: float = DEFAULT_TEMPERATURE_MAX_FACTOR,
) -> float:
    """Return measurement variance scaled by temperature quality."""
    if base_variance <= 0:
        return 0.0
    if temperature_c is None:
        return base_variance * 2
    lower, upper = band
    penalty = 0.0
    if temperature_c < lower:
        penalty = lower - temperature_c
    elif temperature_c > upper:
        penalty = temperature_c - upper
    factor = 1.0 + (penalty * scale_per_degree)
    factor = min(factor, max_factor)
    return base_variance * factor


def kalman_update(
    *,
    estimate: float | None,
    variance: float | None,
    measurement: float | None,
    measurement_variance: float,
    process_variance: float = DEFAULT_KALMAN_PROCESS_VARIANCE,
) -> tuple[float | None, float | None]:
    """Update the 1D Kalman estimate for capacity."""
    if measurement is None:
        return estimate, variance
    if measurement_variance <= 0:
        return measurement, 0.0
    if estimate is None or variance is None:
        return measurement, measurement_variance

    predicted_variance = variance + max(process_variance, 0.0)
    kalman_gain = predicted_variance / (predicted_variance + measurement_variance)
    updated_estimate = estimate + kalman_gain * (measurement - estimate)
    updated_variance = max(0.0, (1 - kalman_gain) * predicted_variance)
    return updated_estimate, updated_variance


def seed_kalman_estimate(
    *,
    last_sample: float | None,
    last_temperature: float | None,
) -> tuple[float | None, float | None]:
    """Seed the Kalman estimate from the latest full sample."""
    if last_sample is None:
        return None, None
    return last_sample, temperature_variance(last_temperature)


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


def variance_to_std(variance: float | None) -> float | None:
    """Return the standard deviation for a variance value."""
    if variance is None or variance < 0:
        return None
    return round(math.sqrt(variance), 3)
