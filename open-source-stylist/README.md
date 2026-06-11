# Open Source Stylist

Automated outfit transfer pipeline, fully local:

```text
person photo + outfit package
-> try-on generation (QIE-2511 via ComfyUI)
-> per-region measured evaluation (deterministic gates + advisory VLM)
-> restoration shell + targeted repair
-> final image + measured report
```

Stack: Python, ComfyUI, LM Studio, Qwen-Image-Edit-2511, SAM 3, RTX 4090 Laptop 16GB.

**Status (2026-06-10):** restarted. Design is canonical; implementation is being
rebuilt from zero under a measurement-first plan. The previous attempt is preserved
read-only in `archive/`.

## Where to start

- `CLAUDE.md` — project instructions and SOP
- `design/SYSTEM_DESIGN.md` — canonical architecture (V1/V2/V3)
- `METHODOLOGY.md` — how knowledge is produced and changes accepted
- `BUILD_PLAN.md` — assembly plan: stages 0–7, contracts, acceptance criteria
- `knowledge/` — verified facts vs hypotheses
- `experiments/` — protocolled experiments (protocol → results → conclusion)
- `assets/` — test inputs (person photos, garment references)
