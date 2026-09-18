# E-009 — per-axis comparison (R1 Lightning vs R2 fair no-Lightning)

Advisory gates; owner verdict is the acceptance. No aggregate score.

## Body (pose joints) + Face (ArcFace)
| arm | seed | hipΔ% | shoulderΔ% | ratioΔ% | pose_mism° | face cosine |
|---|---|---|---|---|---|---|
| R1_lightning | 42 | -8.82 | -0.82 | 8.77 | 3.0 | 0.8056 |
| R1_lightning | 123 | -9.0 | -2.48 | 7.19 | 2.1 | 0.7597 |
| R2_full_cfg5 | 42 | -28.72 | -16.3 | 17.44 | 10.7 | 0.348 |
| R2_full_cfg5 | 123 | -8.26 | 0.52 | 9.58 | 2.2 | 0.3733 |

## Item colour — ΔE / verdict / hueΔ° / reliable
| arm | seed | top | bottom | belt | earrings | shoes |
|---|---|---|---|---|---|---|
| R1_lightning | 42 | 2.15/PASS/5.3/Y | 3.36/WARN/5.8/Y | 5.7/FAIL/1.1/Y | 0.83/PASS/0.1/Y | 5.4/FAIL/26.4/n |
| R1_lightning | 123 | 1.67/PASS/5.9/Y | 3.76/WARN/5.6/Y | 5.42/FAIL/1.7/Y | 5.64/FAIL/2.0/Y | 3.48/WARN/15.7/n |
| R2_full_cfg5 | 42 | SKIP_SANITY | SKIP_SANITY | SKIP_SANITY | 2.77/PASS/7.4/Y | 4.45/WARN/14.9/n |
| R2_full_cfg5 | 123 | 1.56/PASS/2.3/Y | 18.71/FAIL/102.9/n | 9.22/FAIL/44.3/Y | 1.23/PASS/3.0/Y | 10.53/FAIL/61.1/n |
