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
