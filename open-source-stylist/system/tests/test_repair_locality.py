"""Locality contract for the single-item repair stitch (E-011, METHODOLOGY §2.6).

The repair executor MUST change nothing outside the garment mask. These deterministic tests exercise
the stitch+measure path (no GPU): a no-op edit changes nothing; a hard-mask edit changes ONLY the
masked region (outside-mask change = 0) while the masked region really does change.
"""

import numpy as np

from system.repair.repair import stitch_and_measure


def _scene():
    base = np.tile(np.arange(80, dtype=np.uint8).reshape(1, 80, 1), (80, 1, 3))  # gradient
    fg = np.zeros((80, 80), bool)
    fg[30:50, 30:50] = True  # central garment region
    bbox = (20, 60, 20, 60)  # bbox with context around the mask
    return base, fg, bbox


def test_noop_edit_changes_nothing():
    base, fg, bbox = _scene()
    y0, y1, x0, x1 = bbox
    edited = base[y0:y1, x0:x1].copy()  # identical crop
    out, outside_pct = stitch_and_measure(base, fg, bbox, edited, feather=0.0)
    assert outside_pct == 0.0
    assert np.array_equal(out, base)


def test_hard_mask_edit_is_local():
    """A crop that differs EVERYWHERE, composited with a hard mask (feather=0), must change only
    the masked region — outside-mask change is exactly 0, and the masked region truly changes."""
    base, fg, bbox = _scene()
    y0, y1, x0, x1 = bbox
    edited = np.full((y1 - y0, x1 - x0, 3), 200, np.uint8)  # differs from the gradient everywhere
    out, outside_pct = stitch_and_measure(base, fg, bbox, edited, feather=0.0)
    assert outside_pct == 0.0                      # locality holds despite a full-crop edit
    assert (out[fg] != base[fg]).any()             # the garment region really changed
    assert np.array_equal(out[~fg], base[~fg])     # everything outside the mask is byte-identical
