"""
Wait for required TCP dependencies before starting the API.
"""

from __future__ import annotations

import os
import socket
import sys
import time


def _wait_for_port(host: str, port: int, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    last_error: OSError | None = None

    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=3):
                print(f"[bootstrap] ready: {host}:{port}")
                return
        except OSError as exc:
            last_error = exc
            print(f"[bootstrap] waiting for {host}:{port} ...")
            time.sleep(2)

    raise TimeoutError(
        f"Timed out after {timeout_seconds}s waiting for {host}:{port}. "
        f"Last error: {last_error}"
    )


def main() -> int:
    timeout_seconds = int(os.getenv("DOCKER_DEP_WAIT_TIMEOUT", "120"))
    deps = [
        (os.getenv("QDRANT_HOST", "qdrant"), int(os.getenv("QDRANT_PORT", "6333"))),
        (os.getenv("REDIS_HOST", "redis"), int(os.getenv("REDIS_PORT", "6379"))),
    ]

    for host, port in deps:
        _wait_for_port(host, port, timeout_seconds)

    print("[bootstrap] all dependencies reachable")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[bootstrap] startup failed: {exc}", file=sys.stderr)
        raise
