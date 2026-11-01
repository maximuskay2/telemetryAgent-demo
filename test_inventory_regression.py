import threading
import time
import inventory as solution
def test_acquire_all_sorted_order():
    with solution._registry_guard:
        solution._locks.clear()
    items = ['shock', 'sprocket', 'gasket']
    acq = solution.acquire_all(items)
    try:
        names = [n for n, _ in acq]
        assert names == sorted(items), f'expected sorted order got {names}'
        assert len(acq) == len(items)
    finally:
        solution.release_all(acq)

def test_round_trip_acquire_release():
    with solution._registry_guard:
        solution._locks.clear()
    acq = solution.acquire_all(['a', 'b'])
    try:
        assert len(acq) == 2
        for _, lk in acq:
            assert not lk.acquire(blocking=False)
        assert [n for n,_ in acq] == ['a', 'b']
    finally:
        solution.release_all(acq)
    for _, lk in acq:
        got = lk.acquire(blocking=False)
        assert got, 'lock should be free after release'
        lk.release()

def test_concurrent_overlapping_no_deadlock():
    with solution._registry_guard:
        solution._locks.clear()
    barrier = threading.Barrier(2)
    results = []
    errors = []
    def worker(items):
        try:
            barrier.wait(timeout=2)
            acq = solution.acquire_all(items)
            time.sleep(0.05)
            solution.release_all(acq)
            results.append(True)
        except Exception as e:
            errors.append(e)
    t1 = threading.Thread(target=worker, args=(['sprocket', 'gasket'],))
    t2 = threading.Thread(target=worker, args=(['gasket', 'sprocket'],))
    t1.start()
    t2.start()
    t1.join(timeout=3)
    t2.join(timeout=3)
    assert not t1.is_alive(), 'deadlock detected in t1'
    assert not t2.is_alive(), 'deadlock detected in t2'
    assert len(results) == 2, f'both workers should complete, got {results} errors {errors}'
    assert not errors

def test_concurrent_three_way_overlap():
    with solution._registry_guard:
        solution._locks.clear()
    barrier = threading.Barrier(3)
    results = []
    def worker(items):
        barrier.wait(timeout=2)
        acq = solution.acquire_all(items)
        time.sleep(0.02)
        solution.release_all(acq)
        results.append(1)
    threads = [
        threading.Thread(target=worker, args=(['sprocket', 'gasket', 'shock'],)),
        threading.Thread(target=worker, args=(['gasket', 'shock', 'sprocket'],)),
        threading.Thread(target=worker, args=(['shock', 'sprocket', 'gasket'],)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=3)
        assert not t.is_alive(), 'deadlock in 3-way test'
    assert len(results) == 3

def test_empty_and_single_item():
    with solution._registry_guard:
        solution._locks.clear()
    acq = solution.acquire_all([])
    assert acq == []
    solution.release_all(acq)
    acq = solution.acquire_all(['single'])
    try:
        assert len(acq) == 1
        assert acq[0][0] == 'single'
    finally:
        solution.release_all(acq)
