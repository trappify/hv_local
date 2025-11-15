"""Ensures default Home Assistant credentials exist."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .docker_control import DockerController


@dataclass
class UserSetup:
    """Create a default owner account if it doesn't exist."""

    config_dir: Path
    docker: DockerController

    def has_user(self, username: str) -> bool:
        return username in self._list_usernames()

    def _list_usernames(self) -> List[str]:
        result = self.docker.exec_in_service(
            "homeassistant",
            [
                "python3",
                "-m",
                "homeassistant",
                "--script",
                "auth",
                "-c",
                "/config",
                "list",
            ],
            capture=True,
            check=False,
        )
        usernames: List[str] = []
        for line in (result.stdout or "").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("Total users"):
                continue
            usernames.append(stripped)
        return usernames

    def ensure_user(self, username: str, password: str, display_name: str) -> bool:
        if self.has_user(username):
            return False

        command = [
            "python3",
            "-m",
            "homeassistant",
            "--script",
            "auth",
            "-c",
            "/config",
            "add",
            username,
            password,
        ]
        self.docker.exec_in_service("homeassistant", command, check=False)
        return True

    def ensure_onboarding_flag(self) -> None:
        storage = self.config_dir / ".storage"
        storage.mkdir(parents=True, exist_ok=True)
        onboarding_file = storage / "onboarding"
        if onboarding_file.exists():
            return
        onboarding_file.write_text(
            json.dumps(
                {
                    "version": 1,
                    "minor_version": 1,
                    "key": "onboarding",
                    "data": {
                        "done": ["user", "core_config", "integration", "analytics"]
                    },
                },
                indent=2,
            )
        )
