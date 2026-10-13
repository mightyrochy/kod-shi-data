# E-010 comparison: A (QIE Lightning) vs B (FitDiT garment-faithful try-on)

Garment fidelity is the HARD gate. Body is secondary. Owner verdict per axis.

## Identity (ArcFace cosine)
| arm | item | seed | face cosine | verdict |
|---|---|---|---|---|
| A_qie_lightning | all | 42 | 0.8056 | PASS |
| A_qie_lightning | all | 123 | 0.7597 | PASS |
| B_fitdit | blouse | 42 | 0.9718 | PASS |
| B_fitdit | blouse | 123 | 0.9689 | PASS |
| B_fitdit | skirt | 42 | 0.9776 | PASS |
| B_fitdit | skirt | 123 | 0.9765 | PASS |

## Garment fidelity
FashionSigLIP retrieval-rank and DISTS: PENDING_CALIBRATION
Build calibration set before these numbers are decision-grade.

## Acceptance (STARTER.md)
- Axis 1 HARD GATE: garment same item (owner per-item verdict)
- Axis 2: identity cosine >= 0.57 and not below arm A
- Axis 3: body reported, blocks only if grossly wrong
