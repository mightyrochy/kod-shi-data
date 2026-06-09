# Session Log

## 2026-06-09 - Strict Masked Locality Proof Run

Work:

- Created a ComfyUI RGBA input with the edit mask in the alpha channel.
- Built `comfyui_api_prompt.json` from the FLUX Fill workflow nodes.
- Ran the job through ComfyUI API.
- Saved output artifacts under
  `runs/000001/repair/masked_local_edit_proof_v1/outputs/`.
- Created before/after, target crop before/after, amplified diff, leakage
  stats, verifier result, and verdict.

Verification:

- ComfyUI accepted the prompt with no node errors.
- Run completed successfully.
- Outside-mask pixel change was very low:
  `outside_changed_ratio = 0.00048431261146094723`.
- Visual review: identity/body/background/side view/footwear/earrings preserved.

Verdict:

- Partial pass.
- Pass for strict locality / preservation.
- Fail as meaningful semantic outfit repair because belt dominance remained and
  the workflow had weak reference/detail control.

Next:

- Test Qwen semantic/reference local repair with a locality mechanism, or rerun
  FLUX Fill only with a more precise mask if stricter locality confidence is
  needed.

## 2026-06-09 - Masked Local Edit Proof Inputs Prepared

Work:

- Chose `two_view_prompt_v4/output/candidate_01.png` as the base for the first
  strict masked locality proof.
- Copied it to `runs/000001/repair/masked_local_edit_proof_v1/input_base.png`.
- Created `edit_mask.png` and `edit_mask_preview.png` for the front-view waist /
  belt / blouse-hem layer boundary.
- Narrowed the mask after preview so it does not touch hands.
- Created `repair_instruction.txt`, `settings.json`, `run_inputs.md`, and
  `repair_request.json`.
- Set the executor candidate to `comfyui_flux_fill` with the local FLUX Fill
  workflow.

Verification:

- JSON files parse.
- Fallback schema checks passed for the repair request.
- All file references marked `exists` are present.
- Local workflow path exists:
  `C:/Users/Admin/ComfyUI/user/default/workflows/flux_fill_inpaint_cots.json`.
- No image edit was run.

Next:

- Review the mask preview, then run or revise the strict masked locality proof.

## 2026-06-09 - Active Docs Cleaned And Archived

Work:

- Archived old starter/pre-cleanup documents into `docs/archive/`.
- Replaced the active `README.md` and `docs/architecture.md` with current
  project-frame versions.
- Rewrote `docs/postproduction_strategy.md` around the current postproduction
  model: Qwen 2511 as base engine, masked local generative edit as core repair
  executor, deterministic cleanup as support only.
- Updated `prompts/evaluation_and_repair_planner.md`.
- Updated `schemas/evaluation_and_repair_plan.schema.json` to version 1.1 so
  it no longer routes to old `run_color_repair` / `run_local_inpaint` actions.
- Consolidated `PROJECT_LEDGER.md` into one non-duplicated durable path.
- Marked DEC-010's original executor list as superseded by DEC-011.

Verdict:

- Active docs no longer present the old broad starter MVP as the current
  architecture.
- Superseded material was archived, not deleted.
- Current next postproduction choice remains: strict masked locality proof or
  Qwen semantic/reference repair with a locality mechanism.

Next:

- Choose the first postproduction capability proof from the current ledger and
  repair contract.

## 2026-06-09 - Original Chat Memory Recovery Added

Work:

- User pointed out that earlier `.md` memory did not reliably preserve the full
  project context because large file sections were rewritten.
- Read `PROJECT_LEDGER.md`, `SESSION_LOG.md`, `ROADMAP.md`, `NOT_NOW.md`, and
  extracted the source architecture from `Велика Ціль.docx`.
- Added `Memory Recovery - Original Chat Start To Handoff` to
  `PROJECT_LEDGER.md`.
- Restored the first user intent, big-goal architecture, early open-source tool
  framing, Qwen-vs-VTON reasoning, Wardrobe parking, user-experience constraint,
  anti-drift strategy, system audit summary, run 000001 path, prompt experiment
  conclusions, and original handoff state.
- Fixed encoding damage in the new ledger recovery block.

Verdict:

- `PROJECT_LEDGER.md` now contains the missing durable context from the original
  chat start through the handoff to another chat.
- The project memory rule is reinforced: ledger is append-oriented durable
  memory; state is only current snapshot.

Next:

- Use `PROJECT_LEDGER.md` as the first durable reference before any resumed
  postproduction work.

## 2026-06-09 - Project Memory Ledger Added

Work:

- Created `PROJECT_LEDGER.md` as the durable project path.
- Recorded the canonical frame: Qwen-Image-Edit-2511 fp8mixed is the primary
  Try-On/Base Edit Engine for the current phase.
- Reconstructed the path through M0, run 000001, front-only Qwen run,
  two-view prompt v2/v3/v4, postproduction planning, failed color repair,
  masked local edit proof setup, ComfyUI migration, and tool research.
- Updated `WORKFLOW.md` and `AGENTS.md` so new sessions read
  `PROJECT_LEDGER.md`.
- Added `DEC-012 - Project Ledger Preserves The Durable Path`.
- Rewrote `PROJECT_STATE.md` as a short current snapshot.

Verdict:

- `PROJECT_LEDGER.md` is now the canonical durable memory of the project path.
- `PROJECT_STATE.md` is current state only.
- `SESSION_LOG.md` remains work-block history.
- Research docs are supporting notes unless promoted into `PROJECT_LEDGER.md` or
  `DECISIONS.md`.

Next:

- Review `PROJECT_LEDGER.md`, then resume postproduction from the open question:
  strict locality/preservation proof or Qwen semantic/reference repair with a
  locality mechanism.

## 2026-06-09 - Local Workflow Capability Matrix Added

Work:

- Inspected local ComfyUI workflow candidates without running generation.
- Parsed existing and blueprint workflow JSON files:
  `flux_fill_inpaint_cots.json`, `Image Edit (Qwen 2511).json`,
  `Image Inpainting (Qwen-image).json`, and
  `Image Inpainting (Flux.1 Fill Dev).json`.
- Checked key local model availability.
- Checked specific ComfyUI node availability for FLUX/Qwen inpaint/edit nodes.
- Created
  `docs/postproduction_local_workflow_capability_matrix_2026-06-09.md`.

Verdict:

- Qwen 2511 Image Edit is the strongest semantic/reference outfit repair
  candidate, but the inspected blueprint does not expose direct mask control.
- FLUX.1 Fill is the strongest strict masked locality/preservation candidate,
  but weaker for reference-faithful outfit detail.
- Qwen-image inpainting is blocked by missing
  `Qwen-Image-InstantX-ControlNet-Inpainting.safetensors`.
- SDXL inpaint was not detected locally.
- Local availability is an integration fact, not the main selection criterion.

Next:

- Choose which capability to test first: strict locality/preservation, or
  semantic/reference outfit repair with a locality mechanism.

## 2026-06-09 - Postproduction Tool Research Added

Work:

- Researched current local/open and cloud/API tools relevant to postproduction:
  Qwen Image Edit, FLUX Fill, SDXL inpaint, BrushNet, PowerPaint, HD-Painter,
  Paint-by-Example, AnyDoor, reference-guided inpainting research, SAM,
  GroundingDINO, fashion parsing, LM Studio VLMs, FLUX Kontext, Gemini image
  editing, OpenAI image edits, and Adobe Firefly Fill.
- Created `docs/postproduction_tool_research_2026-06-09.md`.
- Ranked tools against the project needs: locality, preservation, clothing
  usefulness, reference use, ComfyUI/LM Studio integration, runtime,
  reproducibility, and local/open deployment.

Verdict:

- Qwen 2511 and FLUX.1 Fill dev are the local core executor candidates.
- Mask building and verification are first-class subsystems, not side details.
- A workflow should not be selected only because it already exists locally.
- The next work should be a capability matrix before choosing the first proof
  executor.

Next:

- Inspect available local Qwen/FLUX/possibly SDXL masked-edit workflows and
  create a capability matrix without running image generation.

## 2026-06-09 - ComfyUI Update Safety Snapshot

Work:

- Inspected local Comfy-related folders without running an update.
- Identified `C:\Users\Admin\ComfyUI` as the likely active workspace.
- Found existing workflows, including
  `C:\Users\Admin\ComfyUI\user\default\workflows\flux_fill_inpaint_cots.json`.
- Confirmed key model files are present for Qwen 2511, FLUX Fill, Qwen VAE,
  Qwen text encoders, SAM, GroundingDINO, and Lightning LoRA.
- Created `docs/comfyui_update_safety_snapshot_2026-06-09.md`.
- After migration, checked `http://127.0.0.1:8000/system_stats`.
- Confirmed the running backend still uses `C:\Users\Admin\ComfyUI` as
  `--base-directory`, `C:\Users\Admin\ComfyUI\user` as user directory, and
  `C:\Users\Admin\ComfyUI\input/output` as input/output directories.

Verdict:

- The current ComfyUI workspace contains important working state and should not
  be overwritten blindly by Comfy Desktop update/migration.
- The existing FLUX Fill workflow may be useful for the first masked local
  generative edit proof.
- The Desktop instance prompt points to `C:\Users\Admin\ComfyUI-Installs`, but
  the backend still points to the existing working workspace, which is a good
  sign.

Next:

- If proceeding through Comfy Desktop setup, keep Local selected, avoid Express
  Install unless its behavior is clear, and verify the migration target before
  accepting changes.

## 2026-06-09 - Masked Local Edit Proof Intent Prepared

Work:

- Created
  `runs/000001/repair/masked_local_edit_proof_v1/test_intent.md`.
- Created `schemas/postproduction_repair_request.schema.json`.
- Created
  `runs/000001/repair/masked_local_edit_proof_v1/repair_request.draft.json`.
- Defined the first proof as a test of ComfyUI masked local generative edit.
- Framed the target as a general local layer-boundary/detail failure class.
- Listed success criteria, failure conditions, and planned run-folder files.
- Reframed runnable inputs as a real runtime repair request rather than loose
  ad-hoc files.
- Verified the schema and draft JSON parse, and ran a structural check for
  required fields and file statuses.
- Did not run ComfyUI or edit any image.

Verdict:

- The proof intent and draft runtime request are ready.
- The draft request shows the shape of the data that should enter
  postproduction under the hood.

Next:

- Prepare the planned assets in the draft request and move it toward
  `ready_to_run`.

## 2026-06-09 - Postproduction Contract Reframed Around Real Tools

Work:

- Rewrote `docs/postproduction_system_contract.md`.
- Reframed postproduction around concrete tools:
  LM Studio VLM evaluator/verifier, rule-based planner, SAM/GroundingDINO/manual
  mask builder, ComfyUI masked local generative edit, deterministic cleanup, and
  run-folder logging.
- Removed the unclear split between description-only repair and
  reference-guided repair. Both are inputs to the same masked local edit class.
- Defined deterministic color/tone cleanup as a support executor, not the main
  postproduction proof.
- Added a Codex R&D work rule: before taking practical action in this area,
  state what will be done, why, which tool/executor is involved, expected
  improvement, failure condition, and files to be written.
- Corrected the shoe color repair verdict from partial pass to failed R&D
  process and visual repair.

Verdict:

- The core postproduction executor to prove is masked local generative edit
  through ComfyUI.
- Final product behavior should be automatic under the hood; human validation is
  only an R&D safeguard while the system is being designed.

Next:

- State Codex intent for one masked local generative edit proof before running
  any tool or editing any image.

## 2026-06-09 - First Postproduction Executor Tested

Work:

- Created `tools/postproduction_color_repair.py` for deterministic masked color
  repair.
- Ran a shoe color repair test on
  `runs/000001/experiments/two_view_prompt_v4/output/candidate_01.png`.
- Created `runs/000001/repair/color_repair_shoes_v1`, which exposed a mask
  leakage failure: the floor was colored because the feathered polygon mask was
  too broad.
- Added brightness/saturation guards to the color repair executor.
- Created `runs/000001/repair/color_repair_shoes_v2` with repaired image, mask,
  before/after sheet, report JSON, and verdict notes.
- Verified the script compiles and the repair JSON files parse.

Verdict:

- Failed as an R&D process and visual repair.
- The target was not validated before execution and the result made the outfit
  worse.
- The narrow technical lesson remains: deterministic masked color repair is only
  a support cleanup tool for carefully validated color-only cases.

Next:

- Reframe the postproduction contract around the real core executor: masked
  local generative edit.

## 2026-06-08 - Initial Project Control Setup

Work:

- Read the user's project goal from `Велика Ціль.docx`.
- Created the first starter architecture files.
- Audited the local machine, ComfyUI, LM Studio, installed models, and old project folders.
- Created a system audit at `docs/system_audit_2026-06-08.md`.
- Added project-control files to prevent Codex drift across long chats.
- Checked the control files for milestone consistency and missing source-of-truth links.

Verdict:

- The machine is ready for a local Qwen 2511 based workflow.
- `M0 - Project Control System` is complete.
- The next useful step is not more architecture. It is one repeatable manual run.

Next:

- Start `M1 - One Controlled Manual Outfit Run`.

## 2026-06-08 - Prepared Run 000001 From Old Test Assets

Work:

- Copied the user's old test assets into a clean repeatable run folder.
- Created `runs/000001/outfit/outfit_package.json`.
- Created `runs/000001/qwen/prompt.txt`.
- Created `runs/000001/qwen/settings.json`.
- Created `runs/000001/qwen/reference_board.png` as a fuller debug board.
- Created `runs/000001/qwen/reference_board_clean.png` as the main Qwen image 2 board.
- Created `runs/000001/notes.md`.
- Verified JSON files parse.
- Visually inspected the clean reference board.

Verdict:

- `runs/000001` is prepared.
- The clean board is usable for a first test, but still carries some reference-model leakage risk.
- Generation has not been run yet.

Next:

- Wire `runs/000001` to the simplest local ComfyUI Qwen 2511 execution path.

## 2026-06-08 - Five Manual Qwen Candidates Reviewed

Work:

- User generated five candidates in ComfyUI with the same run package.
- Copied latest five ComfyUI outputs into `runs/000001/output/`.
- Created `runs/000001/output/manifest.json`.
- Created `runs/000001/output/contact_sheet_5_candidates.png`.
- Created `runs/000001/evaluation/manual_evaluation_5_candidates.json`.
- Updated `runs/000001/notes.md`.

Verdict:

- Strong baseline / partial pass.
- Qwen consistently removes old sweater, jeans, and socks.
- Qwen consistently creates the ivory blouse, brown skirt, green shoes, and gold earrings.
- Main failures are exact detail fidelity: belt, shoe structure/texture, earring detail, exact skirt slit, and fabric detail.
- Candidate 01 is the best first repair target.

Next:

- Do one focused repair test on candidate 01.
- Choose exactly one repair target first: belt visibility or shoe detail.

## 2026-06-08 - Two-View Prompt V2 Reviewed

Work:

- User changed input to two-view person image as image 1 and clean board as image 2.
- User used a shorter outfit-layout prompt.
- Copied latest five ComfyUI outputs into `runs/000001/experiments/two_view_prompt_v2/output/`.
- Created `runs/000001/experiments/two_view_prompt_v2/output/contact_sheet_5_candidates.png`.
- Created `runs/000001/experiments/two_view_prompt_v2/evaluation/manual_evaluation.json`.
- Created `runs/000001/experiments/two_view_prompt_v2/notes.md`.

Verdict:

- Two-view input is useful and improves side-view/body-shape diagnostics.
- Candidate 01 is the best two-view balance.
- Identity risk is higher than front-only; candidate 03 changes hair color.
- Belt control is inconsistent and often too visible.

Next:

- Run `two_view_prompt_v3` with stricter identity preservation and clearer belt wording.

## 2026-06-08 - Two-View Prompt V3 Reviewed And V4 Prepared

Work:

- User reported v3 results were very consistent but not accurate.
- Copied latest five ComfyUI outputs into `runs/000001/experiments/two_view_prompt_v3/output/`.
- Created `runs/000001/experiments/two_view_prompt_v3/output/contact_sheet_5_candidates.png`.
- Created `runs/000001/experiments/two_view_prompt_v3/evaluation/manual_evaluation.json`.
- Created `runs/000001/qwen/reference_board_neutral_labels.png`.
- Created `runs/000001/experiments/two_view_prompt_v4/input/prompt.txt`.
- Created `runs/000001/experiments/two_view_prompt_v4/notes.md`.

Verdict:

- V3 is consistent but inaccurate.
- Explicit/simple outfit color words may increase consistency while reducing visual-reference fidelity.
- V4 removes simple outfit color words and uses neutral board labels while keeping identity preservation.

Next:

- Run v4 3-5 times and compare fidelity against v3.

## 2026-06-08 - V4 Promoted As Base And Postproduction Plan Created

Work:

- User clarified that colors are lower priority because they are more repairable in postproduction.
- Added `DEC-006 - Base Generation Prioritizes Hard-To-Repair Features`.
- Copied latest five v4 outputs into `runs/000001/experiments/two_view_prompt_v4/output/`.
- Created `runs/000001/experiments/two_view_prompt_v4/output/contact_sheet_5_candidates.png`.
- Created `runs/000001/experiments/two_view_prompt_v4/evaluation/manual_evaluation.json`.
- Updated `runs/000001/experiments/two_view_prompt_v4/notes.md`.
- Created `runs/000001/repair/postproduction_plan_v1.md`.

Verdict:

- V4 is the current best base-generation direction.
- It preserves the hard-to-repair things better: identity, body/anatomy, two-view consistency for this diagnostic input, outfit structure, and shoes placement.
- Main remaining issue is belt dominance, which is a local repair candidate.

Next:

- Run the first local postproduction test: waist-area belt visibility repair on v4 candidate 01.

## 2026-06-08 - Anti-Overfit Correction For Postproduction

Work:

- User warned not to overfit the system to one perfect test result.
- Added `DEC-007 - Do Not Overfit The Pipeline To One Test Outfit`.
- Created `docs/postproduction_strategy.md`.
- Reframed `runs/000001/repair/postproduction_plan_v1.md` as an example, not the core architecture.
- Updated `PROJECT_STATE.md`.

Verdict:

- The belt issue is useful as an example of a layer visibility error.
- The next architecture step is a general repair taxonomy and policy, not local tuning of one belt.

Next:

- Create a structured repair-plan schema and manual evaluator checklist from `docs/postproduction_strategy.md`.

## 2026-06-08 - Postproduction Scope And Resource Budget Corrected

Work:

- User clarified that repairability rules depend on what the postproduction system actually is.
- User clarified that generating 3-5 Qwen candidates by default is wasteful because one pass takes about 30-40 seconds.
- Added `DEC-008 - Default To Single Base Generation`.
- Added `DEC-009 - Define Postproduction Before Repairability Rules`.
- Expanded `docs/postproduction_strategy.md` with default runtime flow, modules, and budget policy.
- Updated `PROJECT_STATE.md`.

Verdict:

- Multi-candidate generation is research mode, not default product behavior.
- The next step is a postproduction system contract, not a repair-plan schema alone.

Next:

- Define the postproduction system contract: inputs, outputs, modules, budget, and failure limits.

## 2026-06-08 - Postproduction System Contract Added

Work:

- Created `docs/postproduction_system_contract.md`.

Verdict:

- Postproduction v1 is now defined as one base generation, one evaluation, zero to two local repair passes, and final evaluation.
- Multi-candidate generation remains research mode.
- Repair planning schema should be the next concrete artifact.

Next:

- Create `schemas/evaluation_and_repair_plan.schema.json`.

## 2026-06-08 - Pose Priority Clarified

Work:

- User clarified that exact pose preservation is not critical because real photos will not be perfectly controlled.
- Updated `DEC-006` and project state to prioritize body/anatomy, garment fit, identity, structure, and layering over exact pose copying.

Verdict:

- Pose is a conditional priority, not a universal top priority.
- For real product behavior, believable anatomy and garment fit matter more than copying the exact pose.

Next:

- Continue with postproduction planning using the updated evaluation priority.

## 2026-06-08 - Automatic Repair Planner Contract Started

Work:

- User clarified that repairability can only be defined after deciding what the
  postproduction system actually contains.
- User clarified that 3-5 Qwen generations are acceptable for tests but too
  expensive to normalize in the final product.
- Created `schemas/evaluation_and_repair_plan.schema.json`.
- Created `prompts/evaluation_and_repair_planner.md`.
- Created `runs/000001/experiments/two_view_prompt_v4/evaluation/repair_plan_example.schema_v1.json`.
- Validated the new JSON files parse correctly.

Verdict:

- The system now has a contract for future automatic evaluator output.
- Manual repair plans are examples for bootstrapping; they are not the intended
  product workflow.
- Repairability is now tied to actual modules: color repair, local inpaint,
  reference-guided detail repair, or regenerate.

Next:

- Test whether LM Studio/VLM can fill the repair-plan schema from images and
  references.

## 2026-06-08 - Executor-First Correction For Postproduction

Work:

- User challenged the assumption that the postproduction system was already
  fixed.
- Reframed the postproduction contract as a hypothesis, not a proven design.
- Added `DEC-010 - Prove Repair Executors Before General Repair Planning`.
- Updated `PROJECT_STATE.md` so the next step is an executor bake-off, not a
  broader automatic planner.

Verdict:

- A repair plan is only useful after there is a real tool that can execute it.
- The next postproduction work should test concrete executors first:
  deterministic color repair, local inpaint, and reference-guided detail repair.

Next:

- Start with the cheapest executor test: deterministic color repair on a garment
  mask, recording result quality, runtime, and failure modes.
