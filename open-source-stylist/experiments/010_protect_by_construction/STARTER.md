# E-010 — session starter

Paste the block below into a fresh Claude Code session to execute E-010 on its own.
It is self-contained; it does not depend on the conversation that created it.

---

You are picking up the **Open Source Stylist** project at `C:\Users\Admin\Open Source Stylist`
(git branch `foundation-cleanup-2026-06-15`). Your task is to execute **experiment E-010 —
protect-by-construction (inpaint) try-on**.

**Read first, before acting:** `experiments/010_protect_by_construction/protocol.md` (the signed
spec — follow it), `CURRENT_STATE.md` (canonical project status), `CLAUDE.md` (SOP). The
protocol is authoritative for arms, axes, acceptance, and phases.

**The idea in one line:** the current pipeline re-draws the whole person from an empty latent
(`EmptyQwenImageLayeredLatentImage`, denoise 1.0), so the body slims ~9% (owner-rejected in
E-009). Instead, edit **only the clothing region** of the source photo so face / skin / hands /
body-outside-clothing / background stay as **source pixels by construction**. Measure whether
body drift drops **without regressing garment fidelity or face** — garment accuracy is a HARD
GATE (a body win bought by a blurry or wrong-detail garment does NOT pass).

**Start with Phase 0 (a build; begin read-only):**
1. Verify an inpaint engine in the local ComfyUI (`:8000`, must be live — check
   `ComfyUIClient().system_stats()`). Preferred **FLUX Fill** (model + nodes; query
   `/object_info`). Fallback: **QIE-Edit masked / img2img** (VAE-encode the source as the base
   latent + a mask + denoise < 1). If NEITHER exists locally, **stop and tell the owner the exact
   missing model/node** — downloading is a GUI step you cannot do.
2. Build a **clothing-region mask** on `assets/person/person_front.png` (torso + legs where
   garments sit; dilate for seams). Reuse `system/segmentation/grounded_sam.py`.
3. Build an **inpaint workflow** in `system/workflows/` (content-addressed + hashed like the
   existing templates; thread cfg/sampler/scheduler/negative/denoise/mask — do NOT bake params,
   that bug was just fixed). Extend `system/run_slice.py` / `system/adapter/adapter.py` to pass
   the new params (the adapter currently hardcodes `sampler=euler`/`scheduler=simple` at
   `adapter.py:62-63`, and `run_slice` exposes only cfg/steps/engine).
   Phase 0 ends at an **owner checkpoint** (one inpaint output reviewed) before the A/B.

**Reuse, do not rebuild:**
- `system/run_slice.py` — the audited vertical slice (validated input → exact generation request →
  exact filled workflow → output+hashes → segmentation+sanity → gates → manifest+report). Build the
  E-010 runner as a thin wrapper over it, like `experiments/009_body_preservation/run_e009.py`.
- Gates: `system/gates/body_pose.py` (skeletal body via MediaPipe Tasks API; model at
  `system/gates/models/pose_landmarker_full.task`, git-ignored), `color.py` (ΔE + hue/chroma split),
  `identity.py` (ArcFace).
- **Arm A (baseline) already exists** — E-009 Lightning results in
  `experiments/009_body_preservation/results/R1_lightning/` (hip ~−9%). Do NOT regenerate A.
- Color-gate references: `assets/outfits/outfit_001/eval_references.json`. Source person mask:
  `experiments/001_segmentation_masks/results/person_front/person.png`. Board: `outfit_001`
  variant `hybrid_mask_crop` (frozen PNG, SHA-verified by `resolve_board`).

**Environment gotchas (these will bite otherwise):**
- Python 3.10 system interpreter; run with `PYTHONPATH=.`. No project venv is configured.
- ComfyUI `:8000` must be live for generation/segmentation. LM Studio (`:1234`) is not needed.
- **Downloads:** system Python's SSL fails on the local TLS-intercept cert
  (`CERTIFICATE_VERIFY_FAILED`) — download any model via PowerShell `Invoke-WebRequest` (Windows
  trust store), NOT python `requests`/`urllib`.
- Console is `cp1251`: reconfigure stdout to utf-8 before printing `Δ`/`°` (see `run_e009.py`).
- A 20-step full / inpaint generation can exceed the 10-minute shell cap — run generation in the
  background or per-cell, and make the runner **resumable** (skip cells whose
  `results/.../manifest.json` already exists).
- Outputs: `experiments/010_protect_by_construction/results/` is the tracked record. `runs/` is
  throwaway scratch (git-ignored) — never treat it as the record.
- `mediapipe==0.10.35` is installed (Tasks API only — `mp.solutions` does not exist). Pin it in
  `requirements.txt` if you touch deps.

**Acceptance (from the protocol — garment is a hard gate):** inpaint wins ONLY if hip |Δ%| is
materially below A's ~8.85% AND face cosine ≥ 0.57 and not below A AND, for every required item,
colour/presence/layering are not worse than A AND the owner's per-item detail verdict is not worse.
Owner verdict is the acceptance; gates are advisory; no aggregate score.

**Discipline (CLAUDE.md):** the owner makes visual quality verdicts at checkpoints; you do all
mechanical/technical work yourself (never hand the owner commands). Do NOT run generation without
an owner OK at a checkpoint. Commit per completed step; stage ONLY files you create/change (the
working tree has ~50 pre-existing dirty files unrelated to this task). The repo has NO git remote —
do not push or rewrite history without explicit owner approval. End commit messages with:
`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

**Your first concrete action:** read the three docs above, then check the inpaint engine in ComfyUI
and report whether FLUX Fill / QIE-masked is available (or the exact blocker). Generate nothing
until Phase 0 is built and the owner approves at the checkpoint.
