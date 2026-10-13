# E-007 hybrid supplement report

**Run completed:** 2026-06-14
**Status:** generation and measurements complete; owner review pending

## Integrity

- 5/5 hybrid outputs exist at 720 x 1024.
- Seeds: 42, 123, 456, 789, 1337.
- Hybrid board SHA-256:
  `542051b334f0b02114093c574ea2e4ae31e137afb368a786ab434e16109aba83`.
- Corrected blouse mask SHA-256:
  `24c6e20892552556d7875725040968a6853b5e152cfbc571b86c72fd32ff7084`.
- Layout SHA-256:
  `c06f02b5a20470f0145aee23442baf892e5f640ac53b82f614c1a46470d543e6`.
- The original A/B outputs, state, and measurements were not overwritten.

## Comparison limit

The hybrid supplement changes both the board and the layout text. The old layout
ended with `shoes on bare feet`; the current layout explicitly names wedge
sandals. Therefore, the supplement can rank the complete corrected input as a
candidate, but it cannot separate the effect of the board from the effect of the
layout correction.

## Visual comparison

| Check | Masked crops | Rectangular crops | Hybrid |
|---|---:|---:|---:|
| Requested shoes visible | 0/5 | 0/5 | 5/5 |
| V neckline consistent | 3/5 | 5/5 | 5/5 |
| Central blouse buttons visible | input defect | inconsistent | 5/5 |
| Usable measurement-mask sets | 1/5 | 5/5 | 5/5 |

The hybrid outputs are more consistent in garment completeness. The blouse shade
still appears too light/yellow compared with the reference. Skirt length and body
silhouette continue to vary, so the hybrid is not a complete quality solution.

## Measurements

| Metric | Masked crops | Rectangular crops | Hybrid |
|---|---:|---:|---:|
| Identity cosine mean | 0.7967 | 0.7688 | 0.7870 |
| Proportion diagnostic mean | 15.632% | 5.828% | 12.644% |
| Top color dE | 4.710 (n=1) | 3.048 (n=5) | 2.400 (n=5) |
| Bottom color dE | 2.860 (n=1) | 4.000 (n=5) | 4.100 (n=5) |
| Shoes color dE | 29.667 (n=3) | 29.692 (n=5) | 6.220 (n=5) |
| Belt color dE | 5.115 (n=2) | 8.254 (n=5) | 4.864 (n=5) |
| Earrings color dE | 3.987 (n=3) | 6.240 (n=5) | 3.704 (n=5) |

Masked-arm color means remain non-comparable because most masks failed sanity.
The top-color metric says the hybrid is numerically closer, but it does not
override the visible blouse-shade mismatch.

## Provisional result

Hybrid is the better next input candidate for garment completeness, not a proven
overall winner. It resolves the missing buttons and absent footwear while keeping
identity stable. Blouse color and silhouette fidelity remain open problems.

Review files:

- `three_way_contact_sheet.png` - same-seed generated outputs.
- `three_way_mask_overlays.png` - measurement-mask coverage.
