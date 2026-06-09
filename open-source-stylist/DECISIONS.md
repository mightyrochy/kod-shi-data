# Decisions

This file records architectural decisions so they do not need to be re-litigated
in every chat.

## DEC-001 - Qwen 2511 Is The Primary Try-On/Edit Engine

Date: 2026-06-08

Decision:

Use Qwen-Image-Edit-2511 as the main image-edit layer for the first working
pipeline.

Reason:

The user has already tested IDM-VTON, CatVTON, and FASHN VTON v1.5 and found
Qwen-Image-Edit-2511 better for the desired multi-item outfit transfer behavior.
The local machine already has Qwen 2511 models installed.

Implication:

Do not spend early milestones benchmarking many VTON systems. Compare later only
when there is a stable run/evaluation harness.

## DEC-002 - Postproduction Is Surgical Repair

Date: 2026-06-08

Status:

```text
active principle, tool priority refined by DEC-011
```

Decision:

Postproduction should fix specific failures from the evaluator rather than
redesign or regenerate the whole image.

Examples:

- color mismatch inside a garment mask;
- lost texture or print;
- missing cuff/button/hem detail;
- old clothing remnants;
- wrong layering in a local region.

Original implication:

The repair layer needs masks, local edits, and deterministic color tools before
it needs more creative models.

Update:

After the failed shoe color repair test and later tool research, deterministic
color/tone cleanup is treated as a support executor only. The current core
postproduction executor class is masked local generative edit, recorded in
DEC-011.

## DEC-003 - Old Pipelines Are Archives

Date: 2026-06-08

Decision:

Old COTS pipelines are not the foundation of the new project.

Reason:

They contain useful ideas, but previous attempts became too complex before the
core generation/evaluation/repair loop was reliable.

Implication:

Extract useful pieces only after inspection. Prefer a clean small implementation
in this repository.

## DEC-004 - Project Memory Lives In Files

Date: 2026-06-08

Decision:

Project continuity must live in repo files, not in a long Codex chat.

Implication:

Every substantial work block updates `PROJECT_STATE.md` and `SESSION_LOG.md`.
New Codex chats should resume by reading the control files.

## DEC-005 - Delay Wardrobe/Catalog Features

Date: 2026-06-08

Decision:

Wardrowbe-like functionality is valuable but delayed until the core manual loop
works.

Reason:

Catalogs and wardrobe logic add product value, but they do not solve the current
hardest problem: identity-preserving outfit transfer with reliable detail
repair.

Implication:

Do not install or integrate wardrobe systems during M1-M4 unless explicitly
re-scoped.

## DEC-006 - Base Generation Prioritizes Hard-To-Repair Features

Date: 2026-06-08

Decision:

When evaluating Qwen base generations, prioritize features that are hard to fix
in postproduction:

1. person identity;
2. body shape and proportions;
3. body anatomy and physically plausible garment fit;
4. outfit structure and layering logic;
5. garment shapes and silhouettes;
6. footwear/accessory placement;
7. pose/camera preservation when the input requires it;
8. colors and fine surface details.

Reason:

Colors and some texture/detail errors can plausibly be repaired later with
mask-based postproduction. Identity drift, broken body shape, bad anatomy,
incorrect garment structure, and failed layering are much harder to repair
after generation.

Pose note:

Exact pose preservation is not always critical. Real user photos will not be
clean front/side studio images, and the system should handle imperfect natural
poses. What matters is not copying the exact pose at all costs, but preserving a
plausible body, believable garment fit, and the user's identity.

Implication:

Do not reject a base candidate mainly because of color drift if identity,
body/anatomy, structure, silhouette, and logic are strong. Prefer a stable base
image with repairable color/detail issues over a visually exact but unstable
image. Reject candidates where body shape, anatomy, garment fit, or layering are
broken, even if colors look good.

## DEC-007 - Do Not Overfit The Pipeline To One Test Outfit

Date: 2026-06-08

Decision:

Do not tune the system only to make `runs/000001` pass perfectly.

Reason:

The current outfit is a diagnostic case, not the product. A repair that only
solves one belt, one blouse, or one skirt can make the demo look better while
making the actual system less general.

Implication:

Postproduction work must be designed as a general failure taxonomy and repair
policy. A local belt repair can be used as one example, but it should not become
the next architectural goal by itself. Prefer reusable categories such as:

- layer visibility error;
- garment shape error;
- color/tone mismatch;
- texture/detail loss;
- accessory scale/placement error;
- old clothing remnant;
- body/identity damage;
- background damage.

## DEC-008 - Default To Single Base Generation

Date: 2026-06-08

Decision:

Do not design the product around generating 3-5 Qwen candidates by default.

Reason:

Each Qwen Image Edit pass takes meaningful time and GPU resources. Multi-candidate
generation is useful for research and benchmarking, but it is wasteful as the
default product path.

Implication:

The default runtime path should be:

```text
one base Qwen generation
-> evaluator
-> local postproduction if repairable
-> regenerate only when the base fails hard-to-repair checks
```

Use multiple candidates only when:

- running research/benchmark tests;
- the user explicitly requests alternatives;
- the first result is borderline and cheaper local repair is unlikely to work;
- the system is tuning prompts or workflows offline.

## DEC-009 - Define Postproduction Before Repairability Rules

Date: 2026-06-08

Decision:

Do not finalize repairable/reject categories until the shape of the postproduction
system is defined.

Reason:

Whether an error is repairable depends on available postproduction tools:

- masks;
- deterministic color correction;
- local inpainting;
- reference-guided detail repair;
- optional upscaling/detail restoration;
- evaluator feedback.

Implication:

The next architecture task is to define the postproduction system itself:

- inputs;
- outputs;
- repair modules;
- decision flow;
- cost/time budget;
- failure limits.

Only after that should repairability rules become strict.

## DEC-010 - Prove Repair Executors Before General Repair Planning

Date: 2026-06-08

Status:

```text
active principle, first-executor list superseded by DEC-011
```

Decision:

Do not build a broad automatic repair planner before proving which
postproduction executors actually work.

Reason:

A repair plan is only useful if a known tool can execute it. A general JSON plan
without a reliable executor becomes another abstract layer and can cause the
project to drift.

Original implication:

The next postproduction milestone was framed as a small executor bake-off:

- deterministic color repair on garment masks;
- local inpaint on a non-face region;
- reference-guided detail repair on a small accessory/detail.

Each executor must have:

- a concrete input;
- a concrete output;
- runtime cost;
- failure modes;
- a clear rule for when not to use it.

Only after at least one executor works should the repair-plan schema become the
thing that routes work automatically.

Update:

The deterministic shoe color repair test failed as both process and visual
repair. It proved that deterministic color cleanup is support only, not the
first meaningful proof of postproduction quality.

Current executor direction is recorded in DEC-011:

```text
masked local generative edit
```

## DEC-011 - Masked Local Generative Edit Is The Core Postproduction Executor

Date: 2026-06-09

Decision:

The core postproduction executor should be masked local generative edit through
ComfyUI, using tools such as Qwen Image Edit masked/local workflows or FLUX
Fill/inpaint workflows.

Reason:

The main postproduction need is not cosmetic filtering. It is local semantic
repair: fixing a bounded clothing/accessory/detail region while preserving
identity, body, garment structure, and background.

Implication:

Postproduction tool roles are:

- LM Studio VLM for evaluator/verifier;
- rule-based planner for first repair routing;
- manual/SAM/GroundingDINO/fashion parsing paths for mask building;
- ComfyUI masked local generative edit for main repair;
- deterministic color/tone/blend cleanup only as a support executor;
- run-folder logging for reproducibility.

Deterministic cleanup is not proof of postproduction quality by itself. The next
executor proof should test masked local generative edit with a written intent
before any image edit is run.

## DEC-012 - Project Ledger Preserves The Durable Path

Date: 2026-06-09

Decision:

Add `PROJECT_LEDGER.md` as the canonical durable project path.

Reason:

`PROJECT_STATE.md` became too large and mixed current state, research notes,
failed tests, and next steps. `SESSION_LOG.md` records work blocks, but it is
not enough by itself to keep the whole project journey visible across chats.

Implication:

- `PROJECT_LEDGER.md` records what was decided, what was tested, what worked,
  what failed, where the project is now, and what remains open.
- `PROJECT_STATE.md` should become a current snapshot.
- `SESSION_LOG.md` remains a chronological work log.
- Research docs are supporting notes unless promoted into `PROJECT_LEDGER.md`
  or `DECISIONS.md`.
- New sessions should read `PROJECT_LEDGER.md` after `PROJECT_STATE.md`.
