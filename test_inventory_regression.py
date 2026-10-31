import threading
import time
import inventory as solution
def test_round_trip_canonical_order():
    acquired = solution.acquire_all(["c", "a", "b"])
    try:
        names = [name for name, _ in acquired]
        assert names == sorted(["c", "a", "b"]), f"expected sorted order {sorted(['c','a','b'])} got {names}"
        # locks should be held - try non-blocking acquire should fail
        for _, lock in acquired:
            assert not lock.acquire(blocking=False), "lock should be held"
    finally:
        solution.release_all(acquired)
    # after release locks should be free
    for name in ["a","b","c"]:
        l = solution._lock_for(name)
        assert l.acquire(blocking=False)
        l.release()

def test_release_reverse_and_reacquire():
    a1 = solution.acquire_all(["a"])
    solution.release_all(a1)
    a2 = solution.acquire_all(["a", "b"])
    solution.release_all(a2)
    a3 = solution.acquire_all(["b", "a"])
    names = [n for n,_ in a3]
    assert names == ["a","b"]
    solution.release_all(a3)

def test_concurrent_overlapping_no_deadlock():
    barrier = threading.Barrier(2)
    errors = []
    results = []
    def worker(items):
        try:
            barrier.wait(timeout=2)
            acquired = solution.acquire_all(items)
            try:
                names = [n for n,_ in acquired]
                # must be in canonical sorted order
                assert names == sorted(items), f"not canonical: {names} vs {sorted(items)}"
                time.sleep(0.02)
                results.append(True)
            finally:
                solution.release_all(acquired)
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=worker, args=(["b", "a"],))
    t2 = threading.Thread(target=worker, args=(["a", "b"],))
    t1.start()
    t2.start()
    t1.join(timeout=3)
    t2.join(timeout=3)
    assert not t1.is_alive(), "deadlock detected: t1 still alive"
    assert not t2.is_alive(), "deadlock detected: t2 still alive"
    assert not errors, f"errors in threads: {errors}"
    assert len(results) == 2

def test_concurrent_three_way_overlap():
    barrier = threading.Barrier(3)
    results = []
    def worker(items):
        barrier.wait(timeout=2)
        acq = solution.acquire_all(items)
        time.sleep(0.02)
        solution.release_all(acq)
        results.append(1)
    threads = [
        threading.Thread(target=worker, args=(["a","b","c"],)),
        threading.Thread(target=worker, args=(["c","a"],)),
        threading.Thread(target=worker, args=(["b","c"],)),
    ]
    for t in threads: t.start()
    for t in threads: t.join(timeout=3)
    for t in threads: assert not t.is_alive(), "deadlock in 3-way test"
    assert len(results) == 3

def test_empty():
    acq = solution.acquire_all([])
    assert acq == []
    solution.release_all(acq)
