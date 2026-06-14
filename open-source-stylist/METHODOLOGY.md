# METHODOLOGY — how this system is built

Created 2026-06-10 after the restart decision. These rules exist because the previous
attempt failed on process, not on tools: experiments without stated questions,
conclusions from unreliable evaluation, tweaks that passed tests without solving
problems. This document governs all engineering decisions. CLAUDE.md governs
collaboration (communication, confirmation, git, reporting); this file governs
how knowledge is produced and how changes are accepted.

---

## 1. Knowledge classification

Every claim about system behavior has exactly one status, tracked in `knowledge/`:

| Status | Meaning | Requirements |
|---|---|---|
| **Verified** | safe to build decisions on | deterministic measurement, reproduced in ≥2 independent runs, OR explicitly confirmed by the owner on direct evidence |
| **Observation** | something seen once | single run, or subjective judgment (VLM or AI-assistant visual opinion). Points where to look; decides nothing |
| **Hypothesis** | plausible, unproven | any claim not yet tested under these rules, including ALL findings of the previous attempt |

Rules:
- Decisions rest on Verified facts only. If a needed fact is a Hypothesis, the next
  step is the experiment that verifies it — not a decision that assumes it.
- Promotion (Hypothesis → Verified) happens only via a protocolled experiment (§2).
- Demotion is immediate: any contradicting evidence drops a fact back to Hypothesis,
  with a dated note in `knowledge/`.
- `knowledge/verified.md` and `knowledge/hypotheses.md` are append-only, date-stamped.
- VLM output and AI-assistant visual comparison are *never* sufficient for Verified.
  They produce Observations only. Instruments (pixel math, embeddings, masks,
  deterministic scripts) and the owner's eyes produce Verified facts.

## 2. Experiment discipline

An experiment exists to inform a decision. No decision at stake — no experiment.

**Before running** (written to `experiments/NNN_name/protocol.md`):
1. **Question** — one sentence, falsifiable.
2. **Decision informed** — which build/architecture decision depends on the answer.
3. **Method** — inputs, configuration, number of runs, what varies, what is fixed.
4. **Acceptance criteria** — what result means what, defined BEFORE seeing results.
   Numeric thresholds where possible.
5. **Cost estimate** — GPU time, sessions.
6. **Integration FAIL tests** — for any new or modified gate path, one known-FAIL
   case must be written in `system/tests/` before execution: a fixed input that
   the gate must score as FAIL. Tests exercise the full measurement path from
   inputs to verdict. A gate without a FAIL test is not validated.

**After running:**
- Raw results go to `experiments/NNN_name/results/` unmodified (including failures).
- `conclusion.md` is written only after the owner has seen the results, when the
  outcome involves visual quality. Instrument-only outcomes (pure numbers) may be
  concluded without owner review but are still reported.
- The conclusion states: answer to the question, knowledge status changes
  (what got promoted/demoted), and the decision now unblocked.

**Banned:**
- Running generation experiments before the instruments that judge them are
  validated (design P9).
- Re-running with tweaked settings until something passes, then reporting the pass
  ("fishing"). Every re-run with changed parameters is a new protocol or an explicit,
  documented parameter sweep declared in the original protocol.
- Concluding from K=1 where variance is known to exist (diffusion outputs!). The
  variance baseline experiment defines the noise floor; differences below it are noise.

## 3. Change acceptance rules

For every proposed change (code, prompt, workflow, parameter):

1. **Problem class, not test instance.** The change must address the *class* of problem,
   stated in one sentence ("garment references contaminate conditioning with model
   bodies"), not the instance ("run 3 shoes were black"). If the statement of what the
   change fixes only mentions a specific test case — rejected.
2. **Full-picture check.** Before acceptance, state which stages/contracts the change
   touches and why it does not narrow general capability. A change that helps one
   outfit but plausibly hurts others (e.g., hardcoding an outfit-specific rule into the
   adapter) is rejected.
3. **No quiet fixes during experiments.** Configuration is frozen for the duration of
   a protocolled experiment. Bugs found mid-experiment stop the experiment; the fix is
   applied; the experiment restarts. No mixed-config result sets.
4. **Generality test for prompt/panel changes:** the change must be expressible as a
   rule for the stage ("never include color words"; "crop references to garment only"),
   not as content for one outfit.
5. **Right tool for THIS job when reusing a component.** Reusing an existing module
   for a new job requires re-asking "is this the right tool for the new job", not
   just "does it run". The board reused the §5 measurement segmenter (GroundingDINO+
   SAM+union) to isolate garments — a parsing job that segmenter is wrong for — and it
   passed unnoticed through two reviews. A reuse that silently repurposes a tool is a
   change and gets the full-picture check.
6. **View the artifact before diagnosing it.** A claim about a visual artifact (a
   board, a mask, a generated image) is not made from numbers/filenames alone — open
   and look. Two diagnoses of the E-007 board were wrong because nobody viewed it; the
   face detector + the eye settled it in one look. Numbers locate; eyes confirm.

## 4. Verification ladder

Three levels; a stage climbs all three before it is "done":

1. **Component tests** — deterministic units (clients, mask math, color math) have
   reproducible tests with known inputs/outputs. Run on demand, cheap.
2. **Stage acceptance** — the stage meets its contract on real project data, verified
   against the acceptance criteria written in BUILD_PLAN before implementation.
3. **End-to-end run** — the stage operates inside the closed loop without manual help.

Definition of done for a stage = all three levels passed + contract documented +
knowledge entries written. "Code written" is not done.

## 5. Evaluation discipline

- Deterministic gates decide what they can measure (color ΔE, identity cosine,
  proportions). Their thresholds are calibrated on controlled cases before first use.
- VLM judges semantics only (presence, layering) and is **advisory** until its
  agreement rate with owner verdicts is measured (a calibration experiment with a
  defined sample). Its reliability is itself a measured quantity.
- AI-assistant visual comparison is an Observation source, never a verdict source.
  When the assistant reviews images, it must state what it can and cannot reliably
  see at the given resolution.
- The owner's verdict is final on visual quality. The system's job is to bring the
  owner a measured per-region report, not to replace the owner's eyes.
- Measurement code fails loudly: a missing metric is an error, never a default.
  `.get("metric_key", 0)` is forbidden in gate and runner code — use direct key
  access. A KeyError is the correct signal that a gate contract was broken.

## 6. Where things live

| Artifact | Location |
|---|---|
| Canonical design | `design/SYSTEM_DESIGN.md` (revisions in `design/revisions/`) |
| Assembly plan + stage contracts | `BUILD_PLAN.md` |
| This discipline | `METHODOLOGY.md` |
| Verified facts | `knowledge/verified.md` |
| Hypotheses & observations | `knowledge/hypotheses.md` |
| Stage contracts (JSON schemas) | `system/contracts/` |
| Code (module per stage) | `system/` |
| Experiments | `experiments/NNN_name/` (protocol.md, results/, conclusion.md) |
| Test inputs (person, garments) | `assets/` |
| Previous attempt (read-only) | `archive/` |

Nothing returns from `archive/` into the live tree. Ideas may be re-derived;
artifacts are rebuilt under current rules (owner decision, 2026-06-10).

---

Changes to this document: append-only, date-stamped, owner-approved.
