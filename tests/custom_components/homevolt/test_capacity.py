"""Unit tests for capacity sampling helpers."""

from __future__ import annotations

from custom_components.homevolt.capacity import is_full, sample_total_when_full, sample_when_full


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
