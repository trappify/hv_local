# Using This Template for New Integrations

The workflow below is optimized so Codex CLI (or any other automation) can repeatedly spin up identical Home Assistant dev environments without guesswork.

## 1. Create a new repository from this template

```
gh repo create <new-repo> --template hass_template --public
# or fork/duplicate using any other workflow you prefer
```

> The resulting project already includes the devcontainer, docker compose file, helper scripts, tests, and configuration snapshot.

## 2. Clone and bootstrap

```
git clone <new-repo>
cd <new-repo>
python3 scripts/configure_repo.py --non-interactive
```

The configure script copies `.env.example` to `.env`, makes the git hooks executable, and registers repository-local git settings. Codex agents should run this immediately after cloning.

## 3. Start or manage the Home Assistant instance

Use the helper script (or the equivalent `Makefile` targets) so automation stays consistent:

- `python3 scripts/ha_manager.py start` – boot the container and ensure the environment is ready.
- `python3 scripts/ha_manager.py start --auto` – only start if it is not already running (useful for hooks).
- `python3 scripts/ha_manager.py stop|restart|rebuild|status` – lifecycle commands.

The first free UI port (within `8123-9123`) will be detected automatically and written to `.env` under `HOST_HA_PORT`. Multiple template-derived projects can run on the same host with no extra work.

## 4. Verify persistence

The `homeassistant/` directory is bind-mounted into the container. Anything installed via HACS, the UI, or additional custom components remains intact between restarts. Codex agents should never delete this directory when iterating on a project.

## 5. Develop the integration

- Place custom integration code under `homeassistant/custom_components/<integration_slug>`.
- Update `configuration.yaml` (or supporting files) to load the integration.
- Use HACS (already auto-installed on startup) for dependencies or to install the integration being tested.

## 6. Testing expectations for automation

1. Keep or expand the pytest suite under `tests/`. Any new helper code must be covered.
2. Run `pytest` (or `make test`) before handing off work.
3. Do not hand back changes unless the test suite succeeds.

## 7. Codex CLI reminder

When opening a Codex CLI session for a project created from this template:

1. Run `python3 scripts/configure_repo.py --non-interactive` if `.env`/hooks might be stale.
2. Use the `scripts/ha_manager.py` commands instead of raw Docker invocations.
3. Mention in AGENTS.md/README when new behaviors are introduced so future agents inherit the context.

Following this checklist keeps every new integration project aligned and ensures Home Assistant is always ready for manual or automated verification.
