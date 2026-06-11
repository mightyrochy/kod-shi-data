# E-004 — Proportions gate threshold calibration

**Date:** 2026-06-11
**Status:** ready to run

---

## Question

Does the proportions gate detect known width distortion and pass natural
same-person variation? What threshold separates the two?

## Decision informed

`system/gates/proportions.py` threshold — the maximum normalised-width change (%)
above which the gate flags a proportions failure. Applied in evaluation to check
that generated images do not distort the person's body shape.

## Method

**Instrument:** `system/gates/proportions.py` → `compare(mask_a, mask_b)`.
Score = max of |shoulder_change_pct|, |waist_change_pct|, |hip_change_pct|.

**Masks:**

| ID | Source | How obtained |
|----|--------|-------------|
| mask_front | experiments/001_segmentation_masks/results/person_front/person.png | reused from E-001 |
| mask_twoview | person_two_view.png left-half crop → segmentation (ComfyUI) | new run |
| mask_scaled_10 | mask_front, cv2.resize fx=1.10 fy=1.0 | synthetic, in-script |
| mask_scaled_20 | mask_front, cv2.resize fx=1.20 fy=1.0 | synthetic, in-script |
| mask_scaled_30 | mask_front, cv2.resize fx=1.30 fy=1.0 | synthetic, in-script |

**Pairs:**

| Pair ID | Mask A | Mask B | Expected class | Expected score (approx) |
|---------|--------|--------|----------------|------------------------|
| NAT-01 | mask_front | mask_twoview | natural variation | low |
| SYN-10 | mask_front | mask_scaled_10 | synthetic +10% | ~10% |
| SYN-20 | mask_front | mask_scaled_20 | synthetic +20% | ~20% |
| SYN-30 | mask_front | mask_scaled_30 | synthetic +30% | ~30% |
| SAN-00 | mask_front | mask_front | sanity (0% change) | ~0% |

**Procedure:**
1. Segment person_two_view.png left crop → mask_twoview (ComfyUI).
2. Synthesise scaled masks in-script (no segmentation needed).
3. Run compare() on all pairs; record max_abs_change_pct for each.
4. Threshold = midpoint of (NAT-01 max_abs, SYN-10 max_abs).
   If NAT-01 ≥ SYN-10 (gap too small): threshold NOT promoted; investigate zones.

**Acceptance criteria:**
- SAN-00 score < 1% (gate is deterministic; any larger value = bug).
- NAT-01 score < SYN-10 score (natural < smallest synthetic).
- Gap NAT-01 to SYN-10 ≥ 5 percentage points.
- Threshold documented in knowledge/verified.md.

**Failure modes:**
- mask_twoview face count ≠ 1 (composite bleed) → crop more aggressively; document.
- NAT-01 ≥ SYN-10 → zones may overlap (arm position dominates hip zone, etc.);
  examine per-zone data; adjust zone fractions and re-run.
- SAN-00 > 1% → implementation bug in measure(); fix before proceeding.
