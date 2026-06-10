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
Pipeline exists as documentation, schemas, and prompts only.
The only executable code is `tools/postproduction_color_repair.py` — a standalone color correction tool, not connected to the pipeline.

Everything else must be built.

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
  /runs/          — individual test runs (NNNNNN format)
  /prompts/       — role prompts (stylist, person_analysis, outfit_adapter, evaluator)
  /schemas/       — JSON schemas for pipeline data
  /tools/         — standalone utility scripts
  LEDGER.md       — run history and test observations
  DECISIONS.md    — architectural decisions and rationale
  WORKFLOW.md     — current pipeline state
  FINDINGS.md     — empirical findings from testing (ground truth)
  SYSTEM_DESIGN.md — full system design across V1/V2/V3, stage interfaces, open questions
  PLAN.md          — active build & verification roadmap (phases A–F), living document
  CLAUDE.md       — this file
```

---

## Technical context

**Confirmed:**
- Qwen-Image-Edit-2511 with Lightning LoRA is the current default try-on engine — best results so far at 4 steps, but only tested against old models (IDM-VTON, CatVTON). Newer VTON models not yet benchmarked. Status: current default, pending bench-off.
- 40 steps produces worse results than 4 steps with Lightning LoRA — do not increase steps without disabling LoRA
- Prompt influence is weak — model relies primarily on reference images, not text instructions
- FLUX Fill confirmed for masked inpainting (mask locality: 0.048% outside mask)
- LM Studio runs local VLM for person analysis and evaluation (localhost:1234)
- ComfyUI is the execution environment (localhost:8000)

**Known problems:**
- Consistency: same input produces slightly different results each run (expected diffusion behavior)
- Consistency breaks further on dual-view images (front+side) — model does not maintain outfit coherence between views
- Color and texture accuracy: model approximates, does not reproduce exactly — this is why postproduction exists
- Body proportions: model sometimes alters waist/hip proportions when adding clothing

**Evaluation criteria for any generated output:**
1. Identity preserved (same person, same face, same hair)
2. All intended outfit items present
3. Outfit logic followed (layering, visibility, what's over what)
4. Color and texture match reference images

A result passes only when all four criteria are met or explicitly accepted by the user.

---

## Previous work
Files in this project are from a previous development attempt.
- Read them to understand context, past decisions, and what was tested
- LEDGER.md and FINDINGS.md are the ground truth for what was observed empirically
- Do not treat previous code or architecture as the correct approach
- Approach each problem fresh based on goals, not on what was previously attempted
