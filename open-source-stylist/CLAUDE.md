# Project: AI Stylist Pipeline

## What this is
Automated outfit transfer pipeline:
`person photo + style request → same person in new outfit`

Stack: Python, ComfyUI, LM Studio, Qwen-Image-Edit-2511, FLUX Fill, local RTX 4090.

## Working style

**Communication:**
- Concise, direct, engineering-first
- No flattery. Never start a response with "ти правий", "чудово", or any variant
- No filler lists of "what we won't do" or "what's not important"
- State intent clearly before acting
- If uncertain — say so explicitly. Never present guesses as facts
- If something is unknown about the local environment (UI, file paths, tool availability) — ask, don't assume

**On results:**
- Report failures plainly: what failed, why, what the fix is
- No "partial pass" verdicts. A result either meets the criteria or it doesn't
- Quality verdict requires explicit user validation — never self-declare success on visual output
- After each task: short factual summary — what was done, what the result was, what's next

**Before acting:**
- For any task that modifies files or runs generation: state the plan first, wait for confirmation
- Exception: read-only operations (reading files, checking status) can proceed without confirmation

## Project structure
```
/project-root
  /runs/          — individual test runs (NNNNNN format)
  /prompts/       — role prompts (stylist, person_analysis, outfit_adapter, evaluator)
  /schemas/       — JSON schemas for pipeline data
  LEDGER.md       — decisions and test history
  DECISIONS.md    — architectural decisions
  WORKFLOW.md     — current workflow state
```

## Previous work
The files in this project are from a previous development attempt.
- Read them to understand context, decisions already made, and what was tested
- Do not treat them as the correct solution or follow their approach by default
- Approach architecture fresh, based on goals — not on what was previously attempted

## V1 goal
A closed pipeline that runs end-to-end, even if fragile:
`input photo + style request → ComfyUI generation → evaluation → repair if needed → output`

Priority: close the loop first. Polish comes later.

## Key technical context
- Qwen-Image-Edit-2511 is the confirmed try-on engine (tested, best results)
- FLUX Fill confirmed for masked inpainting (locality: 0.048% outside mask)
- LM Studio runs local VLM for person analysis and evaluation
- ComfyUI is the execution environment
- All processing is local — no external API calls for generation

## Evaluation criteria for any generated output
1. Identity preserved (same person)
2. All intended outfit items present
3. Outfit logic followed (layering, visibility)
4. No simplification of details (buttons, buckles, textures)

A result passes only when all four criteria are met or explicitly accepted by the user.
