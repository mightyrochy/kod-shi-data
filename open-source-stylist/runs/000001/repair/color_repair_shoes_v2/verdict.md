# Deterministic Color Repair - Shoes V2

Date: 2026-06-09

## Purpose

Test whether a cheap deterministic postproduction executor can shift a
garment/accessory color inside a mask without changing structure, identity,
body, face, or background.

## Input

- Base image: `runs/000001/experiments/two_view_prompt_v4/output/candidate_01.png`
- Target region: dark shoe pixels inside manually defined shoe polygons.
- Target color: `#0f3f35`, sampled as a practical dark green close to the shoe
  reference.

## Output

- Repaired image: `repaired_candidate_01.png`
- Mask: `shoe_mask.png`
- Before/after sheet: `before_after.png`
- Machine report: `report.json`

## Verification

- JSON files parse successfully.
- Visual review confirms the repair is local to the shoe regions.
- V1 failed because the raw feathered polygon mask also colored the floor.
- V2 added a dark-pixel guard, which prevented visible floor damage.

## Verdict

Failed as an R&D process and visual repair.

The target was not validated before execution, and the resulting image made the
outfit look worse. This experiment should not be treated as proof that
deterministic color repair improves postproduction quality.

The technical lesson is narrower: deterministic cleanup may be useful for
color-only corrections when:

- the garment or accessory shape is already acceptable;
- a mask exists;
- the target pixels can be separated from nearby skin/floor/background by simple
  brightness or saturation guards;
- the desired repair is hue/tone, not new detail.

It should not be used when:

- the mask touches similarly dark background or body regions;
- the garment shape is wrong;
- missing buckles, straps, seams, or texture are the main failure;
- the repair needs semantic understanding or new image content.

Runtime in this first implementation was about 3.27 seconds on the test image.
Runtime alone is not a success criterion; visual improvement and target
validation are required.

## Next

Use this as a negative example. The next postproduction proof should target the
core executor: masked local generative edit through ComfyUI, with test intent
written before any image edit is run.
