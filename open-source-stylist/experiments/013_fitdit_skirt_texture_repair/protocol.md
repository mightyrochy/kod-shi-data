# E-013 — FitDiT skirt-texture repair of the QIE holistic output

**Status:** protocol written 2026-06-21, BEFORE running (METHODOLOGY §2). Owner-directed plan:
"take the QIE result with the flat skirt, repair it with FitDiT, look at the result; if good, use
original / flat / good as the calibration triplet."

## 1. Question (falsifiable)
Can FitDiT re-render the **skirt region** of the E-012 QIE holistic output (which is the right shape but
**flat / low-texture**) to **restore fabric texture**, using a continuous-silhouette textured skirt
reference at high resolution — while staying a SKIRT (not pants) and preserving the rest of the image?

## 2. Decision informed
Whether FitDiT is a viable **per-item texture repairer** on top of the QIE holistic spine (an alternative
/ complement to the QIE crop-and-stitch repair, E-011). Also tests the **resolution lever** for texture
(1152×1536 — untested; the 768×1024 used in E-010 was the low option, and the global-res lever was
falsified for QIE specifically, not for FitDiT).

## 3. Method
FitDiT (canonical, per FITDIT_AUDIT_2026-06-21): the node + invocation are faithful; skirts work with a
**continuous-silhouette** garment.
- **vton_image** = `experiments/012_holistic_workflow_fix/results/holistic_v1_fixed_graph.png` (the QIE
  output with the flat skirt).
- **garm_image** = `experiments/010.../results/proto_chain/skirt_filled_crop.png` — continuous silhouette
  (slit as internal line, no through-gap → no pants) WITH visible fabric texture.
- **mask + pose** = native `FitDiTMaskGenerator(category="Lower-body")` on the vton_image.
- **FitDiTTryOn**: resolution **1152×1536** (the texture lever), n_steps 20, image_scale 2.0, seed 42,
  with_offload (VRAM).
- One run. Varies vs E-012: the skirt region is re-rendered by FitDiT at high res.

## 4. Acceptance criteria (defined before results)
- **PRIMARY — owner verdict (full resolution):** the repaired skirt has **restored fabric texture** (not
  flat), **stays a skirt** (not pants/leggings), and identity + upper body (blouse/belt) + background are
  preserved. PASS/FAIL.
- **Advisory (instruments, on the segmented skirt region vs the skirt reference):**
  - texture_ratio IMPROVES vs the QIE flat skirt (E-012 ≈ 0.51) toward 1.0;
  - garment-correspondence FashionSigLIP sim HOLDS (still the same item, rank 1) — texture restored without
    losing identity;
  - DISTS improves (lower) vs the QIE skirt (≈ 0.31).
- Status: single run + owner eye + advisory → Observation.

## 5. Cost
1 GPU run (FitDiT maskgen + tryon at 1152×1536, offload) ≈ a few minutes.

## 6. Honest unknowns
- Whether FitDiT's lower-body draping changes the skirt SHAPE/length vs the QIE skirt (a new variable —
  acceptable if it's a proper textured skirt; owner judges).
- Whether 1152×1536 actually lifts texture or hits the same approximation ceiling.
- Stitch boundary: FitDiT regenerates the masked lower body; the waist/belt transition must stay clean.

## 7. Step 2 (conditional)
If the FitDiT skirt is owner-accepted: use the **triplet** — original reference (textured), the QIE flat
skirt (negative), the FitDiT repaired skirt (positive) — as labelled anchors to **calibrate** the texture
gate + garment-correspondence thresholds (turn advisory numbers into decision-grade ones, METHODOLOGY §1).
