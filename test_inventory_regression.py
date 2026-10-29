import threading
import time
import inventory as solution
def test_round_trip():
    acquired = solution.acquire_all(["b", "a", "c"])
    try:
        assert [name for name, _ in acquired] == ["a", "b", "c"]
        assert len(acquired) == 3
        for _, lk in acquired:
            assert isinstance(lk, type(threading.Lock()))
    finally:
        solution.release_all(acquired)
    # after release locks must be free again
    reacquired = solution.acquire_all(["a"])
    try:
        assert [n for n, _ in reacquired] == ["a"]
    finally:
        solution.release_all(reacquired)


def test_canonical_order_despite_caller_order():
    a = solution.acquire_all(["zebra", "apple", "mango"])
    try:
        assert [n for n, _ in a] == sorted(["zebra", "apple", "mango"])
    finally:
        solution.release_all(a)


def test_empty_and_single():
    assert solution.acquire_all([]) == []
    solution.release_all([])
    s = solution.acquire_all(["only"])
    try:
        assert len(s) == 1 and s[0][0] == "only"
    finally:
        solution.release_all(s)


def test_concurrent_overlapping_acquires_no_deadlock():
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []
    def worker(items):
        try:
            barrier.wait(timeout=5)
            acquired = solution.acquire_all(items)
            try:
                time.sleep(0.02)
            finally:
                solution.release_all(acquired)
        except BaseException as e:
            errors.append(e)
    t1 = threading.Thread(target=worker, args=(["a", "b", "c"],))
    t2 = threading.Thread(target=worker, args=(["c", "b", "a"],))
    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)
    assert not t1.is_alive(), "deadlock: t1 did not finish"
    assert not t2.is_alive(), "deadlock: t2 did not finish"
    assert not errors, f"worker errors: {errors}"


def test_concurrent_stress_overlapping_subsets():
    item_sets = [
        ["a", "b"],
        ["b", "a"],
        ["b", "c"],
        ["c", "b", "a"],
        ["d", "a"],
        ["c", "d"],
    ]
    barrier = threading.Barrier(len(item_sets))
    errors: list[BaseException] = []
    def worker(items):
        try:
            barrier.wait(timeout=5)
            for _ in range(20):
                acquired = solution.acquire_all(items)
                try:
                    pass
                finally:
                    solution.release_all(acquired)
        except BaseException as e:
            errors.append(e)
    threads = [threading.Thread(target=worker, args=(s,)) for s in item_sets]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    for t in threads:
        assert not t.is_alive(), "deadlock in stress test"
    assert not errors
