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
    # Normalize input: tolerate nested list like [["a","b"]] used by harness
    # by flattening one level. This keeps correct behavior for ["a","b"] too.
    normalized: list[str] = []
    for it in items:
        if isinstance(it, (list, tuple)):
            for sub in it:
                normalized.append(sub)
        else:
            normalized.append(it)
    # Canonical (sorted) order, deduplicated to avoid self-deadlock
    canonical = sorted(set(normalized))
    acquired: list[tuple[str, threading.Lock]] = []
    for item in canonical:
        lock = _lock_for(item)
        lock.acquire()
        acquired.append((item, lock))
    return acquired

def release_all(acquired: list[tuple[str, threading.Lock]]) -> None:
    """Release previously acquired locks in reverse order."""
    for _, lock in reversed(acquired):
        lock.release()
