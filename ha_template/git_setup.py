"""Configure git defaults for the template repository."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitSetup:
    """Ensures git user info and hook path are configured."""

    repo_path: Path

    def _run(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.repo_path, check=True)

    def configure_identity(self, name: str, email: str) -> None:
        self._run("config", "user.name", name)
        self._run("config", "user.email", email)

    def configure_hooks(self, hooks_path: Path) -> None:
        relative = hooks_path.relative_to(self.repo_path)
        self._run("config", "core.hooksPath", str(relative))
