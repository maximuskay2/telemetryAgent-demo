import threading
import time
import inventory as solution
def test_round_trip():
    acq = solution.acquire_all(["b", "a"])
    assert [n for n, _ in acq] == ["a", "b"]
    # locks should be held
    assert not solution._lock_for("a").acquire(blocking=False)
    assert not solution._lock_for("b").acquire(blocking=False)
    solution.release_all(acq)
    # after release locks are free
    assert solution._lock_for("a").acquire(blocking=False)
    solution._lock_for("a").release()
    assert solution._lock_for("b").acquire(blocking=False)
    solution._lock_for("b").release()

def test_acquire_sorted_order():
    acq = solution.acquire_all(["z", "m", "a"])
    assert [n for n, _ in acq] == ["a", "m", "z"]
    solution.release_all(acq)
    acq2 = solution.acquire_all(["c", "b", "a"])
    assert [n for n, _ in acq2] == ["a", "b", "c"]
    solution.release_all(acq2)

def test_concurrent_overlapping_no_deadlock():
    barrier = threading.Barrier(2)
    results = []
    def worker(items):
        barrier.wait()
        acq = solution.acquire_all(items)
        time.sleep(0.02)
        solution.release_all(acq)
        results.append(True)
    t1 = threading.Thread(target=worker, args=(["a", "b"],))
    t2 = threading.Thread(target=worker, args=(["b", "a"],))
    t1.start()
    t2.start()
    t1.join(timeout=2)
    t2.join(timeout=2)
    assert not t1.is_alive(), "deadlock detected in t1"
    assert not t2.is_alive(), "deadlock detected in t2"
    assert len(results) == 2

def test_concurrent_three_way():
    barrier = threading.Barrier(3)
    results = []
    def worker(items):
        barrier.wait()
        acq = solution.acquire_all(items)
        time.sleep(0.01)
        solution.release_all(acq)
        results.append(True)
    threads = [
        threading.Thread(target=worker, args=(["x", "y", "z"],)),
        threading.Thread(target=worker, args=(["z", "x"],)),
        threading.Thread(target=worker, args=(["y", "z", "x"],)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=2)
    for t in threads:
        assert not t.is_alive(), "deadlock in 3-way test"
    assert len(results) == 3

def test_empty_and_single():
    acq = solution.acquire_all([])
    assert acq == []
    solution.release_all(acq)
    acq2 = solution.acquire_all(["single_item_test"])
    assert len(acq2) == 1 and acq2[0][0] == "single_item_test"
    solution.release_all(acq2)

def test_locks_are_same_object():
    acq1 = solution.acquire_all(["dup_check_a"])
    lock1 = acq1[0][1]
    solution.release_all(acq1)
    acq2 = solution.acquire_all(["dup_check_a"])
    lock2 = acq2[0][1]
    assert lock1 is lock2
    solution.release_all(acq2)

def test_stress_many_threads():
    barrier = threading.Barrier(10)
    results = []
    def worker():
        barrier.wait()
        for _ in range(20):
            items = ["stress1", "stress2", "stress3", "stress4"]
            acq = solution.acquire_all(list(reversed(items)))
            time.sleep(0.001)
            solution.release_all(acq)
        results.append(True)
    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
    for t in threads:
        assert not t.is_alive(), "deadlock in stress test"
    assert len(results) == 10
