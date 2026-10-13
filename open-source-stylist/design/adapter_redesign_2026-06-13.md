# Adapter redesign — task-correct conditioning (historical proposal)

Date: 2026-06-13. Status: **partly implemented, then superseded where noted.**
Current behavior is defined by `SYSTEM_DESIGN.md` and E-007 v2 (2026-06-14).
Author context: written after discovering that the generation conditioning never
expressed the system's task (see "Problem" below). On approval, the contract here
folds into design/SYSTEM_DESIGN.md §6 [3] and the adapter code; the exact prompt
wording and board-label question become the rescoped prompt-strategy experiment.

---

## 1. Problem (evidence)

The system's task is: **person photo + outfit → the SAME person wearing the new
outfit, garments taken from the references.** None of the conditioning layers
expressed that task:

- **Positive prompt** ([prompt.py:44]): `"A person wearing {descriptions}.
  {visibility_notes} Full body, standing pose."` — a text-to-image instruction.
  No "keep this person", no "transfer from the reference board". `layering_order`
  is never read (dead field); only free-text `visibility_notes` reaches the model.
- **Negative prompt** (workflow node 8): hardcoded empty.
- **`negative_constraints`** in the outfit package (which DO say "do not change the
  person's identity/face/body", "do not copy any model's face/body"): never read by
  any code.
- **Board** (panel.py): a 3×N grid of garment crops on white. No rendered labels,
  no worn-look, no spatial body mapping. The model sees disconnected thumbnails.
- **cfg = 1.0** in both workflows (verified). At cfg=1.0 classifier-free guidance is
  off: `output = cond` and the negative prompt is mathematically ignored. So under
  the Lightning config, a negative prompt has **zero effect** — preservation cannot
  be delegated to negatives there.

Identity held in past runs only because QIE-2511 is an edit model that leans on
image1 structurally — incidental, not instructed. All E-005/E-006/E-008 generation
conclusions are confounded by this (instruments E-001…E-004 unaffected).

---

## 2. The contract the adapter must satisfy

The generation request must express, at the layer where it actually takes effect:

1. **Preserve** the person: face, hair, skin, body proportions, pose, framing, background.
2. **Replace only clothing** with the specific garments shown in the reference board.
3. **Follow layering** (order + visibility) from `layout_logic`.
4. **Take appearance (color/texture) from the references**, not from text.
5. **Do not** import any reference model's face/body/competing items.

Items 1–5 are the task. The redesign routes each to a layer that can carry it.

---

## 3. Positive prompt — STRAIGHT FIX (structure) + TESTED (wording)

**Straight fix (not optional, not a tuning choice):** the prompt must state the
edit/transfer task and preservation, because under cfg=1.0 it is the ONLY textual
channel that affects output. Contract for `build_prompt`:

- Frame as an edit of image1, not generation of a new person. e.g. opens with an
  instruction to keep the person and edit only the clothing.
- Name preservation targets explicitly (face, hair, body, pose, background).
- State that garments come from the reference image (image2).
- Carry layering: use `layering_order` (currently dead) + `visibility_notes`.
- No color words (existing rule; H-COLOR still pending E-007).

**Tested, not asserted:** the exact phrasing and verbosity. The general-prompts
principle (less text → model leans on the board) and the need for an explicit task
frame both pull on the wording. Which concrete phrasing performs best is the
rescoped prompt-strategy experiment (was E-007), with arms sharing one corrected
baseline as control and pre-registered acceptance criteria. The redesign fixes the
CONTRACT; the experiment picks the wording. We do not ship one phrasing as "the
answer" without the test.

---

## 4. Negative prompt — DEFERRED by the cfg=1.0 finding

`negative_constraints` SHOULD carry the preservation/anti-contamination negatives,
but wiring them into node 8 while cfg=1.0 does nothing. Therefore:

- Under the Lightning (cfg=1.0) config: do **not** rely on negatives; preservation
  lives in the positive prompt (§3). Wiring them in is harmless but inert — defer.
- The negative channel becomes real only at cfg>1 (a no-Lightning config). Note:
  the current `qie2511_vton.json` (full-model) workflow ALSO has cfg=1.0 baked in —
  so bench rows 2–3 (no-Lightning) as templated would not use guidance either. If
  the bench tests negatives, those rows need cfg>1 and a populated node 8. Capture
  this as a bench-prep item; not a V1-baseline change.

---

## 5. Board — STRAIGHT FIX (layering data) + TESTED (labels)

**Straight fix:** none of the board's pixels change, but the adapter must pass
layering to the model via the prompt (§3), since the grid itself cannot convey it.

**Tested, not asserted:** whether the board should carry rendered per-cell labels
(QIE can read in-image text) or spatial body-region arrangement. Unverified that
labels help; could also add noise. Treat "labeled board" and "clean grid" as
candidate arms in the prompt-strategy experiment, decided on gates + owner review.
Default for the corrected baseline: clean grid (current), labels tested as a variant.

---

## 6. Masks — RELATED FIX (separable from the prompt/board work)

Not part of generation conditioning, but corrupts the panel crops and every
evaluation gate, and the owner grouped it into the review.

- **Root cause:** `ImpactFlattenMask` takes the UNION of all GroundingDINO
  detections for a label (grounded_sam.py). Multiple detections → one merged mask
  (the "top absorbed bottom/belt" failures). No instance selection.
- **Fix:** select a single instance instead of unioning — largest-area or
  highest-confidence box → SAM on that box only. Optionally per-label threshold.
- **Verification:** the existing sanity guard + a FAIL test on a known multi-
  detection case; re-segment E-001 assets and confirm masks unchanged-or-better.
- Separable: can be approved and landed independently of the prompt redesign.

---

## 7. Code touched (on approval)

- `system/adapter/prompt.py` — `build_prompt` rewritten to the §3 contract; consume
  `layering_order`.
- `system/adapter/adapter.py` — pass `negative_constraints` through to the request
  (stored even if inert at cfg=1.0, so it's ready for cfg>1 bench rows).
- `system/workflows/*.json` — node 8 wired to a `__NEGATIVE_PROMPT__` placeholder
  (inert at cfg=1.0, correct at cfg>1).
- `system/segmentation/grounded_sam.py` — instance selection instead of union (§6).
- `system/contracts/generation_request.json` — add optional `negative_prompt`
  (already present in schema) population.

---

## 8. Re-baseline plan (after the redesign lands)

Per METHODOLOGY §3.3 (bug found → stop, fix, restart the affected experiments):

1. Land the adapter redesign (§3) + mask fix (§6) with tests.
2. Demote the confounded knowledge entries with dated errata: V-VAR-001,
   V-COLOR-002, V-ID-002, V-PROP-002 reversal, V-RES-001, V-REF-001/002 — marked
   "confounded by mis-specified conditioning (pre-2026-06-13 adapter); re-baseline
   pending." Keep the numbers (they're real measurements of the wrong task).
3. Re-run E-005 (variance baseline) under the corrected adapter → the first honest
   generation baseline. Owner reviews outputs + gates.
4. Decide from the new baseline what to re-run of E-006 (resolution) and E-008
   (cropped vs raw). H-REF-CONTAMINATION and H-PROPORTIONS re-open against it.
5. Rescoped prompt-strategy experiment (was E-007) runs against the corrected
   baseline to pick wording / board-label variant.

---

## 9. Owner decisions (resolved 2026-06-13)

1. **Board: labeled crops.** Each cell carries a rendered text label matching the
   reference role — "blouse front", "blouse back", "belt", "shoes", "earrings", etc.
   (Labels come from item_id + the reference file role, drawn into each cell.)
2. **Prompt: board-referencing transfer instruction.** The positive prompt instructs
   re-dressing the input person USING the board, the layout/layering, and the on-board
   labels — not describing garments as free text. Preservation stated positively
   (cfg=1.0 → negatives inert).
3. **This is E-007**, the re-baseline: build the task-correct adapter (labeled board +
   board/layout/label-referencing transfer prompt), then test whether it expresses the
   task vs the confounded baseline. "Combinations of board+prompt" — the two channels
   working together — are what E-007 measures.
4. **Negatives:** stay empty for now. cfg=1.0 makes them inert under Lightning. The
   negative channel is isolated later by E-014 (after the bench Lightning-fidelity
   rows, at cfg>1, single variable). The Lightning-fidelity rows themselves run with
   an empty negative so Lightning/steps are the only variables there.
5. **Mask instance selection** (§6): still to confirm default (largest-area vs
   highest-confidence) at implementation — largest-area is the proposed default.

---

## 10. What this does NOT change

- Instruments (E-001…E-004 calibrations), V-QIE-001, V-ENV-001 — stand.
- The measurement-first ordering (P9) and all gate code — unchanged.
- METHODOLOGY guard to add on approval: any model-facing instruction (prompt,
  negative, board) is reviewed against the system task statement, not only for code
  validity — the gap that let this persist through two code reviews.

---

## 11. UPDATE 2026-06-13 — board/mask sections superseded by §6a of SYSTEM_DESIGN

This proposal's §5 (board) and §6 (masks) are superseded after the E-007 board-
contamination forensics. The first E-007 attempt ran on a contaminated board and is
INVALID (hypotheses.md O-BOARD-001…005).

- **§5 board** — the "labeled crop board" still holds (labels approved), but the way
  crops are produced changes: NOT in-loop GroundingDINO+SAM+union. E-007 v2 selects
  one of two already-built, hash-verified PNGs (masked or rectangular). It does not
  tile or isolate anything at generation time.
- **§6 masks** — the instance-selection idea was the right instinct but the wrong
  layer: the real fix is to stop doing garment isolation with a general detector in
  the loop, not to post-process its union. The earlier no-face/size "validator stack"
  framing is reframed (owner): remove the chaos (deterministic isolation) rather than
  police it; a no-face/size check belongs on the one-time asset prep, not as an in-loop
  policeman. The §5 measurement RegionMap (generated images) is a separate matter and
  may also move to a parser — to be tested, not assumed.
- Storage: current experiment boards are durable inputs and are reused byte-for-byte.

The positive-prompt contract (§3), the cfg=1.0 → preservation-in-positive finding
(§1, §4), and E-014 (negative channel test) are UNAFFECTED and stand.
