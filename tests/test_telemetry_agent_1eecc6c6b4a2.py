from inventory import acquire_all, release_all

def test_acquire_all_uses_canonical_order():
    held = acquire_all(["brake-pad", "axle"])
    try:
        assert [name for name, _ in held] == ["axle", "brake-pad"]
    finally:
        release_all(held)

def test_acquire_all_canonical_order_multiple():
    held = acquire_all(["widget", "axle", "brake-pad"])
    try:
        assert [name for name, _ in held] == sorted(["widget", "axle", "brake-pad"])
    finally:
        release_all(held)
