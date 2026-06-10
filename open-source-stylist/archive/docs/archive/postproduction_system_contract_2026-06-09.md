# Postproduction System Contract

Last updated: 2026-06-09

This contract defines the postproduction layer for Open Source Stylist.

Postproduction is an automatic local repair stage after one usable base
generation. It improves repairable regions while preserving identity, body,
garment structure, and background.

## Product Runtime Shape

Final product flow:

```text
manual or selected outfit package
-> Qwen Image Edit base generation through ComfyUI
-> evaluator through LM Studio
-> repair planner
-> mask builder
-> masked local repair through ComfyUI
-> verifier through LM Studio and image checks
-> saved run folder
```

The user should not need to choose masks, repair targets, or executor settings
in the final product. Those choices happen under the hood.

During R&D, Codex must state intent before taking practical action in this
area, especially before running tools or editing images:

```text
what I am about to do:
target failure:
why this target matters:
executor/tool being tested:
expected improvement:
failure condition:
files that will be written:
```

This is a collaboration rule for development work. It is not a product-runtime
step. In the final system, target selection, masking, repair, and verification
should happen automatically under the hood.

## Inputs

Required:

- source person image;
- base generated image;
- outfit package;
- reference board or item reference images;
- base generation prompt;
- base generation settings;
- evaluator result.

Optional:

- person analysis;
- existing masks;
- reference crops;
- user priority settings;
- previous repair reports.

Runtime input should be represented as a structured repair request, not loose
files passed by convention.

Schema:

```text
schemas/postproduction_repair_request.schema.json
```

The request points to all assets and declares their status:

- `exists` for assets already available;
- `planned` for assets that must be prepared before execution;
- `missing` for blockers;
- `not_applicable` when a field is intentionally unused.

Executor code should only run requests marked `ready_to_run`.

## Outputs

Required:

- final image or rejection/regeneration verdict;
- evaluation JSON;
- repair plan JSON;
- mask image(s);
- repair prompt/instruction;
- repair settings;
- repair log.

Optional:

- reference crops used by a repair;
- intermediate repaired images;
- before/after sheets;
- protected-region difference maps.

## Toolchain

### 1. Evaluator

Purpose:

- decide whether the base generation is usable;
- identify hard failures;
- identify local repair candidates.

Tools:

- R&D start: manual checklist;
- product direction: LM Studio vision-language model producing structured JSON;
- support checks: image comparison and protected-region difference maps.

Evaluator output should classify failures, not prescribe visual taste.

Example failure classes:

- identity damage;
- body/anatomy damage;
- wrong garment type;
- wrong large-scale outfit structure;
- wrong local object/detail;
- wrong local shape;
- wrong layer boundary;
- wrong material/texture;
- wrong color/tone;
- old source clothing remnant;
- background damage.

### 2. Repair Planner

Purpose:

- choose the next action from evaluator output;
- select one repair target per pass;
- choose an executor class;
- set risk limits and verification criteria.

Tools:

- V1: rule-based Python planner using JSON schema;
- later: LM Studio LLM/VLM may help fill or explain the plan, but rules remain
  the guardrail.

Planner actions:

```text
accept
local_masked_edit
deterministic_cleanup
regenerate_base
reject
```

Planning rules:

- identity, body/anatomy, global structure, or severe background failures route
  to `regenerate_base` or `reject`;
- local structure/detail/material failures route to `local_masked_edit`;
- mild color/tone/blending failures may route to `deterministic_cleanup`;
- uncertain masks lower repair confidence;
- every action must name what success and failure look like.

### 3. Mask Builder

Purpose:

- define the editable region;
- define protected regions;
- refine masks before repair.

Tools:

- R&D: manual painted mask or manual polygon mask;
- available local direction: SAM;
- available local direction: GroundingDINO + SAM for text-located objects;
- future direction: human/fashion parsing for body and garment regions;
- OpenCV/Pillow for mask cleanup, expansion, contraction, feathering, and edge
  refinement.

Mask outputs:

- edit mask;
- protected face/hair/skin/body/background masks when relevant;
- mask confidence and notes.

Mask requirements:

- include enough context for the model to repair the region;
- avoid face and identity regions by default;
- protect exposed skin and body outline unless the task explicitly requires
  garment/body boundary repair;
- save every mask used in the run folder.

### 4. Repair Executor

Purpose:

- perform the actual local repair.

Executor classes:

#### A. Masked Local Generative Edit

Primary postproduction executor.

Tools:

- Qwen Image Edit masked/local workflow through ComfyUI;
- FLUX Fill / inpaint workflow through ComfyUI if it gives better local control.

Inputs:

- base image;
- edit mask;
- protected masks when available;
- local instruction;
- outfit package facts;
- relevant reference image/crop/board;
- negative constraints;
- denoise/strength/seed/settings.

Use for:

- local old-clothing remnants;
- local layer boundary failures;
- missing or wrong local details;
- small shape corrections;
- material/texture repair;
- removing unwanted local objects;
- adding missing local garment/accessory elements when the surrounding structure
  is already usable.

#### B. Deterministic Cleanup

Support executor.

Tools:

- Pillow/OpenCV image operations.

Use for:

- mild color or tone matching;
- small blending cleanup;
- edge softening;
- local sharpening or detail contrast after semantic repair.

Limits:

- does not create missing content;
- does not fix wrong shape or wrong garment logic;
- requires a reliable mask and verifier;
- should be low strength.

#### C. Regenerate Base

Fallback action when local repair is the wrong tool.

Tools:

- Qwen Image Edit base workflow through ComfyUI.

Use for:

- identity damage;
- broken anatomy;
- wrong main garment type;
- globally wrong outfit structure;
- large old-clothing remnants;
- severe background/camera damage.

#### D. Reject

Use when the result is not worth repairing and regeneration is outside the
current budget or cannot solve the issue with current tools.

### 5. Verifier

Purpose:

- decide whether repair improved the target;
- detect damage outside the target region;
- choose accept, retry, regenerate, or reject.

Tools:

- R&D: manual visual review;
- product direction: LM Studio VLM;
- support checks: before/after sheet, protected-region diff, mask leakage check.

Verifier checks:

- target improved;
- identity preserved;
- face/hair/glasses preserved;
- body outline and anatomy preserved;
- background preserved;
- outfit structure not worsened;
- no new artifacts outside the mask.

### 6. Run Logger

Purpose:

- make every repair reproducible and reviewable.

Tools:

- Python file operations;
- JSON;
- Markdown notes;
- saved images.

Required run artifacts:

```text
runs/<run_id>/repair/<repair_id>/
  input_base.png
  edit_mask.png
  protected_masks/
  reference_crop_or_board.*
  repair_instruction.txt
  settings.json
  output.png
  before_after.png
  verifier_result.json
  verdict.md
```

## Runtime Budget

Default product budget:

```text
1 base Qwen generation
1 evaluator pass
0-2 local repair passes
1 final verifier pass
```

Research mode may generate multiple candidates or compare executors, but every
comparison must live in a run folder with inputs, outputs, settings, and
verdict.

## Repair Pass Rules

- One repair target per pass.
- Use the smallest safe mask with enough context.
- Keep face repair out of the default workflow.
- Preserve body outline and exposed skin unless the repair specifically needs
  that boundary.
- Stop after two failed local repair attempts.
- Record failed repairs as failed; do not relabel them as partial passes unless
  the target visibly improved and no higher-priority damage was introduced.

## Current V1 Priority

The core postproduction tool to prove is:

```text
masked local generative edit through ComfyUI
```

The first useful proof should answer:

- can the workflow accept base image + mask + instruction + reference evidence;
- can it change only the masked local clothing/accessory region;
- can it preserve identity, body, and background;
- can it improve a general repair class such as local detail, layer boundary,
  old-clothing remnant, or material/texture;
- what runtime and failure modes appear.

Deterministic cleanup remains a support tool, not the main proof of
postproduction quality.
