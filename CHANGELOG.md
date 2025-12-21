# Changelog

## 0.0.13
- Seed Kalman SoH estimates from the last full sample on upgrade to avoid returning to `unknown`.

## 0.0.12
- SoH estimation now uses a temperature-weighted Kalman filter on full-charge samples for smoother capacity tracking.

## 0.0.11
- Added SoH baseline options: auto-max or manual usable capacity (kWh).

## 0.0.10
- Added state-of-health sensors that use an auto-max baseline from full-charge samples (total and per-module).

## 0.0.9
- Full-charge capacity sampling now captures once per full cycle, preventing repeated updates while SOC stays above the threshold.
- `next_discharge_start` now treats schedule types `4`/`5` (grid discharge/cycle) as discharge events.
- Dev container runs Home Assistant as the host UID/GID via `.env` to avoid root-owned files in bind mounts.

## 0.0.4
- Added device registry support so all sensors attach to a single Homevolt device with stable identifiers and config URL; default device name set to `Homevolt`.
- Polled `/error_report.json` to surface health/diagnostic signals: overall health sensor, overall problem binary sensor, and per-subsystem problem sensors with active error details.
- Documented branding behavior and clarified bundled icons.

## 0.0.5
- Adjust grid frequency display to show two decimal places while keeping raw values unchanged.

## 0.0.6
- Added full-charge capacity sampling sensors (per-module and total) to track usable battery energy at ~100% SOC over time; configurable SOC threshold via Options.

## 0.0.7
- Default SOC threshold lowered to `99.0%` for full-charge capacity sampling sensors.

## 0.0.8
- Added schedule helper sensors: next charge/discharge start timestamps plus a generic “next schedule event” timestamp/type.

## 0.0.3
- Added repository branding: new icon (`icon.png`) and logo (`logo.png`) generated from hv_hacs_icon.png for HACS display.

## 0.0.2
- Added per-module sensors (SOC, min/max cell temperature, cycle count, available energy in kWh, alarms) and converted available energy to kWh with two decimals.
- Module alarm sensors now show `OK` when clear.
- Schedule state/setpoint sensors hold the last known value to avoid transient `unknown` during transitions.

## 0.0.1
- Initial release of the Homevolt Local integration.
