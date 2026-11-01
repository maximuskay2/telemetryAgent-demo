import threading
import time
import random
import inventory as solution
def test_round_trip():
    acquired = solution.acquire_all(['b','a'])
    try:
        assert [n for n,_ in acquired] == ['a','b']
        for _, lk in acquired:
            assert not lk.acquire(blocking=False)
    finally:
        solution.release_all(acquired)
    acquired2 = solution.acquire_all(['a'])
    try:
        assert len(acquired2) == 1
    finally:
        solution.release_all(acquired2)

def test_acquire_empty():
    acquired = solution.acquire_all([])
    assert acquired == []
    solution.release_all(acquired)

def test_acquisition_order_sorted():
    items = ['z','m','a','k']
    acq = solution.acquire_all(items)
    try:
        assert [n for n,_ in acq] == sorted(set(items))
    finally:
        solution.release_all(acq)

def test_concurrent_overlapping_no_deadlock():
    barrier = threading.Barrier(2)
    items1 = ['itemB','itemA']
    items2 = ['itemA','itemB']
    errors = []
    def worker(items):
        try:
            barrier.wait(timeout=2)
            acq = solution.acquire_all(items)
            try:
                time.sleep(0.02)
            finally:
                solution.release_all(acq)
        except Exception as e:
            errors.append(e)
    t1 = threading.Thread(target=worker, args=(items1,))
    t2 = threading.Thread(target=worker, args=(items2,))
    t1.start()
    t2.start()
    t1.join(timeout=3)
    t2.join(timeout=3)
    assert not t1.is_alive(), 'deadlock detected: t1 still alive'
    assert not t2.is_alive(), 'deadlock detected: t2 still alive'
    assert not errors

def test_concurrent_many_no_deadlock():
    item_pool = [f'res{i}' for i in range(5)]
    def worker():
        for _ in range(50):
            items = random.sample(item_pool, k=3)
            if random.random() < 0.5:
                items = list(reversed(items))
            acq = solution.acquire_all(items)
            try:
                time.sleep(0.001)
            finally:
                solution.release_all(acq)
    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
        assert not t.is_alive(), 'deadlock in stress test'

def test_release_reverse_order():
    items = ['x','y','z']
    acq = solution.acquire_all(items)
    assert [n for n,_ in acq] == sorted(items)
    solution.release_all(acq)
    acq2 = solution.acquire_all(list(reversed(items)))
    try:
        assert [n for n,_ in acq2] == sorted(items)
    finally:
        solution.release_all(acq2)
