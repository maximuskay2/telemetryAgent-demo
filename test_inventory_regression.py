import threading
import time
import inventory as solution
def test_round_trip():
    acq = solution.acquire_all(['b', 'a', 'c'])
    assert [k for k, _ in acq] == ['a', 'b', 'c']
    for _, lk in acq:
        assert not lk.acquire(blocking=False)
    solution.release_all(acq)
    for _, lk in acq:
        assert lk.acquire(blocking=False)
        lk.release()

def test_empty():
    acq = solution.acquire_all([])
    assert acq == []
    solution.release_all(acq)

def test_sorted_order_with_reverse_input():
    acq = solution.acquire_all(['z', 'm', 'a'])
    assert [k for k, _ in acq] == ['a', 'm', 'z']
    solution.release_all(acq)

def test_concurrent_overlapping_no_deadlock():
    errors = []
    barrier = threading.Barrier(2)
    def worker(items):
        try:
            barrier.wait(timeout=1)
            acq = solution.acquire_all(items)
            time.sleep(0.02)
            solution.release_all(acq)
        except Exception as e:
            errors.append(e)
    t1 = threading.Thread(target=worker, args=(['item2', 'item1'],))
    t2 = threading.Thread(target=worker, args=(['item1', 'item2'],))
    t1.start()
    t2.start()
    t1.join(timeout=2)
    t2.join(timeout=2)
    assert not t1.is_alive(), 'deadlock: t1 hung'
    assert not t2.is_alive(), 'deadlock: t2 hung'
    assert not errors, f'errors: {errors}'

def test_concurrent_three_way():
    errors = []
    def worker(items):
        try:
            for _ in range(30):
                acq = solution.acquire_all(items)
                time.sleep(0.001)
                solution.release_all(acq)
        except Exception as e:
            errors.append(e)
    threads = [
        threading.Thread(target=worker, args=(['a', 'b', 'c'],)),
        threading.Thread(target=worker, args=(['c', 'a'],)),
        threading.Thread(target=worker, args=(['b', 'c'],)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=3)
    for t in threads:
        assert not t.is_alive(), 'deadlock in 3-way'
    assert not errors

def test_release_allows_reacquire():
    acq1 = solution.acquire_all(['x', 'y'])
    solution.release_all(acq1)
    acq2 = solution.acquire_all(['y', 'x'])
    assert [k for k, _ in acq2] == ['x', 'y']
    solution.release_all(acq2)
