# E-017 — Editor-engine fidelity bench-off: QIE vs FLUX.1-Kontext vs OmniGen2

Created 2026-06-26. Protocol BEFORE running (METHODOLOGY §2). This is the long-deferred engine bench-off
(BUILD_PLAN Stage 6), narrowed to the one axis that matters right now: **garment fidelity**.

## Why we are here (the thread, so we don't lose it)
- The QIE + FitDiT combined path produced "stitched-from-pieces" results (seams + body-shape distortion).
- Fresh field research (research/SURVEY_fashion_ai_landscape_2026-06-26.md, REFERENCE_MATRIX_2026-06-26.md)
  proposed an inverted, seam-free architecture: **holistic QIE base → gate → seam-free repair of only the failing
  garment → harmonize**, dropping FitDiT.
- Owner's valid objection: **QIE garment fidelity is insufficient on fine detail (texture, cut, e.g. cuff
  softness) — that is exactly why FitDiT was added.** A QIE-only loop may not reach the needed garment accuracy.
- We never actually tested the obvious alternatives. Phase-0 (2026-06-16) only checked **FLUX *Fill*** (text-only,
  disqualified) — NOT **FLUX.1-Kontext** (in-context, multi-image) or **OmniGen2** (multi-image subject-driven).
  Both accept reference garment IMAGES (verified 2026-06-26), so both satisfy the image-conditioning requirement.
- So before bolting anything else onto QIE, **compare the base editing engine against higher-fidelity
  alternatives** on the same task.

## Question
On the SAME person + SAME board + SAME minimal instruction, which local editing engine renders the outfit with
the **highest garment fidelity** (texture / fabric / details like buttons / exact cut / colour taken from the
reference) while preserving **identity, pose, and body proportions**:
**QIE-Image-Edit-2511  vs  FLUX.1-Kontext [dev]  vs  OmniGen2**?

## Decision this informs
The base try-on engine for V1 — and, downstream, whether a separate repair model (FitDiT / Kontext / QIE-inpaint)
is still needed at all, or whether one engine alone clears the fidelity bar.

## Method
- One person photo + one board (garment-reference panel) + one minimal instruction ("keep the person and pose;
  dress them in the garments on the board; take all colour and texture from the board").
- Each engine in its NATIVE reference-image mode:
  - **QIE-2511:** board panel as image2 (current working setup).
  - **FLUX.1-Kontext:** stitched-panel board (single canvas) and/or separate reference-latents — try the panel
    first for parity with QIE.
  - **OmniGen2:** multi-image subject-driven (person + garment images).
- Fixed seed where the engine allows; ~1MP working resolution; all local; 16 GB.
- **Appearance (colour/texture) must come from the reference image, not text** (project rule; text = instruction).

## What we measure
- **Primary — owner's eye** on garment fidelity (texture sharpness, fabric realism, button/detail accuracy, cut,
  colour-from-reference). Quality verdict is the owner's (SOP).
- **Secondary instruments** (record-only, to support the eye): identity (ArcFace), body proportions (MediaPipe),
  garment similarity (FashionSigLIP **+ DISTS**), colour (CIEDE2000) per garment region.

## Acceptance / how we decide
Owner reviews the engines' outputs side by side on the same inputs and picks which (if any) reaches acceptable
garment fidelity. That choice sets the base engine and whether a repair stage is still required. No "partial pass".

## Engine setup status (2026-06-26)
- **QIE-2511 fp8** — installed, working. ✓
- **FLUX.1-Kontext [dev]** — NOT installed. Need: `flux1-kontext-dev` fp8 (~12 GB) [+ FLUX VAE `ae.safetensors`
  if missing]; FLUX text-encoders (`t5xxl`, `clip_l`) already present. Runs in **core ComfyUI** (no custom node →
  low dependency risk). License: **Non-Commercial** (fine for evaluation; matters only if we ship commercial).
- **OmniGen2** — NOT installed. Need: `ComfyUI-OmniGen2` custom node + weights (~8–15 GB). **Dependency risk** on
  our bleeding-edge stack (torch 2.10+cu130, py3.12) — verify before installing.
- Already on disk but NOT candidates: FLUX *Fill* (text-only), Z-Image-Turbo (T2I only; no edit variant released).

## Staging (do not download everything blind)
1. **QIE vs Kontext** — one download (~12 GB), low risk. Build the Kontext board workflow, run both, owner judges.
2. **Add OmniGen2** as the third only if warranted (careful custom-node install; check cu130 dep compatibility).

## Environment snapshot (so we don't re-derive it)
ComfyUI 0.25.1, `.venv` Python 3.12.11, torch 2.10.0+cu130, port :8000. Installed editors: QIE-2509/2511,
FLUX Fill, Z-Image-Turbo. Nunchaku deferred (no cu130/torch2.10 wheel — see REFERENCE_MATRIX verification note).

## Pending / open
- **Owner GO needed on downloads** (Kontext first, or both at once) — big disk/bandwidth, system change.
- OmniGen2 custom-node dependency compatibility with cu130/torch2.10 — verify read-only before install.

## Inputs (reuse frozen assets)
person + board from `assets/` / `ComfyUI/input/` (`e016_person.png`, `e016_board.png`). Same files across all
engines for a fair comparison.

## Pointers
BUILD_PLAN Stage 6 (engine bench-off) · design/SYSTEM_DESIGN.md §8 · research/REFERENCE_MATRIX_2026-06-26.md ·
research/SURVEY_fashion_ai_landscape_2026-06-26.md · E-016 (QIE+FitDiT debug, what we're moving away from).

---

## Run 1 results (2026-06-26) — QIE vs Kontext (OmniGen2 not yet run)

Inputs: `e016_person.png` + `e016_board.png` (6-cell garment panel), same minimal instruction, seed 42, ~1MP, all native modes.

| Run | Engine / method | Settings | Result on the person |
|---|---|---|---|
| `qie_e017_00001` | QIE-2511, TextEncodeQwenImageEditPlus (image1=person, image2=board) | cfg 4.0, 20 steps, euler/simple, shift 3.1, denoise 1.0 | **Full outfit transferred** — peplum blouse + brown pencil skirt w/ slit + green wedges, identity/pose/bg preserved. Owner verdict: **does NOT clear the fidelity bar.** |
| `kontext_board_00001` | FLUX.1-Kontext dev, chained ReferenceLatent (person base + board ref) — the *alternative* method | guidance 2.5, cfg 1, 20 steps, euler/simple, denoise 1.0 | **No real transfer** — kept grey sweater, only recoloured jeans green. |
| `kontext_stitch_00001` | FLUX.1-Kontext dev, **ImageStitch (creator-recommended default**, per official `flux_kontext_dev_basic` subgraph) | guidance 2.5, cfg 1, 20 steps, euler/simple, denoise 1.0 | **No change at all** — person preserved identical (grey sweater + blue jeans). Board dominates width → person ~31.75% of canvas, downscaled small. |

Settings sourced from the official ComfyUI template subgraph "Image Edit (Flux.1 Kontext Dev)" — not invented.

**Finding:** QIE is the only engine of the two that transfers the outfit; its fidelity is owner-rejected. Both Kontext methods — including the creators' own default — fail to re-dress the person. Read (not decision-grade): Kontext dev is an instruction-EDIT model, not an outfit-transfer model; our collage board + small person region compound it.

**Open confound before judging Kontext:** the board is a 6-cell collage, not a clean garment image. Isolation pending = Kontext with ONE clean garment crop + direct "replace the top with this" edit, to test whether Kontext can transfer at all with a proper reference.

**Next (owner decides):** (A) Kontext clean-single-garment isolation, or (B) bring in the third engine OmniGen2 (multi-image subject-driven — the staged fidelity contender).
