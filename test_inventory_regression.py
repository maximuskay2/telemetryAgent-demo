import threading
import time
import inventory as solution
def test_round_trip():
    items = ['b', 'a', 'c']
    acquired = solution.acquire_all(items)
    try:
        names = [n for n, _ in acquired]
        assert names == sorted(items)
        for _, lk in acquired:
            assert not lk.acquire(blocking=False)
    finally:
        solution.release_all(acquired)
    acq2 = solution.acquire_all(['a'])
    solution.release_all(acq2)

def test_empty():
    acq = solution.acquire_all([])
    assert acq == []
    solution.release_all(acq)

def test_canonical_order():
    acq = solution.acquire_all(['z', 'm', 'a'])
    try:
        assert [n for n, _ in acq] == ['a', 'm', 'z']
    finally:
        solution.release_all(acq)

def test_concurrent_overlapping_no_deadlock():
    errors = []
    def worker(items, iters):
        try:
            for _ in range(iters):
                acq = solution.acquire_all(items)
                try:
                    time.sleep(0.001)
                finally:
                    solution.release_all(acq)
        except Exception as e:
            errors.append(e)
    t1 = threading.Thread(target=worker, args=(['a', 'b', 'c'], 50))
    t2 = threading.Thread(target=worker, args=(['c', 'b', 'a'], 50))
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)
    assert not t1.is_alive()
    assert not t2.is_alive()
    assert not errors

def test_many_threads_stress():
    errors = []
    sets = [['a', 'b'], ['b', 'a'], ['b', 'c'], ['c', 'b'], ['a', 'c'], ['c', 'a']]
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
    threads = [threading.Thread(target=worker, args=(s,)) for s in sets]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
        assert not t.is_alive()
    assert not errors
