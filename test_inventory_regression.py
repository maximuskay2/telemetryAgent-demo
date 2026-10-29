import inventory as solution
import threading
import time

def test_round_trip_sorted():
    acquired = solution.acquire_all(['c', 'a', 'b'])
    try:
        names = [n for n, _ in acquired]
        assert names == ['a', 'b', 'c']
        assert len(acquired) == 3
    finally:
        solution.release_all(acquired)
    reacquired = solution.acquire_all(['x'])
    try:
        assert [n for n, _ in reacquired] == ['x']
    finally:
        solution.release_all(reacquired)
    empty = solution.acquire_all([])
    assert empty == []
    solution.release_all(empty)

def test_concurrent_overlapping_no_deadlock():
    barrier = threading.Barrier(2)
    errors = []
    def worker(items):
        try:
            barrier.wait(timeout=5)
            acq = solution.acquire_all(items)
            try:
                time.sleep(0.02)
            finally:
                solution.release_all(acq)
        except Exception as e:
            errors.append(e)
    t1 = threading.Thread(target=worker, args=(['itemA', 'itemB'],))
    t2 = threading.Thread(target=worker, args=(['itemB', 'itemA'],))
    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)
    assert not t1.is_alive()
    assert not t2.is_alive()
    assert errors == []

def test_many_threads_overlapping():
    item_sets = [['i1', 'i2', 'i3'], ['i3', 'i2', 'i1'], ['i2', 'i3'], ['i1', 'i3']]
    errors = []
    def worker(items):
        try:
            for _ in range(20):
                acq = solution.acquire_all(items)
                try:
                    pass
                finally:
                    solution.release_all(acq)
        except Exception as e:
            errors.append(e)
    threads = [threading.Thread(target=worker, args=(s,)) for s in item_sets]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
        assert not t.is_alive()
    assert errors == []
