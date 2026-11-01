import inventory as solution
import threading
import time

def test_acquire_sorted_order():
    acq = solution.acquire_all(['c', 'a', 'b'])
    try:
        assert [name for name, _ in acq] == ['a', 'b', 'c']
    finally:
        solution.release_all(acq)

def test_round_trip_lock_held():
    acq = solution.acquire_all(['x', 'y'])
    try:
        lock_x = solution._lock_for('x')
        assert not lock_x.acquire(timeout=0)
    finally:
        solution.release_all(acq)
    acq2 = solution.acquire_all(['x'])
    try:
        assert len(acq2) == 1
        assert acq2[0][0] == 'x'
    finally:
        solution.release_all(acq2)

def test_release_reverse_order():
    acq = solution.acquire_all(['a', 'b', 'c'])
    try:
        assert len(acq) == 3
    finally:
        solution.release_all(acq)
    acq2 = solution.acquire_all(['a', 'b', 'c'])
    solution.release_all(acq2)

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
    t1 = threading.Thread(target=worker, args=(['item1', 'item2'],))
    t2 = threading.Thread(target=worker, args=(['item2', 'item1'],))
    t1.start()
    t2.start()
    t1.join(timeout=3)
    t2.join(timeout=3)
    assert not t1.is_alive(), 'deadlock t1 still alive'
    assert not t2.is_alive(), 'deadlock t2 still alive'
    assert not errors

def test_concurrent_three_way():
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
    t1 = threading.Thread(target=worker, args=(['a', 'b'],))
    t2 = threading.Thread(target=worker, args=(['b', 'c'],))
    t3 = threading.Thread(target=worker, args=(['c', 'a'],))
    for t in (t1, t2, t3):
        t.start()
    for t in (t1, t2, t3):
        t.join(timeout=3)
        assert not t.is_alive()
    assert not errors

def test_empty_list():
    acq = solution.acquire_all([])
    assert acq == []
    solution.release_all(acq)
