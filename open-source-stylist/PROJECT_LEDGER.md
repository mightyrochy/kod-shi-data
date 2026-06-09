# Project Ledger

Last updated: 2026-06-09

Purpose:

This file preserves the durable project path: what was decided, what was tested,
what worked, what failed, where we are now, and what remains open.

`PROJECT_STATE.md` is the short current snapshot. `SESSION_LOG.md` is the
chronological work-block log. This ledger is the recovered project memory that
should not be erased when the current snapshot changes.

## Canonical Current Frame

Project:

```text
Open Source Stylist
```

Goal:

Create an open source automatic stylist and outfit transfer pipeline that takes
a person photo, a style request, and outfit constraints, then outputs the same
person in a new outfit with identity/body preservation and an evaluation report.

Current strategy:

```text
manual outfit package
-> Qwen-Image-Edit-2511 through ComfyUI
-> evaluator through LM Studio
-> targeted postproduction repair
-> repeatable run folder
```

Primary Try-On/Base Edit Engine:

```text
Qwen-Image-Edit-2511 fp8mixed through ComfyUI
```

Other tools are evaluated as postproduction, masking, evaluation, or benchmark
tools. They are not replacements for Qwen 2511 in the current phase unless the
roadmap is explicitly changed.

Active milestone:

```text
M1 - One Controlled Manual Outfit Run
```

## Recovered Original Context

The first user intent was not "make one prompt." It was:

```text
Help build an open-source automatic stylist and outfit-transfer system.
Understand existing solutions, why Qwen 2511 works better here, and how a
future wardrobe-like layer could fit.
```

The project source document, `Velyka Tsil.docx` / `Велика Ціль.docx`, defines
the product as:

```text
automatic stylist + outfit transfer pipeline
```

The user gives:

- person image;
- short style request;
- optional constraints: budget, colors, dislikes, occasion, season, mood.

The system should:

1. analyze the person in the photo;
2. choose or receive a concrete outfit;
3. generate the same person in the new outfit;
4. evaluate the result;
5. repair or retry when needed.

Important preservation targets:

- identity;
- face;
- body shape;
- hair color;
- skin tone.

The intended architecture from the original document:

```text
User photo + style request
-> Person analysis
-> Stylist System
-> Outfit Adapter
-> Qwen image edit
-> Afterproduction/Postproduction
-> Evaluation / retry
```

The Stylist System should output structured outfit evidence, not vague fashion
advice:

- concrete item images;
- wearing/layering logic;
- visible/hidden parts;
- overlap rules.

The Outfit Adapter should not choose style or invent details. It converts the
structured outfit layout into Qwen-ready prompt/reference evidence.

## Existing Solution Landscape

The early exploration separated tools by role:

- dedicated virtual try-on models;
- general image-edit models;
- segmentation/masking tools;
- evaluation/VLM tools;
- future wardrobe/catalog systems.

The user had already tested:

- IDM-VTON;
- CatVTON;
- FASHN VTON v1.5;
- Qwen-Image-Edit-2511.

Durable conclusion:

```text
Qwen-Image-Edit-2511 is the current primary base edit engine because it gave
better multi-item outfit-transfer behavior for this project than the tested
dedicated VTON systems.
```

Dedicated VTON tools may be useful references, but the current hard problem is
the full controlled loop:

```text
outfit evidence -> Qwen generation -> evaluation -> targeted repair
```

## Parked Wardrobe Direction

Wardrobe-like functionality remains valuable:

- user wardrobe;
- item catalog;
- outfit recommendation;
- item tags;
- occasion/weather/style filters;
- reuse of owned garments.

But it is parked until the core run/evaluate/repair loop works.

Durable implication:

```text
Wardrobe/Catalog is a later layer, not part of M1-M4.
```

## User Experience Constraint

The user said this is their first project of this kind and that they have no
programming/IT background.

Codex should:

- lead step by step;
- explain non-technically first;
- avoid vague engineering tasks;
- keep each work block small;
- state intent before practical R&D actions;
- record durable progress in files.

The previous memory process failed because large `.md` files were rewritten and
important path context was lost. This ledger exists to prevent that.

## Local Environment And Old Attempts

Environment:

- RTX 4090 Laptop GPU, 16 GB VRAM;
- 32 GB RAM;
- ComfyUI local backend;
- LM Studio local backend;
- Qwen 2511 fp8mixed/bf16 and related Qwen models present;
- SAM, GroundingDINO, and FLUX Fill present.

Old project material is archive material, not the foundation.

Useful old ideas:

- structured outfit JSON;
- visual reference boards;
- evidence tiles;
- prompt packaging;
- run folders.

Risk from old attempts:

- pipelines grew too complex before the core loop became reliable.

## Run 000001

Run folder:

```text
runs/000001
```

Diagnostic assets included:

- person front image;
- two-view person image;
- blouse front/back;
- skirt front/back/flat;
- jacket;
- dress;
- earrings;
- shoes;
- belt;
- sweater.

Active diagnostic outfit:

- ivory voluminous-sleeve blouse with V neckline, front buttons, shaped waist,
  and peplum/hem;
- brown long straight skirt with front slit;
- brown belt as secondary waist detail;
- dark green wedge sandals;
- gold disc earrings.

This outfit is diagnostic only. The system must generalize through failure
classes and repair policies, not through overfitting to this belt, shoes,
blouse, skirt, or earrings.

## Base Generation Path

### Front-Only Run

Outputs:

- `runs/000001/output/candidate_01.png` through `candidate_05.png`
- `runs/000001/output/contact_sheet_5_candidates.png`
- `runs/000001/evaluation/manual_evaluation_5_candidates.json`

Verdict:

- strong baseline / partial pass;
- old sweater, jeans, and socks removed;
- outfit concept stable;
- detail fidelity weak: belt, shoe structure/texture, earring detail, skirt
  slit, fabric behavior.

### Two-View Prompt V2

Purpose:

Use two-view person input as image 1 and a clean reference board as image 2.

Verdict:

- useful two-view baseline;
- side/body diagnostics improved;
- outfit concept stable;
- identity risk increased;
- belt control inconsistent.

### Two-View Prompt V3

Purpose:

Use stricter identity preservation and simpler explicit wording.

Verdict:

- very consistent;
- less accurate;
- likely pushed Qwen toward generic outfit priors instead of exact visual
  reference matching.

### Two-View Prompt V4

Folder:

```text
runs/000001/experiments/two_view_prompt_v4
```

Changes:

- two-view person input;
- neutral-label reference board;
- removed simple item color words;
- kept strong identity preservation;
- visual references treated as source of truth.

Verdict:

- current best base-generation direction;
- identity stable enough;
- hair/glasses/general face preserved;
- body shape, anatomy, and side silhouette useful;
- top-over-skirt structure stable;
- top hem/peplum relation better than v3;
- skirt silhouette and slit stable;
- wedge sandals and earrings readable.

Remaining failures:

- belt too dominant;
- blouse construction simplified;
- sandal material/buckle detail simplified;
- earring surface detail simplified;
- exact colors imperfect but lower priority.

## Durable Decisions

### Qwen 2511 Is Primary

Qwen-Image-Edit-2511 fp8mixed through ComfyUI is the primary Try-On/Base Edit
Engine for the current phase.

### Base Generation Priority

Base Qwen outputs are judged first on hard-to-repair qualities:

1. identity;
2. body shape and proportions;
3. body anatomy and plausible garment fit;
4. outfit structure and layering logic;
5. garment shapes and silhouettes;
6. footwear/accessory placement;
7. pose/camera preservation when the input requires it;
8. colors and fine surface details.

Colors and fine details are lower priority because they are more plausible
postproduction targets. Exact pose preservation is conditional.

### Default Runtime Budget

The default product path should prefer:

```text
one base Qwen generation
-> evaluator
-> local postproduction if repairable
-> verifier/final report
```

Multi-candidate generation is research mode.

### Postproduction Meaning

Postproduction is surgical local repair after a usable Qwen base generation.

It should not redesign the outfit, casually repaint regions, or repair
unvalidated targets during R&D.

## Postproduction Work So Far

Created:

- `docs/postproduction_strategy.md`
- `docs/postproduction_system_contract.md`
- `schemas/postproduction_repair_request.schema.json`
- `runs/000001/repair/masked_local_edit_proof_v1`

Earlier supporting files:

- `schemas/evaluation_and_repair_plan.schema.json`
- `prompts/evaluation_and_repair_planner.md`

### Failed Color Repair Test

Folders:

```text
runs/000001/repair/color_repair_shoes_v1
runs/000001/repair/color_repair_shoes_v2
```

Tool:

```text
tools/postproduction_color_repair.py
```

Verdict:

- failed as R&D process and visual repair;
- target was not validated with the user before execution;
- shoes were not the right first problem;
- output made the outfit worse;
- deterministic cleanup is only a support tool for carefully validated
  color-only cases.

Durable lesson:

```text
Codex must state intent before practical R&D actions in this project.
This is a collaboration rule for development work, not a product-runtime step.
```

### Current Postproduction Direction

Core executor class to prove:

```text
masked local generative edit
```

Current setup:

```text
runs/000001/repair/masked_local_edit_proof_v1
schemas/postproduction_repair_request.schema.json
```

Status:

- intent prepared;
- runtime repair request prepared;
- base image copy, edit mask, mask preview, repair instruction, and settings
  prepared;
- image edit run completed through ComfyUI API;
- verdict recorded.

Prepared files:

- `runs/000001/repair/masked_local_edit_proof_v1/input_base.png`
- `runs/000001/repair/masked_local_edit_proof_v1/edit_mask.png`
- `runs/000001/repair/masked_local_edit_proof_v1/edit_mask_preview.png`
- `runs/000001/repair/masked_local_edit_proof_v1/repair_instruction.txt`
- `runs/000001/repair/masked_local_edit_proof_v1/settings.json`
- `runs/000001/repair/masked_local_edit_proof_v1/repair_request.json`
- `runs/000001/repair/masked_local_edit_proof_v1/run_inputs.md`

Selected proof target:

```text
front-view waist / belt / blouse-hem layer boundary on v4 candidate_01
```

Executor candidate:

```text
comfyui_flux_fill
```

Reason:

This is the strict-mask locality/preservation proof. It tests whether the
executor can alter a bounded non-face region while preserving identity, body,
side view, footwear, earrings, background, and other unmasked areas.

Result:

```text
partial pass
```

More specific:

```text
pass for strict locality / preservation
fail as meaningful semantic outfit repair
```

Evidence:

- `runs/000001/repair/masked_local_edit_proof_v1/outputs/output.png`
- `runs/000001/repair/masked_local_edit_proof_v1/outputs/before_after.png`
- `runs/000001/repair/masked_local_edit_proof_v1/outputs/target_crop_before_after.png`
- `runs/000001/repair/masked_local_edit_proof_v1/outputs/leakage_stats.json`
- `runs/000001/repair/masked_local_edit_proof_v1/outputs/verifier_result.json`
- `runs/000001/repair/masked_local_edit_proof_v1/outputs/verdict.md`

What passed:

- edit stayed visually local;
- face, hair, glasses, body outside the target, side view, footwear, earrings,
  and background were preserved;
- outside-mask pixel change was very low.

What failed:

- belt remained a dominant wide belt;
- blouse hem became more regular but did not solve the outfit logic issue;
- rectangular mask was too crude for quality repair;
- FLUX Fill workflow did not provide direct reference-image conditioning.

The repair request should look like real product input:

- source image;
- outfit package;
- base generation;
- evaluator verdict;
- repair target;
- mask;
- protected regions;
- references;
- executor;
- instruction;
- verification criteria;
- planned outputs.

## ComfyUI Migration / Update State

Snapshot:

```text
docs/comfyui_update_safety_snapshot_2026-06-09.md
```

Findings:

- Desktop created/uses an instance entry;
- backend still points to `C:\Users\Admin\ComfyUI`;
- input/output still point to:
  - `C:\Users\Admin\ComfyUI\input`;
  - `C:\Users\Admin\ComfyUI\output`;
- shared model paths include:
  - `C:\Users\Admin\ComfyUI\models`;
  - `C:\Users\Admin\ComfyUI-Shared\models`;
- local API at `http://127.0.0.1:8000/system_stats` responded after restart.

Current advice:

```text
Wait on Desktop Update Ready until workflow/model checks are stable.
```

## Postproduction Tool Research State

Research docs:

- `docs/postproduction_tool_research_2026-06-09.md`
- `docs/postproduction_local_workflow_capability_matrix_2026-06-09.md`

Correct framing:

```text
Qwen 2511 fp8mixed = primary Try-On/Base Edit Engine.
Postproduction tools = downstream repair executors or support tools.
```

Current ranking by role:

- Qwen 2511 Image Edit: strongest semantic/reference outfit repair candidate;
- FLUX.1 Fill: strongest strict masked locality/preservation candidate;
- SAM/GroundingDINO/fashion parsing: mask-builder tools;
- LM Studio VLM: evaluator/verifier direction;
- deterministic cleanup: support only.

Local capability notes:

- Qwen 2511 Image Edit blueprint supports prompt + image1/image2/image3, but
  inspected blueprint does not expose direct mask input.
- FLUX.1 Fill supports explicit image+mask inpaint conditioning, but has weaker
  reference/outfit-detail control.
- Qwen-image inpainting blueprint is blocked by missing
  `Qwen-Image-InstantX-ControlNet-Inpainting.safetensors`.
- SDXL inpaint was not detected locally and is not part of the first proof.

## Documentation Cleanup State

Date:

```text
2026-06-09
```

Archived old starter/pre-cleanup material:

- `docs/archive/README_starter_2026-06-08.md`
- `docs/archive/architecture_starter_2026-06-08.md`
- `docs/archive/postproduction_strategy_pre_cleanup_2026-06-09.md`
- `docs/archive/evaluation_and_repair_planner_pre_cleanup_2026-06-09.md`
- `docs/archive/evaluation_and_repair_plan_schema_pre_cleanup_2026-06-09.json`

Active docs now point to the current project frame rather than the old broad
starter MVP.

## Current Open Questions

### Postproduction First Proof

Strict masked locality/preservation proof is complete. The evidence supports
FLUX Fill as a locality/preservation candidate, but not as a final
reference-aware semantic repair executor.

### Qwen Locality Mechanism

Qwen 2511 is the primary base engine and strongest semantic/reference repair
candidate, but the inspected blueprint lacks direct mask input.

Possible locality mechanisms:

- find/build true Qwen masked workflow;
- crop-mask-composite around local region;
- use Qwen for semantic repair on crop and composite back;
- use Qwen-image inpainting if the missing ControlNet model is obtained.

### Evaluator / Verifier

LM Studio VLM still needs a real schema-driven evaluation/verifier test.

It should verify:

- target improved;
- identity/body/background preserved;
- no new artifacts outside mask;
- repair should be accepted, retried, regenerated, or rejected.

## Current Next Small Task

Choose the next postproduction proof:

```text
Qwen 2511 semantic/reference local repair with a locality mechanism
```

Alternative only if needed:

```text
rerun FLUX Fill with a more precise mask to confirm locality further
```
