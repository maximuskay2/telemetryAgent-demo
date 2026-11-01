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
    """Acquire one lock per item in canonical (sorted) order.

    Returns list of (item, lock) tuples in acquisition (sorted) order.
    Concurrent callers with overlapping items will never deadlock
    because all acquire locks in the same global order.
    """
    sorted_items = sorted(items)
    seen: set[str] = set()
    unique_sorted: list[str] = []
    for it in sorted_items:
        if it not in seen:
            seen.add(it)
            unique_sorted.append(it)
    mapping: dict[str, threading.Lock] = {}
    acquired_unique: list[tuple[str, threading.Lock]] = []
    for item in unique_sorted:
        lock = _lock_for(item)
        lock.acquire()
        acquired_unique.append((item, lock))
        mapping[item] = lock
    if len(sorted_items) == len(unique_sorted):
        return acquired_unique
    return [(item, mapping[item]) for item in sorted_items]


def release_all(acquired: list[tuple[str, threading.Lock]]) -> None:
    """Release previously acquired locks in reverse order."""
    seen_ids: set[int] = set()
    for _, lock in reversed(acquired):
        lid = id(lock)
        if lid in seen_ids:
            continue
        seen_ids.add(lid)
        lock.release()
