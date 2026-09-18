# E-007 v2 - Frozen reference-board crop method A/B

**Created:** 2026-06-14
**Status:** original A/B closed; hybrid supplement generated and measured 2026-06-14

The 2026-06-13 attempt is preserved in `protocol_invalid_2026-06-13.md` and
`results_invalid_2026-06-13/`. It is invalid because its board contained product
models and was rebuilt through in-loop segmentation.

## Question

With every other input fixed, does QIE-2511 perform better from garment masks or
from simple owner-prepared rectangular crops?

## Decision informed

Which frozen board variant becomes the reference input for the next adapter
baseline. This experiment does not choose a production garment-isolation system.

## Arms

| Arm | Frozen board |
|---|---|
| A | `assets/outfits/outfit_001/reference_boards/masked_crops.png` |
| B | `assets/outfits/outfit_001/reference_boards/rectangular_crops.png` |

Both boards contain the same seven labeled cells in the same 3 x 3 layout:
blouse front, blouse back, skirt front, skirt back, belt, shoes, earrings.

The PNG files and SHA-256 values are recorded in `outfit_package.json` and
`reference_boards/manifest.json`. The runner verifies them and never rebuilds a board.

## Fixed inputs

- Person: `assets/person/person_front.png`
- Outfit package: `assets/outfits/outfit_001/outfit_package.json`
- Layout: `assets/outfits/outfit_001/outfit layout.txt`
- Prompt: built once from the same board labels and layout text for both arms
- Workflow: `qie2511_vton_lightning`
- Resolution: 720 x 1024
- Steps: 4
- CFG: 1.0
- Seeds: 42, 123, 456, 789, 1337
- Negative prompt: empty

The board PNG is the only variable.

## Procedure

1. Phase 1 generates ten outputs: two board arms x five paired seeds.
2. Owner reviews every same-seed pair before measurements are interpreted.
3. Phase 2 segments outputs and records sanity flags, identity, color, and the
   existing silhouette-width diagnostic.
4. A color region with a sanity flag is not measured; it is recorded as
   `SKIP_SANITY`.
5. The silhouette-width score remains diagnostic because clothing and framing
   affect it; it is not treated as proof of body-shape preservation by itself.

## Acceptance

No automatic aggregate winner is allowed. A board method is selected only when:

- owner review prefers it on at least 3 of 5 paired seeds for correspondence to
  the supplied garments;
- identity does not materially regress;
- the apparent advantage is not explained by invalid masks;
- failures and mixed results are retained, not averaged away.

If neither arm is consistently better, the result is inconclusive and both
boards remain experimental.

## Hybrid supplement

After the original A/B was reviewed, the owner corrected the blouse-front mask
and edited the layout wording. A third frozen candidate is therefore run as an
E-007 supplement rather than silently replacing either original arm.

| Candidate | Frozen board |
|---|---|
| C | `assets/outfits/outfit_001/reference_boards/hybrid_mask_crop.png` |

- Board SHA-256:
  `542051b334f0b02114093c574ea2e4ae31e137afb368a786ab434e16109aba83`
- Corrected blouse mask SHA-256:
  `24c6e20892552556d7875725040968a6853b5e152cfbc571b86c72fd32ff7084`
- Current layout SHA-256:
  `c06f02b5a20470f0145aee23442baf892e5f640ac53b82f614c1a46470d543e6`
- Seeds, workflow, person image, resolution, steps, CFG, and negative prompt
  remain the same as the original A/B.

The hybrid board contains nine labeled cells: blouse mask + crop, skirt mask +
crop, belt mask, earrings mask + crop, and shoes mask + crop.

This supplement changes both the board and layout text relative to arms A/B.
It can determine whether the complete corrected hybrid input is a better next
candidate, but it cannot attribute a difference to the board alone. Outputs,
state, measurements, and comparison sheets are stored under distinct hybrid
filenames so the closed A/B record is never overwritten.
