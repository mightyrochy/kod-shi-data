# Open Source Stylist

Open Source Stylist is an open-source automatic stylist and outfit-transfer
pipeline.

Current working path:

```text
manual outfit package
-> Qwen-Image-Edit-2511 through ComfyUI
-> evaluator through LM Studio
-> targeted postproduction repair
-> repeatable run folder
```

Primary Try-On/Base Edit Engine for the current phase:

```text
Qwen-Image-Edit-2511 fp8mixed through ComfyUI
```

Postproduction tools are downstream repair tools. They do not replace the Qwen
base engine unless the roadmap is explicitly changed.

## Where To Start

- `PROJECT_STATE.md` - current snapshot.
- `PROJECT_LEDGER.md` - durable project path and recovered history.
- `WORKFLOW.md` - how work blocks should be run.
- `ROADMAP.md` - current milestone order.
- `DECISIONS.md` - architectural decisions.
- `SESSION_LOG.md` - chronological work-block notes.

Archived starter material is preserved in:

```text
docs/archive
```

## Active Milestone

```text
M1 - One Controlled Manual Outfit Run
```

Current run:

```text
runs/000001
```

Current best base-generation direction:

```text
runs/000001/experiments/two_view_prompt_v4
```

Current postproduction setup:

```text
runs/000001/repair/masked_local_edit_proof_v1
schemas/postproduction_repair_request.schema.json
```

No broad catalog, UI, database, or multi-model benchmark work is active until
the core run/evaluate/repair loop works.
