import threading, time
import inventory as solution
def test_round_trip_sorted():
    acq = solution.acquire_all(["b", "a"])
    try:
        assert [k for k,_ in acq] == ["a", "b"]
        assert len(acq) == 2
    finally:
        solution.release_all(acq)
    # empty case
    acq2 = solution.acquire_all([])
    assert acq2 == []
    solution.release_all(acq2)

def test_concurrent_overlapping_no_deadlock():
    results = []
    def worker(items):
        acq = solution.acquire_all(items)
        try:
            time.sleep(0.03)
            results.append(1)
        finally:
            solution.release_all(acq)
    t1 = threading.Thread(target=worker, args=(["a", "b"],))
    t2 = threading.Thread(target=worker, args=(["b", "a"],))
    t1.start()
    t2.start()
    t1.join(timeout=2.0)
    t2.join(timeout=2.0)
    assert not t1.is_alive(), "deadlock detected"
    assert not t2.is_alive(), "deadlock detected"
    assert len(results) == 2

def test_concurrent_three_way():
    barrier = threading.Barrier(3)
    done = []
    def worker(items):
        barrier.wait(timeout=2)
        acq = solution.acquire_all(items)
        try:
            time.sleep(0.02)
            done.append(1)
        finally:
            solution.release_all(acq)
    threads = [
        threading.Thread(target=worker, args=(["c","a","b"],)),
        threading.Thread(target=worker, args=(["b","c","a"],)),
        threading.Thread(target=worker, args=(["a","b","c"],)),
    ]
    for t in threads: t.start()
    for t in threads: t.join(timeout=2.0)
    for t in threads: assert not t.is_alive()
    assert len(done) == 3
