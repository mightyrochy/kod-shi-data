# E-007 v2 preliminary report

**Run completed:** 2026-06-14
**Status:** measurements complete; owner review recorded in `../conclusion.md`

## Integrity

- 10/10 outputs exist at 720 x 1024.
- Seeds: 42, 123, 456, 789, 1337 in both arms.
- Masked board SHA-256:
  `1b5229c6f2c5f5d7ca00488228a69d0a358c67829934432285a2ee091aaed832`.
- Rectangular board SHA-256:
  `41d510468934664afc763bd235c076cc194c50d00dee7c3764ced77b0c7b510d`.
- The same prompt, workflow, person image, resolution, sampler, scheduler, CFG,
  steps, and seeds were used for both arms.

## Visual checkpoint

All ten outputs preserve a recognizable version of the input person and include
the blouse, skirt, belt, and matching earrings on both ears. The belt is over the
blouse and the blouse is over the skirt.

All ten outputs omit the shoes. The phrase `shoes on bare feet` resulted in bare
feet rather than shoes worn without socks. Footwear is therefore a shared failure
and cannot distinguish the two crop methods in this run.

The rectangular arm reproduces the V neckline consistently. The masked arm changes
to a round/gathered neckline on seeds 123 and 789. This is a visual observation,
not an automatic winner decision.

## Measurement validity

| Arm | Fully clean mask sets | Color samples per region |
|---|---:|---|
| masked_crops | 1/5 | top 1, bottom 1, shoes 3, belt 2, earrings 3 |
| rectangular_crops | 5/5 | 5 for every region |

On masked seeds 123 and 456, segmentation incorrectly absorbs much of the person
into garment/footwear masks. Masked-arm color means are therefore based on unequal
and very small sample counts and must not be compared directly with rectangular
5/5 means.

## Quantitative observations

| Metric | masked_crops | rectangular_crops | Interpretation |
|---|---:|---:|---|
| Identity cosine mean | 0.7967 | 0.7688 | Both pass; masked higher on 4/5 pairs |
| Proportion diagnostic mean | 15.632% | 5.828% | Rectangular lower on 4/5 pairs |
| Top color dE | 4.710 (n=1) | 3.048 (n=5) | Not decision-grade due unequal n |
| Bottom color dE | 2.860 (n=1) | 4.000 (n=5) | Not decision-grade due unequal n |
| Shoes color dE | 29.667 (n=3) | 29.692 (n=5) | Both fail; outputs contain bare feet |
| Belt color dE | 5.115 (n=2) | 8.254 (n=5) | Not decision-grade due unequal n |
| Earrings color dE | 3.987 (n=3) | 6.240 (n=5) | Not decision-grade due unequal n |

The proportion metric remains diagnostic because it measures the clothed silhouette,
not the underlying body. The rectangular arm is more stable under that diagnostic,
but this alone is not proof of better body preservation.

## Pending decision

No automatic winner is assigned. The owner must review the five same-seed pairs in
`paired_contact_sheet.png`, with particular attention to face, blouse structure,
skirt shape, belt fidelity, earrings, and overall preference. A final conclusion is
written only after that review.
