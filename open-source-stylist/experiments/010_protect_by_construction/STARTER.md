# E-010 — session starter

Paste the block below into a fresh Claude Code session to execute E-010 on its own.
It is self-contained; it does not depend on the conversation that created it.
(Updated 2026-06-15: the reliable method is **inpaint + body-control together** — body-control is
NOT deferred, because it is the only thing that fixes the rejected under-clothing proportions.)

---

You are picking up the **Open Source Stylist** project at `C:\Users\Admin\Open Source Stylist`
(git branch `foundation-cleanup-2026-06-15`). Your task is to execute **experiment E-010 — reliable
try-on = edit-the-photo (inpaint) + body-shape control**.

**Read first, before acting:** `experiments/010_protect_by_construction/protocol.md` (the signed
spec — follow it), `CURRENT_STATE.md`, `CLAUDE.md` (SOP). The protocol is authoritative.

**The core idea — the reliable method is BOTH, neither half alone:**
- The owner-rejected defect is **body proportions** (E-009: hips ~−9%, slimmer figure). That defect
  sits **under the clothing**.
- **Inpaint** (edit only the clothing) keeps the person's pixels OUTSIDE the clothing mask
  (face/skin/hands/legs/background) and takes garments from the **board IMAGE** (not text). It fixes
  identity/face/skin/limbs/background and kills the gross "different person" failure — but it does
  **NOT** pin the body width under the clothing (the model still draws there).
- **Body-shape control** gives the model the source person's pose/silhouette (skeleton or body
  outline) and forces the generated body to match it. This is the **only** mechanism that pins the
  proportions **under** the clothing — i.e. the actual rejected defect. It does not pin face/bg.
So build toward **inpaint + body-control together**. Inpaint alone is a measurement step, not the
goal. (An earlier draft deferred body-control — that was wrong; it deferred the one fix for the
complaint.)

**Hard rule:** the garment must be conditioned on an **image**, never text. The colour-less prompt
means a text-only inpaint (`system/workflows/flux_fill_inpaint.json`, person+mask+text, no board) is
**disqualified** for garment fidelity — kept only as a possible body-only control. Do NOT run it as B.

**Phase 0 — pick a stack that supports ALL THREE (begin read-only):**
(a) garment from image; (b) masked / source-preserving edit; (c) a body/pose-shape control. Plus 16 GB.
This likely reframes the engine choice:
- **QIE-2511:** garment-image yes (image2=board), but masking is uncertain (special 5-D layered
  latent) and there is **no known body ControlNet** → probably cannot do all three.
- **FLUX ecosystem:** FLUX Fill (masked inpaint) + FLUX Redux / IP-Adapter (garment image) + FLUX
  ControlNet (pose/depth) — mature, composable, likely the stack that can do all three. Verify the
  weights are actually installed.
Procedure: query the live ComfyUI (`:8000`) `/object_info` for what is installed across BOTH stacks;
determine which stack can do garment-image + masked-edit + body-control. Produce ONE inpaint test
output and review at an **owner checkpoint** before committing. If no stack supports all three
(esp. the body control), STOP and surface the exact missing model/node — this is a possible
kill-criterion signal (off-the-shelf may not preserve body morphology). Do NOT proceed half-method.

**Arms:** A = full regen baseline (E-009 R1 Lightning, already in
`experiments/009_body_preservation/results/R1_lightning/` — do NOT regenerate). B1 = inpaint only
(measure residual body drift). B2 = inpaint + body-control (expected end state). Fixed: person_front,
outfit_001, board hybrid_mask_crop (frozen, SHA via resolve_board), 720×1024, seeds [42,123],
colour-less prompt.

**Reuse, do not rebuild:**
- `system/run_slice.py` — the audited vertical slice (validated input → exact request → exact filled
  workflow → output+hashes → segmentation+sanity → gates → manifest+report). The E-010 runner
  (`experiments/010_protect_by_construction/run_e010.py`, drafted) wraps it. Reuse the mask/param
  plumbing the FLUX build added; thread cfg/sampler/scheduler/negative/denoise/mask (the adapter
  hardcodes sampler=euler/scheduler=simple at adapter.py:62-63).
- Gates: `system/gates/body_pose.py` (skeletal; MediaPipe Tasks API; model at
  `system/gates/models/pose_landmarker_full.task`, git-ignored), `color.py` (ΔE + hue/chroma),
  `identity.py` (ArcFace). Clothing mask: `experiments/010_protect_by_construction/masks/clothing_region.png`
  (re-review). Color refs: `assets/outfits/outfit_001/eval_references.json`. Source person mask:
  `experiments/001_segmentation_masks/results/person_front/person.png`.

**Acceptance (garment is a HARD gate):** every item's colour/presence/layering not worse than A AND
owner per-item detail not worse; face cosine ≥0.57 and not below A; the **body/proportions verdict is
expected to require B2** (inpaint + control), with B1 judged only on removing the gross failure +
outside-clothing source-clean; no seam/halo the owner rejects. Owner verdict per axis is the
acceptance; gates advisory; no aggregate score.

**Environment gotchas:**
- Python 3.10 system interpreter; run with `PYTHONPATH=.`. No project venv.
- ComfyUI `:8000` must be live; LM Studio not needed.
- Downloads: system Python SSL fails on the local TLS-intercept cert (`CERTIFICATE_VERIFY_FAILED`)
  → download models via PowerShell `Invoke-WebRequest` (Windows trust store), NOT python requests.
- Console is `cp1251`: reconfigure stdout to utf-8 before printing `Δ`/`°` (see `run_e009.py`).
- 20-step / inpaint generation can exceed the 10-minute shell cap → run in background or per-cell;
  make the runner resumable (skip cells whose `results/.../manifest.json` exists).
- Outputs: `experiments/010_protect_by_construction/results/` is the tracked record; `runs/` is
  throwaway scratch (git-ignored).
- `mediapipe==0.10.35` installed (Tasks API only — `mp.solutions` does not exist).

**Discipline (CLAUDE.md):** owner makes visual verdicts at checkpoints; you do all mechanical work
yourself (never hand the owner commands). Do NOT generate without an owner OK at a checkpoint. Commit
per step; stage ONLY files you create/change (~50 pre-existing dirty files are unrelated). NO git
remote — do not push or rewrite history without owner approval. End commit messages with:
`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

**Your first concrete action:** read the three docs, then query ComfyUI `/object_info` and report,
for BOTH the QIE and FLUX stacks, which of the three capabilities (garment-image, masked edit,
body/pose control) are actually installed — and your recommended stack (or the exact missing piece,
especially the body control). Re-review the clothing mask. Build/generate nothing until the owner
approves the stack at the Phase-0 checkpoint.
