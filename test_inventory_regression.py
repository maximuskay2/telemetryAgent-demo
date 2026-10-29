import threading
import time
import inventory as solution
def test_round_trip_canonical_order():
    items = ["zebra", "apple", "mango"]
    acquired = solution.acquire_all(items)
    try:
        # must be returned in canonical sorted order regardless of caller order
        assert [name for name, _ in acquired] == sorted(items)
        # all locks must be held: non-blocking acquire must fail
        for _, lk in acquired:
            assert not lk.acquire(blocking=False)
    finally:
        solution.release_all(acquired)
    # after release locks are free and reusable
    acquired2 = solution.acquire_all(["apple"])
    try:
        assert [n for n, _ in acquired2] == ["apple"]
    finally:
        solution.release_all(acquired2)


def test_empty_round_trip():
    acquired = solution.acquire_all([])
    assert acquired == []
    solution.release_all(acquired)


def test_single_item_round_trip():
    acquired = solution.acquire_all(["only"])
    try:
        assert len(acquired) == 1 and acquired[0][0] == "only"
    finally:
        solution.release_all(acquired)


def test_concurrent_overlapping_no_deadlock():
    a = ["item-A", "item-B"]
    b = ["item-B", "item-A"]
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def worker(items):
        try:
            barrier.wait(timeout=5)
            acq = solution.acquire_all(items)
            try:
                assert [n for n, _ in acq] == sorted(items)
                time.sleep(0.01)
            finally:
                solution.release_all(acq)
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    t1 = threading.Thread(target=worker, args=(a,))
    t2 = threading.Thread(target=worker, args=(b,))
    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)
    assert not t1.is_alive(), "deadlock: thread 1 still alive"
    assert not t2.is_alive(), "deadlock: thread 2 still alive"
    assert not errors, f"worker errors: {errors}"


def test_concurrent_many_threads_overlapping():
    item_sets = [
        ["inv-1", "inv-2", "inv-3"],
        ["inv-3", "inv-2", "inv-1"],
        ["inv-2", "inv-3", "inv-1"],
        ["inv-1", "inv-3"],
        ["inv-3", "inv-1", "inv-2"],
    ]
    barrier = threading.Barrier(len(item_sets))
    errors: list[BaseException] = []

    def worker(items):
        try:
            barrier.wait(timeout=5)
            for _ in range(20):
                acq = solution.acquire_all(items)
                try:
                    assert [n for n, _ in acq] == sorted(items)
                finally:
                    solution.release_all(acq)
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(s,)) for s in item_sets]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    for t in threads:
        assert not t.is_alive(), "deadlock: worker still alive"
    assert not errors, f"worker errors: {errors}"
