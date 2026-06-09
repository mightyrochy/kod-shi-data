# Current Architecture

This document is the active architecture snapshot. The old starter architecture
with catalog retrieval, database storage, and broader MVP stack is archived in:

```text
docs/archive/architecture_starter_2026-06-08.md
```

## Active Pipeline

```text
person photo + manual outfit package
-> Qwen-Image-Edit-2511 through ComfyUI
-> evaluation through LM Studio / manual checklist
-> targeted postproduction repair
-> verifier
-> saved run folder
```

## Roles

### Manual Outfit Package

Defines the outfit as structured evidence:

- garment references;
- required visual details;
- layering and visibility rules;
- forbidden changes.

It is the current substitute for a future stylist/catalog layer.

### Qwen Base Engine

Qwen-Image-Edit-2511 fp8mixed through ComfyUI is the primary try-on/base edit
engine for this phase.

It should produce one usable base image by default. Research runs may generate
multiple candidates, but the product path should not depend on that.

### Evaluator / Verifier

The evaluator checks whether the base image is usable:

- identity;
- body shape and anatomy;
- garment fit;
- outfit structure and layering;
- required items;
- background/camera preservation;
- repairable local failures.

The verifier checks whether a repair improved the target without damaging
protected areas.

### Postproduction

Postproduction is local repair after a usable Qwen base image.

Core executor class:

```text
masked local generative edit
```

Support tools:

- mask building through manual masks, SAM, GroundingDINO, or future parsing;
- deterministic cleanup for carefully bounded color/tone/blend adjustments;
- run-folder logging for reproducibility.

## Current Open Architecture Question

First postproduction capability to prove:

```text
strict masked locality/preservation
```

or:

```text
Qwen semantic/reference repair with a locality mechanism
```

This choice should be based on quality, function, and compatibility with the
whole system, not on whether a workflow already exists locally.

## Parked Layers

These are future layers, not active architecture:

- wardrobe/catalog retrieval;
- database/object storage;
- polished UI;
- cloud deployment;
- broad model leaderboard;
- automatic stylist selection.
