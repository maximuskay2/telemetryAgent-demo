import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from inventory import acquire_all, release_all


def test_acquire_all_uses_canonical_sorted_order():
    # Traceback: deadlock detected acquiring brake-pad after axle.
    # Caller passes brake-pad first, but canonical order must be axle first,
    # so concurrent transfers in opposite orders cannot deadlock.
    items = ['brake-pad', 'axle']
    acquired = acquire_all(items)
    try:
        acquired_items = [item for item, _ in acquired]
        assert acquired_items == sorted(items), (
            f'acquire_all must acquire in canonical sorted order to prevent deadlock; '
            f'expected {sorted(items)!r}, got {acquired_items!r}'
        )
    finally:
        release_all(acquired)


def test_acquire_all_opposite_orders_yield_same_acquisition_order():
    forward = ['axle', 'brake-pad', 'wheel']
    reverse = list(reversed(forward))
    acquired_reverse = acquire_all(reverse)
    try:
        reverse_order = [item for item, _ in acquired_reverse]
    finally:
        release_all(acquired_reverse)
    assert reverse_order == sorted(forward)
