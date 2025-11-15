#!/usr/bin/env python3
"""Configure git and bootstrap local files."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from ha_template.env import EnvManager
from ha_template.git_setup import GitSetup


def ensure_env_file() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        return
    template = REPO_ROOT / ".env.example"
    shutil.copy(template, env_path)


def ensure_hooks_executable() -> None:
    hooks_dir = REPO_ROOT / ".githooks"
    for hook in hooks_dir.glob("*"):
        if hook.is_file():
            hook.chmod(hook.stat().st_mode | 0o111)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--non-interactive", action="store_true")
    args = parser.parse_args()

    ensure_env_file()
    ensure_hooks_executable()

    git = GitSetup(REPO_ROOT)
    git.configure_identity("trappify", "andreas@trappland.se")
    git.configure_hooks(REPO_ROOT / ".githooks")

    env_manager = EnvManager(REPO_ROOT / ".env")
    env_manager.load()
    env_manager.ensure("HOST_HA_PORT", lambda: "auto")


if __name__ == "__main__":
    main()
