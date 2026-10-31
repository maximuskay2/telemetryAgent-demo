"""Demo target service: ordered lock acquisition for inventory transfers.

Stdlib only, so the file runs unmodified in the Modal Sandbox image.
"""

from __future__ import annotations

import threading

_locks: dict[str, threading.Lock] = {}
_registry_guard = threading.Lock()


def _lock_for(item: str) -> threading.Lock:
    with _registry_guard:
        return _locks.setdefault(item, threading.Lock())


def acquire_all(items: list[str]) -> list[tuple[str, threading.Lock]]:
    """Acquire one lock per item; return locks in acquisition order.

    Contract: acquisition order must be canonical (sorted by item name) so
    concurrent callers can never deadlock.
    """
    acquired: list[tuple[str, threading.Lock]] = []
    seen: set[str] = set()
    for item in sorted(items):
        lock = _lock_for(item)
        if item not in seen:
            lock.acquire()
            seen.add(item)
        acquired.append((item, lock))
    return acquired


def release_all(acquired: list[tuple[str, threading.Lock]]) -> None:
    """Release previously acquired locks in reverse order."""
    seen: set[int] = set()
    for _, lock in reversed(acquired):
        lid = id(lock)
        if lid not in seen:
            seen.add(lid)
            lock.release()
