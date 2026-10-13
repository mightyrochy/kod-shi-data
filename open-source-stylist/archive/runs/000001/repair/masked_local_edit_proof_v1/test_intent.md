# Masked Local Generative Edit Proof V1 - Test Intent

Date: 2026-06-09

## What Will Be Tested

Test whether a ComfyUI masked local generative edit workflow can repair one
bounded clothing/accessory region while preserving the rest of the image.

This is a proof of the core postproduction executor, not a final repair of the
outfit.

## Why This Matters

Postproduction quality depends on local semantic repair:

- edit only the failed region;
- preserve identity, body, background, and global outfit structure;
- use outfit/reference evidence;
- produce a reviewable run-folder artifact.

This test should show whether the core executor can be trusted before building
automatic repair planning around it.

## Target Failure Class

General class:

```text
local layer boundary / local garment detail failure
```

The exact region should be chosen only after inspecting the base image and mask
options. The target should be a non-face region where:

- the base image is otherwise usable;
- the issue is local;
- the repair can be judged visually;
- failure will not risk identity or body anatomy.

Candidate region for this run:

```text
waist/top-hem area, because it tests local layer boundary control.
```

## Executor / Tool

Primary tool to test:

```text
ComfyUI masked local generative edit
```

Candidate workflows:

- Qwen Image Edit masked/local workflow;
- FLUX Fill / inpaint workflow if Qwen masked edit is not practical.

The selected workflow must accept:

- base image;
- edit mask;
- local instruction;
- reference evidence from outfit package or reference board;
- settings saved as JSON.

## Expected Improvement

The output is considered improved only if:

- the selected local defect is visibly better;
- the edit remains inside or near the intended mask;
- face, hair, glasses, body outline, hands, legs, and background stay unchanged;
- global outfit structure is not worsened;
- no new obvious artifacts appear.

## Failure Condition

The test fails if:

- the model changes identity, face, body, pose, or background;
- the edit leaks far outside the mask;
- the repaired region looks worse than the base;
- the output changes the outfit logic globally;
- the workflow cannot be run with saved inputs/settings;
- the result cannot be reproduced from the run-folder artifacts.

## Runtime Input Shape

The repair should enter postproduction as a structured request, not as loose
ad-hoc files.

Draft request:

```text
runs/000001/repair/masked_local_edit_proof_v1/repair_request.json
```

Schema:

```text
schemas/postproduction_repair_request.schema.json
```

The request contains:

- source person image;
- outfit package;
- reference board and item references;
- base generation image/prompt/settings;
- evaluator verdict;
- selected repair target;
- edit mask;
- protected regions;
- executor/tool/workflow/settings;
- local instruction;
- verification criteria;
- planned outputs.

## Files To Be Written

Planned folder:

```text
runs/000001/repair/masked_local_edit_proof_v1/
```

Planned files:

```text
test_intent.md
repair_request.json
input_base.png
edit_mask.png
edit_mask_preview.png
reference_evidence.*
repair_instruction.txt
settings.json
outputs/output.png
outputs/before_after.png
outputs/verifier_result.json
outputs/verdict.md
```

Prepared files now exist:

```text
input_base.png
edit_mask.png
edit_mask_preview.png
repair_instruction.txt
settings.json
repair_request.json
run_inputs.md
```

## Current Status

Intent and runtime request prepared. Mask preview reviewed and narrowed so it
does not touch hands. No image edit has been run yet.
