import threading

import inventory as solution
def test_round_trip_sorted_order():
    acquired = solution.acquire_all(['charlie', 'alpha', 'bravo'])
    try:
        assert [item for item, _ in acquired] == ['alpha', 'bravo', 'charlie']
        assert all(lock.locked() for _, lock in acquired)
    finally:
        solution.release_all(acquired)
    assert all(not lock.locked() for _, lock in acquired)


def test_release_allows_reacquire():
    first = solution.acquire_all(['delta', 'echo'])
    solution.release_all(first)
    second = solution.acquire_all(['echo', 'delta'])
    try:
        assert [item for item, _ in second] == ['delta', 'echo']
    finally:
        solution.release_all(second)


def test_concurrent_overlapping_acquires_no_deadlock():
    errors = []

    def worker(items):
        try:
            for _ in range(30):
                acquired = solution.acquire_all(items)
                try:
                    assert all(lock.locked() for _, lock in acquired)
                finally:
                    solution.release_all(acquired)
        except Exception as exc:
            errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=(['shared-a', 'shared-b', 'shared-c'],)),
        threading.Thread(target=worker, args=(['shared-c', 'shared-b', 'shared-a'],)),
        threading.Thread(target=worker, args=(['shared-b', 'shared-a'],)),
        threading.Thread(target=worker, args=(['shared-c', 'shared-a'],)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    assert all(not t.is_alive() for t in threads), 'deadlock detected'
    assert not errors
