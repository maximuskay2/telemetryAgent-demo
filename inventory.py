import threading

_locks = {}
_locks_lock = threading.Lock()

def _get_lock(name):
    with _locks_lock:
        if name not in _locks:
            _locks[name] = threading.Lock()
        return _locks[name]

def acquire_all(names):
    # Acquire locks in canonical (sorted) order to prevent deadlock
    canonical = sorted(names)
    held = []
    for name in canonical:
        lock = _get_lock(name)
        lock.acquire()
        held.append((name, lock))
    return held

def release_all(held):
    for name, lock in reversed(held):
        try:
            lock.release()
        except RuntimeError:
            pass
