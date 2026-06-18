# CURRENT STATE — Open Source Stylist

**Snapshot date:** 2026-06-15
**Purpose:** one honest, non-append-only view of what is true *right now*. Where this
file and an older document disagree, this file wins for "current status"; the older
document remains valid as a dated historical record. Full reasoning lives in `audit/`.

---

## TL;DR

The repository is a **research lab with several sound components, not a working
stylist**. The core architectural direction (edit engine + deterministic preservation
+ measured acceptance + per-item repair) is reasonable. But:

1. There is **no end-to-end pipeline** — no orchestrator, no analysis/evaluation/repair
   modules (they are promised in `BUILD_PLAN.md:280-348` and absent from the tree).
2. There is currently **no decision-grade fact about generated-output quality.** Every
   such "confirmation" was demoted by the 2026-06-13 ERRATUM in `knowledge/verified.md`
   (the generation prompt never expressed the transfer task).
3. Several instruments measure something **narrower than the criterion they are filed
   under** (see "Instruments" below). The gate *code* documents this honestly; the
   BUILD_PLAN/design instrument ledger over-claims coverage.
4. What is labelled V1 is **Try-On V1, not Stylist V1**: the style decision and the
   selection of concrete garments are not modelled at all yet.

Evidence-wise the project is closer to the end of Stage 1 than to E-007.

---

## What IS decision-grade right now

Only these survive the 2026-06-13 ERRATUM (`knowledge/verified.md:493-522`):

- **V-ENV-001** — environment facts (ComfyUI :8000 v0.24.1, RTX 4090 Laptop 16GB, LM
  Studio :1234, Qwen3-VL-8B).
- **V-SEG-001/002/003/004** — segmentation on the static person/garment photos, and the
  "simplest noun wins" prompt rule.
- **V-COLOR-001, V-ID-001, V-PROP-001** — gate threshold *calibrations on static photos*
  (no generation involved): color ΔE PASS≤3/WARN3-5/FAIL>5; identity cosine≥0.57;
  proportions ≤5.3%.
- **V-QIE-001** — output frame formula `4*layers+1`; frame01 is the real output.
- **V-RES-002** — no OOM up to 1.79 MP on this GPU.

Everything else in `verified.md` that was "confirmed on generated images"
(V-VAR-001, V-COLOR-002, V-ID-002, V-PROP-002, V-RES-001, and the E-008 absolute
magnitudes) is **NOT decision-grade** until E-007 re-baseline. The cropped-crop *rule*
V-REF-001 still stands (owner-confirmed on direct visual evidence).

The per-experiment conclusions for E-005 / E-006 / E-008 now carry a CONFOUNDED banner
pointing here and to the canonical erratum.

## What exists in code (live tree)

- ComfyUI client + poll/free, frozen-board hash verification (`system/adapter/panel.py`).
- Prompt construction, GroundingDINO+SAM1 segmentation, segmentation sanity guard.
- Three measurement gates: color, identity (ArcFace), proportions.
- Two deterministic shell modules: `color_match.py`, `background_restore.py`.
- Two workflow templates (full + Lightning), a template filler, JSON contracts.
- Experiment runners E-001…E-008; E-007 v2 is the most recent (closed, mixed verdict).

## What is promised but MISSING

`system/analysis/`, `system/evaluation/`, `system/orchestrator.py`,
`system/shell/face_restore.py`, `system/repair/` — all referenced in `BUILD_PLAN.md`
and none exist. There is no single command `photo + outfit → final image + verified
report`, no retry/repair routing, no VRAM sequencing, no final verdict owner.

## Instruments — what they actually measure

- **Color gate** (`gates/color.py`): mean CIEDE2000 with `normalize_l=True` → a HUE/CHROMA
  indicator, blind to absolute lightness. `delta_e_p90` compares each output pixel to the
  reference *mean*, so it reflects the region's internal texture spread, not a mismatch
  percentile. Honest indicator, misleading name. Does **not** verify "same garment".
- **Proportions gate** (`gates/proportions.py`): row-pixel widths of the *clothed*
  silhouette. Volume sleeves / peplum / skirt change width without changing the body, so
  this is **not** a body-distortion verdict. Reports `framing_delta_pct` to flag invalid
  comparisons (head/feet crop).
- **Identity gate** (`gates/identity.py`): ArcFace cosine, **face only** — not hair, skin,
  body, pose, or background. Threshold 0.57 from a 4-pair calibration (1 same-person pair).

## Foundation defects (status)

| ID | Defect | Status 2026-06-15 |
|---|---|---|
| P1-1 | `pytest` collection ran a real GPU job (`test_layers1.py`, no guard) | **fixed** — renamed `diag_layers1.py` / `diag_configs.py`; pytest no longer collects them |
| P0-3 | E-005/006/008 conclusions said "Promoted to Verified", contradicting the erratum | **fixed** — CONFOUNDED banners added |
| P0-2 | cfg / sampler / scheduler / negative prompt never reached the workflow | **fixed** — both templates parameterized, `fill_workflow` now fails loud on residual `__PLACEHOLDER__`; E-007's closed state files store the pre-change template hash (read-only `--summary` unaffected, re-running a closed phase would correctly hash-mismatch) |
| P0-1 | no end-to-end orchestrator | open — design decision pending |
| P0-4 | instrument ledger over-claims coverage | open — doc fix (gates themselves are honest) |
| P0-5 | `color_match` round-trips the whole image; `background_restore` hard-fails on size mismatch, no feather | open |
| P2-4 | no git remote; `.git` 303 MB from `!experiments/**/*.png`; `settings.local.json` tracked | open — needs backup before any cleanup |

## Where the full analysis lives

- `audit/AUDIT_REPORT_2026-06-15.md` — file-by-file technical audit (independently
  re-verified against the code, 2026-06-15).
- `audit/CONCEPT_ARCHITECTURE_REVIEW_2026-06-15.md` — product/architecture critique
  (Stylist vs Try-On gap, contracts, success-at-outfit-level math).
- `audit/IMPLEMENTATION_BLUEPRINT_2026-06-15.md` — proposed forward stack and work
  packages. External citations spot-checked (Qwen3.5-9B, Garments2Look 2603.14153,
  FashionSigLIP all real); the license-gating claims (Sapiens2/FastFit/OmniTry) still
  need verification before they exclude options.

## Immediate next steps (foundation before more experiments)

1. ✅ Remove GPU side-effect from pytest collection.
2. ✅ Request params (cfg/sampler/scheduler/negative) now reach the filled workflow;
   `fill_workflow` fails loud on any residual `__PLACEHOLDER__`.
3. ✅ One canonical state (this file) + confounded banners + audit docs filed under `audit/`.
4. ◻ Backup/remote before any git size cleanup; then decide LFS / experiment-image policy.
5. ◑ Vertical slice built — `system/run_slice.py` (validated input → exact request →
   exact filled workflow → output+hashes → segmentation+sanity → honest gates → owner
   checkpoint; no repair/VLM). Dry-run reproducibility verified on outfit_001 (Lightning
   cfg=1.0 and full-engine cfg=2.5 both thread through, zero residual placeholders). The
   live `--generate` run is the next owner checkpoint (needs ComfyUI; produces an image
   for visual judgment).
6. ◻ Only after the slice is reproducible: a corrected feasibility bench on ≥2-3 people
   and outfits, with a numeric kill-criterion — before building any catalog/stylist shell.

---

## Active work 2026-06-16 — E-010 garment-faithful try-on (FitDiT)

Generation has moved to a garment-first try-on architecture (see
`experiments/010_protect_by_construction/`: protocol, ENGINE_LANDSCAPE, GEN_INSTRUMENTS, EVAL_INSTRUMENTS).

- **Priority:** garment fidelity = **axis #1** (showing the SPECIFIC item is the product); identity #2;
  body morphology #3 (the QIE ~9% hip slim is non-blocking polish).
- **Engine:** **FitDiT** is the per-garment detail core (strongest open model for detail; ComfyUI; ~16GB).
  E-010 results: **blouse PASS** (owner), **skirt FAIL** (crop slit → FitDiT renders pants). Identity ~0.97
  preserved (FitDiT only edits the masked region). Garment instrument (FashionSigLIP retrieval-rank + DISTS)
  **PENDING_CALIBRATION** → axis #1 is owner-eye-only for now.
- **V1 pipeline:** chained FitDiT on the **source** in the KNOWN layer order (occlusion masks); layering emerges
  from pass order. **QIE holistic dropped for V1** (outfit logic is given, not discovered) → deferred to V2+.
  Accessories via OmniTry. **AnyDressing** (multi-item one-pass, NC) under evaluation as an alternative core.
- These are single-garment runs — the assembled full outfit is not produced yet. FLUX-Fill text-only build
  disqualified (garment from text ≠ image).
- **Drape/placement — universal mechanism (ALL elements), see `experiments/010.../DRAPE_SYNTHESIS.md`:**
  mask/placement is **computed**, not hand-tuned — measure each element's **body-relative fraction on its
  on-model photo** (MediaPipe pose + GroundingDINO/SAM) and transfer to the target's pose. Scale-invariant;
  per-element anchored (waist/shoulders/ears/feet…); occlusion-subtracted by the layer graph; engine-agnostic
  (FitDiT / OmniTry / warping). Placement and fidelity are the two separate axes.
- **E-010 evidence so far:** skirt topology FIXED via a **continuous silhouette** (slit kept as a line, not a
  through-gap → was rendering pants). Foundation built (`system/drape.py`: BodyModel + GarmentDescriptor +
  synthesizer). Length must come from **on-model measurement** (the pixel-ratio placeholder undershot a maxi to
  mid-calf). Fidelity (<100%) is the engine axis → warping.
- **2026-06-18 — measure_on_model + chain verified:** `measure_on_model` implemented + generalised (universal
  primitive: pose + GDINO/SAM → scale-invariant body-relative fractions, any element via anchor/end);
  `agnostic_mask` generalised (`hem_y = anchor_y + frac·(end_y−anchor_y)`). Skirt re-run at the measured maxi
  length (frac 0.917, hem near ankle) — owner: length + topology accepted ("більш менш"). **Chained FitDiT on
  the source verified** (`proto_chain.py`): skirt→blouse, layering emerges from pass order + native-mask overlap
  (blouse peplum over skirt waist). Identity cosine skirt-only **0.976**, chain final **0.929** (≥0.57). Lesson:
  the blouse needs NO mask dilation — FitDiT's native Upper-body mask overlaps the skirt; the earlier
  `_dilate_down` grew the mask the WRONG direction (upward into the face → identity smear), now removed.
- **2026-06-18 — axis #1 now measured (advisory):** the FashionSigLIP/DISTS instrument runs end-to-end on the
  chain result (`proto_fidelity.py`, reusing the per-pass region masks — no ComfyUI). First numbers: both
  rendered items rank **#1/5** vs the outfit decoys (recognisable as their targets). Blouse DISTS **0.211** /
  sim **0.925** (≈ the calibrated "same garment, other view" level 0.21; margin 0.253) — strong. Skirt DISTS
  **0.319** / sim **0.823** (between "same" 0.21 and "different" 0.37; margin only 0.086 over the belt) — the
  weaker item, matching the olive-vs-brown + narrow-silhouette eye verdict. ADVISORY only: a labelled
  calibration set is still required before these are decision-grade.
- **2026-06-18 — warping head-to-head for the skirt: CLOSED (negative).** Arm B (geometric pixel warp): exact
  colour but pasted/flat, DISTS 0.41 > FitDiT 0.319 → loses. Arm C (**Leffa**, MIT, installed standalone — torch
  2.6+cu124 + prebuilt detectron2 + densepose + truststore SSL): renders **trousers, not a skirt** on our person.
  Neither warp beats FitDiT. **FitDiT + drape mask stays the skirt engine.**
- **2026-06-18 — DEEP investigation (owner challenged "VTON can't do skirts" — correctly).** Isolation study
  (`leffa_skirt_runner.py` + `reframe_person.py`): Leffa **install is correct** (example tee transfers perfectly)
  and **Leffa CAN render skirts** (clean skirt on a DressCode example person → proper skirt). The failure is
  **person-distribution + densepose-dominant conditioning**: Leffa conditions topology on the target's **densepose
  IUV**, which **dominates the inpaint mask** (continuous drape mask → still trousers, narrow). Our in-the-wild
  person standing legs-together in jeans → conditional favours trousers; reframing to white-bg/tight transferred
  the colour but NOT the topology. **Why FitDiT wins on the SAME person:** its custom IMAGE mask + garment dominate
  topology (obeys our continuous mask); Leffa's densepose dominates → legs. NOT a fundamental limit, NOT the
  install, NOT diffusers (0.31==0.38), NOT the mask alone. Fix order: FitDiT+drape (robust, works) → cloud
  (FASHN/Kling, robust to in-the-wild) → Leffa only with a fully in-distribution person+garment (brittle).
- **Open:** skirt colour fix (reference colour-transfer on FitDiT, or cloud) — warping ruled out; labelled
  calibration set for the garment instrument (decision-grade thresholds); accessories (belt/earrings/shoes via
  OmniTry — install/VRAM unverified); jeans-below-hem cleanup (skin-inpaint, the agnostic-canvas axis).
