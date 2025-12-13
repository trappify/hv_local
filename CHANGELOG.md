# Changelog

## 0.0.2
- Added per-module sensors (SOC, min/max cell temperature, cycle count, available energy in kWh, alarms) and converted available energy to kWh with two decimals.
- Module alarm sensors now show `OK` when clear.
- Schedule state/setpoint sensors hold the last known value to avoid transient `unknown` during transitions.

## 0.0.1
- Initial release of the Homevolt Local integration.
