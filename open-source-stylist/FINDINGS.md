# FINDINGS — empirical ground truth

Facts verified against the live local environment. Append-only, date-stamped.

---

## 2026-06-10 — environment verification (plumbing smoke test)

**ComfyUI**
- Runs on port **8000**, NOT 8188 as CLAUDE.md states. Version 0.24.1.
- 16GB VRAM total, ~14.7GB free at idle.
- `POST /free` returns 200 (unload/free levers available for VRAM sequencing).
- Image upload via `POST /upload/image` works.

**LM Studio**
- Native REST API v1 (`/api/v1/models`) available alongside OpenAI-compatible API.
- Loaded state lives in `loaded_instances` (list), not a `loaded` boolean.
- Default JIT TTL observed: 60 min.
- Explicit unload via `POST /api/v1/models/unload` works; call takes ~1.1s.

**VLM: qwen3-vl-8b-instruct** (Q4_K_M, 6.2GB, vision-capable, 262k max context)
- Already downloaded — the Qwen3-VL upgrade recommended in SYSTEM_DESIGN_R4 is in place.
- Cold vision call (incl. JIT model load): **11.8s**. Warm call: **0.6s**.
- Schema-enforced structured output (`response_format: json_schema`) works —
  returned valid JSON matching the schema on first try.

**Python**
- System Python 3.10.11; `requests` installed 2026-06-10; PIL 12.2.0, numpy 2.2.6 present.

**Implication for the orchestrator:** VLM load cost is ~12s, unload ~1s. Sequencing
VLM ↔ generation model swaps will cost roughly 15-60s per swap depending on the
generation model's load time (not yet measured — needs a real generation run).

---

## 2026-06-10 — V1-alpha first automated run (run_000001)

**Pipeline:** `python -m pipeline.run_v1alpha 000001`
**Model:** QIE-2511 fp8mixed + Lightning LoRA, 4 steps, euler/simple, cfg=1.0
**Input:** person_front.png (464×672) + qwen/reference_board_clean.png
**Generation time:** 34.3s on RTX 4090 (16GB)
**Evaluation model:** qwen3-vl-8b-instruct (Q4_K_M)

**Automated evaluation result:**
| Criterion | Result | Notes |
|-----------|--------|-------|
| Identity preserved | PASS | Face, hair, body shape, pose, background correct |
| Outfit items present | FAIL | Sandals: black heels instead of dark green wedge; earrings not visible |
| Outfit logic | FAIL | Skirt mid-calf not ankle-length; belt not visible |
| Colors/textures match | FAIL | Sandals wrong color/type; belt absent |
| Overall | FAIL | |

**Pattern confirmed:** Identity is reliably preserved. Accessories (belt, earrings)
and footwear details (color, type, texture) are the primary failure points.
Skirt length tends to be shorter than specified.

**Matches prior manual evaluations** from runs/000001/evaluation/ — automated
evaluator surfaces the same failure modes human review found.

**Generation model load time:** QIE-2511 fp8mixed loads in ~30s (inferred from
34.3s total for 4-step inference; prior smoke test showed idle load = near-instant,
so most of that 34s is model load + 4 inference steps).

**Implication:** Evaluation pipeline is working correctly. Generation quality is
the variable to improve — bench-off (§7 R4) is the next step.

---
