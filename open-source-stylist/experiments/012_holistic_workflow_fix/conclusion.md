# E-012 conclusion — holistic whole-outfit on the corrected QIE-2511 edit graph

**Date:** 2026-06-20. Owner reviewed the whole-outfit output at full resolution
(`results/holistic_v1_fixed_graph.png`; run `runs/outfit_001_hybrid_mask_crop_s42_d8bce7d4b9af`).
Status: **Observation** (single run + owner eye + advisory gates; not Verified).

## Answer to the question
"Does the corrected holistic graph produce a properly-formed whole-outfit generation — is the chronic
under-generation/softness gone?" **YES (owner: 'дуже непогано').**
- The whole outfit (lemon blouse, brown maxi skirt with front slit, belt, earrings, green heeled sandals)
  is rendered and formed in a single whole-figure pass — **no watercolour/under-generation**, the failure
  mode of the old `EmptyQwenImageLayeredLatentImage` graph.
- **Identity (advisory):** ArcFace cosine(person, generated) = **0.9191** (PASS) — vs the old full-cfg
  collapse to 0.348 (E-009). Body (pose joints): hipΔ −6.96 %, shoulderΔ −2.73 %, ratioΔ 4.54 %, pose
  match 4.2°. Strong evidence the fix preserves the person, not just formedness.

**Decision impact:** the editing-first **spine** is viable as built — holistic pass + per-item repair
(E-011, V-REPAIR-001) is the V1 path. This also confirms the chronic holistic softness was the **workflow
bug** (V-QIE-EDIT-001), re-opening whether the E-009 "drift" / E-010 dedicated-VTON detour conclusions
stood on this bug rather than a model limit (see hypotheses H-REPAIR-GEN).

## Residual defects — SEPARATE axes (owner-noted), not the softness bug
1. **Outfit layout violated — blouse tucked into the skirt.** The prompt said "blouse goes over skirt"
   (ambiguous: z-order vs tuck); the peplum should hang untucked. → holistic-pass **instruction** lever
   (explicit "untucked peplum" cue), single-variable isolation run. NOT a graph fault.
2. **Earrings attached unnaturally.** Rendered accurately (board crop is good) but the attachment to the
   ear is off. → QIE small-accessory placement; per-item repair (E-011) on the ear region, or accept as a
   small-accessory limit.
3. **Skirt looks flat — lacks fabric texture (colour is right).** Either the `hybrid_mask_crop` skirt crop
   is itself low-texture (board axis, known from E-007 v2) or the QIE fine-detail ceiling. → check the
   board crop's texture first; then per-item skirt repair against the full-res reference (E-011's purpose).

## Board
`hybrid_mask_crop` (sha256 542051b334f0…) — the measured candidate; it has known blouse-shade/silhouette
caveats (E-007 v2). Board quality is a distinct axis from the workflow fix; defect #3 may live here.

## Honest status
Single run, one board, seed 42 → Observation, not Verified. The workflow fix is strongly indicated
(formed output + identity 0.9191 + body preserved), but generalisation across boards/people/seeds and the
three residual axes remain open.
