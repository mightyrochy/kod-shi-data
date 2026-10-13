# Experiment: two_view_prompt_v4

## Purpose

Test the user's color-word hypothesis.

`two_view_prompt_v3` was very consistent but inaccurate. It used explicit simple
color words and a long preservation prompt. This may have pushed Qwen toward
generic internal color/outfit priors instead of exact visual matching from the
reference board.

## Changes From V3

- Removes simple item color words from the prompt.
- Uses `qwen/reference_board_neutral_labels.png`.
- Keeps strong identity preservation.
- Asks the model to match visual appearance from image 2 instead of naming colors.
- Focuses on construction details and outfit layout.

## Inputs To Use

- Image 1: `../two_view_prompt_v2/input/image_1_person_two_view.png`
- Image 2: `../../qwen/reference_board_neutral_labels.png`
- Prompt: `input/prompt.txt`

## Success Criteria

- Same consistency as v3.
- Better top hem / peplum accuracy.
- Belt is only a partial glimpse.
- Better sandal straps/wedge detail.
- No hair color or identity drift.

## Status

Generated and manually evaluated.

## Updated Verdict

V4 is the current best base-generation direction.

Why:

- consistency is high;
- person identity is stable enough;
- body shape and side view are useful;
- outfit structure is stable;
- top hem / skirt relationship is better than v3;
- remaining issues are more postproduction-friendly than identity or body drift.

Main issue:

- belt is too visible and behaves like a dominant waist belt, not a barely visible glimpse.

Next:

- use `candidate_01.png` or `candidate_04.png` as a postproduction base;
- first repair target should be belt visibility or accepting the visible belt as revised outfit logic.
