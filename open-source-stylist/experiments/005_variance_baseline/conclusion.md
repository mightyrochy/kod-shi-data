# E-005 — Conclusion

**Date:** 2026-06-12
**Status:** COMPLETE
**Owner review:** done (Checkpoint 2 masks, Checkpoint 3 measurements + images)

---

## Answer to the question

Natural run-to-run variance of QIE-2511 Lightning (4-step, layers=2) on outfit_001:

- Identity and proportions are highly stable across seeds.
- Color variance is garment-dependent: bottom/belt/earrings cluster near PASS/WARN
  boundary; shoes show high inter-seed variance; top is in WARN range.
- Shoes exhibit systematic color failure (high dE, high variance) — not noise.

---

## Protocol deviation

Protocol specified full 40-step model (no Lightning). Actual run used Lightning LoRA
4-step (Config B), confirmed by BUILD_PLAN execution notes (2026-06-11) before E-005
was run. All 5 seeds used the same frozen config — no mixed-config result sets.

---

## Instrument failures found and corrected mid-experiment

Two segmentation prompts produced full-silhouette masks on generated images
(same failure mode as shoes in diagnostic):

1. **"shoes . sandals . wedge"** → full silhouette. Fixed to **"footwear"**.
2. **"top"** → full silhouette. Fixed to **"shirt"** (11.5% of image, rows 17–56%).

Both fixes were applied, phase 2 re-run from scratch on all 5 seeds.
No mixed-config result sets. Top dE dropped from 15.57 (invalid) to 3.52 (correct)
after the fix — confirming the masks were the source of the artifact.

Key finding: segmentation prompts on generated images require simple single-word
queries. Compound queries ("shoes . sandals . wedge") and ambiguous single words
("top") cause GroundingDINO to return full-body bounding boxes. Verified
prompts for this domain: shirt / footwear / skirt / belt / earrings / face / person.

---

## Gate measurements (K=5, seeds=[42,123,456,789,1337])

### Color (CIEDE2000, thresholds: PASS<=3, WARN 3-5, FAIL>5)

| Region | mean dE | std  | Seeds PASS | Seeds WARN | Seeds FAIL |
|--------|---------|------|------------|------------|------------|
| top    | 3.52    | 1.32 | 1 (42)     | 3 (123,789,1337) | 1 (456) |
| bottom | 2.97    | 1.33 | 3          | 1 (1337)   | 1 (456)  |
| belt   | 3.00    | 0.84 | 3          | 2 (456,789)| 0        |
| earrings | 3.67  | 1.28 | 2          | 1 (123)    | 1 (1337) |
| shoes  | 14.03   | 6.04 | 0          | 0          | 5 (all)  |

### Identity (ArcFace cosine, threshold >= 0.57)

| Seed | Cosine | Verdict |
|------|--------|---------|
| 42   | 0.8734 | PASS |
| 123  | 0.792  | PASS |
| 456  | 0.7761 | PASS |
| 789  | 0.8743 | PASS |
| 1337 | 0.835  | PASS |

mean=0.830, std=0.040, min=0.776

### Proportions (max_abs_change_pct, threshold <= 5.3%)

All 5 seeds: 0.00% -> PASS

---

## Knowledge status changes

### Promoted to Verified (append to knowledge/verified.md)

- **V-VAR-001**: variance profile (noise floor)
- **V-COLOR-002**: color gate thresholds confirmed on real generated-vs-reference distribution
- **V-ID-002**: identity threshold confirmed on generated images
- **V-PROP-002**: proportions threshold confirmed on generated images
- **V-SEG-004**: segmentation prompt rules for generated images

### Hypotheses status

- **H-COLOR**: color words in prompt degrade color fidelity — still open, to be
  tested in E-007. Top dE=3.52 in WARN range; cannot attribute cause without A/B.
- **H-REF-CONTAMINATION**: un-cropped references distort results — still open, E-008.

---

## Owner observations (Checkpoint 3, 2026-06-12)

- All elements except shoes: lower WARN boundary, "almost PASS".
- Visible difference to eye comes more from flat/textureless generation than from
  color mismatch. If textures improve, dE 3-5 may become perceptually imperceptible.
- Shoes: 3 green variants, 1 black, 1 brown across seeds — high variance confirmed.
- Overall reference correspondence: general fail on current config.
- Texture fidelity is a separate quality dimension not covered by any current gate.

---

## Decisions unblocked

- Color gate thresholds: confirmed, usable for E-006/E-007/E-008.
- Identity gate threshold: confirmed.
- Proportions gate threshold: confirmed.
- All three gate thresholds are no longer provisional.
- Noise floor established: differences below ~1.3 dE (color std), ~0.04 cosine
  (identity) are noise, not signal.
- E-006 (resolution), E-007 (color words), E-008 (reference crops) can proceed.

---

## Open questions (not blocking)

- Shoes systematic FAIL: cause unknown. Candidate: shoes_wedge.webp reference has
  dark teal color; generator produces high variance. Investigated in E-007/E-008.
- Texture quality gate: owner observation. Not in scope for V1 instruments; document
  as known gap in design §6.
- layers=0 single-frame generation: parked per owner instruction; test after E-005.

---

## Erratum — proportions verdict corrected (2026-06-12, post-close)

**Third instrument failure found post-close.** `run_e005.py` had `.get("max_abs_change_pct", 0)`
on a key absent from `proportions.compare()` return dict. All 5 proportions scores silently
defaulted to 0.00%; verdicts were all "PASS" — wrong.

Corrected values: all 5 seeds FAIL (range 7.03–16.0%, mean 11.16%). Systematic pattern.
Owner confirmed visual distortion on seed_1337 (2026-06-12). See verified.md for full
corrected data (V-PROP-002 reversal, V-VAR-001 correction).

Fix applied to: `proportions.py` (added `max_abs_change_pct` to `compare()` return),
`run_e005.py` (direct key access + RuntimeError on None), `measurements.json` (verdicts
corrected from accurate numeric data). Integration FAIL tests added in `system/tests/`.
Rule added to METHODOLOGY §5: measurement code fails loudly — missing metric = error,
never a default.
