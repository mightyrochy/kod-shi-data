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

---

# E-011 resolution — root cause found, v5 owner-ACCEPTED (2026-06-20)

**Date:** 2026-06-20. Owner reviewed `results/repaired_blouse_v5_official.png` at full resolution and
accepted it as the E-011 result. Status: **owner-accepted YES for case 1** (single garment/person/seed;
cross-garment generalisation still open).

## Root cause of the v1–v4 under-generation: the workflow was structurally wrong (not just config)
Causes (1)/(3) above were on the right track but understated. The repair was running a **hacked** QIE
graph, not the official QIE-Image-Edit-2511 edit graph. Reading the official ComfyUI template
(`comfyui_workflow_templates_media_image/templates/image_qwen_image_edit_2511.json`) exposed three
missing essentials:
1. **Latent = `VAEEncode` of the input image** (via `FluxKontextImageScale`), NOT `EmptySD3LatentImage`
   / the layered latent. An edit must denoise FROM the input's latent; generating from an empty latent
   is why the blouse came out "watercolour / under-formed."
2. **`ModelSamplingAuraFlow` (shift 3.1) + `CFGNorm`** model patches before the KSampler — without them
   QIE-2511's sampling schedule is wrong.
3. Negative conditioning is also image-encoded; both conditionings pass through
   `FluxKontextMultiReferenceLatentMethod`. cfg 4.0, euler/simple, denoise 1.0.

`system/workflows/qie2511_edit.json` was rebuilt to match the official graph exactly (node field names
verified via `/object_info`, not guessed). One variable changed vs v4 (the workflow); same base/mask/ref/seed.

## v5 result (official workflow, 20 steps, cfg 4.0, seed 42)
- **Quality — owner ACCEPTED (axis #1):** blouse fully formed — V-neck, covered-button placket, pleated
  peplum waist, dolman sleeves, colour matches the reference. The v1–v4 melting / deformed hands are gone.
- **Locality — YES (deterministic):** 0.232 % outside-mask change (<1 % target).
- **Identity — YES (deterministic):** ArcFace cosine(base, v5) = 0.9984.

## Isolation: the residual soft-cuff is NOT a sampling-budget problem
Owner's one reservation on v5: the **sleeve-cuff zone is slightly soft**. Diagnosis (artifacts viewed, not
theorised): the raw QIE output is already soft at the cuff (so it is the generation, not the stitch/feather;
the cuff sits inside the mask). Test: v6 = same crop at **40 steps** (`results/repaired_blouse_v6_steps40.png`).
**Result: 40 steps did not fix the cuff** — v5/v6 cuff strips are near-identical (sharpness +8–14 % by
Laplacian var, invisible to the eye). So the cuff softness is a **peripheral fine-detail approximation at
low effective resolution**, not a step-budget issue. Two levers now falsified for this defect: global
resolution (E-011 2026-06-19, 1536px) and sampling steps (here). The one untested, mechanistically-distinct
lever is a **tighter per-detail crop** (more pixels-on-cuff) — left as the next move, not run.

## Owner decision
**Accept v5 (20 steps) as the E-011 result.** The core question — can QIE-2511 crop-and-stitch do
reference-faithful, LOCAL single-garment repair — is **YES** for this case (faithful, local, identity-safe).
Residual peripheral-detail softness (cuffs) recorded as a known QIE limit; the tighter-crop lever is the
documented next step if/when a cuff-grade result is required.
