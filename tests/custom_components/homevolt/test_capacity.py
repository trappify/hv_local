"""Unit tests for capacity sampling helpers."""

from __future__ import annotations

from custom_components.homevolt.capacity import (
    calculate_soh,
    is_full,
    kalman_update,
    sample_total_when_full,
    sample_when_full,
    seed_kalman_estimate,
    select_baseline,
    temperature_variance,
    update_auto_max_baseline,
    variance_to_std,
)


def test_is_full_threshold() -> None:
    assert is_full(None, 99.5) is False
    assert is_full(99.4, 99.5) is False
    assert is_full(99.5, 99.5) is True
    assert is_full(100.0, 99.5) is True


def test_sample_when_full_updates_once_per_full_cycle() -> None:
    value, was_full = sample_when_full(
        current_value=10.0,
        soc=50.0,
        threshold=99.5,
        previous_value=9.0,
        was_full=False,
    )
    assert value == 9.0
    assert was_full is False

    value, was_full = sample_when_full(
        current_value=10.0,
        soc=99.5,
        threshold=99.5,
        previous_value=value,
        was_full=was_full,
    )
    assert value == 10.0
    assert was_full is True

    value, was_full = sample_when_full(
        current_value=10.5,
        soc=99.6,
        threshold=99.5,
        previous_value=value,
        was_full=was_full,
    )
    assert value == 10.0
    assert was_full is True

    value, was_full = sample_when_full(
        current_value=10.5,
        soc=98.0,
        threshold=99.5,
        previous_value=value,
        was_full=was_full,
    )
    assert value == 10.0
    assert was_full is False

    value, was_full = sample_when_full(
        current_value=None,
        soc=99.5,
        threshold=99.5,
        previous_value=value,
        was_full=was_full,
    )
    assert value == 10.0
    assert was_full is False


def test_sample_total_when_full_requires_all_modules_full() -> None:
    modules = [
        {"soc": 99.6, "energy_available": 5.55},
        {"soc": 99.7, "energy_available": 5.45},
    ]
    value, was_full = sample_total_when_full(
        modules=modules,
        threshold=99.5,
        previous_value=None,
        was_full=False,
    )
    assert value == 11.0
    assert was_full is True

    modules_not_full = [
        {"soc": 99.6, "energy_available": 5.55},
        {"soc": 98.0, "energy_available": 5.45},
    ]
    value, was_full = sample_total_when_full(
        modules=modules_not_full,
        threshold=99.5,
        previous_value=10.5,
        was_full=was_full,
    )
    assert value == 10.5
    assert was_full is False


def test_sample_total_when_full_ignores_incomplete_payloads() -> None:
    modules = [
        {"soc": 99.6, "energy_available": 5.55},
        {"soc": 99.7},
    ]
    value, was_full = sample_total_when_full(
        modules=modules,
        threshold=99.5,
        previous_value=10.0,
        was_full=False,
    )
    assert value == 10.0
    assert was_full is False


def test_update_auto_max_baseline_tracks_highest_sample() -> None:
    assert update_auto_max_baseline(current_sample=None, previous_baseline=None) is None
    assert update_auto_max_baseline(current_sample=10.0, previous_baseline=None) == 10.0
    assert update_auto_max_baseline(current_sample=9.5, previous_baseline=10.0) == 10.0
    assert update_auto_max_baseline(current_sample=10.5, previous_baseline=10.0) == 10.5
    assert update_auto_max_baseline(current_sample=0.0, previous_baseline=10.0) == 10.0


def test_calculate_soh_returns_percentage() -> None:
    assert calculate_soh(current_sample=None, baseline=10.0) is None
    assert calculate_soh(current_sample=10.0, baseline=None) is None
    assert calculate_soh(current_sample=-1.0, baseline=10.0) is None
    assert calculate_soh(current_sample=10.0, baseline=0.0) is None
    assert calculate_soh(current_sample=9.0, baseline=10.0) == 90.0
    assert calculate_soh(current_sample=9.25, baseline=10.0) == 92.5


def test_select_baseline_prefers_manual_when_configured() -> None:
    assert select_baseline(strategy="manual", manual_baseline=None, auto_baseline=10.0) is None
    assert select_baseline(strategy="manual", manual_baseline=-1.0, auto_baseline=10.0) is None
    assert select_baseline(strategy="manual", manual_baseline=12.0, auto_baseline=10.0) == 12.0
    assert (
        select_baseline(
            strategy="manual",
            manual_baseline=12.0,
            auto_baseline=10.0,
            module_count=2,
        )
        == 6.0
    )
    assert select_baseline(strategy="auto", manual_baseline=12.0, auto_baseline=10.0) == 10.0


def test_temperature_variance_scales_with_band() -> None:
    base = 0.04
    assert temperature_variance(20.0, base_variance=base) == base
    assert temperature_variance(10.0, base_variance=base) > base
    assert temperature_variance(35.0, base_variance=base) > base
    assert temperature_variance(None, base_variance=base) == base * 2


def test_kalman_update_smooths_measurements() -> None:
    estimate, variance = kalman_update(
        estimate=None,
        variance=None,
        measurement=12.0,
        measurement_variance=0.04,
    )
    assert estimate == 12.0
    assert variance == 0.04

    estimate2, variance2 = kalman_update(
        estimate=estimate,
        variance=variance,
        measurement=11.5,
        measurement_variance=0.04,
    )
    assert estimate2 is not None
    assert variance2 is not None
    assert estimate2 != estimate
    assert variance2 < (variance + 0.0025)


def test_variance_to_std_handles_edges() -> None:
    assert variance_to_std(None) is None
    assert variance_to_std(-1.0) is None
    assert variance_to_std(0.0) == 0.0


def test_seed_kalman_estimate_uses_sample() -> None:
    estimate, variance = seed_kalman_estimate(last_sample=None, last_temperature=20.0)
    assert estimate is None
    assert variance is None

    estimate, variance = seed_kalman_estimate(last_sample=12.2, last_temperature=20.0)
    assert estimate == 12.2
    assert variance is not None
