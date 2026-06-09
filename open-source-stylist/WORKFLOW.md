# Working Protocol

This file defines how Codex should work on the project.

## Core Rule

Every work block must have one small target.

Good target:

```text
Create a run folder contract and prepare runs/000001.
```

Bad target:

```text
Build the whole stylist pipeline.
```

## Session Start Checklist

For a new Codex chat or a resumed long chat:

1. Read `AGENTS.md`.
2. Read `PROJECT_STATE.md`.
3. Read `PROJECT_LEDGER.md`.
4. Read this file.
5. Confirm the active milestone from `ROADMAP.md`.
6. State the one target for the work block.

If the user asks a broad question, answer it, but do not start broad
implementation without narrowing the next action.

## Session End Checklist

Before finishing after any meaningful work:

1. Update `PROJECT_STATE.md` if the current state changed.
2. Update `PROJECT_LEDGER.md` if the durable project path changed.
3. Add one entry to `SESSION_LOG.md`.
4. Update `DECISIONS.md` if an architectural choice was made.
5. Record blockers as concrete missing inputs or failed checks.
6. Name the next smallest task.

## Project Memory Files

Use these files for different jobs:

- `PROJECT_LEDGER.md`: durable path of the project. Append or update carefully
  when the real project story changes.
- `PROJECT_STATE.md`: current snapshot only. Keep it short enough to read at the
  start of every session.
- `SESSION_LOG.md`: chronological work-block notes. It is useful history, but
  it is not the only source of the project path.
- `DECISIONS.md`: architectural decisions that should not be re-litigated.

Research docs in `docs/` are supporting notes unless a conclusion is promoted
into `PROJECT_LEDGER.md` or `DECISIONS.md`.

## Task Contract

Each task should have:

- purpose;
- inputs;
- output files;
- verification;
- verdict.

If any of these are unclear, choose the smallest reasonable assumption and
record it. Ask the user only when the missing answer blocks progress.

## Run Folder Contract

Every generated experiment should live under:

```text
runs/<run_id>/
  input/
  references/
  outfit/
  qwen/
  output/
  evaluation/
  repair/
  notes.md
```

Minimum useful run files:

```text
runs/<run_id>/input/person.*
runs/<run_id>/input/request.txt
runs/<run_id>/outfit/outfit_package.json
runs/<run_id>/qwen/prompt.txt
runs/<run_id>/qwen/settings.json
runs/<run_id>/output/generated.*
runs/<run_id>/evaluation/evaluation.json
runs/<run_id>/notes.md
```

If generation or evaluation fails, still save:

```text
runs/<run_id>/notes.md
runs/<run_id>/qwen/blocker.json
```

## Definition Of Done

A task is done only when:

- the requested file/code/artifact exists;
- it was checked in the simplest appropriate way;
- the result or blocker is recorded;
- the next step is smaller than a milestone.

## Anti-Drift Rules

Stop expanding and return to the active milestone if:

- a task needs more than one new external tool;
- a task proposes database + UI + model changes together;
- the work is mainly a discussion without an artifact;
- a failure is not tied to a saved run folder;
- the next step cannot be described in one sentence.

## When To Use Old Project Files

Use old files only for a named purpose:

- inspect a schema;
- copy a proven prompt idea;
- compare a run output;
- recover a ComfyUI API approach;
- reuse a reference board concept.

Do not import old project structure wholesale.

## When To Use Extra Agents

Use sub-agents only when the user explicitly asks for agent delegation or
parallel agent work.

Good delegated tasks later:

- inspect old adapter code and summarize reusable parts;
- research one specific postproduction model;
- review a schema for contradictions.

Do not delegate the immediate blocking task.
