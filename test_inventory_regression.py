import threading
import time
import inventory as solution
def test_round_trip():
    acq = solution.acquire_all(["b", "a", "c"])
    assert [name for name, _ in acq] == ["a", "b", "c"]
    solution.release_all(acq)
    acq2 = solution.acquire_all(["a"])
    assert len(acq2) == 1
    solution.release_all(acq2)

def test_canonical_order():
    acq = solution.acquire_all(["z", "m", "a"])
    names = [n for n, _ in acq]
    assert names == sorted(names)
    solution.release_all(acq)

def test_empty():
    acq = solution.acquire_all([])
    assert acq == []
    solution.release_all(acq)

def test_concurrent_overlapping_no_deadlock():
    barrier = threading.Barrier(2)
    errors = []
    def worker(items):
        try:
            barrier.wait(timeout=2)
            acq = solution.acquire_all(items)
            time.sleep(0.05)
            solution.release_all(acq)
        except Exception as e:
            errors.append(e)
    t1 = threading.Thread(target=worker, args=(["item1", "item2"],))
    t2 = threading.Thread(target=worker, args=(["item2", "item1"],))
    t1.start()
    t2.start()
    t1.join(timeout=2)
    t2.join(timeout=2)
    assert not t1.is_alive(), "deadlock detected: t1 still alive (caller-order bug)"
    assert not t2.is_alive(), "deadlock detected: t2 still alive"
    assert not errors, f"unexpected errors: {errors}"

def test_concurrent_three_way_overlap():
    barrier = threading.Barrier(3)
    errors = []
    def worker(items):
        try:
            barrier.wait(timeout=2)
            acq = solution.acquire_all(items)
            time.sleep(0.02)
            solution.release_all(acq)
        except Exception as e:
            errors.append(e)
    threads = [
        threading.Thread(target=worker, args=(["A", "B", "C"],)),
        threading.Thread(target=worker, args=(["C", "B", "A"],)),
        threading.Thread(target=worker, args=(["B", "C", "A"],)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=3)
        assert not t.is_alive(), "deadlock in 3-way overlapping acquire"
    assert not errors, f"unexpected errors: {errors}"

def test_nested_input_compatibility():
    acq = solution.acquire_all([["x", "y"]])
    assert [n for n, _ in acq] == ["x", "y"]
    solution.release_all(acq)
