# E-010 — session starter

Paste the block below into a fresh Claude Code session to execute E-010 on its own. Self-contained.
(Updated 2026-06-16: **garment fidelity is axis #1**; body is secondary. Generation core =
detail-preserving VTON/warping, not text-only inpaint.)

---

You are picking up the **Open Source Stylist** project at `C:\Users\Admin\Open Source Stylist`
(git branch `foundation-cleanup-2026-06-15`). Execute **experiment E-010 — garment-faithful try-on**.

**Read first:** `experiments/010_protect_by_construction/protocol.md` (signed spec), and its companions
`ENGINE_LANDSCAPE.md` (engine survey, 7 families), `GEN_INSTRUMENTS.md` (generation tools),
`EVAL_INSTRUMENTS.md` (measurement). Also `CURRENT_STATE.md` and `CLAUDE.md` (SOP).

**Priority (this is the key correction):** **garment accuracy is the product** — showing the SPECIFIC
item (lime blouse with buttons, brown skirt, brown belt, gold disc earrings, teal wedge sandals). Axes,
in order: **#1 garment fidelity (HARD gate)**, **#2 identity (face)**, **#3 body morphology (secondary;
the E-009 ~9 % hip slim is polish, non-blocking unless gross)**. Do NOT tunnel on body.

**Why the previous build is wrong:** `system/workflows/flux_fill_inpaint.json` is **text-only**
(person + mask + text, no board image). With our colour-less prompt it invents generic clothes → fails
garment fidelity by construction. **Disqualified.** The engine MUST condition the garment on an **image**.
Generic VTON/inpaint also re-synthesises the garment → detail drift; prefer tools that keep the **real
garment pixels** (warping / high-res feature injection).

**Generation instruments (GEN_INSTRUMENTS.md):** core = **FitDiT** (DiT, high-res garment feature
injection, ComfyUI node) or **DiffFit / GP-VTON** (warping) — applied **per garment** (blouse → skirt);
+ **per-item high-res references** (the hybrid board's per-item crops, NOT the 768 tiled board); +
**high-res single-item local repair** (design §5); + **OmniTry** for accessories (belt/earrings/shoes).
Identity (PuLID/InstantID) and body (DensePose/SMPL) are secondary.

**Measurement instruments (EVAL_INSTRUMENTS.md):** garment "same item?" = **retrieval-rank vs decoys via
Marqo-FashionSigLIP + DISTS** + colour(hue/chroma)/palette + silhouette descriptors + PaddleOCR + Qwen-VL
detail checklist + owner per-item verdict. **Build + calibrate this** (labelled crop set) so axis #1 is
measurable — without it, garment fidelity is owner-eye-only.

**Phase 0 — engine selection (garment-first; ENGINE_LANDSCAPE.md):** pick by (a) garment exact-fidelity
on our items, (b) multi-item + accessory coverage, (c) 16 GB local, (d) license (Leffa MIT / OmniTry
CC-BY-SA commercial-OK; CatVTON/IDM-VTON NC = prototype only). Candidates: FitDiT, DiffFit/GP-VTON,
IDM-VTON (best texture), Leffa (light, MIT), + OmniTry accessories; **cloud (FASHN/Kling/GPT-4o)** is the
detail ceiling and a legitimate V1 fallback. Query the live ComfyUI `/object_info`; produce ONE output
with the top candidate; owner checkpoint against the EVAL stack. If no local stack reproduces our items
acceptably → escalate to cloud or a Garments2Look-style fine-tune (rented GPU) — do NOT force a weak engine.

**Arms:** A = current full-regen baseline (E-009 R1 Lightning, in
`experiments/009_body_preservation/results/R1_lightning/` — do NOT regenerate). B = garment-first
pipeline. Reuse `system/run_slice.py` (the audited vertical slice) and the gates
(`system/gates/{body_pose,color,identity}.py`).

**Acceptance:** garment HARD gate (every item: target top-K retrieval, DISTS/colour/detail not worse
than A, owner detail verdict not worse) = the PASS axis; identity ≥ 0.57 and not below A; body measured
+ reported, blocks only if grossly wrong. No aggregate; owner verdict per axis.

**Environment gotchas:** Python 3.10 + `PYTHONPATH=.`; ComfyUI `:8000` live; **downloads via PowerShell
`Invoke-WebRequest`** (system Python SSL fails on the corporate cert); console `cp1251` → reconfigure
stdout to utf-8 for `Δ`/`°`; long generations exceed the 10-min shell cap → background or per-cell +
resumable runner; outputs in `experiments/010_.../results/` (`runs/` is git-ignored scratch);
`mediapipe==0.10.35` (Tasks API only).

**Discipline (CLAUDE.md):** owner makes visual verdicts at checkpoints; you do all mechanical work
yourself; do NOT generate without an owner OK at a checkpoint; commit per step, staging ONLY files you
create/change (~50 pre-existing dirty files are unrelated); NO git remote — no push/history-rewrite
without owner OK. End commit messages with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

**First action:** read the docs; query ComfyUI `/object_info`; report which garment-fidelity cores
(FitDiT/DiffFit/IDM-VTON/Leffa) and OmniTry are available locally (or the exact missing piece) + your
recommended garment-first stack; and scope the EVAL garment-fidelity instrument. Generate nothing until
the owner approves the engine at the Phase-0 checkpoint.
