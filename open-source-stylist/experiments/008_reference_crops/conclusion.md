> **STATUS 2026-06-15 — RULE STANDS, MAGNITUDES CONFOUNDED.** Per the canonical
> ERRATUM in `knowledge/verified.md` (2026-06-13): the cropped-vs-raw CONTRAST and
> the garment-only-crop RULE (V-REF-001) stand — they are owner-confirmed on direct
> visual evidence ("абсолютно не та людина"). But the absolute ΔE / proportion /
> cosine MAGNITUDES in the tables below were measured with the task-incorrect prompt
> and reopen with the re-baseline. Cite the rule and the qualitative contrast; do not
> cite the absolute numbers as decision-grade.

# E-008 — Conclusion: reference panel (cropped vs raw)

**Closed:** 2026-06-13
**Data:** `results/measurements.json`, `results/phase1_state.json`

---

## Answer to the question

**Yes — un-cropped product references severely degrade measured quality.**
The effect is largest on identity (complete collapse), substantial on proportions
(+10pp), and mixed on color (top/belt/earrings worse; bottom better; shoes unchanged).

---

## Decisions unblocked

1. **Adapter panel rule confirmed:** garment-only crops are mandatory for the
   reference panel. Raw product photos cannot be used as conditioning — the
   identity failure alone disqualifies them entirely.

2. **H-REF-CONTAMINATION — split verdict:**
   - Proportions: **CONFIRMED** as a contributing factor (see §§ below).
   - Shoes color: **REFUTED** — raw panel does NOT worsen shoes ΔE.
   - Identity: **CONFIRMED** (not in the original hypothesis scope, but same mechanism).

3. **Proportions root cause — open.** Contamination explains ~10pp of the
   distortion (21.52% raw vs 11.16% cropped); the baseline 11.16% distortion
   on cropped references remains unexplained. Next suspect: Lightning-specific
   behavior — bench rows 2-3.

4. **Shoes systematic FAIL cause — open.** H-REF-CONTAMINATION refuted for
   shoes; another cause drives the 14 dE baseline failure.

---

## Gate results — raw condition B (K=5, seeds [42,123,456,789,1337])

### Owner checkpoint observation (Phase 1, seed_42 visual review)

"Абсолютно не та людина на кожній генерації. Елементи одягу теж багато де далекі від оригіналу."

Gates confirmed this quantitatively (see below).

### Identity

| Condition | Mean cosine | std | PASS/5 |
|-----------|------------|-----|--------|
| A cropped (E-005) | 0.830 | 0.040 | 5/5 |
| B raw | 0.008 | 0.023 | 0/5 |

Raw condition produces near-zero cosine on all seeds — the generated person shares
essentially no face embedding with the input person. Mechanism: when the reference
panel contains full-body product photos, the model generates the product model's
identity rather than the input person's.

### Proportions

| Condition | Mean max_abs_pct | std | FAIL/5 | vs threshold 17.3% |
|-----------|-----------------|-----|--------|---------------------|
| A cropped (E-005) | 11.16% | 3.07% | 5/5 | below |
| B raw | 21.52% | 3.03% | 5/5 | **above → CONFIRMED** |

Raw is 10.36pp worse. Per protocol §4.2, raw mean 21.52% > threshold 17.3%
→ H-REF-CONTAMINATION confirmed for proportions.

Note: cropped baseline also fails (11.16% > 5.3%). Contamination accounts for
~10pp of the distortion; the remaining 11.16% baseline distortion is not from
reference contamination.

### Color ΔE (CIEDE2000)

| Region | A cropped mean ± std | B raw mean ± std | Δ | Verdict |
|--------|----------------------|------------------|---|---------|
| top | 3.52 ± 1.32 | 9.25 ± 4.75 | +5.73 | raw worse |
| bottom | 2.97 ± 1.33 | **0.89 ± 0.44** | −2.08 | raw better* |
| shoes | 14.03 ± 6.04 | 13.82 ± 0.76 | −0.21 | not worse → REFUTED |
| belt | 3.00 ± 0.84 | 5.58 ± 2.10 | +2.58 | raw worse |
| earrings | 3.67 ± 1.28 | 8.59 ± 1.43 | +4.92 | raw worse |

*Bottom "better" in raw: mask corruption on seeds 123/456 may influence this
(bottom mask ~99% consumed by top → measuring the wrong region). On seeds with
clean bottom masks (42, 789, 1337): 0.30/0.74/1.20 dE — still better than
baseline. Interpretation: full skirt reference photos give the model a strong
skirt-color signal. This finding is moot given identity failure.

Shoes: raw mean 13.82 ≈ cropped 14.03 (within noise floor 6.04) → contamination
refuted for shoes. The systematic shoes FAIL has a different cause.

### Sanity guard (O-SEG-GAP-001 — first live test)

| Seed | Flags | Detail |
|------|-------|--------|
| 42 | clean | — |
| 123 | garment_overlap | bottom 98.7% inside top; belt 52.2% inside top |
| 456 | garment_overlap | bottom 99.1% inside top; belt 38.0% inside top |
| 789 | garment_overlap | belt 99.5% inside top |
| 1337 | clean | — |

3/5 seeds flagged. The top mask absorbed bottom and/or belt — segmentation
failure from the model generating an output where garment boundaries are merged
or indistinct (expected given identity collapse). The new pairwise overlap check
caught these corruptions that the three prior checks would have missed.
Color measurements for flagged seeds should be read with this caveat.

---

## Knowledge status changes

### Promoted to Verified

- **V-REF-001**: Adapter panel rule — garment-only crops mandatory (see below).
- **V-REF-002**: H-REF-CONTAMINATION split verdict — confirmed for proportions
  and identity; refuted for shoes (see below).

### Hypotheses updated

- **H-REF-CONTAMINATION**: split status — proportions/identity confirmed, shoes
  refuted (append to hypotheses.md with date).
- **H-PROPORTIONS**: contamination accounts for ~10pp; residual 11.16%
  unexplained. Next suspect: Lightning-specific behavior.
- **O-SEG-GAP-001**: resolved — pairwise garment overlap check implemented
  (sanity.py, commit 5f8ceda, 2026-06-13); first live detection: 3/5 seeds
  in this experiment.

---

---

## Additional owner observations (2026-06-13, post-close visual review of all 5 raw seeds)

Owner reviewed all 5 raw-condition outputs in full, adding:

- **Blouse (top):** only one seed has a blouse color resembling the reference; all
  others are white. Gate: raw top mean dE = 9.25 vs cropped 3.52. Visual explanation:
  the model generates a generic white shirt rather than the specific blouse color.
- **Earrings:** all 5 seeds show grey/silver disc-shaped earrings with arbitrary
  patterns — not the specific ridged spiral texture of the reference. Gate: raw
  earrings mean dE = 8.59 vs cropped 3.67. Visual explanation: disc shape is
  preserved (from reference), but color and texture default to generic silver.
- **Shoes:** confirmed in prior erratum — all 5 seeds black, one high-heeled.

Collectively these observations describe a **generic-fashion-model effect**: when
full-body product photos appear in the reference panel, the model generates a
"standard fashion photo with a generic model in generic clothes" rather than
"this specific person wearing this specific outfit." Reference-image colors,
textures, and identity are all overridden by the model's fashion-photo prior.

This is not a collection of independent per-item contamination hits — it is one
mechanism affecting all items simultaneously. The per-item dE numbers in the table
above measure the degree of each item's deviation, but the root cause is the same
for all: full-body reference photos supply too many competing signals (other person's
body, background, incidental colors) for the model to isolate the individual garments.

The garment-only crop rule (V-REF-001) directly addresses this mechanism.

---

## Erratum — shoes verdict revised (2026-06-13, owner visual review)

Original shoes verdict ("REFUTED") was wrong. Gate-based comparison (mean dE
13.82 vs 14.03) was correct numerically but insensitive to the type-of-failure.

Owner observation after close: all 5 raw-condition seeds produced black shoes;
one seed produced high heels instead of wedge sandals. The uncropped skirt
reference photo shows a model wearing black high heels — a direct visual match
to the output. The gate scored both conditions at ~14 dE against the teal wedge
reference and reported no difference; it cannot distinguish "consistently black
heels from contamination" from "randomly wrong shoes."

**Revised verdict:**
- Shoes, raw condition: H-REF-CONTAMINATION **CONFIRMED** (owner direct visual
  evidence, 2026-06-13).
- Shoes, cropped condition (E-005): contamination source removed; shoes still
  fail (14 dE, high variance: 3 green / 1 black / 1 brown). Different cause.

See V-REF-002 correction in `knowledge/verified.md`.

*Written 2026-06-13. Data in results/measurements.json.*
