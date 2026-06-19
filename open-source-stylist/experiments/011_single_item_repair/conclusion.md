# E-011 conclusion — single-item repair (QIE-2511 crop-and-stitch), first run

**Date:** 2026-06-19. Owner reviewed `results/repaired_blouse.png` (METHODOLOGY §2 — conclusion after
owner verdict on visual quality). Status: **Observation** (single run + owner eye; not Verified).

## Answer to the question
"Can QIE-2511 crop-and-stitch do reference-faithful, LOCAL single-garment repair?"
**Partial — the mechanism is structurally sound, the quality is not yet acceptable.**
- **Locality — YES (deterministic):** 0.211 % of outside-mask pixels changed (<1 % target). The
  crop-and-stitch guarantee holds; the locality contract test passes.
- **Identity — YES (deterministic):** ArcFace cosine(base, repaired) = 0.9995 (face is outside the mask).
- **Reference direction — YES (advisory):** the repaired top moved toward the blouse reference
  (FashionSigLIP sim 0.61→0.80, DISTS 0.36→0.32 vs the original sweater region).
- **Quality — NO (owner verdict, axis #1):** the blouse is "under-formed / under-finished, slightly
  blurry" with "an artifact at the neckline." Rejected.

## Likely causes (grounded; to test ONE variable at a time — not by fishing)
1. **Resampling blur.** The manifest shows the crop was upscaled to `work_res 912×1024` for QIE, then
   downscaled back to crop size and stitched — two resamples soften the result, and QIE generated at a
   non-native scale of a partly-interpolated input. → Test: run at the source's NATIVE crop resolution, or
   upscale the SOURCE first so the crop is natively large (IMPLEMENTATION_BLUEPRINT §9.5).
2. **Mask–silhouette mismatch (neckline artifact).** The mask was the SWEATER silhouette (crew neck); the
   target blouse has a V-neck. Pasting the V-neck blouse only within the crew-neck mask cuts/mismatches at
   the neck. This is the VTON agnostic-mask principle (DEEP_RESEARCH §1.3): the mask must match the TARGET
   garment's silhouette, not the old garment's exact shape. → Test: a neckline-aware / target-shaped mask
   (union of old mask + the garment's expected region; or a parser-derived agnostic for the category).
3. **QIE config** (secondary): cfg 2.5 is low for a no-Lightning edit (BUILD_PLAN bench notes cfg≈4–7);
   the layered-latent holistic mechanism may not be ideal for a tight crop edit. → Test only after (1)/(2).

## Decision unblocked
Repair as an architecture is **viable in principle** (locality + identity + correct direction by
construction) but **not yet at acceptable quality**. It does NOT yet validate "holistic + repair clears
the whole-outfit bar." Next: address cause (1) [resolution] then (2) [mask shape] as single-variable
follow-ups, OR record E-011 as "mechanism sound, quality open" and move to the broader feasibility gate.
This is the editing-spine repair path; it already behaved far more cleanly (local, identity-perfect, no
hallucinated topology) than the 2026-06-18 dedicated-VTON detour.
