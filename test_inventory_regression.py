import threading
import time
import inventory as solution
def test_round_trip_sorted_order():
    acquired = solution.acquire_all(['zebra', 'apple', 'mango'])
    try:
        assert [name for name, _ in acquired] == ['apple', 'mango', 'zebra']
        for _, lock in acquired:
            assert lock.locked()
    finally:
        solution.release_all(acquired)
    for _, lock in acquired:
        assert not lock.locked()

def test_empty():
    acquired = solution.acquire_all([])
    assert acquired == []
    solution.release_all(acquired)

def test_single_item():
    acquired = solution.acquire_all(['solo'])
    try:
        assert len(acquired) == 1
        assert acquired[0][0] == 'solo'
    finally:
        solution.release_all(acquired)

def test_concurrent_overlapping_no_deadlock():
    barrier = threading.Barrier(2)
    results = []
    errors = []
    def worker(items):
        try:
            barrier.wait(timeout=2)
            acq = solution.acquire_all(items)
            time.sleep(0.02)
            solution.release_all(acq)
            results.append(True)
        except Exception as e:
            errors.append(e)
    t1 = threading.Thread(target=worker, args=(['B', 'A'],))
    t2 = threading.Thread(target=worker, args=(['A', 'B'],))
    t1.start()
    t2.start()
    t1.join(timeout=3)
    t2.join(timeout=3)
    assert not t1.is_alive(), 't1 deadlocked'
    assert not t2.is_alive(), 't2 deadlocked'
    assert not errors
    assert len(results) == 2

def test_concurrent_three_way():
    items_list = [
        ['c', 'b', 'a'],
        ['a', 'c'],
        ['b', 'a'],
        ['c', 'a', 'b'],
    ]
    barrier = threading.Barrier(len(items_list))
    done = []
    def worker(items):
        barrier.wait(timeout=2)
        for _ in range(5):
            acq = solution.acquire_all(items)
            time.sleep(0.01)
            solution.release_all(acq)
        done.append(1)
    threads = [threading.Thread(target=worker, args=(it,)) for it in items_list]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
        assert not t.is_alive(), 'deadlock detected in three-way test'
    assert len(done) == len(items_list)

def test_release_all_reverse_order_releases():
    acq = solution.acquire_all(['x', 'y'])
    locks = [l for _, l in acq]
    solution.release_all(acq)
    for l in locks:
        assert not l.locked()
        assert l.acquire(blocking=False)
        l.release()
