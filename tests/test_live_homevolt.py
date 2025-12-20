"""Live integration checks against a running Home Assistant instance."""

from __future__ import annotations

import json
import os
import ssl
import urllib.request
from typing import Any

import pytest

HA_URL = os.getenv("HA_URL", "").rstrip("/")
HA_TOKEN = os.getenv("HA_TOKEN", "")
VERIFY_SSL = os.getenv("HA_VERIFY_SSL", "true").lower() not in {"0", "false", "no"}


@pytest.fixture(autouse=True)
def _require_live_config() -> None:
    missing = []
    if not HA_URL:
        missing.append("HA_URL")
    if not HA_TOKEN:
        missing.append("HA_TOKEN")
    if missing:
        pytest.fail(
            "Missing required environment variables for live checks: "
            + ", ".join(missing)
            + ". Set them before running pytest.",
            pytrace=False,
        )


def _api_get(path: str) -> Any:
    url = f"{HA_URL}{path}"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    request = urllib.request.Request(url, headers=headers)
    context = None
    if not VERIFY_SSL and url.startswith("https://"):
        context = ssl._create_unverified_context()
    with urllib.request.urlopen(request, timeout=10, context=context) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _state_index() -> dict[str, dict[str, Any]]:
    states = _api_get("/api/states")
    return {state["entity_id"]: state for state in states}


def _find_by_name(states: dict[str, dict[str, Any]], friendly_name: str) -> dict[str, Any] | None:
    for state in states.values():
        if state.get("attributes", {}).get("friendly_name") == friendly_name:
            return state
    return None


def _as_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _skip_if_no_live_data(states: dict[str, dict[str, Any]]) -> None:
    soc_state = _find_by_name(states, "Homevolt Battery State of Charge")
    if not soc_state:
        pytest.skip("Homevolt integration not loaded in this HA instance.")
    if soc_state["state"] in {"unknown", "unavailable"}:
        pytest.skip("Homevolt data not available; battery may be offline.")


@pytest.mark.live
def test_homevolt_entities_have_live_values() -> None:
    """Verify key Homevolt sensors report live values when the battery is online."""
    states = _state_index()
    _skip_if_no_live_data(states)

    required_names = [
        "Homevolt System State",
        "Homevolt Health",
        "Homevolt Battery State of Charge",
        "Homevolt Battery Temperature",
        "Homevolt Battery Power",
        "Homevolt Grid Power",
        "Homevolt Solar Production",
        "Homevolt Load Power",
        "Homevolt Grid Frequency",
        "Homevolt Voltage L1",
        "Homevolt Voltage L2",
        "Homevolt Voltage L3",
        "Homevolt Grid Energy Imported",
        "Homevolt Grid Energy Exported",
        "Homevolt Solar Energy Produced",
        "Homevolt Battery Charge Energy",
        "Homevolt Battery Discharge Energy",
    ]

    for name in required_names:
        state = _find_by_name(states, name)
        assert state is not None, f"Missing sensor: {name}"
        assert state["state"] not in {"unknown", "unavailable"}, f"{name} has no data"

    health = _find_by_name(states, "Homevolt Health")
    assert health is not None
    assert health["state"] in {"ok", "warning", "error", "unknown"}

    soc = _find_by_name(states, "Homevolt Battery State of Charge")
    assert soc is not None
    soc_value = _as_float(soc["state"])
    assert soc_value is not None
    assert 0 <= soc_value <= 100

    frequency = _find_by_name(states, "Homevolt Grid Frequency")
    assert frequency is not None
    freq_value = _as_float(frequency["state"])
    assert freq_value is not None
    assert 40 <= freq_value <= 70

    binary_problem = _find_by_name(states, "Homevolt Problem")
    assert binary_problem is not None
    assert binary_problem["state"] in {"on", "off"}


@pytest.mark.live
def test_full_capacity_sampling_when_available() -> None:
    """Ensure full-available sensors are populated once sampling conditions are met."""
    states = _state_index()
    _skip_if_no_live_data(states)

    module_full = [
        state
        for state in states.values()
        if state.get("attributes", {}).get("friendly_name", "").startswith(
            "Homevolt Battery Module"
        )
        and "Full Available Energy" in state.get("attributes", {}).get("friendly_name", "")
    ]
    if not module_full:
        pytest.skip("Module full-available sensors not present.")

    for state in module_full:
        if state["state"] in {"unknown", "unavailable"}:
            pytest.skip("Full-available sensors not sampled yet.")
        value = _as_float(state["state"])
        assert value is not None
        assert value >= 0
