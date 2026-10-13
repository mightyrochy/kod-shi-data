# E-009 — QIE config comparison (body · face · item colour): Lightning vs fair no-Lightning

**Status:** APPROVED 2026-06-15 (owner-signed, §"Owner sign-off"). Phase 1 pending.
**Created:** 2026-06-15
**Governed by:** METHODOLOGY.md §2; BUILD_PLAN Stage 6 ("a fair no-Lightning config is a
separate work item, required before bench rows 2–3", BUILD_PLAN.md:174-176).

---

## 1. Question

Which QIE-2511 generation config better serves the V1 goal on outfit_001 — **Lightning
4-step (cfg 1.0)** or a **fair no-Lightning regime (20-step, cfg ≈ 5)** — judged across the
preservation/fidelity axes together, not body alone:

- **Body shape** (skeletal, `body_pose.py`) — the originally-motivating defect;
- **Face identity** (ArcFace cosine);
- **Item colour** per garment (per-region ΔE + hue/chroma split).

Body motivated this: Lightning narrows the **hips ~9% with shoulders held** (s42 −8.8% /
s123 −8.9%, pose match ≤3°, visibility 0.999, consistent across seeds). But config choice
also moves face and colour — a confounded full-model probe on 2026-06-15 (cfg 2.5, empty
negative) happened to give an excellent blouse ΔE (0.28) yet wrecked the skirt colour and
dropped identity to 0.63. So the config must be chosen across **all** axes, per-item, not on
one number.

That probe is **INVALID and discarded**: cfg 2.5 is the confounded under-guided config
BUILD_PLAN.md:169-176 / :381-384 warns against (no-Lightning needs **cfg ≈ 4–7**). The fair
row is only now runnable because cfg/sampler/negative reach the engine after the P0-2 fix
(commit 5bec8a9). Out of scope: the negative channel (held empty on both arms, isolated by
E-014) and raising Lightning steps (archive/WORKFLOW.md:60-61, "40 steps confirmed worse").

---

## 2. Decision informed

Which regime to adopt as the V1 generation baseline, decided on a **per-axis** basis (body,
face, each item's colour) — feeding the engine/regime decision (BUILD_PLAN Stage 6) and the
body-fidelity kill-criterion (morphology = identity, evaluation criterion 1). A config that
wins one axis but breaks another (e.g. great blouse colour, distorted body) does NOT win.

---

## 3. Method

### 3.1 Arms (regime comparison, negative held empty)

| Arm | Engine / workflow | Steps | CFG | Negative |
|-----|-------------------|------:|----:|----------|
| R1 — Lightning | `qie2511_vton_lightning` (4-step LoRA) | 4 | 1.0 | empty |
| R2 — fair full model | `qie2511_vton` (no LoRA) | 20 | **5.0** | empty |

cfg=5.0 is the midpoint of the documented 4–7 band. If R2 is ambiguous (see §4 guard), a cfg
bracket (4.0, 7.0) is the first follow-up — NOT a return to seed/prompt tweaking.

### 3.2 What varies / what is fixed

Varies: generation **regime** only (Lightning-on 4-step cfg1 vs Lightning-off 20-step cfg5),
bundled exactly as BUILD_PLAN frames rows 1 vs 2/3. Fixed:

| Parameter | Value |
|-----------|-------|
| Person image | `assets/person/person_front.png` |
| Outfit / board | `outfit_001` / `hybrid_mask_crop` (frozen PNG, SHA-256 verified) |
| Prompt | task-correct `build_prompt(pkg, reference_board_variant="hybrid_mask_crop")` |
| Resolution | 720×1024 · Layers 2 · Denoise 1.0 · sampler euler / scheduler simple |
| Seeds | [42, 123] (primary); 456 for tie-break (colour/face have higher seed variance) |

### 3.3 Measurement per output — three co-primary axes (all already produced by `run_slice`)

| Axis | Metric | Notes |
|------|--------|-------|
| **Body** | `body_pose`: hip_width_norm %, shoulder_width_norm %, ratio %, pose_mismatch_deg, visibility | clothing-robust; pose_mismatch < 10° required for a valid comparison |
| **Face** | ArcFace cosine vs `person_front` | face only — not hair/skin/body |
| **Item colour** | per region (top, bottom, belt, earrings, shoes): ΔE + hue_delta + chroma_delta + hue_reliable | judged **per item**; dark/low-chroma items are hue-unreliable (flagged) |
| Layering / sanity | mask sanity flags, garment-overlap | advisory; a flagged output is read with caveat |

No aggregate score. Each run writes a full manifest (input hashes, filled workflow, output
hash) under `runs/`; manifests + `generated.png` for both arms are copied into
`experiments/009_body_preservation/results/` so the record is self-contained.

### 3.4 Phases

- **Phase 1 (GPU):** generate R1 and R2 for seeds [42, 123]; run the full gate suite per output.
- **Checkpoint (owner):** per arm, review `generated.png` and judge the four criteria
  (same person incl. body, all items present, layering, colour/texture). The owner verdict,
  not any gate, is the acceptance.
- **Phase 2:** assemble the per-axis comparison table (R1 vs R2, both seeds), apply §4, write
  `conclusion.md`.

---

## 4. Acceptance criteria (fixed before results are seen)

Reported as a **per-axis table** (R1 vs R2). A config wins only if it does not regress a
critical axis. Baselines from R1: hip ≈ −8.85%, shoulder ≈ −1.3%, face cosine ≈ 0.78
(s42 0.806 / s123 0.75).

**Body (skeletal):**
- R2 |hip change| ≤ **4.5%** (≥ half removed), shoulders not worse, owner "same body" → slimming
  is a Lightning-regime artifact.
- R2 |hip change| ≥ **7%** on a VALID output → slimming intrinsic to QIE → config is not the
  fix → escalate (composite/conditioning or accepted floor).
- 4.5–7% / ambiguous → cfg bracket (4, 7).

**Face identity:**
- Report cosine per seed; both arms must clear 0.57 to be valid. Flag any arm whose mean
  drops > the E-005 noise floor (0.04) below the other; large face loss is a config cost.

**Item colour (per item):**
- For each of the 5 items, record ΔE verdict (PASS≤3 / WARN / FAIL) **and** the hue/chroma
  diagnosis. Count, per arm, items reproduced within PASS/WARN and flag any item a config
  visibly breaks (e.g. the cfg-2.5 probe's green skirt). hue is only decisive when reliable.
- Owner confirms per item; do not treat a low ΔE on a hue-unreliable (dark) item as a pass.

**Overall:** owner picks the config from the per-axis table, weighing tradeoffs (e.g. better
colour vs worse body) and the one measured cost of no-Lightning here: **~5× slower** (213s vs
44s) and a cfg that must be tuned in 4–7. (Head-cropping above ~1024px is a *Lightning* failure
at off-tuned resolution per V-RES-001 — NOT a no-Lightning con, and irrelevant to E-009, which
fixes both arms at 720×1024. Whether no-Lightning *unlocks* higher resolution without that crop
is a separate Stage-6 row-3b question, not tested here.)

**Validity guard (prevents repeating the 2026-06-15 confound):** if R2 fails identity
(cosine < 0.57) or the owner calls the output broken/blurred, the row is an **invalid config**,
NOT "the full model is worse." Re-tune cfg within 4–7 and rerun before recording any
no-Lightning conclusion.

**Knowledge:** record per-axis findings in `knowledge/` with the per-seed numbers and owner
verdicts — including whether body slimming is Lightning-specific, intrinsic, or inconclusive.

---

## 5. Runner

`experiments/009_body_preservation/run_e009.py` — a thin wrapper over
`system.run_slice.run_slice` per (arm, seed); collates body/face/colour into a per-axis table
and copies each run's manifest + `generated.png` into `results/`. No new generation logic; it
reuses the audited vertical slice so every parameter provably reaches the engine.

---

## 6. Cost estimate

| Step | Est. time |
|------|-----------|
| R1 Lightning ×2 seeds (gen + segment + gates) | ~6–8 min |
| R2 full model ×2 seeds (20-step gen ~3.5 min each + segment + gates) | ~12–16 min |
| **Total GPU time** | **~20 min** |

---

*Protocol written 2026-06-15. Answers the Lightning-vs-fair-no-Lightning config question
across body/face/colour on outfit_001, one person. Generalisation across people/outfits/poses
is NOT claimed and belongs to the Stage-6 matrix / a wider benchmark.*

---

## Owner sign-off

- [x] Arms, fixed config, and the cfg≈5 fair no-Lightning value approved.
- [x] Three co-primary axes (body, face, item colour) and the per-axis decision rules approved.
- [x] Validity guard approved before any run.

**Signed:** owner, 2026-06-15 (approved in session; status → APPROVED, ready for Phase 1).
