#!/usr/bin/env python3
"""CLI entry point for managing the Home Assistant dev container."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from ha_template.ha_manager import HomeAssistantManager


def build_manager() -> HomeAssistantManager:
    return HomeAssistantManager(REPO_ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the Home Assistant template container.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start the dev container")
    start_parser.add_argument("--auto", action="store_true", help="Only start if not already running.")

    subparsers.add_parser("stop", help="Stop the dev container")
    subparsers.add_parser("restart", help="Restart the dev container")
    subparsers.add_parser("rebuild", help="Pull images and rebuild the dev container")
    subparsers.add_parser("status", help="Show docker compose status")

    autostart_parser = subparsers.add_parser("autostart", help="Start only when new changes exist.")
    autostart_parser.add_argument("--quiet", action="store_true", help="Suppress already-running message.")

    args = parser.parse_args()
    manager = build_manager()

    if args.command == "start":
        changed = manager.start(auto=args.auto)
        if not changed and args.auto:
            print("Home Assistant already running; auto start skipped.")
    elif args.command == "stop":
        manager.stop()
    elif args.command == "restart":
        manager.restart()
    elif args.command == "rebuild":
        manager.rebuild()
    elif args.command == "status":
        print(manager.status())
    elif args.command == "autostart":
        changed = manager.start(auto=True)
        if not changed and not args.quiet:
            print("Home Assistant already running; auto start skipped.")


if __name__ == "__main__":
    main()
