# E-008 — Reference panel: cropped vs raw product photos

**Status:** DRAFT — awaiting owner sign-off before execution
**Created:** 2026-06-13
**Governed by:** METHODOLOGY.md §2; BUILD_PLAN Stage 2

---

## 1. Question

Do un-cropped product reference photos in the conditioning panel degrade measured
quality (proportions, identity, color ΔE) compared to garment-only cropped
references?

---

## 2. Decision informed

**Adapter panel rule:** whether the reference panel MUST use garment-only crops
(current adapter default) or whether raw product photos are equivalent.

Secondary: provides evidence on H-REF-CONTAMINATION — the hypothesis that full
product photos introduce model bodies and incidental objects (e.g., black heels
visible on skirt reference) into conditioning, causing proportions distortion and
shoe color failure observed in E-005.

If raw is not worse → H-REF-CONTAMINATION refuted for these dimensions; the
proportions and shoes failures need a different suspect (next candidate:
Lightning-specific behavior, bench rows 2–3).

---

## 3. Method

### 3.1 Conditions

| Condition | Panel construction | Generation | Data source |
|-----------|-------------------|------------|-------------|
| A — Cropped | Garment-only crops via SAM segmentation (current adapter default) | K=5 seeds | **E-005 baseline — data exists, no new generation needed** |
| B — Raw | Full product photos tiled (no segmentation, no cropping) | K=5 seeds | **New generation, this experiment** |

### 3.2 What varies

Panel construction method only: condition B skips the SAM garment-crop step and
tiles the original product images directly.

### 3.3 What is fixed

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
| Resolution | 720×1024 (V-RES-001) |
| Person image | `assets/person/person_front.png` |
| Outfit | `outfit_001` |
| Prompt | identical for both conditions (from `adapter.prompt.build_prompt`) |
| Seeds | [42, 123, 456, 789, 1337] — same as E-005 |

Raw panel cell size: 256px (same as cropped panel), full product image resized
to fit cell with white padding — no alpha compositing, no masking.

### 3.4 Measurement per output

After each generation: segmentation with the full sanity guard (all four checks,
including pairwise garment-overlap — O-SEG-GAP-001 now implemented).

| Gate | Metric |
|------|--------|
| Identity | ArcFace cosine vs `person_front.png` |
| Color (per-region) | CIEDE2000 + L* normalization; mean ΔE for top, bottom, belt, earrings, shoes |
| Proportions | max(shoulder/waist/hip abs_change_pct) vs `person_front.png` |

Reference images and masks for color gate: same as E-005/E-006 (E-001 mask dir).

Any sanity guard flag — including garment_overlap — is recorded verbatim and
reported before proceeding to gate values for that seed.

### 3.5 Runner phases

**Phase 1 (GPU):** build raw panel → generate all 5 seeds → segment seed_42 +
produce overlays → save state.

**Checkpoint:** owner reviews seed_42 overlays and sanity flags before phase 2.

**Phase 2 (CPU):** segment remaining 4 seeds → compute all gates → assemble
comparison table (raw vs E-005 cropped baseline).

---

## 4. Acceptance criteria

Defined before results are seen.

### 4.1 Raw-condition gate results

Produce per-seed measurements for all gates in condition B. Assemble a comparison
table: raw mean ± std vs cropped mean ± std (E-005) for each metric.

### 4.2 Decision rule — H-REF-CONTAMINATION

**Proportions:**
- Raw significantly worse (mean > baseline mean + 2×baseline_std):
  → contamination contributes to proportions distortion.
  Baseline: mean=11.16%, std=3.07% → threshold = 11.16 + 2×3.07 = 17.3%.
  "Significantly worse" = raw mean > 17.3%.
- Raw within noise (mean within ±2×baseline_std of baseline):
  → H-REF-CONTAMINATION refuted for proportions; new suspect needed.

**Shoes color:**
- Raw shoes mean dE > 18.0 (baseline 14.03 + 2×baseline_std 6.04 = 26.1 is too
  loose; use 18.0 as a meaningful upper marker):
  → raw shoes systematically worse → contamination plausible for shoes.
- Raw shoes mean dE ≤ baseline mean dE (14.03):
  → raw NOT worse for shoes → contamination refuted for shoes.
- Zone between (14.03–18.0): inconclusive — note as observation, not verdict.

**Identity and other color regions:**
- Compare means; flag any raw deterioration > E-005 noise floor (identity std
  0.040; per-region color std from E-005 table).

### 4.3 Knowledge entries

Write to `knowledge/`:
- Whether H-REF-CONTAMINATION is confirmed, refuted, or inconclusive (per §4.2).
- Observation on any incidental findings (e.g., shoes variance pattern in raw condition).

---

## 5. Runner

`experiments/008_reference_crops/run_e008.py`

Key difference from E-005/E-006 runners: `build_raw_panel()` tiles full product
photos using PIL only — no ComfyUI/SAM required for panel construction.

Segmentation prompts imported from `system/segmentation/prompts.py`
(`REGION_PROMPTS`, `generated_prompts`) — the canonical source; not copied.

---

## 6. Cost estimate

| Step | Estimated time |
|------|---------------|
| Build raw panel (PIL, no GPU) | < 1 min |
| Generate 5 seeds at 720×1024 Lightning 4-step | ~3–5 min |
| Segment 5 outputs (SAM + GDINO) | ~5–15 min |
| Gate computation (CPU) | < 1 min |
| **Total GPU time** | **~10–20 min** |

---

## 7. Integration FAIL test

Pairwise garment-overlap check in sanity guard: covered by
`system/tests/test_segmentation_fail.py` test 6 (added 2026-06-13, all 6 tests
green, commit 5f8ceda). The belt-inside-bottom FAIL case directly mirrors the
E-006 corruption that motivated O-SEG-GAP-001.

---

*Protocol written 2026-06-13. No results exist yet. Do not modify this file
after the first generation run — append a conclusion.md instead.*
