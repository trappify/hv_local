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
