# Project: AI Stylist Pipeline

## What this is
Automated outfit transfer pipeline:
`person photo + style request → same person in new outfit`

The goal is a system that analyzes a person's photo, selects a specific outfit, and generates a photo of that same person wearing the new outfit — preserving identity, body shape, and outfit details accurately.

**Development roadmap:**
- V1: closed pipeline, single frontal photo, manual outfit input, automated generation and evaluation
- V2: agent retrieves real garments from store catalogs
- V3: personal wardrobe integration

Stack: Python, ComfyUI, LM Studio, Qwen-Image-Edit-2511, FLUX Fill, local RTX 4090.
All processing is local. No external API calls for generation.

---

## Current state
**Component testing, 2026-06-14.** The first implementation attempt is archived
(read-only) in `archive/`. Active code contains ComfyUI clients, frozen-board
selection, prompt construction, segmentation, three measurement instruments,
workflow templates, and experiment runners.

E-007 v2's original A/B is closed with a mixed owner verdict and no winning board.
The measured `hybrid_mask_crop` supplement is the next input candidate: it restores
buttons and footwear consistently, while blouse color and silhouette remain open.
Generation code must reuse the selected frozen PNG and verify its SHA-256; it must
not rebuild boards.

Decisions rest on the effective status recorded in `knowledge/verified.md`, including
dated reversals and caveats, plus direct owner review where the instruments do not
measure the relevant quality.

---

## SOP — how we work

### Communication
- Concise, direct, engineering-first
- No flattery. Never open with "ти правий", "чудово", "excellent", or any variant
- No filler: no lists of what we won't do, what's not important, or what's out of scope
- State intent clearly before acting
- If uncertain — say so explicitly. Never present guesses as facts
- If something about the local environment is unknown (paths, ports, tool availability) — ask, do not assume

### Before acting
- For any task that modifies files, deletes files, or runs generation: state the plan first, wait for confirmation
- Read-only operations (reading files, checking status, scanning) proceed without confirmation
- Never delete or overwrite files without explicit permission

### Division of labor (owner ↔ agent) — both failure modes are violations
The owner's job is **judgment**: visual quality verdicts, accepting or rejecting
results at checkpoints, priorities, architecture decisions. The agent's job is
**all mechanical and technical work** — these two never trade places.

- The agent runs scripts, edits files, installs packages, debugs errors, retries
  failures, restarts services — **itself**. Never hand the owner a command to run,
  lines to paste, or an "if error X, do Y" branch. Execute, observe, handle the
  error, report the outcome. (Failure mode 1: "making the owner the terminal".)
- Sole exception — actions the agent physically cannot perform (GUI-only steps,
  logins, downloads behind authentication). Then: one precise step with the exact
  path/URL, then wait. Surface the blocker immediately; never silently substitute
  an alternative.
- Checkpoints come from BUILD_PLAN and experiment protocols: named visual
  artifacts the owner reviews, named decisions the owner signs. Between
  checkpoints the agent works autonomously; AT a checkpoint it stops and waits.
  Presenting one artifact does not authorize skipping the next checkpoint.
  (Failure mode 2: "owner corrected me once, so now full autopilot".)
- A correction about one failure mode never flips to the other: "do mechanical
  work yourself" does not mean "skip checkpoints"; "stop at checkpoints" does not
  mean "ask the owner to run commands".

### Task sizing
- Before starting any non-trivial task, the assistant (Claude Code / Claude AI) must soberly assess its scope and complexity
- Based on that assessment, recommend the execution mode: which model (Opus / Sonnet / Haiku / Fable), what effort level, and whether the task belongs in Claude Code or Claude AI chat
- If a task is too large for one session or one model tier — say so and propose how to split it
- Do not inflate small tasks into big ones, and do not start big tasks casually as if they were small

**Effort level reference** (UI scale: low → medium → high → extra → max → ultracode; "extra" is the API level `xhigh`). Effort controls the model's reasoning and token budget — it affects thinking depth, number of tool calls, and thoroughness of verification, not just response length:
- `low` — short, scoped, mechanical tasks where speed matters and intelligence doesn't: running known scripts, status checks, commits, renames, formatting
- `medium` — routine engineering inside established patterns: small fixes, adding code by analogy with existing code, doc updates. Good cost/quality balance for ordinary work
- `high` — the default and the workhorse. New modules, integrations, non-trivial debugging, most pipeline-building work in this project
- `extra` (`xhigh`) — deep research, architecture design, long agentic sessions, debugging across multiple systems, bench-off analysis. Noticeably higher token spend
- `max` — frontier-difficulty problems only. No token constraints; documented diminishing returns and overthinking risk on normal tasks. Session-only setting
- `ultracode` — not a model effort level: a Claude Code mode that pins `extra` and additionally lets Claude orchestrate multi-agent workflows autonomously. For very large multi-part builds; the most expensive option; session-only
- The effort scale is calibrated per model — the same level name means different depth on different models. Combine with model choice: Haiku/Sonnet + low–medium for routine, Sonnet + high as default, Opus/Fable + extra for design and research

### Reporting results
- After each task: short factual summary — what was done, what the result was, what's next
- Report failures plainly: what failed, why, what the fix is
- No "partial pass" verdicts. A result either meets the criteria or it doesn't
- Quality verdict on visual output requires explicit user validation — never self-declare success

### Git discipline
- Propose a commit after every completed step (written script, passing test, updated prompt, changed document)
- Never wait until "everything is ready" to commit
- Use short descriptive commit messages that say what changed and why

### Documentation discipline
- Never overwrite existing records in .md files — only append
- Date-stamp all new entries
- Never delete existing content without explicit permission
- If documentation contradicts the actual code, flag the discrepancy — do not silently update to match either

---

## Project structure
```
/project-root
  /design/         — SYSTEM_DESIGN.md (canonical) + revisions/
  /system/         — code, one module per architecture stage; contracts/ = JSON schemas
  /knowledge/      — verified.md (decision-grade facts) + hypotheses.md
  /experiments/    — NNN_name/ (protocol.md BEFORE running, results/, conclusion.md)
  /assets/         — test inputs: person photos, garment references per outfit
  /archive/        — previous attempt, read-only; nothing returns from it
  METHODOLOGY.md   — knowledge classification, experiment discipline, change acceptance
  BUILD_PLAN.md    — assembly plan: stages 0–7, contracts, acceptance criteria
  PROJECT_LEDGER.md — history of the previous attempt
  CLAUDE.md        — this file
```

---

## Technical context

**Environment (cheap to re-verify; Stage 0 `env_check` promotes these to Verified):**
- ComfyUI is the generation server — port :8000 on this machine (docs elsewhere say :8188; trust env_check)
- LM Studio serves the VLM/LLM (localhost:1234): OpenAI-compatible inference + native REST v1 with explicit model unload
- Default try-on engine: Qwen-Image-Edit-2511 fp8mixed (16GB VRAM constraint); engine decision finalized by bench-off (BUILD_PLAN Stage 6)

**Knowledge discipline (METHODOLOGY.md §1):**
- `knowledge/verified.md` — decision-grade facts. Decisions rest ONLY on these.
- `knowledge/hypotheses.md` — everything else, including ALL findings of the previous attempt (H-COLOR, H-REF-CONTAMINATION, H-LIGHTNING, H-VLM-LOWRES, …). Each names the experiment that verifies it.
- VLM output and AI-assistant visual comparison are never decision-grade — they produce observations only. Deterministic gates and the owner's eyes produce verdicts.

**Evaluation criteria for any generated output:**
1. Identity preserved (same person, same face, same hair, same body proportions)
2. All intended outfit items present
3. Outfit logic followed (layering, visibility, what's over what)
4. Color and texture match reference images

A result passes only when all four criteria are met or explicitly accepted by the user.

---

## Previous work
The previous development attempt lives in `archive/`, read-only.
- Read it to understand context and what was tried; PROJECT_LEDGER.md is its history
- Nothing returns from archive into the live tree: ideas may be re-derived, artifacts are rebuilt under current rules
- None of its empirical findings is decision-grade (see knowledge/hypotheses.md)
- Approach each problem fresh based on goals, not on what was previously attempted
