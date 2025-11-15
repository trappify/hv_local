"""Tests for the Homevolt data processor."""

from __future__ import annotations

from datetime import datetime, timezone

from custom_components.homevolt.models import HomevoltPayload
from custom_components.homevolt.processor import summarize


def _base_payload() -> HomevoltPayload:
    status = {
        "uptime": "1234s",
        "wifi_status": {"signal": -55, "ssid": "homevolt"},
        "lte_status": {"rsrp": -110},
        "mqtt_status": "connected",
        "w868_status": "ok",
        "ems_status": "ok",
    }
    ems = {
        "ems": [
            {
                "ems_data": {
                    "state_str": "charging",
                    "soc_avg": 7345,
                    "sys_temp": 225,
                    "power": -1800,
                    "frequency": 50038,
                    "warning_str": ["temp_high"],
                    "info_str": ["grid_synced"],
                },
                "ems_voltage": {"l1": 2315, "l2": 2320, "l3": 2305},
                "bms_data": [
                    {"soc": 7200, "cycle_count": 14},
                    {"soc": 7500, "cycle_count": 12},
                ],
                "error_str": "none",
            }
        ],
        "sensors": [
            {"total_power": 1000, "energy_imported": 1.2, "energy_exported": 0.1, "phase": {"l1": 400}},
            {"total_power": 2500, "phase": {"l1": 1500}},
            {"total_power": -1500},
        ],
        "aggregated": {"state_str": "charging"},
    }
    schedule = {
        "local_mode": "auto",
        "schedule": [
            {
                "from": 0,
                "to": 9999999999,
                "type": 1,
                "params": {"setpoint": 3500},
            }
        ],
    }
    return HomevoltPayload(status=status, ems=ems, schedule=schedule)


def test_summarize_populates_metrics() -> None:
    """The summary should convert raw payloads into typed measurements."""
    payload = _base_payload()
    summary = summarize(payload, datetime(2025, 1, 1, tzinfo=timezone.utc))

    assert summary.metrics["system_state"] == "charging"
    assert summary.metrics["battery_soc"] == 73.45
    assert summary.metrics["battery_temperature"] == 22.5
    assert summary.metrics["battery_power"] == -1800
    assert summary.metrics["grid_power"] == 1000
    assert summary.metrics["solar_power"] == 2500
    assert summary.metrics["load_power"] == -1500
    assert summary.metrics["frequency"] == 50.038
    assert summary.metrics["voltage_l1"] == 231.5
    assert summary.metrics["voltage_l2"] == 232.0
    assert summary.metrics["voltage_l3"] == 230.5
    assert summary.metrics["schedule_state"] == "charge"
    assert summary.metrics["schedule_setpoint"] == 3500

    battery_attrs = summary.attributes["battery"]
    assert battery_attrs["modules"][0]["soc"] == 72
    assert battery_attrs["modules"][1]["cycle_count"] == 12

    schedule_attrs = summary.attributes["schedule"]
    assert schedule_attrs["local_mode"] == "auto"
    assert schedule_attrs["setpoint"] == 3500

    system_attrs = summary.attributes["system"]
    assert system_attrs["warnings"] == ["temp_high"]
    assert system_attrs["info"] == ["grid_synced"]


def test_summarize_handles_missing_data() -> None:
    """Missing payload keys should not break the calculation."""
    payload = HomevoltPayload(status={}, ems={}, schedule=None)
    summary = summarize(payload, datetime(2025, 1, 1, tzinfo=timezone.utc))

    # All metrics should exist with None defaults rather than raising.
    assert "battery_soc" in summary.metrics
    assert summary.metrics["battery_soc"] is None
    assert summary.attributes["system"]["warnings"] == []
