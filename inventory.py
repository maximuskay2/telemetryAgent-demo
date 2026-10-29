"""Demo target service: ordered lock acquisition for inventory transfers.

Stdlib only, so the file runs unmodified in the Modal Sandbox image.

Fixed: `acquire_all` acquires locks in canonical (sorted) order, so
concurrent transfers over the same items can never deadlock.
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

    Contract: acquisition order is canonical (sorted by item name) so
    concurrent callers can never deadlock.
    """
    acquired = []
    for item in sorted(items):
        lock = _lock_for(item)
        lock.acquire()
        acquired.append((item, lock))
    return acquired


def release_all(acquired: list[tuple[str, threading.Lock]]) -> None:
    """Release previously acquired locks in reverse order."""
    for _, lock in reversed(acquired):
        lock.release()
