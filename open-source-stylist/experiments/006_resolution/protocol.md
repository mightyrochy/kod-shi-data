# E-006 — Resolution sensitivity (does generation resolution change measured quality?)

**Status:** CLOSED — executed 2026-06-12; see `conclusion.md` and `results/`
**Created:** 2026-06-12
**Governed by:** METHODOLOGY.md §2; BUILD_PLAN Stage 2

---

## 1. Question

Does the generation resolution materially change measured gate scores (identity,
color ΔE, body proportions), and if so, which resolution gives the best combination
of quality, speed, and VRAM safety?

---

## 2. Decision informed

**Working resolution for all remaining Stage 2–7 experiments and production.**
Currently inherited from E-005 (720×1024, `max_side=1024`).  This experiment either
confirms that value or selects a better one on evidence.

The decision is taken once.  All subsequent experiments (E-008, E-007, bench-off)
use the resolution chosen here.

---

## 3. Method

### 3.1 What varies

| Tier | Resolution | max_side | Megapixels |
|------|-----------|----------|------------|
| Low  | 576×816   | 816      | 0.47 MP    |
| Baseline | 720×1024 | 1024 | 0.74 MP (**E-005 data; 5 seeds already exist**) |
| High | 896×1280  | 1280     | 1.15 MP    |
| High+ | 1120×1600 | 1600   | 1.79 MP    |

Resolution is the **only** variable.  All other parameters are frozen at the
E-005 config (Lightning 4-step, layers=2, same seeds).

### 3.2 What is fixed

| Parameter | Value |
|-----------|-------|
| Model | `qwen_image_edit_2511_fp8mixed.safetensors` |
| LoRA | `flux_lightning_4step_lora.safetensors` |
| Steps | 4 (Lightning) |
| Sampler | euler |
| Scheduler | simple |
| CFG | 1.0 |
| Denoise | 1.0 |
| Layers | 2 |
| Person image | `assets/person/person_front.png` |
| Outfit | `outfit_001` |
| Reference panel | **reuse the panel built for E-005** — same panel for all three tiers; panel is not resolution-dependent |
| Seeds | [42, 123, 456, 789, 1337] (same as E-005) |

K = 5 seeds per tier.  Baseline tier (720×1024) reuses E-005 gate results
directly — no new generation needed for that tier.  New generation: 5 (Low) + 5
(High) + 5 (High+) = **15 new images**.

### 3.3 Measurement per output

After each generation: segmentation (with sanity guard applied to every mask),
then all three gates:

| Gate | Metric |
|------|--------|
| Identity | ArcFace cosine vs `person_front.png` face |
| Color (per-region) | CIEDE2000 + L* normalization; mean ΔE for top, bottom, belt, earrings, shoes |
| Proportions | max(shoulder/waist/hip abs_change_pct) vs `person_front.png` |

Any sanity guard flag is recorded verbatim in `results/`.  Flagged masks are
reported to the owner with an overlay before that seed's gate values are used.

### 3.4 VRAM monitoring

Log VRAM usage via `nvidia-smi` before and after each generation.  If any tier
triggers an OOM or causes a queue stall, stop that tier and record the failure —
VRAM OOM is a legitimate experimental outcome, not an error to retry through.
High+ (1120×1600, 1.79MP) pushes close to the 16GB ceiling and may OOM; this is
expected and useful data about the system's ceiling.

### 3.5 Timing

Record wall-clock time per generation (from workflow submit to image download).
VRAM pressure and generation time both inform the resolution choice.

---

## 4. Acceptance criteria

Defined before results are seen.

### 4.1 Per-tier summary table

One row per tier: mean ± std for identity cosine, per-region color ΔE (top, bottom,
shoes), proportions max_abs_pct, mean generation time (seconds), peak VRAM (MB).

### 4.2 Resolution choice rule

Choose the resolution that satisfies **all** of the following:

1. **Identity:** no tier drops mean cosine > 0.05 below the E-005 baseline (0.830).
   A drop > 0.05 = significant identity degradation.
2. **Proportions:** tier does not materially worsen the already-failing proportions
   score (already 11.16% mean at baseline — a further +5 pp would indicate the
   resolution change itself distorts proportions).
3. **VRAM:** no OOM on the RTX 4090 Laptop (16GB).
4. **Time:** generation time < 3× the baseline tier's time.

**If all tiers pass:** choose the lowest resolution that does **not** degrade
measured quality vs baseline by more than the noise floor (identity std 0.040,
color std per-region from E-005).  Prefer lower resolution where quality is
indistinguishable — it costs less GPU time.

**If High+ OOMs:** record the VRAM ceiling; continue with remaining tiers that
completed.  High+ OOM is an expected and informative outcome — it documents the
system's physical limit.

**If High OOMs too:** record; choose between Low and Baseline on quality data.

**If no tier passes criterion 1 or 2:** escalate to owner — this is a new finding
that requires a decision, not a mechanical resolution selection.

### 4.3 Knowledge entries

Document in `knowledge/verified.md`:
- V-RES-001: chosen working resolution and the data justifying it.
- V-RES-002: VRAM ceiling — highest resolution that completes without OOM, with
  peak VRAM recorded for all tiers that ran.

---

## 5. Runner

`experiments/006_resolution/run_e006.py` — to be written before execution.

Sequence:
1. Reuse the E-005 panel (path from `experiments/005_variance_baseline/results/panels/reference_panel.png`).
2. Load `outfit_package.json`; confirm panel path exists.
3. For each tier in [Low, High, High+] (baseline data already exist for 720×1024):
   a. For each seed in [42, 123, 456, 789, 1337]:
      - Build workflow with the tier resolution.
      - Upload person image + panel to ComfyUI.
      - Log VRAM before submit (`nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits`).
      - Submit, poll, download output; record wall time.
      - Log VRAM after download.
      - Save to `results/{tier}_{resolution}/seed_{seed}/generated.png`.
4. `POST /free` after each tier to reclaim VRAM.
5. Segmentation + sanity guard on every new output.
6. Gate computation on all outputs (new + E-005 baseline reuse).
7. Assemble per-tier summary; save `results/measurements.json`.

**Checkpoint:** after all tiers' generations are done (before gate computation),
save all overlays to `results/{tier}/seed_{seed}/overlays/`.  If any sanity flag
fires, stop and report to owner before continuing.

---

## 6. Cost estimate

| Step | Estimated time |
|------|---------------|
| Low tier: 5 × Lightning 4-step at 576×816 | ~5–10 min |
| High tier: 5 × Lightning 4-step at 896×1280 | ~10–20 min |
| High+ tier: 5 × Lightning 4-step at 1120×1600 (if no OOM) | ~15–25 min |
| Segmentation of 15 new outputs | ~5–15 min |
| Gate computation (CPU) | <1 min |
| **Total GPU time** | **~35–70 min** |

---

## 7. Integration FAIL test

Covered by `system/tests/test_segmentation_fail.py` (written before this
experiment, 2026-06-12): tests verify the sanity guard fires on synthetic
bad masks before guarding any real experimental data.

---

*Protocol written 2026-06-12. Historical experiment; see `conclusion.md` for the
recorded result and later task-conditioning errata.*
