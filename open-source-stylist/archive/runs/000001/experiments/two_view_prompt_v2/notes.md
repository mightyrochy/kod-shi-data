# Experiment: two_view_prompt_v2

## Purpose

Test whether using the two-view person image as `image 1` improves body-shape
and side-view preservation compared with the front-only input.

## Input

- `input/image_1_person_two_view.png`
- `input/image_2_reference_board_clean.png`
- `input/prompt.txt`

Prompt used:

```text
change outfit of woman from image 1 to outfit from image 2 using "outfit layout"

Outfit layout:
- The blouse hem remains visible over the upper skirt.
- The skirt starts underneath the blouse hem.
- Same earings on both ears.
- belt is barely visible from under the blouse hem
- wedge sandals on bere feet

keep woman unchanged
```

## Outputs

- `output/candidate_01.png`
- `output/candidate_02.png`
- `output/candidate_03.png`
- `output/candidate_04.png`
- `output/candidate_05.png`
- `output/contact_sheet_5_candidates.png`

## Verdict

Useful two-view baseline, but not clean enough as a final route yet.

Compared with the front-only run:

- side view and shoe silhouette are easier to inspect;
- outfit concept remains stable;
- identity risk is higher;
- belt control is worse in several candidates.

Best candidate:

- `candidate_01.png`

Main failure:

- candidate 03 changes hair color, so short "keep woman unchanged" is not strong enough.

Next:

- Try a stricter two-view prompt that explicitly preserves face, blonde hair,
  glasses, body shape, background, and both original poses.
