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

## V-VAR-001 — E-005 variance profile / noise floor (2026-06-12, K=5 seeds)

Source: `experiments/005_variance_baseline/`, Lightning 4-step, outfit_001.

| Gate | Metric | mean | std | range |
|------|--------|------|-----|-------|
| Identity (ArcFace cosine) | cosine | 0.830 | 0.040 | 0.776-0.874 |
| Proportions (max_abs_change_pct) | % | 0.00 | 0.00 | 0.00-0.00 |
| Color top (CIEDE2000) | dE | 3.52 | 1.32 | 1.17-5.17 |
| Color bottom | dE | 2.97 | 1.33 | 1.29-5.15 |
| Color belt | dE | 3.00 | 0.84 | 2.22-4.41 |
| Color earrings | dE | 3.67 | 1.28 | 2.45-5.65 |
| Color shoes | dE | 14.03 | 6.04 | 8.19-25.21 |

Noise floor: differences below ~1.3 dE (color) or ~0.04 cosine (identity)
are within natural generation variance, not signal.
Shoes show systematic FAIL (not noise) -- cause under investigation.

---

## V-COLOR-002 — Color gate thresholds confirmed on generated-vs-reference distribution (2026-06-12, E-005)

Confirms V-COLOR-001 provisional thresholds. Real generated-vs-reference distribution
(K=5, outfit_001) is consistent with calibrated thresholds -- no revision required.

| Verdict | dE range | Confirmed |
|---------|----------|-----------|
| PASS    | <= 3.0   | yes |
| WARN    | 3.0-5.0  | yes -- correctly captures perceptual borderline zone |
| FAIL    | > 5.0    | yes |

Owner observation (2026-06-12): at dE 3-5, color discrepancy is perceptually
borderline -- visible difference driven more by texture flatness than by color offset.
WARN zone correctly requires owner review rather than automatic pass or fail.

**Scope note added 2026-06-12 (code review):** the color gate runs with
normalize_l=True, which removes a uniform L* (lightness) offset before measuring.
It therefore gates HUE and CHROMA fidelity, not absolute lightness — a too-dark or
washed-out garment of the correct hue can still PASS. This is deliberate (lighting/
drape differ between flat product photo and worn garment), but it confirms the owner
observation mechanistically: the "texture flatness" that dominates perception at
dE 3–5 lives in lightness/texture, which this gate does not cover. The bench-off's
advisory texture indicator (design §8) is the intended cover for that gap.

---

## V-ID-002 — Identity gate threshold confirmed on generated images (2026-06-12, E-005)

Confirms V-ID-001 provisional threshold (0.57). All 5 generated seeds scored
>= 0.776 (min). Large margin above threshold preserved even with generator-induced
facial changes. No revision required.

Threshold: cosine >= 0.57 -> PASS.

---

## V-PROP-002 — Proportions gate threshold confirmed on generated images (2026-06-12, E-005)

Confirms V-PROP-001 provisional threshold (5.3%). All 5 seeds scored 0.00%.
Generator preserves body proportions with no measurable distortion on outfit_001.
No revision required.

Threshold: max_abs_change_pct <= 5.3% -> PASS.

---

## V-SEG-004 — Segmentation prompts for generated images (2026-06-12, E-005 Checkpoint 2)

GroundingDINO prompts that work correctly on AI-generated full-body images.
General single-word queries outperform compound queries (owner principle confirmed
empirically: compound/specific prompts return full-body bounding boxes).

| Region | Working prompt | Verified behavior |
|--------|---------------|-------------------|
| top (blouse/shirt) | "shirt" | 11.5% of image, rows 17-56% |
| bottom (skirt) | "skirt" | correct region |
| shoes/footwear | "footwear" | 0.4% of image, rows 95-100% |
| belt | "belt" | correct region |
| earrings | "earrings" | correct region |
| face | "face" | correct region |
| person (silhouette) | "person" | correct region |

Prompts that FAIL on generated images (return full silhouette):
- "top" -> full body bounding box
- "shoes . sandals . wedge" -> full body bounding box

Rule: use the simplest recognizable noun. Compound queries with "." separator
are unreliable on generated images with synthetic textures.

---

## V-VAR-001 correction — proportions row (2026-06-12, instrument bug fix)

Proportions row in V-VAR-001 was wrong: `run_e005.py` used `.get("max_abs_change_pct", 0)`
on a key absent from `compare()` output → silently scored 0.00% for all seeds.

Corrected proportions data (K=5, same seeds):

| Gate | mean | std | range |
|------|------|-----|-------|
| Proportions (max_abs_change_pct) | 11.16% | 3.07% | 7.03–16.0% |

All 5 seeds FAIL (threshold 5.3%). Noise floor for proportions cannot be estimated —
systematic signal dominates. V-VAR-001 original table should be read with this correction
applied to the proportions row.

---

## V-PROP-002 reversal — instrument bug corrected (2026-06-12)

Supersedes V-PROP-002 (2026-06-12). The original entry was based on wrong data.

**Bug:** `run_e005.py` used `.get("max_abs_change_pct", 0)` on a key absent from
`compare()` output. Fix: key added to `proportions.py compare()` return dict;
runner updated to direct key access with RuntimeError on None. `measurements.json`
verdicts corrected from existing numeric data (shoulder/waist/hip pcts were accurate).

**Corrected finding:** QIE-2511 Lightning (4-step, layers=2) systematically distorts body
proportions beyond the 5.3% threshold on outfit_001.

| Seed | shoulder | waist | hip | max_abs | Verdict |
|------|----------|-------|-----|---------|---------|
| 42   | +3.64%   | −4.18% | +7.03% | 7.03%  | FAIL |
| 123  | +12.63%  | −2.11% | +4.61% | 12.63% | FAIL |
| 456  | +5.69%   | −8.27% | +9.03% | 9.03%  | FAIL |
| 789  | +7.58%   | −11.09%| +5.77% | 11.09% | FAIL |
| 1337 | +16.0%   | −9.99% | +6.8%  | 16.0%  | FAIL |

Systematic direction: waist always narrows (−4% to −11%); shoulders always widen
(+4% to +16%); hips always widen (+5% to +9%).

Owner confirmed (2026-06-12, visual review of seed_1337 vs input): distortion is real.
Face, chest, hips, and waist all affected; not attributable solely to outfit silhouette
geometry. Other seeds may have partial silhouette contribution but pattern is consistent.

V-PROP-001 threshold 5.3% is correctly calibrated — it reliably detects real distortion.
The generator, not the threshold, is the failure. Cause under investigation (candidate:
H-PROPORTIONS, H-REF-CONTAMINATION).

---

## V-QIE-001 — QIE-2511 output frame count formula (2026-06-12, source code + 2 empirical runs)

Source: `comfy_extras/nodes_qwen.py` line 129 (ComfyUI 0.24.1); confirmed by
diagnostic runs in `experiments/005_variance_baseline/results/`.

`EmptyQwenImageLayeredLatentImage` creates a 5D latent:
`[batch_size, 16, layers+1, height//8, width//8]`

Qwen VAE uses causal 4x temporal compression (identical to video VAE convention).
Decoded output frame count:

**`output_frames = 4 * layers + 1`**

Empirical confirmations:
- layers=2 -> 9 frames (Config A and B in test_configs.py)
- layers=1 -> 5 frames (test_layers1.py, 2026-06-12)

**frame01 is always the primary generated output** (temporal position 0).
Frames 02..N are auxiliary temporal positions; always lower quality / blurry.

E-005 frozen config: layers=2, frame01 saved as output.

---

## V-RES-001 — Working resolution confirmed (2026-06-12, E-006, K=5 seeds × 3 tiers)

Source: `experiments/006_resolution/`, Lightning 4-step, outfit_001, seeds [42,123,456,789,1337].

**Working resolution: 720x1024 (max_side=1024) — FOR THE LIGHTNING 4-STEP CONFIG.**
Scope correction (2026-06-12): E-006 varied resolution only on the Lightning-4
config. This is a fact about the *Lightning + resolution* pairing, not about
QIE-2511 in general. The head-cropping interpretation (O-RES-002) is that the
Lightning LoRA is tuned near 720-1024px; a full-model (no-Lightning) config may
not crop at higher resolutions — and color dE was best at High+ (see note below).
The bench-off (Stage 6) therefore tests a no-Lightning High+ variant before any
"720x1024 is the working resolution" claim is generalized beyond Lightning.

| Tier | Resolution | Identity mean | PASS/5 | Proportions mean |
|------|-----------|--------------|--------|-----------------|
| baseline | 720x1024 | 0.830 | 5/5 | 11.16% |
| low | 576x816 | 0.491 (1 det.) | 0/5 | 24.68% |
| high | 896x1280 | 0.299 | 1/5 | 15.65% |
| high_plus | 1120x1600 | — (0 det.) | 0/5 | 32.35% |

Decision rule (protocol §4.2 criterion 1): no tier may drop mean cosine >0.05
from baseline (0.830). All three new tiers fail this criterion.

Root cause (observation): Low and High+ produce head-cropped outputs on most seeds
(face not detectable by ArcFace). High produces inconsistent identity (4/5 catastrophic).
QIE-2511 Lightning appears tuned for ~720-1024px images; significant deviation
causes compositional failures.

Note: color dE for top/bottom improves at higher resolution (High+ best: 1.54/1.65 dE
vs baseline 3.52/2.97). This gain cannot be exploited in current config — identity
failure is disqualifying.

**Caveat added 2026-06-12 (code review of proportions gate):** the proportions
column for low/high/high+ (24.68%, 15.65%, 32.35%) is NOT reliable as body
distortion. Those tiers produced head-cropped outputs, which changes the silhouette
bbox and therefore the fixed body-fraction zones the gate measures — the number
reflects framing change, not a 32% body distortion. The proportions gate now
reports `framing_delta_pct` so this is detectable going forward; the only sound
proportions reading at non-baseline tiers is "framing differs, comparison invalid".
The baseline 720×1024 row framed full body consistently (identity PASS, masks landed
correctly), so its proportions signal stands.

---

## V-RES-002 — VRAM ceiling: no OOM within tested range (2026-06-12, E-006)

Source: same as V-RES-001.

QIE-2511 Lightning (fp8mixed, layers=2) completed all 5 seeds without OOM at
1120x1600 (1.79MP) on RTX 4090 Laptop (16GB). VRAM ceiling not reached within
the tested range.

Peak VRAM readings (nvidia-smi, after generation):
- Low 576x816: ~10.6GB (includes model load on cold start)
- High 896x1280: ~4.0GB
- High+ 1120x1600: ~0.35GB (aggressive inter-seed offload at this resolution)

**Measurement caveat (2026-06-12):** these readings were taken AFTER each generation
completed, when ComfyUI had already offloaded the model — they are NOT true
in-generation peaks (a 0.35GB "peak" at the heaviest tier is physically impossible
for active sampling; same artifact explains the 346MB residual in O-RES-003). The
only sound conclusion is the binary one: no OOM occurred up to 1.79MP. If VRAM
headroom ever becomes a decision input, measure with sampling DURING generation.

---

## V-REF-001 — Adapter panel rule: garment-only crops mandatory (2026-06-13, E-008, K=5)

Source: `experiments/008_reference_crops/`, same config as E-005 (Lightning 4-step,
720x1024, outfit_001, seeds [42,123,456,789,1337]).

Raw (uncropped) product photos as the reference panel cause complete identity
collapse: mean cosine 0.008 (0/5 PASS) vs garment-only-crops baseline 0.830
(5/5 PASS). Gap = 0.822 — the two conditions are qualitatively different regimes,
not a graded trade-off. Owner confirmed visually: "абсолютно не та людина".

**Rule (decision-grade):** The reference panel MUST use garment-only crops.
Full product photos are disqualified as conditioning input for QIE-2511 in this
pipeline. This rule is implemented as the default in `system/adapter/panel.py`.

---

## V-REF-002 — H-REF-CONTAMINATION split verdict (2026-06-13, E-008, K=5)

Source: same as V-REF-001. Conditions: A = cropped (E-005 baseline), B = raw.

**Proportions — CONFIRMED as a contributing factor:**

| Condition | Mean max_abs_pct | vs threshold (17.3%) |
|-----------|-----------------|----------------------|
| A cropped | 11.16% | below |
| B raw | 21.52% | above → confirmed |

Raw is 10.36pp worse. Contamination accounts for ~10pp of the proportions
distortion. The remaining 11.16% baseline distortion (cropped condition) is
NOT from reference contamination — a different cause is active even with
garment-only crops. Next candidate: Lightning-specific behavior (bench rows 2-3).

**Shoes color — REFUTED:**

Raw shoes mean dE = 13.82, cropped = 14.03. Difference 0.21 is within the noise
floor (std 6.04). The systematic shoes FAIL (14 dE, 5/5 seeds) is not caused by
contamination from full product photos. Cause remains unknown.

**Identity — CONFIRMED (contamination mechanism):**

Raw panel destroys identity (cosine 0.008 vs 0.830). Mechanism: full-body product
photos cause the model to generate the product model's face/body instead of the
input person. This extends the contamination hypothesis beyond the originally stated
scope (proportions/items) to identity.

---
