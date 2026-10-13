# E-002 conclusion

Date: 2026-06-11

## Answer to the question

Yes -- CIEDE2000 + lightness normalization produces monotonic, separable scores
sufficient to define provisional pass/warn/fail thresholds.

CIE76 was rejected mid-experiment: it compressed differences on dark/desaturated
colors (same perceptual shift measured ~2 on navy vs ~5 on brown skirt), and the
natural photo-pair noise (3.99-5.19) overlapped the signal window. Both problems
are resolved by the new metric.

## Metric

CIEDE2000 + L* normalization (align region mean L* before comparison).
Implemented in `system/gates/color.py`.

Effect of L* normalization on Series B (same garment, front vs back):

| pair                | CIE76 | CIEDE2000 + L-norm |
|---------------------|-------|--------------------|
| skirt front/back    | 3.99  | 0.68               |
| blouse front/back   | 5.19  | 1.04               |

Photo-pair noise collapsed ~5x. Signal window is now usable.

## Scores (CIEDE2000 + L-norm)

### Series A -- synthetic hue shifts (skirt_front.webp)

| shift_deg | dE_mean | dE_p90 |
|-----------|---------|--------|
| 0         | 0.28    | 9.48   |
| 5         | 1.78    | 9.75   |
| 10        | 5.06    | 11.14  |
| 15        | 7.20    | 12.59  |
| 20        | 10.36   | 14.70  |
| 30        | 14.88   | 18.54  |
| 45        | 19.77   | 22.52  |
| 60        | 23.37   | 25.65  |
| 90        | 27.91   | 29.62  |

Monotonic 0-90 deg. Violations at 120-180 are expected hue-circularity wrap-around.

### Series B -- same garment front/back (natural variation)

| pair                | dE_mean | per-item baseline |
|---------------------|---------|-------------------|
| skirt front/back    | 0.68    | 0.68              |
| blouse front/back   | 1.04    | 1.04              |

Natural variation ceiling: 1.04

### Series C -- different garments

| pair           | dE_mean |
|----------------|---------|
| skirt vs belt  | 5.16    |
| skirt vs shoes | 19.66   |
| skirt vs blouse| 15.97   |

### Pool -- fine-grained shifts, owner visual review

| garment     | shift | dE_mean | owner verdict         |
|-------------|-------|---------|----------------------|
| blouse_navy | 7.5   | 1.67    | PASS                 |
| blouse_navy | 10.0  | 2.57    | PASS (upper limit)   |
| blouse_navy | 12.5  | 3.02    | FAIL                 |
| dress_pink  | 7.5   | 3.97    | PASS (upper limit)   |
| dress_pink  | 10.0  | 6.77    | FAIL                 |

## Provisional thresholds (owner confirmed 2026-06-11)

| verdict | delta_e_mean    |
|---------|-----------------|
| PASS    | <= 3            |
| WARN    | 3 -- 5          |
| FAIL    | > 5             |

WARN zone goes to owner review.

Note: a single threshold cannot simultaneously place both navy 10 deg (2.57) and
pink 7.5 deg (3.97) in PASS -- the two colors have different perceptual sensitivity.
The WARN zone absorbs this: navy 12.5 deg (3.02) goes to owner who can confirm FAIL;
pink 7.5 deg (3.97) goes to owner who can confirm PASS. Acceptable for V1.

Per-item adaptive baseline: where front+back reference photos exist, dE(front, back)
is that item's own noise floor (skirt: 0.68, blouse: 1.04). These are tighter than
the global PASS threshold and serve as item-specific reference for E-005 analysis.

## Status

Instrument validated. Thresholds provisional -- final calibration after E-005
(generator noise floor: real distribution of generated-vs-reference comparisons).
Recorded in knowledge/verified.md as V-COLOR-001.
