# Experiment: two_view_prompt_v3

## Purpose

Repeat the two-view input test with stricter identity preservation.

This responds to `two_view_prompt_v2`, where the two-view approach was useful
but at least one candidate changed hair color and the belt became too visible.

## Inputs To Use

- Image 1: `../two_view_prompt_v2/input/image_1_person_two_view.png`
- Image 2: `../two_view_prompt_v2/input/image_2_reference_board_clean.png`
- Prompt: `input/prompt.txt`

## Test Goal

Keep the benefits of two-view input:

- front and side outfit consistency;
- side-view body shape;
- side-view shoe readability.

Reduce the failures:

- hair color drift;
- face/identity drift;
- too-visible belt.

## Status

Prepared, not generated yet.
