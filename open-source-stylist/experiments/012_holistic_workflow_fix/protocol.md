# E-012 — holistic whole-outfit generation on the corrected QIE-2511 edit graph

**Status:** protocol written 2026-06-20, BEFORE running (METHODOLOGY §2). Follows the
holistic-workflow bug fix (commit 6b9d1f7): `qie2511_vton.json` rebuilt from the broken layered-latent
graph to the official QIE-Image-Edit-2511 edit graph (V-QIE-EDIT-001). Owner-directed.

## 1. Question (falsifiable)
Does the corrected holistic graph — `VAEEncode`-of-person latent + `ModelSamplingAuraFlow`(3.1) + `CFGNorm`
+ image-encoded negative, instead of the empty `EmptyQwenImageLayeredLatentImage` and no model patches —
produce a **properly-formed whole-outfit generation**, i.e. the chronic under-generation/softness of the
old graph is GONE in a single whole-figure pass?

## 2. Decision informed
Whether the editing-first **spine** is viable as built (SYSTEM_DESIGN §3). If the corrected graph generates
cleanly with the person/body preserved, the holistic pass + per-item repair (E-011, V-REPAIR-001) is the V1
path. **This also re-tests whether the E-009 "drift" and the E-010 dedicated-VTON detour stood on this
workflow bug rather than a model limit** (E-009 named `EmptyQwenImageLayeredLatentImage` + denoise 1.0 "the
root cause of the drift"). If softness/drift persists on the corrected graph, the limit is elsewhere
(board, or a genuine model ceiling) — a legitimate, separating outcome.

## 3. Method
Orchestrator: `system/run_slice.py --generate` (the built vertical slice: SHA-verified frozen board →
task-correct prompt → exact filled workflow → output + hashes → segmentation + advisory gates → owner
checkpoint). One run, full-model (non-Lightning) path:
- engine `qie-2511` (→ `qie2511_vton.json`), **steps 20, cfg 4.0**, euler/simple, denoise 1.0 (the official
  Comfy reference that produced the accepted E-011 repair).
- person = `assets/person/person_front.png`; outfit = `outfit_001`; board = **`hybrid_mask_crop`**
  (the measured candidate; SHA-verified by `resolve_board`). seed 42.
- prompt: built by the adapter (task-correct "keep this exact person / re-dress from the board"; no colour
  words, H-COLOR enforced). Negative empty.
- Fixed: person, board, seed, settings. Varies vs history: ONLY the corrected workflow graph.
- Baseline of comparison: the documented old-graph behaviour (watercolour/under-generated; E-009 identity
  collapse to 0.348 at full cfg, ~9% slim on Lightning). Not re-run — its failure is on record.

## 4. Acceptance criteria (defined before results)
- **PRIMARY — owner verdict (axis #1, full resolution):** the whole-outfit output is **properly formed** —
  garments present and rendered (not melted/under-generated), no watercolour softness. Owner PASS/FAIL.
- **Identity (advisory, deterministic):** ArcFace cosine(person, generated) — report; a real fix should be
  far above the old full-cfg collapse (0.348). Not the decider, but a red flag if it collapses.
- **Body (advisory, deterministic):** pose-joint hip/shoulder deltas (clothing-robust) — report; watch for
  the old slimming/expansion drift.
- **Status:** single run + owner eye + advisory gates → **Observation** (decides direction, not Verified).
  No aggregate score; owner verdict is the acceptance (METHODOLOGY §5).

## 5. Cost
1 GPU run (~3–6 min cold) + segmentation for the advisory gates. Cheap relative to the decision it informs.

## 6. Honest unknowns
- **Board quality is a SEPARATE axis:** `hybrid_mask_crop` still had a wrong blouse shade / poor silhouette
  diagnostic (E-007 v2). A board defect propagating into the output is NOT a workflow-fix failure — keep
  the two apart in the verdict.
- Whether a whole-figure edit at denoise 1.0 preserves identity/body well (the core thing the fix should
  improve over the empty-latent regeneration).
- Fine-detail fidelity ceiling remains (repair layer, E-011, addresses that separately) — this test is
  about gross formedness/drift, not cuff-grade detail.
