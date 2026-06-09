# Project State

Last updated: 2026-06-09

## Mission

Build an open source automatic stylist and outfit transfer pipeline.

The system should take a person photo, a style request, and optional
constraints, then output the same person in a new outfit with identity/body
preservation and an evaluation report.

## Current Strategy

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

This is already chosen for the current phase. Postproduction tools are
downstream repair tools, not replacements for the primary try-on engine.

## Active Milestone

Milestone:

```text
M1 - One Controlled Manual Outfit Run
```

Status:

```text
active
```

M0 is complete.

## Current Truth

Full durable path:

```text
PROJECT_LEDGER.md
```

Current run:

```text
runs/000001
```

Current best base-generation direction:

```text
runs/000001/experiments/two_view_prompt_v4
```

Important verdict:

- v4 is the current best Qwen base direction.
- It preserves hard-to-repair features better than prior attempts: identity,
  body/anatomy, two-view consistency, outfit structure, and footwear/accessory
  placement.
- Remaining issues are postproduction candidates: local layer/detail/material
  problems, especially belt dominance and simplified details.

Failed postproduction attempt:

```text
runs/000001/repair/color_repair_shoes_v2
```

Verdict:

- failed as R&D process and visual repair;
- deterministic color cleanup is support only;
- it is not proof of postproduction quality.

Current postproduction setup:

```text
runs/000001/repair/masked_local_edit_proof_v1
schemas/postproduction_repair_request.schema.json
```

Status:

- intent prepared;
- runtime repair request prepared:
  `runs/000001/repair/masked_local_edit_proof_v1/repair_request.json`;
- base image copy, edit mask, mask preview, repair instruction, and settings
  prepared;
- selected target: front-view waist / belt / blouse-hem layer boundary on
  `candidate_01`;
- executor candidate: `comfyui_flux_fill` using local FLUX Fill workflow;
- image edit run completed through ComfyUI API;
- verdict: partial pass;
- passed strict locality/preservation;
- failed as meaningful semantic outfit repair because the belt remained
  dominant and reference/detail control was weak.

## Current Environment

ComfyUI:

```text
http://127.0.0.1:8000
C:\Users\Admin\ComfyUI
```

LM Studio:

```text
http://127.0.0.1:1234
```

Key local assets:

- Qwen-Image-Edit-2511 fp8mixed and bf16;
- Qwen VAE;
- Qwen text encoders;
- Qwen Lightning LoRA;
- FLUX.1 Fill dev;
- SAM;
- GroundingDINO.

Comfy Desktop migration/restart check:

- backend still points to `C:\Users\Admin\ComfyUI`;
- input/output still point to `C:\Users\Admin\ComfyUI\input` and
  `C:\Users\Admin\ComfyUI\output`;
- shared model paths include `C:\Users\Admin\ComfyUI\models` and
  `C:\Users\Admin\ComfyUI-Shared\models`;
- details: `docs/comfyui_update_safety_snapshot_2026-06-09.md`.

## Current Open Questions

### Postproduction First Proof

Choose which capability to prove first:

1. strict masked locality/preservation;
2. semantic/reference outfit repair with Qwen 2511 plus a locality mechanism.

The choice should be based on quality, function, and system compatibility.

### Qwen Locality Mechanism

Qwen 2511 is the primary base engine and strongest semantic/reference repair
candidate, but the inspected ComfyUI blueprint does not expose direct mask
input.

Possible paths:

- find/build true Qwen masked workflow;
- crop-mask-composite around a local region;
- Qwen semantic repair on crop, then composite back;
- Qwen-image inpainting if the missing ControlNet model is obtained.

### Evaluator / Verifier

LM Studio VLM still needs a real schema-driven evaluation/verifier test.

## Immediate Next Task

Documentation recovery and cleanup is complete for the active control docs.

Recommended next action:

```text
Use the completed strict locality proof as evidence.
Next choose whether to test Qwen semantic/reference local repair with a locality
mechanism, or rerun FLUX Fill only with a more precise mask if locality needs
one more confirmation.
```

## Source Of Truth Files

- `AGENTS.md` - how Codex must work in this repo.
- `PROJECT_STATE.md` - current snapshot only.
- `PROJECT_LEDGER.md` - durable project path.
- `WORKFLOW.md` - session and task protocol.
- `ROADMAP.md` - milestone order.
- `DECISIONS.md` - architectural decisions.
- `NOT_NOW.md` - parked scope.
- `SESSION_LOG.md` - chronological work-block history.

Supporting docs:

- `docs/system_audit_2026-06-08.md`
- `docs/comfyui_update_safety_snapshot_2026-06-09.md`
- `docs/postproduction_system_contract.md`
- `docs/postproduction_tool_research_2026-06-09.md`
- `docs/postproduction_local_workflow_capability_matrix_2026-06-09.md`

Archived starter/superseded material:

- `docs/archive/`
