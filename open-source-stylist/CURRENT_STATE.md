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
