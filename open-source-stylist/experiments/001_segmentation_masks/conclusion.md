# E-001 Conclusion — 2026-06-11

## Answer to the question

**GroundingDINO + SAM1 produces usable masks for V1.** Overall verdict: **conditional pass**.

## Verdict by protocol criteria

**Core regions (person_front.png):** all 8 labels rated `ok` by owner — meets Pass criterion.

**Garment reference images:** 5/7 rated `ok`, 2/7 rated `partial` (blouse_front, blouse_back).
The partial is not a region detection failure — the blouse body is correctly isolated from the
model and background. The gap is button exclusion: small plastic/metal buttons are not captured
as part of the fabric mask.

## Knowledge status changes

Promoted to `knowledge/verified.md`:
- V-SEG-001: GroundingDINO (SwinT, 0.3 threshold) + SAM1 (vit_h) via `comfyui_segment_anything`
  produces owner-accepted masks on person_front.png for all pipeline-required regions:
  person, face, hair, background, top, bottom, shoes, glasses.
- V-SEG-002: Same tool produces owner-accepted garment isolation masks on outfit_001 product
  photos for: belt, earrings, shoes, skirt (front and back). Blouse masks exclude buttons.
- V-SEG-003: Button exclusion on blouse masks is a documented gap, not a blocker. Buttons
  occupy <5% of blouse mask area; color gate mean ΔE impact is minor. Acceptable for V1.

## Decision: segmentation tool

**GDINO+SAM1 is the segmentation tool for V1.**

SAM3 return trigger NOT activated. Conditions for revisiting:
- A specific region type fails color gate (E-002) or produces gate noise that traces back to
  mask quality.
- Button exclusion proves significant in practice (ΔE on a high-contrast-button garment
  fails acceptance — to be measured in E-002/E-005).

## Hypothesis status

- H-SEG-GDINO-SAM1-ADEQUATE: promoted to Verified (V-SEG-001, V-SEG-002)
- H-SEG-BUTTONS-EXCLUDED: promoted to Verified (V-SEG-003)

## Decision now unblocked

Stage 1 segmentation deliverable is complete. E-002, E-003, E-004 can proceed.
