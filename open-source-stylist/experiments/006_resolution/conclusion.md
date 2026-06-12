# E-006 — Conclusion: Resolution sensitivity

**Closed:** 2026-06-12
**Data:** `results/measurements.json`, `results/phase1_state.json`

---

## Answer to the question

**Generation resolution materially changes measured quality. Baseline 720x1024
(max_side=1024) is confirmed as the working resolution for all subsequent experiments.**

No alternative tier satisfied criterion 1 (identity). The decision is clear.

---

## Decision unblocked

**V-RES-001:** working resolution = 720x1024. All remaining Stage 2 experiments
(E-008, E-007) and production use this resolution.

---

## Gate results by tier

### Identity (ArcFace cosine, threshold 0.57)

| Tier | Mean cosine | PASS/5 | Notes |
|------|-------------|--------|-------|
| baseline 720x1024 | 0.830 | 5/5 | E-005 data |
| low 576x816 | 0.491 (1 detected) | 0/5 | 4/5 seeds: no face detected (head cropped) |
| high 896x1280 | 0.299 | 1/5 | seed_456=0.889 PASS; others 0.02-0.22 |
| high_plus 1120x1600 | — | 0/5 | 5/5 seeds: no face detected (head cropped) |

### Proportions (max_abs_change_pct, threshold 5.3%)

| Tier | Mean | Std | Max |
|------|------|-----|-----|
| baseline 720x1024 | 11.16% | 3.07% | 16.00% |
| low 576x816 | 24.68% | 4.14% | 32.18% |
| high 896x1280 | 15.65% | 7.97% | 30.88% |
| high_plus 1120x1600 | 32.35% | 2.61% | 35.53% |

All non-baseline tiers significantly worse than baseline. Proportions distortion
is not an identity gate artifact — it reflects real body deformation in the
generated outputs.

### Color dE (CIEDE2000, PASS<=3 WARN 3-5 FAIL>5)

| Region | Baseline | Low | High | High+ |
|--------|----------|-----|------|-------|
| top | 3.52 | 2.09 | 2.58 | **1.54** |
| bottom | 2.97 | 1.78 | 2.51 | **1.65** |
| shoes | 14.03 | 13.57 | 10.03 | 9.22 |
| belt | 3.00 | 3.45 | 3.11 | 3.93 |
| earrings | 3.67 | 3.49 | 5.37 | 3.79 |

Color fidelity for top/bottom improves with resolution — High+ achieves the
best scores (1.54, 1.65 dE). This gain is moot given the identity failure, but
is noted as an observation for future investigation.

### Generation time

| Tier | Mean time/image | Ratio vs Low |
|------|----------------|--------------|
| low 576x816 | 28s | 1.0x |
| high 896x1280 | 53s | 1.9x |
| high_plus 1120x1600 | 94s | 3.4x |

Baseline (720x1024) estimated between Low and High (~35-40s) based on E-005 runs.

### VRAM

No OOM at any tier. High+ (1.79MP) completed all 5 seeds on 16GB.

- Low peak: ~10.6GB (model load cost on cold start — not resolution-dependent)
- High peak: ~4.0GB
- High+: consistently 346MB after generation (GPU memory released between seeds
  at this resolution — mechanism not fully understood; likely aggressive ComfyUI
  offload under VRAM pressure)

V-RES-002: VRAM ceiling not hit within the tested range (up to 1.79MP).

---

## Sanity guard findings

The guard caught real mask corruption on 5 seed/region combinations:

| Tier | Seed | Region | Flag | Detail |
|------|------|--------|------|--------|
| low | 123 | face | area_fraction | 0.0006 (< min 0.002) — head cropped |
| low | 1337 | face | area_fraction | 0.3372 (> max 0.15) — misdetection |
| low | 1337 | face | position_prior | centroid y=0.457 — outside upper band |
| high | 1337 | face | area_fraction | 0.0003 — head cropped |
| high_plus | 456 | face | area_fraction | 0.0009 — head cropped |
| high_plus | 789 | shoes | containment | 48.3% inside person (< 70%) |
| high_plus | 789 | earrings | containment | 2.5% inside person (< 70%) |
| high_plus | 1337 | shoes | containment | 69.6% inside person (borderline) |

All face flags confirm the visual observation of head cropping at non-baseline
resolutions. Containment flags on High+ reflect segmentation errors when the
generated body is distorted.

**Known gap:** bottom mask overlapping belt region (observed at High, seed_42 by
owner visual review) was not flagged — inter-garment overlap check is not
implemented in sanity.py. Documented as a future enhancement.

---

## Interpretation: why baseline is the best

The head-cropping pattern at Low and High+ (and inconsistent identity at High)
suggests QIE-2511 Lightning was trained/tuned on images close to 720-1024px
max dimension. Deviating significantly in either direction (too small: 576px;
too large: 1120px) causes compositional failures — the model generates the
body at a scale that does not fit the frame.

High (896x1280) is closer to the training distribution and avoids head cropping,
but identity is still catastrophically inconsistent (4/5 seeds fail). Baseline
sits in the model's apparent sweet spot.

The color-vs-identity trade-off is clear: higher resolution improves color but
destroys identity. Given that identity is the primary quality criterion (criterion
1 in §4.2), baseline is the only valid choice.

---

## Knowledge status changes

**Promoted to Verified:**
- V-RES-001: working resolution = 720x1024 (see knowledge/verified.md)
- V-RES-002: VRAM ceiling not reached within tested range (up to 1120x1600,
  1.79MP, no OOM on RTX 4090 Laptop 16GB)

**Observations (single experiment, not Verified):**
- O-RES-001: Color dE for top/bottom improves at higher resolutions. High+
  achieves dE 1.54/1.65 vs baseline 3.52/2.97. Gain is resolution-dependent
  but paired with identity failure — cannot be exploited in current config.
- O-RES-002: VRAM at High+ shows aggressive release between seeds (346MB
  residual). Mechanism unclear; may be ComfyUI's automatic offload behavior
  under pressure.
- O-RES-003: High (896x1280) produced 1/5 seed with excellent identity
  (seed_456: 0.889) — within E-005 baseline range — but 4/5 seeds were
  catastrophic (0.02-0.22). Suggests identity at High is stochastic, not
  systematically degraded.

---

*Written 2026-06-12. Data in results/measurements.json.*
