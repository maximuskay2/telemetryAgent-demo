import threading
import time
import inventory as solution
def test_round_trip():
    acquired = solution.acquire_all(["apple", "banana"])
    try:
        assert [n for n, _ in acquired] == ["apple", "banana"]
        # locks must be held: non-blocking acquire should fail
        for _, lk in acquired:
            assert lk.acquire(blocking=False) is False
    finally:
        solution.release_all(acquired)
    # after release locks must be free and re-acquirable
    reacquired = solution.acquire_all(["banana", "apple"])
    try:
        assert [n for n, _ in reacquired] == ["apple", "banana"]
    finally:
        solution.release_all(reacquired)


def test_canonical_sorted_order():
    items = ["delta", "alpha", "charlie", "bravo"]
    acquired = solution.acquire_all(items)
    try:
        names = [n for n, _ in acquired]
        assert names == sorted(items)
    finally:
        solution.release_all(acquired)
    # empty and single-item edge cases
    assert solution.acquire_all([]) == []
    one = solution.acquire_all(["solo"])
    try:
        assert [n for n, _ in one] == ["solo"]
    finally:
        solution.release_all(one)


def test_concurrent_overlapping_no_deadlock():
    items_a = ["inv-a", "inv-b", "inv-c"]
    items_b = list(reversed(items_a))
    barrier = threading.Barrier(2)
    errors = []
    def worker(items):
        try:
            barrier.wait(timeout=5)
            acquired = solution.acquire_all(items)
            try:
                assert [n for n, _ in acquired] == sorted(items)
                time.sleep(0.005)
            finally:
                solution.release_all(acquired)
        except Exception as e:  # noqa: BLE001
            errors.append(e)
    for _ in range(20):
        barrier = threading.Barrier(2)
        errors.clear()
        t1 = threading.Thread(target=worker, args=(items_a,), daemon=True)
        t2 = threading.Thread(target=worker, args=(items_b,), daemon=True)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)
        assert not t1.is_alive(), "deadlock: thread1 stuck acquiring"
        assert not t2.is_alive(), "deadlock: thread2 stuck acquiring"
        assert not errors, f"worker errors: {errors}"


def test_concurrent_disjoint_and_overlap_roundtrip():
    # broader overlap: 4 threads with shuffled orders must all finish
    orders = [
        ["w", "x", "y", "z"],
        ["z", "y", "x", "w"],
        ["y", "w", "z", "x"],
        ["x", "z", "w", "y"],
    ]
    barrier = threading.Barrier(len(orders))
    errors = []
    def worker(items):
        try:
            barrier.wait(timeout=5)
            acq = solution.acquire_all(items)
            try:
                time.sleep(0.002)
            finally:
                solution.release_all(acq)
        except Exception as e:  # noqa: BLE001
            errors.append(e)
    threads = [threading.Thread(target=worker, args=(o,), daemon=True) for o in orders]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
    for t in threads:
        assert not t.is_alive(), "deadlock with shuffled overlapping acquires"
    assert not errors
