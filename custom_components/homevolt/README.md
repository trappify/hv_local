# Homevolt Local (Unofficial)

This custom integration talks directly to the Homevolt battery gateway over the local network and exposes its JSON endpoints as coordinator-driven sensors in Home Assistant. It is designed for installation via HACS – the integration code lives under `custom_components/homevolt` so any Home Assistant instance can add this repository as a custom source and keep receiving updates.

## Shout-out

Most endpoint knowledge, JSON structures, and sensor ideas originate from [fatuuse's Homevolt package shared on the Home Assistant Community forum](https://community.home-assistant.io/t/homevolt-package/845654). That community contribution made it possible to bootstrap this integration quickly – thank you!

## Features

- Authenticate against the local Homevolt web UI (HTTP or HTTPS, with optional certificate validation).
- Poll `/status.json`, `/ems.json`, and `/schedule.json` to gather battery, grid, and scheduling data.
- Publish coordinator-backed sensors for SOC, temperature, voltages, grid/solar/load power, EMS state, and the active schedule state/setpoint.
- Provide per-sensor attributes such as module SOC values, warning/info strings, LTE/Wi-Fi status, and attribution details. Module-level sensors appear when the gateway reports modules.
- Surface `/error_report.json` as:
  - `sensor.homevolt_health` (`ok`/`warning`/`error`/`unknown`) with warning/error counts and active items in attributes.
  - `binary_sensor.homevolt_problem` (problem on if any warning or error) with the same active items.
  - Per-subsystem problem binary sensors (diagnostic) showing only that subsystem’s active items.
- All entities are grouped under a single Homevolt device in Home Assistant. The integration tile may still show a generic icon because custom integrations only display branded logos once the assets are upstreamed to `home-assistant/brands`; HACS will use the bundled icons shipped with this repo.

## Disclaimer

This integration is **not** an official Tibber/Homevolt product. Use it at your own risk, inspect the code before installing updates, and never expose the Homevolt web interface directly to the Internet.

## Local testing

When developing in this repository, the devcontainer-managed Home Assistant instance bind-mounts this folder directly into `/config/custom_components/homevolt` (see `docker-compose.yml`). Restart Home Assistant (`python3 scripts/ha_manager.py restart`) after making changes so the container reloads the updated code.

## Tips for use

- Use `binary_sensor.homevolt_problem` for alerting/automations: it turns on if any warning or error is active.
- Check `sensor.homevolt_health` for severity (`ok`/`warning`/`error`/`unknown`) and counts in attributes.
- Per-subsystem problem sensors (diagnostic) help narrow down which area is affected; see the Homevolt device page to review subsystem-specific active items.

### Tracking usable capacity (aging)

If you charge to (near) 100% SOC a few times a week, the best practical “capacity over time” signal is the module energy that remains when full:

- `sensor.homevolt_battery_module_<n>_full_available_energy` (kWh): samples `Available Energy` once when module SOC crosses the configured threshold (default `99.0%`), then holds the value until SOC drops below the threshold.
- `sensor.homevolt_battery_full_available_energy` (kWh): sum of modules, sampled once when all modules cross the threshold, then holds until any module drops below.

State-of-health sensors use a temperature-weighted Kalman estimate of full capacity (based on full-charge samples and module max temps) and turn it into a percentage using a baseline (auto-max by default, or a manual usable kWh if configured in Options). Set **SoH baseline strategy** to `manual` and enter your usable capacity in kWh when you want an absolute baseline.

- `sensor.homevolt_battery_state_of_health` (%): total SoH vs. max observed full sample.
- `sensor.homevolt_battery_module_<n>_state_of_health` (%): per-module SoH vs. max observed full sample.


To smooth this into a long-term trend, add a Home Assistant **Statistics** helper on top of one of these sensors (e.g. 30-day mean).

### Seeing the next scheduled action

If `/schedule.json` includes upcoming entries, Homevolt Local exposes “next schedule” helper sensors:

- `sensor.homevolt_next_charge_start` (timestamp) → next `charge` entry (type `1`).
- `sensor.homevolt_next_discharge_start` (timestamp) → next `discharge` entry (type `2`).
- `sensor.homevolt_next_schedule_event_start` / `sensor.homevolt_next_schedule_event_type` → next non-idle entry (types `1/2/4/5`).
