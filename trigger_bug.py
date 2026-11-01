"""Reproduce the seeded deadlock for real and ship its traceback.

Two threads transfer the same items in opposite order through
`inventory.acquire_all` until they deadlock (the bug: caller-order locking).
The stuck thread's real stack is printed as a Python traceback and, with
--key, POSTed to TelemetryAgent's log ingest like any forwarder batch.

  python trigger_bug.py
  python trigger_bug.py --key ta_live_... \
      [--api https://api-production-0c9a.up.railway.app]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request

from inventory import acquire_all, release_all

DEFAULT_API = "https://api-production-0c9a.up.railway.app"
PAIRS = (["axle", "brake-pad"], ["brake-pad", "axle"])


def transfer(items: list[str], stop: threading.Event) -> None:
    while not stop.is_set():
        held = acquire_all(items)
        release_all(held)


def reproduce(timeout_s: float = 20.0) -> list[str]:
    """Run opposite-order transfers until two threads stop moving."""
    sys.setswitchinterval(1e-6)
    stop = threading.Event()
    threads = [
        threading.Thread(target=transfer, args=(items, stop), daemon=True)
        for items in PAIRS
    ]
    for thread in threads:
        thread.start()
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(0.5)
        frames = sys._current_frames()
        stuck = [
            (thread, frames.get(thread.ident))
            for thread in threads
            if thread.is_alive() and frames.get(thread.ident) is not None
            and frames[thread.ident].f_code.co_name == "acquire_all"
        ]
        if len(stuck) == 2:
            time.sleep(1.0)
            frames = sys._current_frames()
            still = [
                frames.get(thread.ident) for thread, _ in stuck
                if frames.get(thread.ident) is not None
                and frames[thread.ident].f_code.co_name == "acquire_all"
            ]
            if len(still) == 2:
                return _as_traceback(still[0])
    stop.set()
    raise SystemExit(f"no deadlock within {timeout_s:.0f}s (try again)")


def _as_traceback(frame) -> list[str]:
    stack = [
        line.rstrip("\n")
        for chunk in traceback.format_stack(frame)
        for line in chunk.splitlines()
    ]
    return (
        ["Traceback (most recent call last):"]
        + stack
        + [
            "TimeoutError: deadlock in acquire_all: two transfers lock "
            "axle and brake-pad in opposite order and wait on each other "
            "forever"
        ]
    )


def _commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def send(api: str, key: str, lines: list[str]) -> str:
    now = time.time()
    body = {
        "service": "inventory",
        "release": "demo",
        "commit": _commit(),
        "lines": [
            {"ts": now, "level": "ERROR", "message": line} for line in lines
        ],
    }
    request = urllib.request.Request(
        f"{api.rstrip('/')}/api/ingest/logs",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return f"{response.status} {response.read().decode()}"
    except urllib.error.HTTPError as exc:
        return f"{exc.code} {exc.read().decode()}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("--key", default="", help="ta_live_* logs key")
    args = parser.parse_args()
    lines = reproduce()
    print("\n".join(lines), flush=True)
    if args.key:
        print("\ningest:", send(args.api, args.key, lines))


if __name__ == "__main__":
    main()
