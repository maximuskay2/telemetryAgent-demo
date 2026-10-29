# Demo target service: ordered lock acquisition for inventory transfers.
# Fixed: acquire in canonical sorted order to prevent deadlocks.
from __future__ import annotations
import threading
_locks: dict[str, threading.Lock] = {}
_registry_guard = threading.Lock()

def _lock_for(item: str) -> threading.Lock:
    with _registry_guard:
        return _locks.setdefault(item, threading.Lock())

def acquire_all(items: list[str]) -> list[tuple[str, threading.Lock]]:
    acquired = []
    seen = set()
    for item in sorted(items):
        if item in seen:
            continue
        seen.add(item)
        lock = _lock_for(item)
        lock.acquire()
        acquired.append((item, lock))
    return acquired

def release_all(acquired: list[tuple[str, threading.Lock]]) -> None:
    for _, lock in reversed(acquired):
        lock.release()
