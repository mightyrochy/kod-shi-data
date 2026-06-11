# Verified facts

Append-only, date-stamped. Promotion rules: METHODOLOGY.md §1 —
deterministic measurement reproduced in ≥2 independent runs, or explicit owner
confirmation on direct evidence. Decisions rest only on entries in this file.

---

*(empty at restart, 2026-06-10 — nothing from the previous attempt qualifies.
First expected entries: environment facts from `system/env_check.py` (Stage 0),
gate calibration thresholds (Stage 1).)*

---

## V-ENV-001 — Environment facts (2026-06-11, env_check.py, run confirmed GREEN)

Source: `python system/env_check.py`, both servers live, chat round-trip passed.

| Fact | Value |
|---|---|
| ComfyUI URL | http://localhost:8000 |
| ComfyUI version | 0.24.1 |
| Python (ComfyUI) | 3.12.11 |
| GPU | NVIDIA GeForce RTX 4090 Laptop GPU |
| VRAM total | 16376 MB |
| VRAM free (idle) | 15074 MB |
| RAM total | 32387 MB |
| LM Studio URL | http://localhost:1234 |
| LM Studio chat round-trip | 2454 ms (cold, model was just loaded) |
| VLM model key | qwen3-vl-8b-instruct |
| VLM format | GGUF Q4_K_M, 8B params, vision-capable |

Note: VRAM free measured with Qwen3-VL-8B loaded in LM Studio → ~1302 MB consumed by the VLM at idle. ComfyUI had no model loaded at measurement time.

---

## V-SEG-001 — Segmentation: person photo regions (2026-06-11, E-001, owner review)

Source: `experiments/001_segmentation_masks/`, GDINO SwinT (0.3 threshold) + SAM1 vit_h
via `comfyui_segment_anything`. Owner reviewed all overlays and rated each region.

Tool: `system/segmentation/grounded_sam.py`
Image: `assets/person/person_front.png`

All 8 regions rated **ok** by owner:
`person`, `face`, `hair`, `background`, `top`, `bottom`, `shoes`, `glasses`

Note on `face`: mask covers face area around glasses frame; lens apertures excluded —
acceptable, minimal downstream impact.

---

## V-SEG-002 — Segmentation: garment reference images (2026-06-11, E-001, owner review)

Source: same tool as V-SEG-001. Images: `assets/outfits/outfit_001/` (7 product photos).

| Image | Verdict |
|-------|---------|
| belt.jpg | ok |
| blouse_front.webp | partial — blouse isolated, buttons excluded |
| blouse_back.webp | partial — same |
| earrings_disc.webp | ok |
| shoes_wedge.webp | ok |
| skirt_front.webp | ok |
| skirt_back.webp | ok |

---

## V-SEG-003 — Button exclusion in blouse masks (2026-06-11, E-001, owner verdict)

Buttons on blouse_front/back excluded from SAM1 masks. Owner verdict: acceptable for V1.
Rationale: buttons <5% of mask area; color gate mean ΔE impact minor.
Re-evaluate trigger: high-contrast-button garment fails E-002/E-005 color acceptance.

---

## V-COLOR-001 -- Color gate thresholds (2026-06-11, E-002, owner confirmed)

Source: `experiments/002_delta_e_thresholds/`. Metric: CIEDE2000 + L* normalization.
Owner reviewed pool garment images at key hue-shift steps and confirmed verdicts.

| verdict | delta_e_mean    |
|---------|-----------------|
| PASS    | <= 3            |
| WARN    | 3 -- 5          |
| FAIL    | > 5             |

WARN goes to owner review.

**Thresholds are provisional** -- calibrated on product-photo pairs and synthetic
shifts. Final thresholds come from E-005 (real generated-vs-reference distribution).

Perceptual anchors (owner-confirmed):
- navy blouse 10 deg shift: dE=2.57 -- PASS upper limit
- navy blouse 12.5 deg shift: dE=3.02 -- FAIL
- dress pink 7.5 deg shift: dE=3.97 -- PASS upper limit
- dress pink 10 deg shift: dE=6.77 -- FAIL

Natural variation ceiling (Series B): dE=1.04 (same garment, front vs back).
Per-item baseline: skirt=0.68, blouse=1.04.

---

## V-ID-001 — Identity gate threshold (2026-06-11, E-003, PASS)

Source: `experiments/003_arcface_threshold/`, ArcFace buffalo_l (w600k_r50.onnx),
CPUExecutionProvider. All pairs detected, no failures.

| Pair | Type | Cosine |
|------|------|--------|
| person_front vs person_two_view_front | same | 0.9896 |
| person_front vs blouse_front (Model A) | different | 0.1188 |
| person_front vs skirt_front (Model B) | different | 0.1502 |
| Model A vs Model B | different | 0.0927 |

Gap = 0.8394 (same_min 0.9896 − diff_max 0.1502).

**Provisional threshold: 0.57**
- cosine >= 0.57 → PASS (same person)
- cosine < 0.57  → FAIL (different person)

Provisional: gap is large enough to survive moderate generator-induced facial
degradation, but final threshold is confirmed at E-005 when real generated images
are available.

Note: insightface runs on CPU only (CUDAExecutionProvider unavailable). Accurate;
GPU acceleration to be investigated before Stage 3.

---

## V-PROP-001 — Proportions gate threshold (2026-06-11, E-004, PASS)

Source: `experiments/004_proportions_threshold/`. Gate: `system/gates/proportions.py`,
score = max(|shoulder_change_pct|, |waist_change_pct|, |hip_change_pct|).
Masks: E-001 person_front mask (reused) + person_two_view front-crop (new segmentation).

| Pair | Type | max_abs_pct |
|------|------|-------------|
| SAN-00 | sanity | 0.00% |
| NAT-01 | natural variation | 0.35% |
| SYN-10 | synthetic +10% | 10.19% |
| SYN-20 | synthetic +20% | 20.18% |
| SYN-30 | synthetic +30% | 30.22% |

Gap = 9.84% (natural ceiling 0.35%, synthetic floor 10.19%).

**Provisional threshold: 5.3%**
- max_abs_change_pct <= 5.3% -> PASS (proportions preserved)
- max_abs_change_pct > 5.3%  -> FAIL (proportions distorted)

Provisional: calibrated on static photo pairs. Confirmed at E-005 with real
generated images. The 9.84% gap leaves substantial headroom.

---
