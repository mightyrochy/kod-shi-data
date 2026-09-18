# Run 000001 Notes

## Purpose

First clean manual outfit transfer run for `M1 - One Controlled Manual Outfit Run`.

This run uses old test assets, but it is organized as a new repeatable experiment.

## Inputs

- Person image: `input/person_front.png`
- Person analysis reference: `input/person_two_view.png`
- Request: `input/request.txt`
- Outfit package: `outfit/outfit_package.json`
- Qwen prompt: `qwen/prompt.txt`
- Qwen clean reference board: `qwen/reference_board_clean.png`
- Qwen fuller debug board: `qwen/reference_board.png`

## Selected Outfit

Primary selected items:

- ivory blouse;
- brown long skirt;
- brown belt as secondary waist detail;
- dark green wedge sandals;
- gold disc earrings.

Unused references kept for later:

- navy blouse;
- brown jacket;
- gray skirt;
- pink dress;
- fair-isle sweater.

## Expected Failure Risks

- Source person image is relatively small.
- Qwen may leave old jeans/socks visible.
- Qwen may copy model features from garment references if references are used too directly.
- Shoes and earrings may be difficult because they require small-detail transfer.
- Belt visibility can conflict with blouse hem logic.
- The clean reference board reduces but does not fully remove reference-model identity leakage.

## Verdict

Status: five candidates generated manually through ComfyUI.

Generated outputs copied to:

- `output/candidate_01.png`
- `output/candidate_02.png`
- `output/candidate_03.png`
- `output/candidate_04.png`
- `output/candidate_05.png`
- `output/contact_sheet_5_candidates.png`

Manual evaluation:

- `evaluation/manual_evaluation_5_candidates.json`

High-level result:

- Strong baseline.
- Overall outfit transfer works.
- The old sweater, jeans, and socks are removed.
- Main failures are garment detail fidelity: belt, shoe texture/straps, earring detail, exact skirt slit, and exact fabric behavior.
- Candidate 01 is the best first repair target.

Next action:

Use candidate 01 for the first focused repair test. Start with one repair target only: belt visibility or shoe detail.
