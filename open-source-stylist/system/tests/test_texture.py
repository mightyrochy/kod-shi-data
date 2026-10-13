"""Texture-fidelity gate contract (deterministic, no GPU).

A flattened (blurred) copy of a textured region must be flagged LOW_TEXTURE vs the textured reference;
an identical copy must not; a desaturated copy must be flagged FLAT_COLOUR.
"""

import cv2
import numpy as np

from system.gates.texture import compare_texture


def _textured(seed=0):
    rng = np.random.default_rng(seed)
    # a saturated, high-frequency colour patch (stand-in for woven fabric)
    base = rng.integers(0, 256, (200, 200, 3), dtype=np.uint8)
    return cv2.cvtColor(base, cv2.COLOR_RGB2BGR)


def test_identical_region_is_ok():
    ref = _textured()
    r = compare_texture(ref.copy(), ref)
    assert r["verdict"] == "OK"
    assert r["texture_ratio"] >= 0.95


def test_flattened_region_flags_low_texture():
    ref = _textured()
    flat = cv2.GaussianBlur(ref, (0, 0), 6.0)  # same colours, texture smoothed away
    r = compare_texture(flat, ref)
    assert "LOW_TEXTURE" in r["flags"]
    assert r["texture_ratio"] < 0.6


def test_desaturated_region_flags_flat_colour():
    ref = _textured()
    gray = cv2.cvtColor(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)  # kills chroma
    r = compare_texture(gray, ref)
    assert "FLAT_COLOUR" in r["flags"]
    assert r["chroma_ratio"] < 0.6
