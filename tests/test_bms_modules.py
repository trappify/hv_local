from __future__ import annotations

from datetime import datetime, timezone

from custom_components.homevolt.models import HomevoltPayload
from custom_components.homevolt.processor import summarize


def test_summarize_includes_module_temperatures_and_soc() -> None:
    payload = HomevoltPayload(
        status={},
        ems={
            "ems": [
                {
                    "ems_data": {
                        "state_str": "Throttled",
                        "warning_str": [],
                        "info_str": [],
                    },
                    "bms_data": [
                        {
                            "energy_avail": 12,
                            "cycle_count": 20,
                            "soc": 8300,
                            "state": 5,
                            "state_str": "Connected",
                            "alarm": 0,
                            "alarm_str": ["ALARM_SAMPLE"],
                            "tmin": 233,
                            "tmax": 251,
                        },
                        {
                            "energy_avail": 10,
                            "cycle_count": 11,
                            "soc": 9100,
                            "state": 5,
                            "state_str": "Connected",
                            "alarm": 0,
                            "alarm_str": [],
                            "tmin": 241,
                            "tmax": 261,
                        },
                    ],
                    "ems_voltage": {},
                    "ems_aggregate": {},
                }
            ],
            "sensors": [],
        },
        schedule=None,
    )

    data = summarize(payload, datetime(2025, 1, 1, tzinfo=timezone.utc))
    modules = data.attributes["battery"]["modules"]

    assert modules[0]["soc"] == 83
    assert modules[0]["temperature_min"] == 23.3
    assert modules[0]["temperature_max"] == 25.1
    assert modules[0]["energy_available"] == 0.01
    assert modules[0]["cycle_count"] == 20
    assert modules[0]["alarm_flags"] == ["ALARM_SAMPLE"]

    assert modules[1]["soc"] == 91
    assert modules[1]["temperature_min"] == 24.1
    assert modules[1]["temperature_max"] == 26.1
    assert modules[1]["energy_available"] == 0.01

    # Alarm string rendering should be empty when no alarms are present.
    render = lambda flags: ", ".join(flags) if flags else "OK"
    assert render(modules[0]["alarm_flags"]) == "ALARM_SAMPLE"
    assert render(modules[1]["alarm_flags"]) == "OK"
