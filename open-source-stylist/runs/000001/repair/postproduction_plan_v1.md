# Postproduction Plan v1

This plan is now treated as one example under the general strategy in
`docs/postproduction_strategy.md`. Do not tune the whole project around this
single belt issue.

## Base Selection

Current best base direction:

- `runs/000001/experiments/two_view_prompt_v4/output/candidate_01.png`

Alternative bases:

- `runs/000001/experiments/two_view_prompt_v4/output/candidate_04.png`
- `runs/000001/experiments/two_view_prompt_v4/output/candidate_05.png`

## Evaluation Priority

Base generation should preserve hard-to-repair things first:

1. identity;
2. body shape;
3. body anatomy and believable garment fit;
4. outfit structure and layering;
5. garment silhouette;
6. shoes/accessory placement;
7. pose preservation when the input requires it;
8. color and fine texture.

## Example Repair Target

Target:

- belt visibility.

Problem:

- V4 produces a strong visible belt.
- Desired logic says the belt should be only a narrow partial glimpse under the top hem.

Why this target:

- It tests local structure/layering repair.
- It is more meaningful than simple color correction.
- It can be masked around the waist and should not require changing face, body, pose, skirt length, or shoes.

## Example Repair Attempt A

Input:

- candidate image: `../experiments/two_view_prompt_v4/output/candidate_01.png`
- reference board: `../qwen/reference_board_neutral_labels.png`

Mask:

- waist area only;
- include belt, top hem, and the upper 10-15% of skirt;
- exclude face, hair, arms, lower skirt, feet, and background.

Prompt:

```text
Edit only the waist area. Keep the person, face, hair, glasses, body shape,
pose, background, skirt length, shoes, and earrings unchanged.

Make the belt only a narrow partial glimpse under the top hem. The top hem
should remain visible over the upper skirt. The skirt must still start
underneath the top hem. Do not create a full visible waist belt.
```

Success:

- belt no longer dominates the waist;
- top hem remains visible;
- skirt still begins under top hem;
- no damage to face/body/background.

Failure:

- body/waist shape changes;
- top hem disappears;
- skirt waist becomes broken;
- full outfit is regenerated;
- face or background changes.

## Example Repair Attempt B

If A fails, accept visible belt as revised outfit logic for this outfit and move
to repair target 2:

- shoe material/strap/buckle detail.
