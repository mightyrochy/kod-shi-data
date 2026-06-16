# Generation instruments (what produces a garment-faithful result) — 2026-06-16

Garment accuracy is product axis #1 (showing the SPECIFIC item is the product). These are the
generation-side tools, chosen for **garment fidelity first**. They PRODUCE the result; the
measurement stack is in `EVAL_INSTRUMENTS.md`.

**Core principle:** generic VTON / inpaint **re-synthesises** the garment from an embedding → detail
drifts (observed: blouse shade, belt, shoes). Fidelity tools instead **keep the real garment pixels**
— via warping or high-resolution feature injection. The core is chosen for that.

## 1. Core garment-transfer engine (detail-first)
- **FitDiT** (DiT) — purpose-built for *authentic garment details*: GarmentDiT feature extraction +
  **high-resolution garment feature injection**; **ComfyUI node exists** (Jan 2025). Primary candidate.
- **DiffFit / GP-VTON / DualFit** — geometry-aware **warping**: deform the *real* garment onto the body
  (buttons/print/shade survive as actual pixels), then diffusion-refine texture/wrinkles/lighting.
- Chosen over plain VTON/inpaint because those re-synthesise → detail drift.

## 2. Per-item high-resolution reference conditioning (an instrument, not just data)
- Feed each garment its **own full-resolution reference** (the hybrid board's per-item masked crops),
  NOT one downscaled 768 tiled board (audit: detail crushed to 2–25 % of pixels). Multi-reference
  (several views) where available (FastFit / Garments2Look style).

## 3. High-resolution single-item local repair (design §5 / Strategy C)
- After the base pass: crop each garment region → regenerate at high res from the full-res single-item
  reference. Restores fine detail (buttons, hardware, texture) the holistic pass loses.

## 4. Accessory model
- **OmniTry** (belt / earrings / shoes) — garment VTON ignores accessories; OmniTry is purpose-built
  (CC-BY-SA, commercial-OK; verify release + 16 GB).

## 5. Refinement locks
- **ControlNet** (lineart / canny / HED) on garment structure → hold cut / closure lines.
- Tiled upscale for texture.

## 6. Secondary (identity / body — axis #2/#3, no longer the focus)
- Face: **PuLID / InstantID**. Body: **DensePose / SMPL-shape** conditioning (the ~9 % slim is polish
  vs the product-defining garment). These ride along; they are not axis #1.

## Pipeline shape (garment-first)
`FitDiT / warping core (per main garment)` + `per-item high-res references` +
`single-item local repair` + `OmniTry (accessories)` → measured by `EVAL_INSTRUMENTS`.
Identity / body second.

**Local feasibility:** FitDiT has a ComfyUI node; warping/DiT-VTON ~ SDXL-class → fits 16 GB (verify
exact VRAM/license before making it the core). Cloud (FASHN/Kling/GPT-4o) is the detail ceiling / fallback.

**Sources:** [FitDiT](https://github.com/BoyuanJiang/FitDiT) · [FitDiT paper](https://arxiv.org/html/2411.10499v1) ·
[DiffFit](https://arxiv.org/abs/2506.23295) · [GP-VTON](https://arxiv.org/pdf/2303.13756) · [OmniTry](https://omnitry.github.io/)
