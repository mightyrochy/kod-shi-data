# E-005 — Variance baseline (generation noise floor + final gate thresholds)

**Status:** DRAFT — not yet run  
**Created:** 2026-06-11  
**Governed by:** METHODOLOGY.md §2; BUILD_PLAN Stage 2

---

## 1. Question

What is the natural run-to-run variance of the QIE-2511 generation path on a fixed
input, and what gate thresholds does that variance imply?

---

## 2. Decision informed

This experiment informs **three decisions**, all of which are currently provisional:

1. **Variance profile / noise floor** — all future gate comparisons rest on this.
   A difference below the noise floor is noise, not signal.
2. **Color gate thresholds (final)** — V-COLOR-001 thresholds (PASS ≤ 3, WARN 3–5,
   FAIL > 5) were calibrated on product-photo pairs and synthetic shifts; the real
   operating distribution is generated-vs-reference, which has not been measured.
3. **ArcFace identity threshold (final)** — V-ID-001 provisional threshold (0.57)
   was calibrated on a single same-person pair that was near-duplicate (cosine 0.9896);
   generator-induced facial degradation under normal editing conditions is unknown.
4. **Proportions threshold (final)** — V-PROP-001 provisional threshold (5.3%) was
   calibrated on static photo pairs; the generator's body distortion distribution is
   unknown.

All four provisional values are confirmed or revised here.

Additionally, this experiment closes the **segmentation-on-generated-images** gap:
E-001 validated SAM/GroundingDINO masks on real person photos and product shots.
Generated images have different texture, sharpness, and lighting distributions.
Before any gate values are computed, the owner reviews mask overlays on the first
generated output to confirm segmentation is usable in this domain.

---

## 3. Method

### 3.1 Frozen configuration (must not change during the run)

| Parameter | Value |
|-----------|-------|
| Model | `qwen_image_edit_2511_fp8mixed.safetensors` |
| CLIP | `qwen_2.5_vl_7b_fp8_scaled.safetensors` |
| VAE | `qwen_image_vae.safetensors` |
| LoRA | none (full 40-step, no Lightning) |
| Steps | 40 |
| Sampler | euler |
| Scheduler | simple |
| CFG | 1.0 |
| Denoise | 1.0 |
| Person image | `assets/person/person_front.png` |
| Outfit | `outfit_001` (`assets/outfits/outfit_001/outfit_package.json`) |
| Reference panel | built once by adapter v0, reused for all seeds |
| Resolution | auto-detected from person image by `adapter._auto_resolution` |
| Seeds | [42, 123, 456, 789, 1337] |

K = 5 independent runs.  Seeds are fixed and documented.  Any re-run uses the
same seeds — a changed seed is a new data point, not a replacement.

### 3.2 Reference panel

Built by `system/adapter/panel.py` (GroundingDINO + SAM1 garment crops, tiled 3×3
grid, cell_size=256).  Built once before generation; reused for all 5 seeds.

### 3.3 Segmentation of generated outputs

After the first generation (seed=42) and **before computing any gate values**:

1. Run segmentation on the generated image (same `grounded_sam.segment` call).
2. Save and review mask overlays for all regions relevant to outfit_001:
   `person`, `face`, `hair`, `background`, `top`, `bottom`, `shoes`, `belt`, `earrings`.
3. **Owner reviews the overlays.** Verdict per region: ok / partial / fail.
4. If ≥ the core regions (person, face, background, top, bottom, shoes) receive
   "ok" or "partial (acceptable)" — proceed with gate computation for all 5 runs.
5. If any core region fails — stop, document the failure, investigate before continuing.

This owner review step is **mandatory before any gate values are used for thresholds**.

### 3.4 Gate measurements per run

For each of the 5 generated outputs (after owner OKs segmentation):

| Gate | Measurement | Tool |
|------|-------------|------|
| Color (per-region) | CIEDE2000 + L* normalization, mean ΔE per garment region (top, bottom, shoes, belt, earrings); PASS/WARN/FAIL per V-COLOR-001 provisional thresholds | `system/gates/color.py` |
| Identity | ArcFace cosine between person_front.png face crop and generated image face crop | `system/gates/identity.py` |
| Proportions | max(shoulder/waist/hip abs_change_pct) between person_front.png and generated image | `system/gates/proportions.py` |

Color WARN verdicts are reported individually per region, never rolled up into a
single pass/fail aggregate.  Any WARN → explicitly surfaced to owner before threshold
conclusions are drawn.

### 3.5 Reference values for color comparison

For each garment region, compare the generated region mask against the primary
reference image crop (garment-segmented, same as panel cell):
- blouse → `blouse_front.webp` garment crop
- skirt → `skirt_front.webp` garment crop
- belt → `belt.jpg` garment crop
- shoes → `shoes_wedge.webp` garment crop
- earrings → `earrings_disc.webp` garment crop (if visible)

---

## 4. Acceptance criteria

Defined before results are seen.

### 4.1 Segmentation review (owner gate)
- ≥ core regions (person, face, background, top, bottom, shoes) rated ok/acceptable
  by owner on the first generated output.
- All region verdicts documented in `results/segmentation_review.md`.

### 4.2 Variance profile
- Numeric distribution documented: mean ± std for each gate across K=5 runs.
- This distribution IS the noise floor — no threshold criteria on the variance itself.

### 4.3 Color threshold revision
- If the K=5 mean ΔE for a passing garment (same garment as reference, plausible
  color transfer) is **within** the current WARN zone (3–5): widen PASS, document
  the revision with the supporting data.
- If mean ΔE for a clearly-wrong garment falls in PASS: widen FAIL boundary,
  document.
- If current provisional thresholds survive the real distribution without change:
  document that explicitly.
- Final thresholds must be justified by the actual distribution, not assumed.

### 4.4 Identity threshold revision
- Measure ArcFace cosine for all 5 runs.
- If ≥ 4 of 5 runs score ≥ 0.57 with visually acceptable identity (owner confirms
  on first run): provisional threshold confirmed.
- If consistent degradation below 0.57: revise threshold downward with documented
  support; note if identity is still visually acceptable at the new threshold.
- The new threshold must leave a clear separation between acceptable and degraded
  identity.

### 4.5 Proportions threshold revision
- Measure max_abs_change_pct for all 5 runs.
- If all 5 runs score below 5.3%: provisional threshold confirmed.
- If natural generation variance reaches or exceeds 5.3%: revise upward with
  documented support.
- The new threshold must not flag normal generation as distortion.

### 4.6 Overall outcome
All three threshold verdicts (confirm or revise) plus the variance profile are
documented in `knowledge/verified.md` as new entries V-VAR-001 (noise floor),
V-COLOR-002 (final color thresholds), V-ID-002 (final identity threshold),
V-PROP-002 (final proportions threshold), each with the supporting numbers.

---

## 5. Runner

`experiments/005_variance_baseline/run_e005.py` — to be written before execution.

Sequence (respects VRAM budget):
1. Load outfit_package from `assets/outfits/outfit_001/outfit_package.json`.
2. Build reference panel via adapter v0 (SAM/GDINO active).
3. `POST /free` — unload SAM/GDINO.
4. For each seed in [42, 123, 456, 789, 1337]:
   a. Fill `qie2511_vton.json` template with params.
   b. Upload person image + reference panel to ComfyUI.
   c. Submit workflow, poll, download output.
   d. Save to `results/seed_{seed}/generated.png`.
5. `POST /free` — unload QIE-2511.
6. After first generation (seed=42): produce segmentation overlays for owner review.
   Pause for owner OK before continuing gate computation.
7. For each generated output: run segmentation, compute all three gates, save JSON.
8. Print summary table; save `results/measurements.json`.

---

## 6. Cost estimate

| Step | Estimated time |
|------|---------------|
| Panel building (7 SAM calls) | ~5–10 min |
| 5 generations × 40 steps | ~15–30 min |
| Segmentation of 5 outputs | ~5–10 min |
| Gate computation (CPU) | <1 min |
| **Total GPU time** | **~25–50 min** |

---

*Protocol written 2026-06-11.  No results exist yet.  Do not modify this file
after the first run — append a conclusion.md instead.*
