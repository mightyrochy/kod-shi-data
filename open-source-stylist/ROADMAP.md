# Roadmap

The roadmap is intentionally narrow. Do not pull later milestones forward until
the active milestone is done.

## M0 - Project Control System

Status: done

Goal:

Create durable project-control files so future Codex sessions can resume without
drift.

Done when:

- `AGENTS.md`, `PROJECT_STATE.md`, `WORKFLOW.md`, `ROADMAP.md`, `DECISIONS.md`,
  `NOT_NOW.md`, and `SESSION_LOG.md` exist.
- The files agree on the active milestone.
- The next task is concrete.

## M1 - One Controlled Manual Outfit Run

Status: active

Goal:

Run one person image and one manual outfit package through the simplest
repeatable Qwen 2511 path.

Inputs:

- person image;
- manual `outfit_package.json`;
- garment reference images or a reference board;
- style request text.

Outputs:

- run folder;
- Qwen prompt/package;
- generated image or recorded blocker;
- evaluation JSON or recorded blocker;
- human-readable verdict.

Avoid:

- wardrobe catalog;
- automatic stylist selection;
- polished app UI;
- database setup;
- broad model comparisons.

## M2 - Evaluator First Pass

Status: planned

Goal:

Use LM Studio VLM to evaluate one generated image against the source person,
outfit package, and references.

Required checks:

- identity preserved;
- old clothing removed;
- required items present;
- layering followed;
- color/material/detail preserved;
- repair target suggested.

## M3 - Targeted Postproduction Repair

Status: planned

Goal:

Repair one specific failed detail or region after a Qwen output.

Candidate first repairs:

- mask-based color correction;
- local inpainting for old clothing remnants;
- detail restoration for buttons, hems, collar, cuffs, print, or texture.

Avoid:

- full-image regeneration;
- automatic style changes;
- face-changing cleanup.

## M4 - Outfit Adapter v1

Status: planned

Goal:

Turn a structured outfit package into Qwen-ready prompt text and visual evidence
without inventing fashion details.

Can reuse ideas from old `outfit_transfer_adapter`, but only after inspecting
the relevant code.

## M5 - Curated Stylist

Status: planned

Goal:

Select outfits from a small curated library of real outfit packages.

This is not a shopping/catalog system yet.

## M6 - Simple Local UI

Status: planned

Goal:

Create a basic local interface for selecting a person image, outfit package, and
running the pipeline.

Use a simple UI only after the command/run-folder flow works.

## M7 - Wardrobe / Catalog Layer

Status: parked

Goal:

Add Wardrowbe-like functionality:

- user wardrobe;
- item tagging;
- outfit recommendation;
- weather/occasion/style filters;
- retrieval over real garments.

Do not start before M1-M4 are useful.
