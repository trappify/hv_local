from pathlib import Path

from ha_template.env import EnvManager


def test_env_manager_roundtrip(tmp_path):
    env_path = tmp_path / ".env"
    manager = EnvManager(env_path)
    manager.set("FOO", "bar")
    assert env_path.read_text().strip() == "FOO=bar"

    manager.ensure("BAR", lambda: "baz")
    assert manager.get("BAR") == "baz"

    manager.set("HOST_HA_PORT", "auto")
    value = manager.ensure("HOST_HA_PORT", lambda: "8123")
    assert value == "8123"
    assert "HOST_HA_PORT=8123" in env_path.read_text()
