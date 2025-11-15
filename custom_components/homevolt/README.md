# Homevolt Local (Unofficial)

This custom integration talks directly to the Homevolt battery gateway over the local network and exposes its JSON endpoints as coordinator-driven sensors in Home Assistant. It is designed for installation via HACS – the integration code lives under `custom_components/homevolt` so any Home Assistant instance can add this repository as a custom source and keep receiving updates.

## Shout-out

Most endpoint knowledge, JSON structures, and sensor ideas originate from [fatuuse's Homevolt package shared on the Home Assistant Community forum](https://community.home-assistant.io/t/homevolt-package/845654). That community contribution made it possible to bootstrap this integration quickly – thank you!

## Features

- Authenticate against the local Homevolt web UI (HTTP or HTTPS, with optional certificate validation).
- Poll `/status.json`, `/ems.json`, and `/schedule.json` to gather battery, grid, and scheduling data.
- Publish coordinator-backed sensors for SOC, temperature, voltages, grid/solar/load power, EMS state, and the active schedule state/setpoint.
- Provide per-sensor attributes such as module SOC values, warning/info strings, LTE/Wi-Fi status, and attribution details.

## Disclaimer

This integration is **not** an official Tibber/Homevolt product. Use it at your own risk, inspect the code before installing updates, and never expose the Homevolt web interface directly to the Internet.

## Local testing

When developing in this repository, the devcontainer-managed Home Assistant instance mounts `homeassistant/custom_components/homevolt`, which is a symlink to this folder. Restart Home Assistant (`python3 scripts/ha_manager.py restart --auto`) after making changes so the container reloads the updated code.
