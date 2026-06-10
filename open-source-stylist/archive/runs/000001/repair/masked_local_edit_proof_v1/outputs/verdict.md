# Masked Local Edit Proof V1 - Verdict

Date: 2026-06-09

## Result

```text
partial pass
```

More precise verdict:

```text
pass for strict locality / preservation
fail as meaningful semantic outfit repair
```

## What Passed

- ComfyUI FLUX Fill workflow ran successfully through API.
- The edit stayed visually local.
- Face, hair, glasses, body outside the target region, side view, footwear,
  earrings, and background appear preserved.
- Pixel leakage check shows very low outside-mask change:

```text
outside_changed_ratio = 0.00048431261146094723
outside_mean_abs_rgb_diff = 1.0751181025731
```

## What Did Not Pass

- The belt is still a dominant wide waist belt.
- The local blouse hem became more regular, but this does not solve the actual
  outfit logic issue.
- The mask was crude and rectangular. It was acceptable for locality smoke
  testing, not for quality repair.
- FLUX Fill had no direct reference-image conditioning in this workflow, so it
  is weak for exact fashion/detail repair.

## Interpretation

This run proves that the local masked executor can preserve most of the image
while changing the target area.

It does not prove that this executor can perform high-quality reference-aware
postproduction repair.

## Next Recommendation

Keep FLUX Fill as the strict locality / preservation candidate.

The next useful proof should test one of these:

```text
Qwen semantic/reference local repair with crop-mask-composite locality
```

or:

```text
one more FLUX Fill locality run with a more precise mask, only if stricter
locality confidence is needed
```
