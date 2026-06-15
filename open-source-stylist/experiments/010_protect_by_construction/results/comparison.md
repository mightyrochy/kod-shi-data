# E-010 — protect-by-construction comparison (A: QIE Lightning vs B: FLUX Fill inpaint)

Advisory gates; owner verdict per axis is the acceptance. No aggregate score.
Garment fidelity is a HARD GATE — body win traded for garment regression does NOT pass.

## Body (pose joints, clothing-robust) + Face (ArcFace)
| arm | seed | hipΔ% | shoulderΔ% | ratioΔ% | pose_mism° | face cosine |
|---|---|---|---|---|---|---|
| A — QIE Lightning (E-009 R1) | 42 | — | — | — | — | — |
| A — QIE Lightning (E-009 R1) | 123 | — | — | — | — | — |
| B — FLUX Fill inpaint | 42 | — | — | — | — | — |
| B — FLUX Fill inpaint | 123 | — | — | — | — | — |

## Item colour — ΔE / verdict / hueΔ° / reliable
| arm | seed | top | bottom | belt | earrings | shoes |
|---|---|---|---|---|---|---|
| A — QIE Lightning (E-009 R1) | 42 | — | — | — | — | — |
| A — QIE Lightning (E-009 R1) | 123 | — | — | — | — | — |
| B — FLUX Fill inpaint | 42 | — | — | — | — | — |
| B — FLUX Fill inpaint | 123 | — | — | — | — | — |

## Acceptance (from protocol §5)
- Body better: mean |hipΔ%| materially below arm A ~8.85% (target ≤ ~4.5%)
- Face not worse: cosine ≥ 0.57 and not below arm A
- Garment not worse (hard gate): every item ΔE not worse, all items present, layering correct
- No seam/halo the owner rejects
- **Owner verdict per item is final; gates are advisory.**
