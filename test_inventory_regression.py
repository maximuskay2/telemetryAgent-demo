import threading
import time
import inventory as solution
def test_round_trip_single():
    acq = solution.acquire_all(["a"])
    assert len(acq) == 1
    assert acq[0][0] == "a"
    solution.release_all(acq)
    # reacquire should succeed immediately
    acq2 = solution.acquire_all(["a"])
    assert acq2[0][0] == "a"
    solution.release_all(acq2)

def test_canonical_sorted_order():
    acq = solution.acquire_all(["c", "a", "b"])
    assert [k for k, _ in acq] == ["a", "b", "c"]
    # each tuple second element is a Lock
    for _, lk in acq:
        assert isinstance(lk, type(threading.Lock()))
    solution.release_all(acq)

def test_empty_list():
    acq = solution.acquire_all([])
    assert acq == []
    solution.release_all(acq)

def test_release_reverse_and_reacquire():
    acq = solution.acquire_all(["x", "y", "z"])
    assert [k for k,_ in acq] == ["x", "y", "z"]
    solution.release_all(acq)
    acq2 = solution.acquire_all(["z", "y", "x"])
    assert [k for k,_ in acq2] == ["x", "y", "z"]
    solution.release_all(acq2)

def test_concurrent_overlapping_no_deadlock():
    barrier = threading.Barrier(2)
    errors = []
    def worker(items):
        try:
            barrier.wait(timeout=2)
            acq = solution.acquire_all(items)
            try:
                time.sleep(0.05)
                assert len(acq) == len(items)
            finally:
                solution.release_all(acq)
        except Exception as e:
            errors.append(e)
    t1 = threading.Thread(target=worker, args=(["item1", "item2"],))
    t2 = threading.Thread(target=worker, args=(["item2", "item1"],))
    t1.start()
    t2.start()
    t1.join(timeout=2)
    t2.join(timeout=2)
    assert not t1.is_alive(), "deadlock detected in t1"
    assert not t2.is_alive(), "deadlock detected in t2"
    assert not errors, f"errors: {errors}"

def test_concurrent_many_threads_no_deadlock():
    # stress with 5 threads overlapping on same items in different orders
    items_sets = [
        ["a", "b", "c"],
        ["c", "a", "b"],
        ["b", "c", "a"],
        ["a", "c"],
        ["b", "a"],
    ]
    barrier = threading.Barrier(len(items_sets))
    errors = []
    def worker(items):
        try:
            barrier.wait(timeout=2)
            for _ in range(5):
                acq = solution.acquire_all(items)
                time.sleep(0.01)
                solution.release_all(acq)
        except Exception as e:
            errors.append(e)
    threads = [threading.Thread(target=worker, args=(s,)) for s in items_sets]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
    for t in threads:
        assert not t.is_alive(), "deadlock in many-thread test"
    assert not errors, f"errors: {errors}"

def test_lock_identity_shared():
    acq1 = solution.acquire_all(["shared1", "shared2"])
    # while held, another thread should block, not create new lock
    # release and reacquire should give same lock objects
    locks1 = {k: id(lk) for k, lk in acq1}
    solution.release_all(acq1)
    acq2 = solution.acquire_all(["shared2", "shared1"])
    locks2 = {k: id(lk) for k, lk in acq2}
    assert locks1 == locks2
    assert [k for k,_ in acq2] == sorted(["shared1","shared2"])
    solution.release_all(acq2)
