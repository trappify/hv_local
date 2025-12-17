# Agent Logbook

This document captures the instructions that apply to any agent contributing to this repository.

1. Always keep the Home Assistant dev container runnable through `python3 scripts/ha_manager.py start`. The configuration directory under `homeassistant/` must remain persistent because it stores credentials, HACS, and any installed integrations.
2. Default credentials are controlled via `.env` (`DEFAULT_HA_USERNAME`, `DEFAULT_HA_PASSWORD`, `DEFAULT_HA_NAME`). Do not hard-code them anywhere else.
3. Never delete the `.githooks` directory. The hooks there keep the template container running automatically after new revisions are pulled or branches are changed.
4. Update or add pytest coverage for every new module or change to the Python tooling. Run `pytest` locally before handing work over.
5. Keep HACS installation automated through `HACSInstaller`. If you need to bump the version, update `.env.example`, rerun `scripts/configure_repo.py`, and verify that the installer test fixtures still decompress correctly.
6. When updating the devcontainer or docker compose definitions, describe the change in `README.md` so future consumers know how to operate the environment.
7. After making configuration or code changes that affect Home Assistant, always run `python3 scripts/ha_manager.py restart` (or `start` if it was stopped) before handing work back so the latest state is live for testing. Confirm the UI is reachable and mention the active IP/port in your summary.
8. When you have to inspect or modify files owned by the container (anything under `homeassistant/.storage`, etc.), do it via `docker exec ha_template sh -c "...`" so the operation runs as the container user. Never try to edit those files from the host using sudo; it will fail and may break permissions.

## Local State Notes (for next session)

- Latest saved snapshot commit: `d4ca1df` (“Add capacity sampling + schedule helper sensors”). This is committed locally only (do not push until validated).
- Home Assistant UI port is assigned dynamically via `.env` (`HOST_HA_PORT`). Confirm runtime port with `python3 scripts/ha_manager.py status`. At last check it was `http://192.168.9.204:8124` (may change on other machines).
- Capacity tracking sensors:
  - Per-module sampled capacity: `sensor.homevolt_battery_module_<n>_full_available_energy` (kWh), only updates when module SOC ≥ `full_capacity_soc_threshold` (default `99.0`), and restores the last sample after restarts.
  - Total sampled capacity: `sensor.homevolt_battery_full_available_energy` (kWh), only updates when *all* modules are full.
- Schedule helper sensors:
  - `sensor.homevolt_next_charge_start`, `sensor.homevolt_next_discharge_start` (timestamps).
  - `sensor.homevolt_next_schedule_event_start` + `sensor.homevolt_next_schedule_event_type` for the next non-idle entry.
  - Schedule type mapping is currently inferred in `custom_components/homevolt/processor.py` (`1=charge`, `2=discharge`, `3=idle`, `4=grid_discharge`, `5=grid_cycle`). Meaning of `4/5` is not fully confirmed.
- Testing: prefer `.venv/bin/python -m pytest -q` (pytest may not be installed globally).
- If future work adds SoH estimation: planned approach is capacity-based SoH using “full available energy” vs a user-provided battery-level usable baseline (e.g. `12.2 kWh` total) and/or a “max observed” baseline; user requested to observe current sensors first.
