# Homevolt Local (Unofficial)

This repository hosts an **unofficial** Home Assistant integration that talks directly to a Homevolt battery gateway over the local network. It mirrors the JSON endpoints exposed by the gateway (`/status.json`, `/ems.json`, `/schedule.json`) and exposes the values as coordinator-driven sensors so you can track battery SOC, temperature, voltages, grid/solar/load power, and the active EMS schedule from any Home Assistant instance.

> ⚠️ Disclaimer: This project is not affiliated with Tibber or the official Homevolt team. Use at your own risk and never expose the Homevolt web interface to the public Internet. Inspect releases before installing them in production.
>
> 🚧 **Early-stage notice**: The Homevolt integration is still under active development and the API surface may change between commits. Expect occasional breaking changes while we refine the data model and Energy dashboard support.

## Features

- Authenticates against the local Homevolt web UI (HTTP or HTTPS, with optional certificate validation).
- Collects detailed telemetry: system status, LTE/Wi-Fi state, battery modules and cycle counts, grid/solar/load power, voltages, and schedule setpoints.
- Provides rich state attributes (warning/info strings, module SOC, attribution) so dashboards can show context alongside each sensor. Each battery module also exposes its own sensors for SOC, min/max cell temperature, cycle count, available energy (kWh), and alarm status.
- Packaged for HACS: add this repository as a custom source and install it on **any** Home Assistant instance.
- Surfaces health and problem indicators from `/error_report.json`:
  - `sensor.homevolt_health` (`ok`/`warning`/`error`/`unknown`) with warning/error counts and active items in attributes.
  - `binary_sensor.homevolt_problem` (on if any warning or error) with the same active items.
  - Per-subsystem problem binary sensors (diagnostic) so you can quickly see which area is affected; attributes show only that subsystem’s active items.
- Entities are grouped under a single Homevolt device for easier navigation. The Home Assistant integration badge may still show the generic icon because custom integrations only get brand logos when they’re merged into the official `home-assistant/brands` repository; the bundled logos are used by HACS installs.

## Energy dashboard

Homevolt Local surfaces cumulative `kWh` sensors so you can drop the integration straight into the Home Assistant Energy dashboard:

- `sensor.homevolt_grid_energy_imported` / `sensor.homevolt_grid_energy_exported` → configure them under **Electricity grid** to track consumption/return to the grid.
- `sensor.homevolt_solar_energy_produced` (and optionally `sensor.homevolt_solar_energy_consumed`) → use under **Solar production**.
- `sensor.homevolt_battery_charge_energy` / `sensor.homevolt_battery_discharge_energy` → map to **Home battery storage** charging/discharging slots.

All of these sensors advertise `device_class: energy` and `state_class: total_increasing`, giving them long-term statistics automatically. After saving the Energy configuration, the existing power sensors continue to drive the live energy flow cards.

## Installation via HACS

1. In Home Assistant, go to **HACS → Integrations → … menu → Custom repositories**.
2. Add `https://github.com/trappify/hv_local` as a repository of type `Integration`.
3. Install “Homevolt Local” from HACS.
4. Restart Home Assistant when prompted.
5. Navigate to **Settings → Devices & Services → Add Integration** and search for “Homevolt Local.”
6. Enter the IP/host of your Homevolt gateway, port (default `443`), username/password (defaults to the local admin account), and whether HTTPS/SSL verification should be used.

After the config entry is created the coordinator will refresh every 30 seconds by default. You can adjust the scan interval and SSL verification behavior through the integration’s Options dialog.

## How it works

- A lightweight HTTP client (`custom_components/homevolt/api.py`) gathers the raw payloads from the gateway.
- `custom_components/homevolt/processor.py` flattens the payloads into typed metrics (W, V, %, °C, etc.) and attaches helpful attributes (phase energy, warnings, local mode, etc.).
- Sensors in `custom_components/homevolt/sensor.py` subscribe to the shared coordinator, so a single poll updates every entity in Home Assistant.

### Credits

The implementation is heavily inspired by [fatuuse’s Homevolt package](https://community.home-assistant.io/t/homevolt-package/845654) shared on the Home Assistant Community forum. Their documentation of the endpoints and original YAML sensors made this integration possible—thank you!

## Local development

This repository still contains the Home Assistant devcontainer/template scaffolding so contributors can spin up a persistent test instance:

1. `python3 scripts/configure_repo.py --non-interactive`
2. `python3 -m venv .venv && source .venv/bin/activate && pip install '.[dev]'`
3. `pytest`
4. `python3 scripts/ha_manager.py start` (automatically installs HACS, assigns a free port, and seeds default credentials `devbox/devbox`).

The dev container bind-mounts `custom_components/homevolt` into `/config/custom_components/homevolt`, so restarting Home Assistant via `python3 scripts/ha_manager.py restart` picks up changes immediately.

## Support & issues

Open issues or feature requests on [GitHub](https://github.com/trappify/hv_local/issues). Include debug logs (`custom_components.homevolt: debug`) and anonymized payload snippets whenever possible so we can reproduce the problem.
