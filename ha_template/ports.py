"""Utilities for selecting free TCP ports."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Callable, Iterable


Checker = Callable[[int], bool]


def _default_checker(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", port))
        except OSError:
            return False
    return True


@dataclass
class PortAllocator:
    """Find an available TCP port within a range."""

    start: int = 8123
    end: int = 9123
    checker: Checker = _default_checker

    def allocate(self, reserved: Iterable[int] | None = None) -> int:
        reserved_set = set(reserved or [])
        for port in range(self.start, self.end + 1):
            if port in reserved_set:
                continue
            if self.checker(port):
                return port
        raise RuntimeError("Unable to find free port for Home Assistant")
