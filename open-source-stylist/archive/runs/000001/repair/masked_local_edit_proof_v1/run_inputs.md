# Masked Local Edit Proof V1 - Prepared Inputs

Status:

```text
inputs prepared; image edit not run
```

## Selected Base

```text
runs/000001/repair/masked_local_edit_proof_v1/input_base.png
```

Original source:

```text
runs/000001/experiments/two_view_prompt_v4/output/candidate_01.png
```

Reason:

Manual evaluation selected `candidate_01.png` as the strongest balance of
identity, structure, two-view consistency, and outfit completeness.

## Selected Target

```text
front-view waist / belt / blouse hem layer boundary
```

Reason:

This is a bounded non-face region. It tests whether postproduction can repair a
local layer-boundary issue without changing identity, body, side view, footwear,
earrings, or background.

This is a general postproduction capability proof. It is not tuning the system
to this specific belt.

## Mask

```text
runs/000001/repair/masked_local_edit_proof_v1/edit_mask.png
runs/000001/repair/masked_local_edit_proof_v1/edit_mask_preview.png
```

Mask box:

```text
x1=455, y1=245, x2=625, y2=340
```

The rectangular mask is intentionally simple. The first proof checks locality
and preservation, not perfect automatic segmentation.

## Executor Candidate

```text
comfyui_flux_fill
```

Workflow candidate:

```text
C:/Users/Admin/ComfyUI/user/default/workflows/flux_fill_inpaint_cots.json
```

Reason:

FLUX Fill is the current strict-mask locality candidate. It is being used here
to test preservation behavior, not as the final semantic outfit-detail repair
solution.

## Prepared Runtime Files

```text
repair_request.json
repair_instruction.txt
settings.json
input_base.png
edit_mask.png
edit_mask_preview.png
```

## Pass / Fail

Pass:

- masked waist/layer boundary improves;
- edit remains local;
- identity/body/background/side-view/footwear/earrings stay visually unchanged.

Fail:

- edit leaks outside mask;
- face/body/background changes;
- outfit is globally redesigned;
- target region becomes worse;
- result cannot be reproduced from saved inputs.
