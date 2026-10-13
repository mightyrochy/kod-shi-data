# Postproduction Strategy

Postproduction is a downstream repair layer after a usable Qwen base generation.
It is not a replacement for Qwen-Image-Edit-2511 and not a hand-tuned fix for
one outfit.

Current base engine:

```text
Qwen-Image-Edit-2511 fp8mixed through ComfyUI
```

Current core postproduction executor class:

```text
masked local generative edit
```

Deterministic cleanup is support only. The failed shoe color repair proved that
simple mask painting/color adjustment is not enough to call postproduction
working.

## Product Flow

```text
one Qwen base generation
-> evaluator
-> local repair request if base is usable
-> masked/local repair executor
-> verifier
-> accept, retry locally, regenerate base, or reject
```

Multi-candidate Qwen generation is research mode, not the default product path.

## Repair Boundary

Postproduction may repair bounded failures:

- local layer boundary error;
- small old-clothing remnant;
- accessory scale, placement, or detail error;
- local texture/material/detail loss;
- local color or tone mismatch;
- local blend artifact.

Postproduction should preserve:

- face and identity;
- hair/glasses unless explicitly targeted;
- body outline and anatomy;
- global outfit structure;
- background and camera;
- unmasked clothing regions.

Regenerate or reject when the base has hard failures:

- identity damage;
- broken body anatomy;
- wrong main garment;
- large-scale outfit structure failure;
- physically implausible garment fit;
- severe background/camera change.

## Tool Roles

### Evaluator

Finds whether the base image is usable and names concrete repair targets.

Current likely tool:

```text
LM Studio VLM + schema-driven checklist
```

Manual evaluation remains acceptable during R&D when the result is recorded in
the run folder.

### Repair Request Builder

Turns an evaluator finding into product-like runtime input:

- source person image;
- outfit package;
- base generation;
- target region;
- mask;
- protected regions;
- references;
- executor choice;
- repair instruction;
- verification criteria.

Current schema:

```text
schemas/postproduction_repair_request.schema.json
```

### Mask Builder

Creates the region to edit and regions to protect.

Candidate tools:

- manual mask for first controlled proof;
- SAM;
- GroundingDINO;
- future human/fashion parsing if needed.

### Masked Local Generative Edit Executor

Main repair class. It should edit only the requested region while preserving the
rest of the image.

Candidate implementation paths:

- FLUX.1 Fill for strict image+mask inpaint locality;
- Qwen 2511 semantic/reference repair with crop-mask-composite locality;
- true Qwen masked/inpaint workflow if available or obtained.

### Deterministic Cleanup

Support executor for narrow color, tone, blend, and edge cleanup.

Use only when:

- the mask is reliable;
- the target is color/tone/blend, not structure;
- the source region is already structurally correct;
- the verifier can detect damage.

### Run Logger

Every repair attempt must save:

- intent;
- request JSON;
- masks;
- workflow/settings;
- output;
- verifier notes;
- verdict.

## First Proof Choice

There are two valid first proofs:

```text
strict masked locality/preservation
```

This answers: can a masked inpaint workflow change only the masked region and
leave everything else stable?

```text
Qwen semantic/reference local repair
```

This answers: can Qwen repair a clothing/detail region according to outfit
evidence while a locality mechanism prevents global drift?

The first choice should be made from quality, function, and compatibility with
the whole system, not from local workflow convenience.

## Current Test Folder

```text
runs/000001/repair/masked_local_edit_proof_v1
```

Status:

- intent prepared;
- draft runtime repair request prepared;
- no image edit has been run.
