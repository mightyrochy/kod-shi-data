"""FAIL test for _largest_area_mask (grounded_sam.py — instance selection).

Per METHODOLOGY §2 p.6: one known-FAIL case that exercises the full measurement
path from inputs to verdict. The "failure mode" being tested is the old
ImpactFlattenMask union behavior — the test asserts that _largest_area_mask
returns ONLY the largest component, not the union of all components.

The FAIL assertion: if union behavior were returned, selected_area == union_area
(small_area + large_area). The fix must give selected_area == large_area.

To run from project root:
    python -m pytest system/tests/test_instance_selection_fail.py -v
"""

import cv2
import numpy as np
import pytest

from system.segmentation.grounded_sam import _largest_area_mask


def _encode_mask(arr: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".png", arr)
    assert ok, "cv2.imencode failed in test helper"
    return encoded.tobytes()


def _decode_mask(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)


# ---------------------------------------------------------------------------
# FAIL test: two disjoint components — must return the large one, not the union
# ---------------------------------------------------------------------------

def test_instance_selection_picks_largest_not_union():
    """_largest_area_mask must return the single largest connected component.

    Old behavior (ImpactFlattenMask union): returns all foreground pixels from
    every detected instance → area == small_area + large_area.

    Required behavior (this fix): returns only the largest component →
    area == large_area.

    A union-returning implementation would fail the strict equality below.
    """
    H, W = 200, 200

    # Two disjoint rectangles: small (top-left) and large (center block).
    union_mask = np.zeros((H, W), dtype=np.uint8)
    union_mask[0:10, 0:10] = 255       # small: 100 px, top-left corner
    union_mask[60:160, 60:160] = 255   # large: 10 000 px, center

    small_area = 100
    large_area = 10_000
    union_area = small_area + large_area

    result_bytes = _largest_area_mask(_encode_mask(union_mask))
    result = _decode_mask(result_bytes)

    selected_area = int((result > 128).sum())

    assert selected_area == large_area, (
        f"Expected largest component ({large_area} px), got {selected_area} px. "
        f"Union area would be {union_area} px — indicates union behavior instead of selection."
    )


# ---------------------------------------------------------------------------
# Positive control: single component passes through unchanged
# ---------------------------------------------------------------------------

def test_instance_selection_single_component_unchanged():
    """Single-component mask must be returned as-is (no area lost)."""
    H, W = 100, 100
    mask = np.zeros((H, W), dtype=np.uint8)
    mask[20:80, 20:80] = 255  # one component, 3600 px

    result_bytes = _largest_area_mask(_encode_mask(mask))
    result = _decode_mask(result_bytes)

    assert int((result > 128).sum()) == 3600


# ---------------------------------------------------------------------------
# Empty mask: returns input bytes unchanged (no crash)
# ---------------------------------------------------------------------------

def test_instance_selection_empty_mask_no_crash():
    """All-zero mask must not raise and must return an all-zero mask."""
    empty = np.zeros((100, 100), dtype=np.uint8)
    result_bytes = _largest_area_mask(_encode_mask(empty))
    result = _decode_mask(result_bytes)
    assert int((result > 128).sum()) == 0
