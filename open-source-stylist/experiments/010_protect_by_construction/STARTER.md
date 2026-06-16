# E-010 — session starter

Paste the block below into a fresh Claude Code session to execute E-010 on its own.
It is self-contained; it does not depend on the conversation that created it.
(Updated 2026-06-15: re-architected from text-only FLUX Fill to **reference-conditioned inpaint**.)

---

You are picking up the **Open Source Stylist** project at `C:\Users\Admin\Open Source Stylist`
(git branch `foundation-cleanup-2026-06-15`). Your task is to execute **experiment E-010 —
edit-the-photo try-on (reference-conditioned inpaint)**.

**Read first, before acting:** `experiments/010_protect_by_construction/protocol.md` (the signed,
re-architected spec — follow it), `CURRENT_STATE.md`, `CLAUDE.md` (SOP). The protocol is
authoritative.

**The idea in one line:** the current pipeline re-draws the whole person from an empty latent
(`EmptyQwenImageLayeredLatentImage`, denoise 1.0) → the body slims ~9% (owner-rejected, E-009).
Instead, **edit only the clothing region of the source photo** so face / skin / hands / body
outside the clothing / background stay as source pixels by construction, and take the new
garments from the **reference board IMAGE**.

**Hard rule (this disqualified the first build):** the engine MUST condition the garment on an
**image**, not text. The task-correct prompt is deliberately colour-less ("appearance from board
only"), so a text-only inpaint (`system/workflows/flux_fill_inpaint.json` — person+mask+text, no
board) invents generic clothes and fails garment fidelity by construction. That build is kept ONLY
as a possible body-only control; it is NOT the product path. Do NOT run it as arm B.

**Be honest about what inpaint fixes (do not oversell):** editing only the clothing protects, by
construction, everything OUTSIDE the clothing mask (face, hair, neck, hands, visible skin, lower
legs, background). It does NOT pin the body width UNDER the clothing — the model still draws there,
and the E-009 hip −9% is measured at hip joints under the skirt (part real slimming, part
slim-skirt-vs-jeans). Report the **shoulder** change as the cleaner body signal. If the clothed-torso
width still drifts and the owner rejects it, that is the next lever (E-011, body/pose-shape control)
— NOT a sign that inpaint failed.

**Phase 0 = engine-selection feasibility gate (pick the mechanism; begin read-only):**
Candidates, priority order — each must keep garment-from-board AND protect outside-clothing pixels:
1. **C1 QIE-Edit native masked:** VAEEncode(source) + clothing mask + denoise<1, with `image2=board`
   kept. Risk: QIE-2511 uses a special 5-D *layered* latent; a standard masked latent may not slot
   in — TEST it live in ComfyUI; if it errors, drop.
2. **C2 QIE full-regen + composite source back** outside the clothing mask (feathered). No new model;
   risk = boundary misalignment (clothing drawn on a slimmed body vs the fuller source).
3. **C3 FLUX Fill + reference conditioner** (FLUX Redux / IP-Adapter on the board / per-garment crops).
   Risk = local availability of those nodes/weights.
4. **C4 garment-image VTON** (IDM-VTON / CatVTON / FLUX-VTON). Risk = install/license/VRAM.
Procedure: query the live ComfyUI (`:8000`) `/object_info` → which of C1–C4 are available? Produce
ONE output with the highest-priority available candidate → **owner checkpoint on that single output**
(garment matches board? face/skin/bg source-clean? seams?). Pick the engine the owner accepts. If only
text-only is available, STOP and name the exact missing model/node to the owner — do NOT use text-only.

**Reuse, do not rebuild:**
- `system/run_slice.py` — the audited vertical slice (validated input → exact request → exact filled
  workflow → output+hashes → segmentation+sanity → gates → manifest+report). The E-010 runner
  (`experiments/010_protect_by_construction/run_e010.py`, already drafted) wraps it. Reuse the
  mask/param plumbing the FLUX build added; verify cfg/sampler/scheduler/negative/denoise/mask reach
  the selected engine (the adapter hardcodes sampler=euler/scheduler=simple at adapter.py:62-63).
- Gates: `system/gates/body_pose.py` (skeletal; MediaPipe Tasks API; model at
  `system/gates/models/pose_landmarker_full.task`, git-ignored), `color.py` (ΔE + hue/chroma split),
  `identity.py` (ArcFace).
- **Arm A baseline exists** — E-009 Lightning in `experiments/009_body_preservation/results/R1_lightning/`
  (hip ~−9%). Do NOT regenerate A.
- Clothing mask already built: `experiments/010_protect_by_construction/masks/clothing_region.png`
  (+ `_nodilate`). Re-review before use. Board: `outfit_001` `hybrid_mask_crop` (frozen, SHA-verified
  by `resolve_board`). Color refs: `assets/outfits/outfit_001/eval_references.json`. Source person
  mask: `experiments/001_segmentation_masks/results/person_front/person.png`.

**Acceptance (garment is a HARD gate):** adopt inpaint only if every item's colour/presence/layering
is **not worse** than A AND the owner's per-item detail verdict is not worse, AND face cosine ≥0.57
and not below A, AND the gross different-person/body failure is removed with outside-clothing
source-clean. If clothed-torso width still drifts → trigger E-011, do not call inpaint a failure.
Owner verdict per axis is the acceptance; gates advisory; no aggregate score.

**Environment gotchas (these will bite otherwise):**
- Python 3.10 system interpreter; run with `PYTHONPATH=.`. No project venv.
- ComfyUI `:8000` must be live (`ComfyUIClient().system_stats()`); LM Studio not needed.
- **Downloads:** system Python SSL fails on the local TLS-intercept cert (`CERTIFICATE_VERIFY_FAILED`)
  → download any model via PowerShell `Invoke-WebRequest` (Windows trust store), NOT python requests.
- Console is `cp1251`: reconfigure stdout to utf-8 before printing `Δ`/`°` (see `run_e009.py`).
- A 20-step / inpaint generation can exceed the 10-minute shell cap → run in background or per-cell,
  and make the runner **resumable** (skip cells whose `results/.../manifest.json` exists).
- Outputs: `experiments/010_protect_by_construction/results/` is the tracked record; `runs/` is
  throwaway scratch (git-ignored) — never the record.
- `mediapipe==0.10.35` is installed (Tasks API only — `mp.solutions` does not exist).

**Discipline (CLAUDE.md):** the owner makes visual quality verdicts at checkpoints; you do all
mechanical/technical work yourself (never hand the owner commands). Do NOT generate without an owner
OK at a checkpoint. Commit per step; stage ONLY files you create/change (the working tree has ~50
pre-existing dirty files unrelated to this task). NO git remote — do not push or rewrite history
without owner approval. End commit messages with:
`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

**Your first concrete action:** read the three docs, then query ComfyUI `/object_info` and report
which engine candidates (C1–C4) are available, plus your recommended pick — and re-review the
existing clothing mask. Build/generate nothing until the owner approves the engine at the Phase-0
single-output checkpoint.
