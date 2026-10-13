# E-011 — single-item high-res local repair (QIE-2511 crop-and-stitch)

**Status:** protocol written 2026-06-19, before running (METHODOLOGY §2). Builds Stage 5 (BUILD_PLAN) /
SYSTEM_DESIGN §7 step 4 / IMPLEMENTATION_BLUEPRINT §9.5 — the repair executor, the untested half of the
"holistic board + high-res single-item repair" architecture. Owner-directed ("робимо 2", 2026-06-19).

## 1. Question (falsifiable)
Can an imported/native **QIE-2511 crop-and-stitch** edit do **reference-faithful, LOCAL** single-garment
repair: regenerate ONE garment region to match its full-resolution reference, while changing ≈nothing
outside the garment mask?

## 2. Decision informed
The V1 repair architecture (SYSTEM_DESIGN §7 / open-question 3): **repair vs regenerate-on-fail**. If QIE
inpaint can do reference-faithful local repair, the holistic-pass detail loss (board pixel-bottleneck,
DEEP_RESEARCH §12.4) is recoverable per item → the editing-first spine becomes viable for whole-outfit
fidelity. If it cannot, V1 redirects to regenerate-on-fail or a dedicated single-garment repair engine
(FitDiT/Leffa, with a correct SCHP agnostic) — a major, legitimate outcome.

## 3. Method
Engine: native QIE-2511 edit (`UNETLoader qwen_image_edit_2511_fp8mixed` + `TextEncodeQwenImageEditPlus`
image1+image2), reused from `system/workflows/qie2511_vton.json`. Crop & feathered stitch done in Python
(`system/repair/repair.py`), so locality = the crop (QIE only sees the region) + mask-limited paste-back.
- **Inputs:** a base image + a garment region mask + that garment's full-resolution reference + a
  repair instruction (no colour words — H-COLOR, enforced).
- **Steps:** bbox(mask)+~20% context → crop; resize crop+mask to a working resolution (÷16); QIE-edit the
  crop conditioned on (crop=image1, garment ref=image2, instruction); decode; resize back; **feather the
  garment mask and composite the edited crop into the base ONLY within the mask**.
- **Controlled first case (no fresh QIE holistic output exists yet, `runs/` empty):** base = source
  `person_front.png` (gray sweater + jeans); repair the **top** region → the lemon blouse
  (`crops/blouse front crop.png`). Real wrong→right garment swap with a known reference + a clean locality
  check (face/jeans/background must not move). Seed 42; QIE full model.
- **Fixed:** person, blouse reference, seed; varies: only the repair pass exists (no holistic baseline mixed in).

## 4. Acceptance criteria (defined before results)
- **Fidelity (axis #1):** the repaired top, vs the blouse reference, scores BETTER than the original
  sweater region on the garment-fidelity instrument (FashionSigLIP retrieval-rank toward the blouse +
  lower DISTS) — ADVISORY (instrument uncalibrated) + **owner per-item verdict** is the decider.
- **Locality (HARD):** pixel change OUTSIDE the dilated garment mask is ≈0 (target: <1% of outside-mask
  pixels changed beyond JPEG/feather noise; report the exact %). This is the property the crop-and-stitch
  must guarantee. **FAIL test:** a synthetic case where the executor is fed a no-op edit must produce
  outside-mask change = 0 (`system/tests/test_repair_locality.py`).
- **Identity not worse:** ArcFace cosine(base, repaired) ≥ the base's own (face is outside the top mask →
  should be ~1.0).
- No aggregate score; owner verdict per axis is the acceptance (METHODOLOGY §5).

## 5. Cost
1 session build + 1–2 GPU edits. Instrument is advisory (calibration is a separate prerequisite,
EVAL_INSTRUMENTS) — this experiment's verdict leans on locality (deterministic) + owner's eye.

## 6. Honest unknowns
- Whether QIE-2511 edit on a tight crop reproduces a specific garment faithfully (the real frontier; even
  SOTA approximates) — this is exactly what E-011 measures.
- Whether the crop loses so much body context that the garment is placed/scaled wrong.
- The garment-fidelity instrument is uncalibrated → its numbers are advisory; the owner's eye decides #1.
