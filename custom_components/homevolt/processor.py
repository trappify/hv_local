"""Translate Homevolt payloads into coordinator-friendly data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .models import HomevoltCoordinatorData, HomevoltPayload

SCHEDULE_TYPE_LABELS = {
    1: "charge",
    2: "discharge",
    3: "idle",
    4: "grid_discharge",
    5: "grid_cycle",
}


def summarize(payload: HomevoltPayload, now: datetime | None = None) -> HomevoltCoordinatorData:
    """Prepare flattened data for the coordinator."""
    now = now or datetime.now(timezone.utc)

    metrics: dict[str, Any] = {}
    attributes: dict[str, dict[str, Any]] = {
        "system": {},
        "battery": {},
        "grid": {},
        "solar": {},
        "load": {},
        "schedule": {},
    }

    status = _ensure_mapping(payload.status)
    ems = _ensure_mapping(payload.ems)
    schedule = _ensure_mapping(payload.schedule) if payload.schedule else {}

    ems_block = _first_list_entry(ems.get("ems"))
    ems_data = _ensure_mapping(ems_block.get("ems_data"))
    ems_voltage = _ensure_mapping(ems_block.get("ems_voltage"))

    # System level metrics
    metrics["system_state"] = _safe_str(
        ems_data.get("state_str") or ems.get("aggregated", {}).get("state_str")
    )
    metrics["wifi_status"] = _safe_str(status.get("wifi_status"))
    metrics["lte_status"] = _safe_str(status.get("lte_status"))

    attributes["system"].update(
        {
            "uptime": status.get("uptime"),
            "wifi_status": status.get("wifi_status"),
            "lte_status": status.get("lte_status"),
            "mqtt_status": status.get("mqtt_status"),
            "w868_status": status.get("w868_status"),
            "ems_status": status.get("ems_status"),
            "warnings": _ensure_list(ems_data.get("warning_str")),
            "info": _ensure_list(ems_data.get("info_str")),
            "error": ems_block.get("error_str"),
        }
    )

    # Battery metrics
    metrics["battery_soc"] = _scaled_value(ems_data.get("soc_avg"), 100)
    metrics["battery_temperature"] = _scaled_value(ems_data.get("sys_temp"), 10)
    metrics["battery_power"] = _as_float(ems_data.get("power"))

    battery_modules: list[dict[str, Any]] = []
    for module in _ensure_list(ems_block.get("bms_data")):
        module_data = _ensure_mapping(module)
        battery_modules.append(
            {
                "soc": _scaled_value(module_data.get("soc"), 100),
                "cycle_count": module_data.get("cycle_count"),
            }
        )
    attributes["battery"].update(
        {
            "modules": battery_modules,
            "warning_flags": _ensure_list(ems_data.get("warning_str")),
            "info_flags": _ensure_list(ems_data.get("info_str")),
        }
    )

    # Grid/Solar/Load channels use deterministic indexes from the EMS payload
    sensors = _ensure_list(ems.get("sensors"))
    _apply_sensor(metrics, attributes["grid"], sensors, 0, "grid_power")
    _apply_sensor(metrics, attributes["solar"], sensors, 1, "solar_power")
    _apply_sensor(metrics, attributes["load"], sensors, 2, "load_power")

    # Frequency and voltages
    metrics["frequency"] = _scaled_value(ems_data.get("frequency"), 1000)
    metrics["voltage_l1"] = _scaled_value(ems_voltage.get("l1"), 10)
    metrics["voltage_l2"] = _scaled_value(ems_voltage.get("l2"), 10)
    metrics["voltage_l3"] = _scaled_value(ems_voltage.get("l3"), 10)

    # Schedule summarization
    active_schedule = _select_schedule(schedule.get("schedule"), now)
    if active_schedule:
        schedule_state = SCHEDULE_TYPE_LABELS.get(active_schedule.get("type"))
        if schedule_state:
            metrics["schedule_state"] = schedule_state
        metrics["schedule_setpoint"] = _as_float(
            _ensure_mapping(active_schedule.get("params")).get("setpoint")
        )
        attributes["schedule"].update(
            {
                "state": schedule_state,
                "setpoint": metrics.get("schedule_setpoint"),
                "from": active_schedule.get("from"),
                "to": active_schedule.get("to"),
                "local_mode": schedule.get("local_mode"),
            }
        )
    else:
        attributes["schedule"]["local_mode"] = schedule.get("local_mode")

    return HomevoltCoordinatorData(metrics=metrics, attributes=attributes)


def _apply_sensor(
    metrics: dict[str, Any],
    target_attributes: dict[str, Any],
    sensors: Iterable[Any],
    index: int,
    metric_key: str,
) -> None:
    sensor = _sensor_by_index(sensors, index)
    metrics[metric_key] = _as_float(sensor.get("total_power"))
    target_attributes.update(
        {
            "phase": sensor.get("phase"),
            "energy_imported": sensor.get("energy_imported"),
            "energy_exported": sensor.get("energy_exported"),
        }
    )


def _select_schedule(
    schedule_list: Iterable[Any] | None, now: datetime
) -> Mapping[str, Any] | None:
    entries = _ensure_list(schedule_list)
    timestamp = now.timestamp()
    for entry in entries:
        data = _ensure_mapping(entry)
        start = _as_float(data.get("from"))
        end = _as_float(data.get("to"))
        if start is None or end is None:
            continue
        if start <= timestamp <= end:
            return data
    return None


def _sensor_by_index(sensors: Iterable[Any], index: int) -> Mapping[str, Any]:
    entries = _ensure_list(sensors)
    if index < len(entries):
        return _ensure_mapping(entries[index])
    return {}


def _ensure_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    return []


def _scaled_value(value: Any, divider: float) -> float | None:
    raw = _as_float(value)
    if raw is None:
        return None
    return raw / divider


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_list_entry(value: Any) -> Mapping[str, Any]:
    entries = _ensure_list(value)
    if entries:
        entry = entries[0]
        if isinstance(entry, Mapping):
            return dict(entry)
    return {}
