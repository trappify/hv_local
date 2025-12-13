# Changelog

## 0.0.4
- Added device registry support so all sensors attach to a single Homevolt device with stable identifiers and config URL; default device name set to `Homevolt`.
- Polled `/error_report.json` to surface health/diagnostic signals: overall health sensor, overall problem binary sensor, and per-subsystem problem sensors with active error details.
- Documented branding behavior and clarified bundled icons.

## 0.0.3
- Added repository branding: new icon (`icon.png`) and logo (`logo.png`) generated from hv_hacs_icon.png for HACS display.

## 0.0.2
- Added per-module sensors (SOC, min/max cell temperature, cycle count, available energy in kWh, alarms) and converted available energy to kWh with two decimals.
- Module alarm sensors now show `OK` when clear.
- Schedule state/setpoint sensors hold the last known value to avoid transient `unknown` during transitions.

## 0.0.1
- Initial release of the Homevolt Local integration.
