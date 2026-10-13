# E-003 — ArcFace identity gate threshold calibration

**Date:** 2026-06-11
**Status:** ready to run

---

## Question

Does ArcFace (buffalo_l) produce a clear separation between same-person and
different-person pairs on our specific photos? What threshold should the identity
gate use?

## Decision informed

`system/gates/identity.py` threshold — the cosine similarity cutoff below which
two images are judged to show different people. Applied in evaluation and
in the deterministic shell (Stage 4).

## Method

**Instrument:** `system/gates/identity.py` — `get_embedding` (ArcFace R100,
buffalo_l, cosine similarity).

**Source images:**

| ID | File | Person | Notes |
|----|------|--------|-------|
| P0 | assets/person/person_front.png | owner | frontal, clear |
| P1 | assets/person/person_two_view.png | owner | composite front+side; script crops left half (frontal) at runtime |
| D1 | assets/outfits/outfit_001/blouse_front.webp | Model A | brunette, beret, frontal |
| D2 | assets/outfits/outfit_001/skirt_front.webp | Model B | auburn hair, frontal |

**Pairs:**

| Pair ID | Image A | Image B | Expected class |
|---------|---------|---------|----------------|
| SP-01 | P0 | P1 | same |
| DP-01 | P0 | D1 | different |
| DP-02 | P0 | D2 | different |
| DP-03 | D1 | D2 | different (bonus) |

**Procedure:**
1. Load each image; for P1 crop the left half before embedding (avoids composite
   ambiguity — ArcFace trained on single faces).
2. Detect face, extract 512-d ArcFace embedding per image.
3. Compute cosine similarity for each pair.
4. Log all raw scores to `results/scores.csv`.
5. Inspect: does SP-01 score clearly exceed all DP-xx scores?
6. Choose threshold at midpoint of the gap (same_min − diff_max) / 2 + diff_max.

**Acceptance criteria:**
- Face detected in all four images (P0, P1-crop, D1, D2).
- SP-01 cosine > all DP-xx cosines (clear separation).
- Gap ≥ 0.15 (sufficient margin for a reliable threshold).
- Threshold value and gap documented in `knowledge/verified.md`.

**Failure modes and responses:**
- P1 crop: face not detected → use person_front.png only; note N=0 same-person
  pairs with second image; still run different-person pairs; document limitation.
- Gap < 0.15 → threshold NOT promoted to Verified; document failure; investigate
  cause before E-005.
- Same-person score unexpectedly low (< 0.3) → flag; possible ArcFace issue with
  glasses or lighting; document and investigate.

## Notes on data constraints

N=1 same-person pair is thin for distribution estimation. Acceptable for V1
because: (a) ArcFace is a calibrated, widely validated model; (b) the operating
condition is frontal portrait vs frontal generated image — a well-studied pair for
this architecture; (c) if the gap is large (≥ 0.15), the threshold is robust.
The final validation happens at E-005 when real generated images are available.
