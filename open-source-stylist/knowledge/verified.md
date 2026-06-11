# Verified facts

Append-only, date-stamped. Promotion rules: METHODOLOGY.md §1 —
deterministic measurement reproduced in ≥2 independent runs, or explicit owner
confirmation on direct evidence. Decisions rest only on entries in this file.

---

*(empty at restart, 2026-06-10 — nothing from the previous attempt qualifies.
First expected entries: environment facts from `system/env_check.py` (Stage 0),
gate calibration thresholds (Stage 1).)*

---

## V-ENV-001 — Environment facts (2026-06-11, env_check.py, run confirmed GREEN)

Source: `python system/env_check.py`, both servers live, chat round-trip passed.

| Fact | Value |
|---|---|
| ComfyUI URL | http://localhost:8000 |
| ComfyUI version | 0.24.1 |
| Python (ComfyUI) | 3.12.11 |
| GPU | NVIDIA GeForce RTX 4090 Laptop GPU |
| VRAM total | 16376 MB |
| VRAM free (idle) | 15074 MB |
| RAM total | 32387 MB |
| LM Studio URL | http://localhost:1234 |
| LM Studio chat round-trip | 2454 ms (cold, model was just loaded) |
| VLM model key | qwen3-vl-8b-instruct |
| VLM format | GGUF Q4_K_M, 8B params, vision-capable |

Note: VRAM free measured with Qwen3-VL-8B loaded in LM Studio → ~1302 MB consumed by the VLM at idle. ComfyUI had no model loaded at measurement time.

---

## V-SEG-001 — Segmentation: person photo regions (2026-06-11, E-001, owner review)

Source: `experiments/001_segmentation_masks/`, GDINO SwinT (0.3 threshold) + SAM1 vit_h
via `comfyui_segment_anything`. Owner reviewed all overlays and rated each region.

Tool: `system/segmentation/grounded_sam.py`
Image: `assets/person/person_front.png`

All 8 regions rated **ok** by owner:
`person`, `face`, `hair`, `background`, `top`, `bottom`, `shoes`, `glasses`

Note on `face`: mask covers face area around glasses frame; lens apertures excluded —
acceptable, minimal downstream impact.

---

## V-SEG-002 — Segmentation: garment reference images (2026-06-11, E-001, owner review)

Source: same tool as V-SEG-001. Images: `assets/outfits/outfit_001/` (7 product photos).

| Image | Verdict |
|-------|---------|
| belt.jpg | ok |
| blouse_front.webp | partial — blouse isolated, buttons excluded |
| blouse_back.webp | partial — same |
| earrings_disc.webp | ok |
| shoes_wedge.webp | ok |
| skirt_front.webp | ok |
| skirt_back.webp | ok |

---

## V-SEG-003 — Button exclusion in blouse masks (2026-06-11, E-001, owner verdict)

Buttons on blouse_front/back excluded from SAM1 masks. Owner verdict: acceptable for V1.
Rationale: buttons <5% of mask area; color gate mean ΔE impact minor.
Re-evaluate trigger: high-contrast-button garment fails E-002/E-005 color acceptance.

---
