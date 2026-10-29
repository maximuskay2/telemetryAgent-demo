import threading
import time
import inventory as solution
def test_round_trip():
    acquired = solution.acquire_all(["apple", "banana"])
    assert [n for n, _ in acquired] == ["apple", "banana"]
    # locks should be held: second non-blocking acquire must fail
    for _, lk in acquired:
        assert not lk.acquire(blocking=False)
    solution.release_all(acquired)
    # after release, locks are free again
    reacquired = solution.acquire_all(["apple", "banana"])
    assert len(reacquired) == 2
    solution.release_all(reacquired)


def test_canonical_sorted_order():
    acquired = solution.acquire_all(["c", "a", "b"])
    try:
        names = [n for n, _ in acquired]
        assert names == sorted(names) == ["a", "b", "c"]
    finally:
        solution.release_all(acquired)


def test_empty():
    acquired = solution.acquire_all([])
    assert acquired == []
    solution.release_all(acquired)


def test_concurrent_overlapping_no_deadlock():
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []
    def worker(items):
        try:
            barrier.wait(timeout=5)
            acq = solution.acquire_all(items)
            try:
                time.sleep(0.02)
            finally:
                solution.release_all(acq)
        except BaseException as e:
            errors.append(e)
    t1 = threading.Thread(target=worker, args=(["a", "b"],))
    t2 = threading.Thread(target=worker, args=(["b", "a"],))
    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)
    assert not t1.is_alive(), "deadlock: t1 still alive"
    assert not t2.is_alive(), "deadlock: t2 still alive"
    assert not errors


def test_concurrent_many_overlapping():
    item_sets = [
        ["a", "b", "c"],
        ["c", "b", "a"],
        ["b", "c", "d"],
        ["d", "a", "b"],
        ["c", "d", "a"],
    ]
    barrier = threading.Barrier(len(item_sets))
    errors: list[BaseException] = []
    def worker(items):
        try:
            barrier.wait(timeout=5)
            for _ in range(20):
                acq = solution.acquire_all(items)
                try:
                    pass
                finally:
                    solution.release_all(acq)
        except BaseException as e:
            errors.append(e)
    threads = [threading.Thread(target=worker, args=(s,)) for s in item_sets]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    for t in threads:
        assert not t.is_alive(), "deadlock with many threads"
    assert not errors
