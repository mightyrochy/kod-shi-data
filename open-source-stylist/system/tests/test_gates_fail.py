"""Integration FAIL tests for each gate.

Each test: one known-FAIL input through the full measurement path → asserts FAIL verdict.
Standard practice per METHODOLOGY §2.

To run from project root:
    python -m pytest system/tests/test_gates_fail.py -v

Note: test_identity_gate_fail requires insightface models downloaded (~300MB first run).
"""

from pathlib import Path

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Proportions gate: 30%-wider synthetic mask (E-004 SYN-30 method)
# ---------------------------------------------------------------------------

def test_proportions_gate_fails_on_30pct_width_scale():
    from system.gates.proportions import compare

    mask_path = ROOT / "experiments/001_segmentation_masks/results/person_front/person.png"
    assert mask_path.exists(), f"Fixture missing: {mask_path}"

    m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    assert m is not None
    h, w = m.shape
    scaled = cv2.resize(m, (int(round(w * 1.30)), h), interpolation=cv2.INTER_NEAREST)

    result = compare(mask_path, scaled)

    assert result["max_abs_change_pct"] is not None, (
        "max_abs_change_pct must not be None — person body not detected in mask"
    )
    assert result["max_abs_change_pct"] > 5.3, (
        f"Expected FAIL (max_abs > 5.3%), got {result['max_abs_change_pct']}%"
    )
    verdict = "PASS" if result["max_abs_change_pct"] <= 5.3 else "FAIL"
    assert verdict == "FAIL"


# ---------------------------------------------------------------------------
# Color gate: clearly different hue regions (synthetic BGR patches)
# ---------------------------------------------------------------------------

def test_color_gate_fails_on_different_hue_regions():
    from system.gates.color import compare_regions

    # Navy blue (BGR) vs orange-brown (BGR): large hue separation → high dE
    img_navy   = np.full((60, 60, 3), [80, 20, 10],  dtype=np.uint8)
    img_orange = np.full((60, 60, 3), [10, 90, 210], dtype=np.uint8)
    mask_full  = np.full((60, 60), 255, dtype=np.uint8)

    result = compare_regions(img_navy, mask_full, img_orange, mask_full, normalize_l=False)

    assert result["delta_e_mean"] is not None, "delta_e_mean must not be None"
    assert result["delta_e_mean"] > 5.0, (
        f"Expected FAIL (dE > 5.0), got {result['delta_e_mean']}"
    )
    verdict = "PASS" if result["delta_e_mean"] <= 3.0 else (
        "WARN" if result["delta_e_mean"] <= 5.0 else "FAIL"
    )
    assert verdict == "FAIL"


# ---------------------------------------------------------------------------
# Identity gate: person vs garment model (different identities)
# ---------------------------------------------------------------------------

def test_identity_gate_fails_on_different_persons():
    from system.gates.identity import compare_faces

    person_img    = ROOT / "assets/person/person_front.png"
    garment_model = ROOT / "assets/outfits/outfit_001/blouse_front.webp"

    assert person_img.exists(),    f"Fixture missing: {person_img}"
    assert garment_model.exists(), f"Fixture missing: {garment_model}"

    result = compare_faces(person_img, garment_model)

    assert result["detected_a"], "No face detected in person_front.png"
    assert result["detected_b"], "No face detected in blouse_front.webp (garment model)"
    assert result["cosine"] is not None, "cosine must not be None when both faces detected"
    assert result["cosine"] < 0.57, (
        f"Expected FAIL (cosine < 0.57), got {result['cosine']:.4f}"
    )
    verdict = "PASS" if result["cosine"] >= 0.57 else "FAIL"
    assert verdict == "FAIL"
