# Codex Operating Rules

This repository is the source of truth for the Open Source Stylist project.
The main job of Codex here is to keep the project moving in small, verified
steps without drifting into endless planning or side quests.

## Start Protocol

At the start of every new Codex chat or major work block:

1. Read `PROJECT_STATE.md`.
2. Read `PROJECT_LEDGER.md`.
3. Read `WORKFLOW.md`.
4. Check `ROADMAP.md` for the current milestone.
5. Check `NOT_NOW.md` before adding scope.
6. If the task changes architecture, read `DECISIONS.md`.

Do not rely on chat memory as the project source of truth.

## End Protocol

Before ending a work block that changed project state:

1. Update `PROJECT_STATE.md`.
2. Update `PROJECT_LEDGER.md` if the durable project path changed.
3. Add a short entry to `SESSION_LOG.md`.
4. Add or update a decision in `DECISIONS.md` if a real architectural choice was made.
5. Keep the next task concrete and small.

## Scope Discipline

Default to the smallest useful next step.

The active project strategy is:

```text
manual outfit package
-> Qwen 2511 edit through ComfyUI
-> evaluator through LM Studio
-> targeted repair
-> repeatable run folder
```

Do not jump to wardrobe catalogs, shopping integrations, Docker, Postgres,
MinIO, polished UI, or multi-model benchmarking unless the active milestone
explicitly calls for it.

## Old Project Material

Older folders are archives, not foundations.

Useful older paths:

- `C:\Users\Admin\OneDrive\Документы\ComfyUI\COTS\outfit_pipeline`
- `C:\Users\Admin\OneDrive\Документы\ComfyUI\COTS\outfit_transfer_adapter`
- `C:\Users\Admin\OneDrive\Документы\ComfyUI\COTS\qwen_tests`
- `C:\Users\Admin\OneDrive\Рабочий стол\проект\CONTROLLED_AI_STYLING_SYSTEM`

Use them only to extract tested ideas, schemas, prompts, or scripts after
inspection. Do not continue them blindly.

## Drift Alarms

Pause and re-center on `PROJECT_STATE.md` if any of these happen:

- The task expands to more than one milestone.
- The discussion becomes mostly architecture without a runnable artifact.
- A small helper script becomes a framework.
- More than one new tool is proposed at once.
- The work focuses on UI, database, catalog, or deployment before the core loop works.
- The model/evaluator/postproduction conversation lacks a specific test image or run folder.

## Verification

Every implementation task needs a verification step, scaled to risk:

- schema files: parse or validate them;
- prompts: run a sample or create a sample expected JSON;
- ComfyUI integration: query the local API or run a dry-run package;
- image generation: save input, prompt, output, settings, and notes;
- evaluator changes: compare against a known output and write a verdict.

## Communication

Explain progress in non-technical language first. Technical details are welcome
when useful, but the user is not expected to be a programmer.
