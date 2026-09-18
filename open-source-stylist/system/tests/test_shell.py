"""Tests for the deterministic restoration shell (color_match, background_restore)."""

import cv2
import numpy as np

from system.shell.background_restore import restore_background
from system.shell.color_match import correct_region


def _lab_stats(bgr, mask):
    lab = cv2.cvtColor(bgr.astype(np.float32) / 255.0, cv2.COLOR_BGR2LAB)
    px = lab[mask > 127]
    return px.mean(axis=0), px.std(axis=0)


def test_color_match_shifts_mean_preserves_texture():
    """Mean moves toward the reference; per-pixel variance (texture) is preserved."""
    rng = np.random.default_rng(0)
    image = rng.integers(70, 130, size=(48, 48, 3)).astype(np.uint8)  # textured region
    ref = np.full((48, 48, 3), (40, 90, 170), dtype=np.uint8)         # different mean color
    mask = np.full((48, 48), 255, dtype=np.uint8)

    mean_in, std_in = _lab_stats(image, mask)
    ref_mean, _ = _lab_stats(ref, mask)

    out = correct_region(image, mask, ref, mask, max_shift=(60, 60, 60))
    mean_out, std_out = _lab_stats(out, mask)

    assert np.all(np.abs(mean_out - ref_mean) < np.abs(mean_in - ref_mean))  # moved toward ref
    assert np.allclose(mean_out, ref_mean, atol=3.0)                          # reaches it (large cap)
    assert np.allclose(std_out, std_in, rtol=0.20, atol=1.5)                  # texture preserved


def test_color_match_bounded_by_max_shift():
    """A far reference cannot pull the region further than max_shift."""
    image = np.full((32, 32, 3), 50, dtype=np.uint8)
    ref = np.full((32, 32, 3), 200, dtype=np.uint8)
    mask = np.full((32, 32), 255, dtype=np.uint8)

    mean_in, _ = _lab_stats(image, mask)
    out = correct_region(image, mask, ref, mask, max_shift=(5, 5, 5))
    mean_out, _ = _lab_stats(out, mask)

    assert mean_out[0] > mean_in[0]                       # moved toward brighter ref
    assert (mean_out[0] - mean_in[0]) <= 5.0 + 1.0        # capped (+ quantization slack)


def test_color_match_empty_mask_fails_loud():
    image = np.full((16, 16, 3), 80, dtype=np.uint8)
    empty = np.zeros((16, 16), dtype=np.uint8)
    full = np.full((16, 16), 255, dtype=np.uint8)
    import pytest

    with pytest.raises(ValueError, match="mask is empty"):
        correct_region(image, empty, image, full)


def test_background_restore_keeps_original_outside_and_generated_inside():
    gen = np.full((20, 20, 3), 200, dtype=np.uint8)
    orig = np.full((20, 20, 3), 50, dtype=np.uint8)
    person = np.zeros((20, 20), dtype=np.uint8)
    person[5:15, 5:15] = 255

    out = restore_background(gen, orig, person)

    m = person > 127
    assert np.all(out[m] == 200)   # inside person = generated
    assert np.all(out[~m] == 50)   # outside person = original
