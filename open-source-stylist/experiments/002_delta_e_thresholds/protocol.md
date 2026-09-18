# E-002 — ΔE threshold separability

Created: 2026-06-11

---

## 1. Question

Are ΔE (CIE76) scores produced by `system/gates/color.py` monotonically increasing
with known hue-shift magnitude, and is there a clear gap between natural garment
variation and genuinely different colors — sufficient to choose pass/warn/fail thresholds?

## 2. Decision informed

The `delta_e_mean` and `delta_e_p90` thresholds used by the color gate in all future
evaluation (Stage 2+). Without verified thresholds the gate has no pass/fail criteria.

## 3. Method

Three test series, all using `compare_regions()` from `system/gates/color.py`.

**Series A — synthetic hue shifts (ground truth known by construction)**

Base image: `assets/outfits/outfit_001/skirt_front.webp`
Mask: `experiments/001_segmentation_masks/results/outfit_001_skirt_front/skirt.png`

For each shift angle in [0, 5, 10, 15, 20, 30, 45, 60, 90, 120, 150, 180] degrees:
- Apply hue rotation in HSV space to the base image pixels inside the mask
- Background (outside mask) left unchanged
- Compare modified image (mask) vs original image (mask) → `delta_e_mean`, `delta_e_p90`

Expected: scores increase monotonically with shift angle.

**Series B — same-garment front/back (natural variation baseline)**

Pairs (using respective garment masks from E-001):
- `skirt_front` vs `skirt_back`  (mask: skirt region)
- `blouse_front` vs `blouse_back` (mask: blouse region)

These are the same physical garments photographed from two angles.
Expected: small ΔE values — this establishes the natural noise floor.

**Series C — different garments (upper bound)**

Reference: `skirt_front` (mask: skirt region)
Compare against (whole image, no mask on comparison side):
- `belt.jpg`
- `shoes_wedge.webp`

Expected: large ΔE values — clearly wrong color if a gate was applied here.

## 4. Fixed / variable

Fixed: images, masks, color.py implementation (CIE76, mean + p90 metrics)
Variable: hue shift angle (Series A); garment pair identity (B, C)

## 5. Success criteria

- Series A scores are monotonically non-decreasing with shift angle
- Series B scores (natural variation) < Series A at some shift threshold
- Series C scores >> Series B
- A visible gap exists that allows choosing `T_pass` and `T_fail` without overlap
  between natural-variation and clearly-wrong-color cases

## 6. Outputs

- `results/scores.csv` — columns: series, pair_name, shift_deg, delta_e_mean, delta_e_p90
- `results/synthetic_shifts/` — PNG overlays for shift angles 0, 30, 90, 180
  (visual confirmation that hue shift is applied correctly)
- `conclusion.md` — thresholds chosen + rationale; appended to `knowledge/verified.md`

## 7. Not in scope

- CIEDE2000 (upgrade only if CIE76 fails separability — per color.py comment)
- Per-pixel ΔE maps
- Any generated images (no ComfyUI, no LM Studio required for this experiment)
