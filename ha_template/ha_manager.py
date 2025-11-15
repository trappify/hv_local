"""Public interface for managing the Home Assistant dev container."""

from __future__ import annotations

import shutil
from pathlib import Path

from .docker_control import DockerController
from .env import EnvManager
from .hacs_installer import HACSInstaller
from .ports import PortAllocator
from .user_setup import UserSetup

DEFAULT_ENV = {
    "HA_CONTAINER_NAME": "ha_template",
    "HOST_HA_PORT": "auto",
    "TZ": "UTC",
    "DEFAULT_HA_USERNAME": "devbox",
    "DEFAULT_HA_PASSWORD": "devbox",
    "DEFAULT_HA_NAME": "Dev Box Owner",
    "HACS_VERSION": "latest",
}


class HomeAssistantManager:
    """Coordinates docker, env files, and Home Assistant config."""

    def __init__(
        self,
        repo_root: Path,
        env_manager: EnvManager | None = None,
        port_allocator: PortAllocator | None = None,
        docker: DockerController | None = None,
        hacs: HACSInstaller | None = None,
        user_setup: UserSetup | None = None,
    ):
        self.repo_root = repo_root
        self.compose_file = repo_root / "docker-compose.yml"
        self.env_path = repo_root / ".env"
        self.config_dir = repo_root / "homeassistant"
        self.env_manager = env_manager or EnvManager(self.env_path)
        self.port_allocator = port_allocator or PortAllocator()
        self.docker = docker or DockerController(self.compose_file)
        self.hacs = hacs or HACSInstaller(self.config_dir)
        self.user_setup = user_setup or UserSetup(self.config_dir, self.docker)

    def _ensure_env_file(self) -> None:
        if not self.env_path.exists():
            shutil.copy(self.repo_root / ".env.example", self.env_path)
        self.env_manager.load()
        for key, value in DEFAULT_ENV.items():
            self.env_manager.ensure(key, lambda v=value: v)
        self._ensure_port()

    def _ensure_port(self) -> None:
        def allocate() -> str:
            return str(self.port_allocator.allocate())

        self.env_manager.ensure("HOST_HA_PORT", allocate)

    def _ensure_config_dirs(self) -> None:
        (self.config_dir / "custom_components").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "www" / "community").mkdir(parents=True, exist_ok=True)
        (self.config_dir / ".storage").mkdir(parents=True, exist_ok=True)

    def prepare(self) -> None:
        self._ensure_env_file()
        self._ensure_config_dirs()
        hacs_version = self.env_manager.get("HACS_VERSION") or DEFAULT_ENV["HACS_VERSION"]
        self.hacs.ensure(hacs_version)
        self.user_setup.ensure_onboarding_flag()

    def start(self, auto: bool = False) -> bool:
        self.prepare()
        if auto and self.docker.is_running():
            return False
        self.docker.up()
        self._ensure_credentials()
        return True

    def stop(self) -> None:
        self.docker.stop()

    def restart(self) -> None:
        self.docker.stop()
        self.start()

    def rebuild(self) -> None:
        self.prepare()
        self.docker.pull()
        self.docker.up(rebuild=True)
        self._ensure_credentials()

    def status(self) -> str:
        return self.docker.status()

    def _ensure_credentials(self) -> None:
        username = self.env_manager.get("DEFAULT_HA_USERNAME") or DEFAULT_ENV["DEFAULT_HA_USERNAME"]
        password = self.env_manager.get("DEFAULT_HA_PASSWORD") or DEFAULT_ENV["DEFAULT_HA_PASSWORD"]
        display_name = self.env_manager.get("DEFAULT_HA_NAME") or DEFAULT_ENV["DEFAULT_HA_NAME"]
        self.user_setup.ensure_user(username, password, display_name)
