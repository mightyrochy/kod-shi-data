"""Integration FAIL tests for mask sanity guard (system/segmentation/sanity.py).

Each test: one known-bad synthetic mask through the full check path → asserts
that at least one SanityFlag is raised and the correct check name fires.

Per METHODOLOGY §2 p.6: tests exercise the full measurement path from inputs
to verdict.  All inputs are synthetic numpy arrays — no file I/O needed.

To run from project root:
    python -m pytest system/tests/test_segmentation_fail.py -v
"""

import numpy as np
import pytest

from system.segmentation.sanity import check, SanityResult


def _blank(h: int, w: int) -> np.ndarray:
    return np.zeros((h, w), dtype=np.uint8)


def _rect(h: int, w: int, r0: int, r1: int, c0: int, c1: int) -> np.ndarray:
    m = _blank(h, w)
    m[r0:r1, c0:c1] = 255
    return m


# ---------------------------------------------------------------------------
# 1. Shoes mask placed in the top of the image → position prior violation
# ---------------------------------------------------------------------------

def test_sanity_shoes_wrong_position_flags():
    """Shoes mask centered near the top of the image must trigger position_prior flag."""
    H, W = 200, 100
    # Place shoes in the top 10% of the image (centroid y ≈ 0.05) — wrong vertical band
    mask = _rect(H, W, r0=0, r1=20, c0=30, c1=70)  # centroid row ~10, y_frac=0.05

    result = check(mask, "shoes")

    assert not result.clean, "Expected at least one flag on shoes mask at top of image"
    check_names = {f.check for f in result.flags}
    assert "position_prior" in check_names, (
        f"Expected 'position_prior' flag; got: {check_names}. "
        f"Flags: {result.flags}"
    )


# ---------------------------------------------------------------------------
# 2. Shoes mask covering 60% of the image → area fraction violation
# ---------------------------------------------------------------------------

def test_sanity_shoes_oversized_flags():
    """Shoes mask covering 60% of the image must trigger area_fraction flag."""
    H, W = 200, 100
    # Fill 60% of image with 'shoes' — impossible for footwear (bound is [0.001, 0.15])
    mask = _rect(H, W, r0=20, r1=140, c0=0, c1=100)  # 120×100 = 12000/20000 = 60%

    result = check(mask, "shoes")

    assert not result.clean, "Expected at least one flag on oversized shoes mask"
    check_names = {f.check for f in result.flags}
    assert "area_fraction" in check_names, (
        f"Expected 'area_fraction' flag; got: {check_names}. "
        f"Flags: {result.flags}"
    )


# ---------------------------------------------------------------------------
# 3. Garment mask with no overlap with person mask → containment violation
# ---------------------------------------------------------------------------

def test_sanity_top_outside_person_flags():
    """Top mask placed entirely outside the person mask must trigger containment flag."""
    H, W = 200, 100

    # Person occupies the right half; top occupies the left half — zero overlap
    person = _rect(H, W, r0=0, r1=H, c0=50, c1=100)
    top    = _rect(H, W, r0=40, r1=120, c0=0, c1=50)  # centroid row ~80, y_frac=0.40

    result = check(top, "top", person_mask=person)

    assert not result.clean, "Expected at least one flag on top mask outside person"
    check_names = {f.check for f in result.flags}
    assert "containment" in check_names, (
        f"Expected 'containment' flag; got: {check_names}. "
        f"Flags: {result.flags}"
    )


# ---------------------------------------------------------------------------
# 4. Entirely empty mask → empty flag
# ---------------------------------------------------------------------------

def test_sanity_empty_mask_flags():
    """An all-zero mask must trigger the 'empty' flag regardless of region."""
    mask = _blank(200, 100)

    result = check(mask, "top")

    assert not result.clean, "Expected 'empty' flag on all-zero mask"
    check_names = {f.check for f in result.flags}
    assert "empty" in check_names, (
        f"Expected 'empty' flag; got: {check_names}"
    )


# ---------------------------------------------------------------------------
# 5. Positive control — clean mask raises no flags
# ---------------------------------------------------------------------------

def test_sanity_valid_shoes_passes():
    """Shoes mask in the correct position and size must produce no flags."""
    H, W = 200, 100
    # Shoes: small mask in the bottom 10% (rows 180–200), ~10% width
    # area frac = 20*30 / (200*100) = 600/20000 = 3% → within [0.001, 0.15]
    # centroid y = (180+200)/2 / 200 = 190/200 = 0.95 → within [0.55, 1.0]
    mask = _rect(H, W, r0=180, r1=200, c0=35, c1=65)

    result = check(mask, "shoes")

    assert result.clean, (
        f"Expected no flags on valid shoes mask; got: {result.flags}"
    )
