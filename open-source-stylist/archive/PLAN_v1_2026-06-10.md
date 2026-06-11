# PLAN — V1 build & verification roadmap

Created 2026-06-10. Derived from SYSTEM_DESIGN_R4 §6 build order, updated with
empirical results from v1alpha runs 1–2 (see FINDINGS.md).

**Discipline:**
- This is a living plan. Phases may change as findings come in — changes are
  recorded in the "Plan changelog" section at the bottom, append-only, date-stamped.
- Each phase has explicit exit criteria. A phase is done when criteria are met,
  not when the code is written.
- Every experiment runs through `runs/experiments/v1alpha/NNNNNN/` with
  `experiment/config.json` (hypothesis stated up front) and `conclusion/`
  (evaluation + human notes). No exceptions — undocumented runs are lost runs.
- Visual quality verdicts require human validation (CLAUDE.md SOP). Automated
  metrics gate, human accepts.

---

## Current status (2026-06-10)

| R4 step | Status |
|---|---|
| 1. Plumbing (ComfyUI client, LM Studio client, run I/O) | ✅ done — smoke test 8/8 |
| 2. Thin closed loop (V1-alpha) | ✅ done — 2 runs executed end-to-end |
| 3. Segmentation + RegionMap | ⬜ Phase B |
| 4. Restoration shell (deterministic) | ⬜ Phase C |
| 5. Repair executor | ⬜ Phase D |
| 6. Bench-off | ⬜ Phase E |
| 7. V1-final | ⬜ Phase F |

**Carry-over findings that shape this plan (from runs 1–2):**
- 464×672 resolution limits both generation detail AND VLM evaluation accuracy
- Body proportions (chest/waist reduction) is a confirmed failure mode with no
  evaluation criterion covering it
- Color-free prompts confirmed better (colors from reference images only —
  permanent rule, see memory + FINDINGS)
- VLM evaluation is advisory-only until deterministic metrics exist (hallucinated
  shoe color, missed earrings at current resolution)

---

## Phase A — Cheap experiments on the existing loop

**Goal:** establish the correct generation substrate (resolution) and measure
natural run-to-run variance BEFORE building heavier stages on top. Both directly
change how every later phase is interpreted.

**Prerequisites:** none — current loop is sufficient.

### A1 — Resolution experiment
- **Hypothesis:** generation at ~2x (928×1344, multiple of 16) improves garment
  detail (slit, pockets, croco texture, earring structure) and VLM evaluation
  accuracy, at acceptable generation-time cost.
- **Method:** same inputs as runs 1–2, only resolution changed. One run at
  928×1344. If VRAM allows and quality clearly improves, optionally one more at
  1160×1680 to find the ceiling.
- **Measure:** generation time, VRAM peak, human detail assessment vs run 2,
  VLM evaluation accuracy vs human assessment (does it stop hallucinating?).
- **Exit criteria:** a chosen working resolution for all subsequent phases,
  logged in FINDINGS.md with timing data.

### A2 — Repeatability baseline (K=5 seeds)
- **Hypothesis:** none — this is calibration. We need to know the natural
  variance of the model before any A-vs-B comparison can be trusted.
- **Method:** 5 runs, fixed distinct seeds (e.g. 1001–1005), best-known config
  (resolution from A1, color-free prompts). Same inputs.
- **Measure:** per-run human pass/fail on each criterion; qualitative variance
  notes (which elements are stable across seeds, which flip).
- **Exit criteria:** documented variance profile in FINDINGS.md — "element X is
  stable, element Y flips between runs" — used as the noise floor for Phase E
  bench-off comparisons.
- **Note:** this also produces the first data for the seed-selection question:
  if 1 of 5 seeds is clearly better, draft-ranking (P5) gains plausibility.

### A3 — Body-proportion criterion in the evaluator
- **Method:** add `body_proportions_preserved` (boolean + notes) to EVAL_SCHEMA
  and the eval prompt: explicit instruction to compare chest/waist/hip silhouette
  between original and generated image. VLM-based, interim — replaced by the
  deterministic gate in Phase C.
- **Exit criteria:** criterion appears in evaluation.json of all subsequent runs;
  sanity-checked against the known run-1 failure (should say FAIL on run-1 output).

**Execution mode:** Sonnet + medium-high. ~1 session.
**Artifacts:** FINDINGS entries; updated evaluator.py; chosen resolution constant.

---

## Phase B — Segmentation stage + RegionMap (SAM 3)

**Goal:** per-region masks on both input and generated images. This is the
enabling stage for every deterministic check and repair operation. One
computation, many consumers (P3, R4 §4).

**Prerequisites:** Phase A (resolution decided — masks must be built at working resolution).

### Work items
1. **B1 — Install & validate SAM 3 nodes.** Candidates from R4 sources:
   `ComfyUI-SAM3` (PozzettiAndrea) or `ComfyUI-Easy-Sam3` (low-VRAM variant with
   aggressive unload — preferred for 16GB). Fallback: comfyui_segment_anything
   (GroundingDINO+SAM1, already installed, older but proven).
   Gating test: text-prompted masks on person_front.png for: "person", "face",
   "hair", "blouse", "skirt", "shoes", "belt", "earrings", "background".
2. **B2 — RegionMap schema.** JSON schema: per-region mask file path + label +
   confidence + bbox. Schema goes to `schemas/region_map.schema.json` —
   resolves part of the contract-naming debt flagged in SYSTEM_DESIGN review notes.
3. **B3 — Segmentation module** (`pipeline/segmentation.py`): input = image path
   + region label list (from outfit_package categories), output = RegionMap +
   mask PNGs in the run folder. Works on both input photos and generated outputs.
4. **B4 — VRAM behavior check.** Measure SAM3 load/inference/unload cost;
   confirm it coexists or sequences cleanly with QIE-2511 and the VLM.

### Exit criteria
- Masks for all 9 region types on run-000001 assets, visually validated by owner
- RegionMap schema committed; segmentation module produces valid instances
- VRAM + timing data in FINDINGS.md

### Risks
- SAM3 misses small regions (earrings, belt) at working resolution → fallback:
  GroundingDINO+SAM on crops, or skip small-accessory masks in V1 (advisory only)
- Node pack quality unknown → P8: validate before integrating, keep fallback ready

**Execution mode:** Sonnet + high. 1–2 sessions.
**Artifacts:** pipeline/segmentation.py, schemas/region_map.schema.json, FINDINGS entry.

---

## Phase C — Deterministic gates + restoration shell (deterministic part)

**Goal:** replace VLM guesswork with measurements where measurement is possible.
After this phase the evaluator is hybrid: VLM for semantics only (presence,
layering), deterministic math for identity, proportions, color.

**Prerequisites:** Phase B (RegionMap).

### Work items
1. **C1 — Body-proportion gate** (`pipeline/gates/proportions.py`):
   from SAM3 person masks on input vs output — shoulder/waist/hip pixel widths
   normalized by person height; threshold on relative change. Replaces interim A3.
   - Verify: must FAIL on run-1 output (known chest/waist reduction), and the
     threshold must be calibrated against A2 variance data (don't flag noise).
2. **C2 — ArcFace identity gate** (`pipeline/gates/identity.py`):
   insightface/ArcFace embedding cosine between input face crop and output face
   crop (face region from RegionMap). Threshold from a small calibration set
   (same person photos vs different-person photos).
3. **C3 — Per-region ΔE color check** (`pipeline/gates/color.py`):
   mean/percentile ΔE (CIELAB) between garment region in output and reference
   garment image. Directly fixes the "VLM said black, shoes were green" class
   of error. Texture: advisory only in V1 (per SYSTEM_DESIGN review note).
4. **C4 — Face/background composite** (`pipeline/shell/composite.py`):
   restore-after for holistic passes — composite original face (and background
   where unchanged) back into the generated image. MediaPipe FaceMesh landmarks →
   piecewise affine warp → Poisson blend. ArcFace gate (C2) validates the result.
5. **C5 — Evaluator integration:** evaluation.json gains a `gates` section
   (proportions / identity / per-garment ΔE, each with measured values + pass/fail);
   VLM section shrinks to semantics (presence, layering, logic).

### Exit criteria
- All gates produce numeric values + verdicts on existing run outputs
- Proportion gate correctly flags run-1, passes acceptable runs
- Composite produces seam-free result on at least one run output (human-validated);
  ArcFace cosine confirms identity improvement
- Full loop run with hybrid evaluation completes end-to-end

### Risks
- Poisson blend seams on lighting mismatch → known risk (R4 §2.5); ArcFace gate
  catches bad blends; if systematic, composite becomes optional per-run flag
- ArcFace on glasses-wearing subject → calibrate thresholds on our actual photos
- New Python deps (insightface, mediapipe, opencv) → version-pin in requirements

**Execution mode:** Sonnet + high; Opus if integration debugging gets deep. 2–3 sessions.
**Artifacts:** pipeline/gates/*, pipeline/shell/composite.py, updated evaluator,
requirements.txt, FINDINGS entries per gate.

---

## Phase D — Repair executor (adopt, don't build — P8)

**Goal:** a working masked-repair capability for flagged regions: the thing that
was never achieved in the previous project attempt.

**Prerequisites:** Phase B (masks). Parallel-safe with Phase C.

### Work items
1. **D1 — Import community crop-and-stitch inpaint workflow** for QIE-2511
   (InpaintCropImproved/InpaintStitchImproved + TextEncodeQwenImageEditPlus;
   sources in R4). Convert to API format, add to pipeline/workflows/.
2. **D2 — Validate on a documented failure:** take a run output with a failed
   accessory (e.g. wrong shoes), mask the region (from RegionMap), repair with
   the single garment reference. Measure: ΔE improvement in-region, pixel change
   outside mask (locality), human verdict.
3. **D3 — OmniTry gating test:** does OmniTry (FLUX.1-Fill LoRA) load and run
   on 16GB with fp8/offload? Yes → accessory-executor candidate for Phase E
   row 6. No → drop it, document, move on. Timebox: one session max.

### Exit criteria
- One successful reference-faithful repair of a real failure, locality preserved
  (outside-mask change ≈ 0), human-accepted
- OmniTry: binary answer documented

### Risks
- QIE-2511 inpaint may repaint the whole crop region ignoring the reference →
  if so, this is a major finding (changes Phase F architecture toward
  regenerate-with-new-seed instead of repair)

**Execution mode:** Sonnet + high. 1–2 sessions.
**Artifacts:** repair workflow JSON, pipeline/repair.py, FINDINGS entries.

---

## Phase E — Bench-off (R4 §7)

**Goal:** pick the generation engine/config for V1-final with automated metrics
instead of eyeballing. Settles the Lightning-fidelity question.

**Prerequisites:** Phases A (resolution, variance floor), B (masks), C (metrics).
Phase D optional but informs row 6.

### Matrix (from R4, confirmed)
| Row | Config | Question answered |
|---|---|---|
| 1 | QIE-2511 + Lightning, 4 steps | baseline |
| 2 | QIE-2511, no Lightning, 20 steps | Lightning fidelity |
| 3 | QIE-2511, no Lightning, 40 steps | (with row 2) |
| 4 | FastFit | strategy B, honest row |
| 5 | Strategy C: holistic clothing pass + per-item accessory passes | hybrid sequential |
| 6 | OmniTry accessories (only if D3 = yes) | accessory executor |

- K=5 seeds per row, same seeds across rows (from A2).
- Second test outfit (harder: more layers, patterned fabric) — assemble before
  starting; assets to runs/experiments/output/.
- **Metrics per run:** per-garment ΔE, proportion-gate delta, ArcFace cosine,
  VLM presence/layering checklist, wall-clock, VRAM peak.
- **P5 correlation side-test:** rank the 5 Lightning drafts (row 1) by automated
  metrics; check whether ranking predicts row-2/3 quality on the same seeds.

### Exit criteria
- Full matrix executed, metrics tabulated in FINDINGS.md
- Engine/config decision recorded in DECISIONS.md with data behind it
- Lightning question answered with same-seed evidence

### Risks
- FastFit integration cost exceeds its value → timebox to one session; a
  documented "did not run in 16GB / in time budget" is an acceptable row result
- 30 runs × generation time — schedule as background batches

**Execution mode:** orchestration Sonnet + high; results analysis Opus/Fable + extra.
1–2 sessions + GPU time.
**Artifacts:** bench scripts, FINDINGS table, DECISIONS.md entry.

---

## Phase F — V1-final

**Goal:** the closed V1 loop on the winning configuration, with repair and retry.

**Prerequisites:** Phase E decision.

### Work items
1. Wire winning config as default; keep losers runnable behind a config flag
2. Retry policy: evaluation fail → repair pass (Phase D executor) for repairable
   defects; new-seed regeneration for unrepairable ones; retry cap (e.g. 3);
   final report (criteria, gate values, repairs done, retry count) per run
3. End-to-end acceptance: N fresh runs (e.g. 5) on both test outfits;
   measure pass rate; owner reviews each
4. Documentation closeout: WORKFLOW.md updated to actual pipeline state;
   schema debt resolved (PersonProfile, GenerationRequest/Result schemas written
   or explicitly deferred to V2 with rationale in DECISIONS.md)

### Exit criteria (V1 definition of done)
- One command runs photo+package → final image + full report, unattended
- Pass rate and failure modes documented over the acceptance batch
- Owner signs off on V1 quality bar (explicit user validation per SOP)

**Execution mode:** Sonnet + high. 1 session + acceptance runs.

---

## Dependency graph

```
A1 (resolution) ─┬─→ B (SAM3 + RegionMap) ─┬─→ C (gates + shell) ─→ E (bench-off) ─→ F (V1-final)
A2 (variance)  ──┤                          └─→ D (repair executor) ──↗
A3 (interim)   ──┘
```

Estimated total: 7–10 working sessions, excluding pure GPU batch time.

---

## Out of scope for V1 (deferred, unchanged from R4)
- Dual-view generation (sharpened hypothesis in R3 §8 — after V1)
- Garment retrieval, wardrobe (V2/V3)
- LoRA fine-tuning on Garments2Look (cloud GPU — deferred)
- Qwen-Image-2.0 — watch monthly; if weights open, add as bench row 7

---

## Plan changelog

- **2026-06-10** — initial plan created (phases A–F) from R4 §6 + runs 1–2 findings.
