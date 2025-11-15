"""Wrapper for docker compose interactions."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, List


class DockerController:
    """Runs docker compose commands with a fixed compose file."""

    def __init__(self, compose_file: Path):
        self.compose_file = compose_file
        self.workdir = compose_file.parent

    def _cmd(self, *args: str) -> List[str]:
        return ["docker", "compose", "-f", str(self.compose_file), *args]

    def run(self, *args: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
        result = subprocess.run(
            self._cmd(*args),
            cwd=self.workdir,
            check=check,
            capture_output=capture,
            text=True,
        )
        return result

    def up(self, rebuild: bool = False) -> None:
        args = ["up", "-d"]
        if rebuild:
            args.extend(["--build", "--force-recreate"])
        self.run(*args)

    def down(self) -> None:
        self.run("down")

    def stop(self) -> None:
        self.run("stop")

    def pull(self) -> None:
        self.run("pull")

    def status(self) -> str:
        result = self.run("ps", "--status=running", capture=True)
        return result.stdout.strip()

    def is_running(self, service: str = "homeassistant") -> bool:
        result = self.run("ps", "-q", service, capture=True, check=False)
        return bool(result.stdout.strip())

    def exec_in_service(
        self,
        service: str,
        command: Iterable[str],
        check: bool = True,
        capture: bool = False,
    ) -> subprocess.CompletedProcess:
        exec_command = ["exec", "-T", service, *command]
        return self.run(*exec_command, check=check, capture=capture)
