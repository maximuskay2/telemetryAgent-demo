from __future__ import annotations

import threading

_locks: dict[str, threading.Lock] = {}
_registry_guard = threading.Lock()

def _lock_for(item: str) -> threading.Lock:
    with _registry_guard:
        return _locks.setdefault(item, threading.Lock())

def acquire_all(items: list[str]) -> list[tuple[str, threading.Lock]]:
    acquired: list[tuple[str, threading.Lock]] = []
    seen: set[str] = set()
    unique_sorted: list[str] = []
    for it in sorted(items):
        if it not in seen:
            seen.add(it)
            unique_sorted.append(it)
    for item in unique_sorted:
        lock = _lock_for(item)
        lock.acquire()
        acquired.append((item, lock))
    return acquired

def release_all(acquired: list[tuple[str, threading.Lock]]) -> None:
    for _, lock in reversed(acquired):
        lock.release()
