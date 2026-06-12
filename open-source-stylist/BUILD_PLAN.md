# BUILD_PLAN — V1 assembly plan

Created 2026-06-10 (restart). Replaces archived PLAN.md.
Governed by METHODOLOGY.md; architecture defined in design/SYSTEM_DESIGN.md.

**The ordering principle (P9):** instruments are built and validated before the
experiments they judge. The previous attempt closed a loop around measurement that
didn't work — generation experiments produced noise. This plan builds the measurement
core first, then lets every generation step be measured from day one.

A stage is complete when its acceptance criteria are met — not when code exists
(METHODOLOGY §4). Stage boundaries are owner checkpoints: results reviewed, knowledge
entries written, next stage confirmed.

---

## Stage 0 — Foundations: contracts, clients, environment

**Purpose:** the skeleton everything plugs into. No generation, no experiments.

**Deliverables:**
1. `system/contracts/` — JSON schemas for all pipeline objects:
   `person_profile`, `outfit_package`, `generation_request`, `generation_result`,
   `region_map`, `evaluation_verdict`, `repair_plan`, `final_output`.
   Contracts first — they are the interfaces every stage depends on.
2. `system/clients/comfyui.py` — submit workflow / poll / download / free.
3. `system/clients/lmstudio.py` — chat + vision + schema-enforced JSON + load/unload.
4. `system/env_check.py` — one command that verifies the whole environment and prints
   facts: ComfyUI port + version, LM Studio API, required models present, VRAM free,
   load/unload round-trip timings. Re-runnable any time; its output re-verifies the
   archived environment hypotheses (ports, timings) cheaply.
5. `system/exp.py` — experiment folder utilities: create `experiments/NNN_name/` with
   protocol template, result capture, log.

**Acceptance criteria:**
- Contracts validate hand-written sample instances of each object.
- Both clients pass component round-trip tests against live servers
  (upload→generate-nothing→poll; chat→schema JSON back).
- `env_check` runs green and its facts are recorded in `knowledge/verified.md`
  (deterministic, reproducible → Verified by definition on second run).

**No experiments in this stage.**
**Execution mode:** Sonnet + high, 1 session.

---

## Stage 1 — Measurement core (the instruments)

**Purpose:** the gates that will judge every future generation. Each instrument is
calibrated on controlled cases where the correct answer is known by construction.

**Deliverables:**
1. `system/segmentation/` — SAM 3 (text-prompted; low-VRAM ComfyUI nodes preferred;
   Grounded-SAM-2 fallback) → `RegionMap` for any image given region labels.
2. `system/gates/color.py` — per-region ΔE (CIELAB), mean + percentiles.
3. `system/gates/identity.py` — ArcFace embedding cosine between two face crops.
4. `system/gates/proportions.py` — shoulder/waist/hip widths from person masks,
   normalized by person height; relative-change score between two images.

**Experiments (each = protocol per METHODOLOGY §2):**

| ID | Question | Decision informed | Method sketch | Acceptance |
|---|---|---|---|---|
| E-001 | Does SAM3 produce usable masks for our region types? | segmentation tool choice (SAM3 vs fallback) | masks for person/face/hair/background + 5 garment types on assets photos + 2 archived generated images; owner reviews overlays | owner accepts masks for ≥ the core regions (person, face, background, top, bottom, shoes); misses documented |
| E-002 | Are ΔE thresholds separable? | color gate thresholds | image pairs: identical (ΔE≈0), synthetically hue-shifted by known amounts, genuinely different garments | monotonic, separable scores; thresholds chosen and written down |
| E-003 | Does ArcFace separate same/different person on our photos? | identity gate threshold | same-person pairs (owner photos) vs different-person pairs (stock) | clear margin between distributions; threshold documented |
| E-004 | Does the proportion gate detect known distortion and ignore noise? | proportion gate threshold | same-person photo pairs (natural variation) vs synthetically width-scaled copies (known %) | gate flags ≥X% synthetic change, passes natural pairs |

**Acceptance criteria:** all four instruments give correct verdicts on controlled
cases; thresholds documented in `knowledge/verified.md`; VRAM behavior of SAM3
measured (coexistence with QIE-2511 / VLM).

**Execution mode:** Sonnet + high, 1–2 sessions.

**Execution notes (2026-06-11):**
- Deliverables 2–4 (color, identity, proportions gates): complete.
- Deliverable 1 (segmentation): module written (`system/segmentation/grounded_sam.py`),
  but using **GroundingDINO + SAM1** (`sam_vit_h`, SAM1 architecture), not SAM3 or
  SAM-2 as specified. This is an intentional, temporary divergence — see rationale below.
- **SAM1 vs SAM-2 divergence:** design specified Grounded-SAM-2 fallback; deployed
  fallback uses SAM1 vit_h. For single static images (V1 scope) the practical difference
  is small: SAM-2's video memory and tracking features are unused. Accepted for E-001.
- **SAM3 blocked:** `comfyui-easy-sam3` fails with `IMPORT FAILED: No module named
  'iopath'`; additional deps (`triton`, `open_clip`, `pycocotools`, `einops`, 8+ others)
  absent from ComfyUI venv. Installing them risks QIE-2511 stability (METHODOLOGY §3:
  full-picture check). Deferred until E-001 gives a concrete failure to justify the risk.
- **Stage 1 NOT yet complete:** E-001–E-004 not run; no thresholds in `knowledge/verified.md`.

**Execution notes (2026-06-11, E-002 interim — direction agreed with owner):**
- E-002 series data (experiments/002_delta_e_thresholds) exposed two instrument
  problems: (1) CIE76 mean ΔE sensitivity depends on the reference color — the same
  perceptual hue shift measured ~2 (navy) vs ~5 (brown), so no universal threshold
  exists in that metric; (2) natural photo-pair noise (same garment, front vs back:
  3.99–5.19) overlaps the chosen FAIL=3.0 and sits close to genuinely-different dark
  items (7.48) — the signal window is too narrow.
- **Agreed direction:** switch metric to CIEDE2000 + lightness normalization
  (`system/gates/color.py`); re-run series A/B/C on the same data (cheap — minutes);
  re-derive thresholds; record them as **provisional**. Final operational thresholds
  come from E-005, where the gate's real distribution (generated vs reference) first
  exists. Per-item adaptive baseline: where front+back reference photos exist,
  ΔE(front, back) is that item's own noise floor. Verdicts are three-zone
  PASS/WARN/FAIL; WARN → owner review.
- **Scope guard:** this closes E-002 as "instrument validated, thresholds
  provisional". E-003/E-004 do not depend on color thresholds — proceed without
  waiting.
- **Pattern blindness documented:** mean ΔE (any metric) cannot judge multi-color/
  patterned garments — the gate gets a second mode (`palette`: dominant-color
  matching / histogram EMD), auto-selected by reference-region modality. Calibration
  of that mode = E-013, tied to patterned-outfit assembly before the bench-off
  (Stage 6). Pattern *spatial* structure (stripe width, print scale) stays
  advisory-only in V1 — design §6, known limitation.

---

## Stage 2 — Generation baseline (first generation, fully measured)

**Purpose:** rebuild the generation path and establish Verified facts about engine
behavior. Several archived hypotheses get their honest re-test here — with
instruments instead of eyeballs.

**Deliverables:**
1. `system/workflows/` — QIE-2511 workflow (API format). P8: check for a maintained
   community workflow first; build from live `/object_info` only if none fits.
2. `system/adapter/` — outfit adapter v0: reference panel compositing (garment-only
   crops), prompt builder (structure/layout only — no color words pending E-007),
   resolution handling.

**Experiments:**

| ID | Question | Decision informed | Method sketch | Acceptance |
|---|---|---|---|---|
| E-005 | What is natural run-to-run variance? | the noise floor for ALL future comparisons **+ final thresholds for all three gates** (color, identity, proportions — replaces the Stage-1 provisional values, which were calibrated on photo pairs with n=1 natural-variation samples, with the real generated-vs-reference distribution) | K=5 fixed seeds, one frozen config, outfit_001; **before computing gates: owner reviews mask overlays on the first generated outputs** (segmentation was validated on real photos only — E-001 never covered the generator's domain); then all gates on every output | variance profile documented (per-gate spread); becomes the Verified noise floor; color/identity/proportion thresholds finalized; segmentation-on-generated-images verdict recorded |
| E-006 | Does generation resolution change measured quality? | working resolution for all later stages | same seeds, 2–3 resolutions; gates compare | resolution chosen on data (gate scores + time + VRAM) |
| E-007 | Do color words in prompts degrade color fidelity? (H-COLOR) | adapter prompt rule | A/B same seeds: prompt with vs without color adjectives; ΔE per garment | rule confirmed/refuted with ΔE numbers vs E-005 noise floor |
| E-008 | Do un-cropped product references distort proportions/items? (H-REF-CONTAMINATION) | adapter panel rule | A/B same seeds: raw product refs vs garment-only crops; proportion gate + ΔE + presence | rule confirmed/refuted with gate numbers |

**Acceptance criteria:** generation runs reproducibly through the new path; noise
floor, working resolution, and the two adapter rules are Verified knowledge with
numbers behind them.

**Reporting discipline (from Stage 1 closure, 2026-06-11):** any WARN from the
color gate is surfaced to the owner explicitly, never aggregated into a pass/fail
roll-up. The WARN band (ΔE 3–5) deliberately holds the zone where owner-confirmed
verdicts overlap across colors (navy fail at 3.02 vs pink pass at 3.97) — collapsing
it silently would reopen the color-dependence hole the band exists to cover.

**Execution notes (2026-06-11, owner review of the first-generation diagnostic):**
- **Config B (Lightning, 4 steps) confirmed as the E-005 configuration** — it is
  bench row 1 (baseline) anyway; E-005 measures variance of the baseline and does
  not depend on resolving the Lightning question.
- **Diagnostic conclusion "full model without Lightning produces invalid output"
  is REJECTED as confounded.** Config A ran 40 steps at cfg=1.0 with an empty
  negative prompt — Lightning-regime settings. The full model requires cfg ≈ 4–7
  with a real negative; blur under cfg=1.0 is the expected symptom of a wrong
  config, not a property of the model. Do NOT record "Lightning required" in
  knowledge/. A fair no-Lightning config is a separate work item, required before
  bench rows 2–3 (otherwise H-LIGHTNING/H-40STEPS gets answered by a confound
  again — the exact failure mode of the archived attempt).
- **The 9-frames explanation is downgraded to hypothesis.** "Frames 02–09 are
  unpacked input images / empty slots" contradicts the observation that they are
  always blurry — inputs would be recognizable. Mechanism not understood yet.
- **P8 retro-step required before E-005 phase 1:** the workflow was built from
  scratch, skipping the plan's "check for a maintained community workflow first".
  Obtain the official/community QIE-2511 workflow (sources: design §13), compare
  node-by-node, establish the semantics of `EmptyQwenImageLayeredLatentImage` and
  `layers`. If doubt remains after comparison: one cheap layers=1 generation as a
  direct hypothesis test. E-005 measurements are not trustworthy until frame
  selection is understood and stable.
- Config C (40 steps, layers=3) timed out; result unknown; not blocking.

**Execution notes (2026-06-12, E-005 closed — order change for remaining experiments):**
- E-005 verdict on the baseline: identity solid (0.776–0.874 vs 0.57); color near-WARN
  on top/bottom/belt/earrings (~3.0–3.7 mean), shoes systematic FAIL (14.0 ± 6.0);
  proportions FAIL on all 5 seeds (7–16%, directional: waist −, shoulders/hips +,
  owner-confirmed on seed_1337).
- **Order changed: E-006 → E-008 → E-007** (was E-006 → E-007 → E-008). Rationale:
  E-008 (cropped vs raw references) attacks BOTH dominant failures at once —
  H-REF-CONTAMINATION is the lead suspect for proportions distortion (model bodies
  in product photos) and for shoes instability (skirt reference photos show the
  model in black heels; 1 of 5 generated outputs produced black shoes — same trail
  as the archived run-000003 observation). E-007 demoted: top nearly passes without
  color words, so E-007 refines an adapter rule rather than hunts a failure cause.
- E-008 framing note: the baseline already uses cropped references, so the A/B is
  "cropped (baseline, data exists) vs raw (5 new generations)". If raw is NOT worse,
  contamination does not explain the proportions distortion and H-PROPORTIONS needs
  another suspect (next candidate: Lightning-specific behavior, bench rows 2–3).

**New work item (2026-06-12, architecture review): mask sanity guard**
`system/segmentation/sanity.py` — deterministic plausibility checks on every mask
before any consumer reads it: area fraction bounds per region type, positional
priors (footwear in the lower band, top in the upper half), garment ⊂ person.
Violations FLAG for owner review (advisory, not a verdict). Motivation: two
silent-mask-corruption incidents inside one experiment (E-005 shoes, top), both
caught late — by the owner's eye or by an exploding ΔE. Build before E-006 so all
remaining A/B experiments run guarded. Design §6 [5] updated accordingly.

**Execution notes (2026-06-12, E-006 closed):**
- **Mask sanity guard** (`system/segmentation/sanity.py`): built before E-006 per plan.
  5 integration FAIL tests in `system/tests/test_segmentation_fail.py`, all green.
- **Working resolution confirmed: 720×1024** (max_side=1024). Gate data (K=5 × 3 tiers):
  baseline 0.830 mean identity 5/5 PASS; Low (576×816) 0/5 PASS; High (896×1280) 1/5
  PASS; High+ (1120×1600) 0/5 PASS. All non-baseline tiers fail identity criterion.
  No OOM at any tier — VRAM ceiling not hit up to 1.79MP (V-RES-002).
- Sanity guard flagged real corruption in 8 instances across the 3 non-baseline tiers
  (face area too small/large, containment violations). Guard is working.
- Known gap documented (O-SEG-GAP-001): inter-garment mask overlap not detected.
  Bottom mask covering belt caught by owner review at High/seed_42.

**Execution mode:** Sonnet + high, 1–2 sessions + GPU time.

**Execution notes (2026-06-11, Stage 2 start):**
- Deliverable 1 (`system/workflows/qie2511_vton.json`): workflow template built from
  live `/object_info` verification. 2-image conditioning (person + reference panel),
  40 steps (full model, no Lightning LoRA), layers=2. `system/workflows/__init__.py`
  provides `load_template` + `fill_workflow` type-safe placeholder utilities.
- Deliverable 2 (`system/adapter/`): adapter v0 complete — `panel.py` (garment-only
  crop + tiled composite via SAM; 3×N grid, cell=256px), `prompt.py` (structural
  prompt builder, color-word-blocked via `_COLOR_WORDS` set), `adapter.py`
  (OutfitPackage → GenerationRequest, auto-resolution from person image).
- `assets/outfits/outfit_001/outfit_package.json`: outfit package created per current
  schema. 5 items (blouse, skirt, belt, shoes, earrings). Descriptions free of color
  words per adapter rule (verified by prompt builder tests).
- E-005 protocol written (`experiments/005_variance_baseline/protocol.md`) with all
  three Stage-1 carry-overs embedded. Runner ready at
  `experiments/005_variance_baseline/run_e005.py`.
- Next step: run `python -m experiments.005_variance_baseline.run_e005` (GPU required;
  ComfyUI and LM Studio not needed for E-005 beyond SAM and QIE-2511).

---

## Stage 3 — Closed loop V1-alpha (measured loop) + VLM calibration

**Purpose:** one command runs the pipeline end-to-end and produces a per-region
measured report. The VLM enters only here — and first gets calibrated.

**Deliverables:**
1. `system/analysis/` — person analysis (Qwen3-VL-8B, `PersonProfile` out).
   **Scope note (2026-06-12):** the general-prompts rule shrank PersonProfile's V1
   role — preserve-attribute text no longer feeds the generation prompt. Build the
   minimal profile (photo_format, framing, visible constraints) needed by the
   orchestrator and report; do not build full attribute analysis for prompt text
   that is now banned. Re-scope at stage entry.
2. `system/evaluation/` — evaluation stage: deterministic gates (stage 1) + VLM
   semantic checks (presence, layering) + report assembly (`EvaluationVerdict`).
3. `system/orchestrator.py` — runs [1]→[3]→[4]→[5]→[6] with VRAM sequencing,
   experiment folder per run, full report.

**Experiments:**

| ID | Question | Decision informed | Method sketch | Acceptance |
|---|---|---|---|---|
| E-009 | What is the VLM's agreement rate with owner verdicts on presence/layering? | VLM's role in evaluation (advisory vs gating vs dropped); usable resolution | VLM checklist on N≥10 outputs from stage 2 runs; owner gives ground-truth verdicts; agreement matrix | agreement rate documented per check type; role decided on data |

**Acceptance criteria:** one command → final report with per-region measurements;
owner reviews an end-to-end run; loop reproducible; VLM role decided.

**Execution mode:** Sonnet + high, 1–2 sessions.

---

## Stage 4 — Restoration shell (deterministic part)

**Purpose:** stop trusting the generator with what can be restored deterministically.

**Deliverables:**
1. `system/shell/face_restore.py` — FaceMesh landmarks → affine warp of original
   face → Poisson blend; ArcFace gate validates output.
   **Conditional, not default (2026-06-12, from E-005):** identity is the
   generator's strongest property (cosine 0.776–0.874 vs 0.57 on all seeds);
   compositing into already-good faces adds Poisson-seam risk for no gain. Face
   restore triggers only when a run's ArcFace score falls below threshold.
2. `system/shell/background_restore.py` — composite original background back.
3. `system/shell/color_match.py` — bounded per-region LAB matching toward reference.

**Known architectural gap (2026-06-12):** the shell has NO deterministic remedy for
body-proportion distortion — the garment legitimately changes the silhouette, so
the original body cannot be composited back. Proportion failures are addressed
generation-side only: E-008 (contamination), bench rows 2–3 (Lightning), and
strategy C protect-by-construction (design §7). If none of these resolves it, V1
retry policy has no action for proportion FAIL — escalate to owner as an
architecture decision before Stage 7.

**Experiments:**

| ID | Question | Decision informed | Method sketch | Acceptance |
|---|---|---|---|---|
| E-010 | Does the deterministic shell measurably improve identity/color without artifacts? | shell default-on vs per-run flag | apply shell to stage-2/3 outputs; ArcFace + ΔE before/after; owner inspects seams | gates improve, no visible seams (owner), or failure modes documented |

**Acceptance criteria:** shell improves measured identity/color on real outputs;
owner confirms no artifacts; integrated into the loop behind a flag.

**Execution mode:** Sonnet + high, 1–2 sessions. New deps (mediapipe, insightface,
opencv) version-pinned.

---

## Stage 5 — Repair executor (adopt, don't build — P8)

**Purpose:** reference-faithful local repair of flagged regions — the capability the
previous project never achieved.

**Deliverables:**
1. Imported community crop-and-stitch inpaint workflow for QIE-2511, converted to
   API format, in `system/workflows/`.
2. `system/repair/` — executor: flagged region + `RegionMap` mask + single garment
   reference → repaired image.

**Experiments:**

| ID | Question | Decision informed | Method sketch | Acceptance |
|---|---|---|---|---|
| E-011 | Can imported QIE-2511 inpaint do reference-faithful, local repair? | repair architecture for V1-final (repair vs regenerate) | repair a real gate-flagged failure (e.g. wrong shoes); in-region ΔE improvement, outside-mask pixel change, owner verdict | repaired region matches reference (ΔE), locality ≈0 outside mask, owner accepts |
| E-012 | Does OmniTry run on 16GB (fp8/offload)? | accessory-executor row in bench-off | load + one accessory try-on; timeboxed 1 session | binary yes/no documented |

**Acceptance criteria:** one verified reference-faithful repair, or the documented
finding that QIE-2511 inpaint cannot do it (which redirects V1-final to
regenerate-on-fail — a major, legitimate outcome).

**Execution mode:** Sonnet + high, 1–2 sessions.

---

## Stage 6 — Engine bench-off

**Purpose:** the engine/strategy decision, made with instruments.
Protocol: design/SYSTEM_DESIGN.md §8 (6 rows × 5 seeds, same seeds across rows;
second harder outfit assembled before start; P5 correlation side-test included).

**Pre-bench work item — palette mode of the color gate (added 2026-06-11):**
the second outfit contains patterned fabric, and mean ΔE is blind on patterns
(same regional mean for a red/white stripe and a solid pink). Before the bench can
judge that outfit, the color gate needs its `palette` mode (dominant-color k-means
palette with weight-aware matching, or histogram EMD; auto-selected when the
reference region is multimodal) — and that mode needs its own calibration:

| ID | Question | Decision informed | Method sketch | Acceptance |
|---|---|---|---|---|
| E-013 | Can palette-distance separate "same patterned garment, different photo" from "different pattern colors"? | color gate applicability to patterned garments (bench row validity) | same series logic as E-002 on the patterned outfit's references: two photos of same patterned item (noise); synthetic hue shift of ONE palette component (signal); different patterned items (upper bound) | separable scores; palette-mode thresholds documented; pattern *spatial* fidelity explicitly excluded (advisory only, design §6) |

**Acceptance criteria:** matrix executed; metrics tabulated; engine/strategy decision
recorded in `knowledge/verified.md` with the data; Lightning question answered with
same-seed evidence; patterned-outfit rows judged by a calibrated palette mode (E-013).

**Execution mode:** orchestration Sonnet + high; analysis Opus/Fable + extra.
1–2 sessions + GPU batch time.

---

## Stage 7 — V1-final

**Purpose:** the closed V1 loop on the winning configuration.

**Deliverables:**
1. Winning config as default; losers runnable behind config flags.
2. Retry policy: gate-fail → repair (if repairable per E-011) or new-seed regeneration;
   retry cap; final report per run (criteria, gate values, repairs, retries).
3. Acceptance batch: N≥5 fresh runs on both outfits; pass rate measured; owner reviews
   each.
4. Docs closeout: design updated to as-built state; contract debt resolved.

**V1 definition of done:**
- One command: photo + outfit package → final image + measured report, unattended.
- Pass rate and failure modes documented over the acceptance batch.
- Owner signs off on the V1 quality bar (explicit, per SOP).

**Execution mode:** Sonnet + high, 1 session + acceptance runs.

---

## Dependency graph

```
Stage 0 (foundations)
   └→ Stage 1 (instruments)
        └→ Stage 2 (generation baseline + adapter rules)
             ├→ Stage 3 (closed loop + VLM calibration)
             │     └→ Stage 4 (shell) ──┐
             └────→ Stage 5 (repair) ───┼→ Stage 6 (bench-off) → Stage 7 (V1-final)
```

Stages 4 and 5 are parallel-safe after stage 3.
Estimated total: 8–12 working sessions + GPU batch time.

---

## Out of scope for V1
- Dual-view (sharpened hypothesis documented in design §9 — after V1)
- Garment retrieval, wardrobe (V2/V3)
- LoRA fine-tuning (cloud GPU — deferred)
- Qwen-Image-2.0 — watch; if weights open, bench row 7

---

## Changelog (append-only)

- **2026-06-10** — initial plan created at restart. Measurement-first ordering (P9)
  replaces the archived plan's thin-loop-first ordering: the previous loop closed
  around unreliable evaluation and produced noise instead of knowledge.
- **2026-06-11** — E-002 interim findings integrated: color gate metric changes to
  CIEDE2000 + lightness normalization; thresholds provisional, finalized by E-005
  (E-005 row updated accordingly); per-item adaptive baseline from multi-view
  reference photos; PASS/WARN/FAIL zones. New E-013 (palette-mode calibration for
  patterned garments) added as pre-bench work item in Stage 6. Stage 1 execution
  notes extended. Design §6 updated in the same change.
- **2026-06-11 (Stage 1 closure)** — three carry-overs into Stage 2: E-005 now
  finalizes ALL three gate thresholds (Stage-1 calibrations used photo pairs with
  n=1 natural-variation samples; identity "same" pair was near-duplicate, cosine
  0.9896); E-005 method gains an owner mask-overlay review on first generated
  outputs (E-001 validated segmentation on real photos only, not the generator's
  domain); Stage 2 reporting discipline added — color-gate WARN always surfaced
  to owner, never aggregated.
- **2026-06-11 (diagnostic review)** — Config B (Lightning 4-step) confirmed for
  E-005; "Lightning required" conclusion rejected as confounded (Config A used
  cfg=1.0 + empty negative — Lightning-regime settings; fair no-Lightning config
  is a prerequisite for bench rows 2–3); 9-frames explanation downgraded to
  hypothesis; P8 retro-step (official QIE-2511 workflow comparison) made a
  blocking prerequisite for E-005 phase 1.
- **2026-06-12 (architecture review, owner-approved)** — post-E-005 system review
  integrated: mask sanity guard added as Stage 2 work item (build before E-006);
  Stage 4 face restore made conditional (ArcFace-triggered — identity measured as
  generator's strongest property); shell's proportion gap documented as known
  architectural limitation with escalation rule before Stage 7; Stage 3 person
  analysis re-scoped to minimal profile (general-prompts rule shrank its role);
  design §§5–8 updated in the same change (strategy C measured motivation,
  proportion gate as primary A-vs-C bench discriminator, advisory texture
  indicator in bench metrics).
