# Open Source Stylist

Automated outfit transfer pipeline, fully local:

```text
person photo + outfit package
-> QIE-2511 (Qwen-Image-Edit-2511) through ComfyUI
-> VLM observations through LM Studio (advisory)
-> human review and conclusions
-> numbered run folder with full record
```

Stack: Python, ComfyUI (:8000), LM Studio (:1234), Qwen-Image-Edit-2511 +
Lightning LoRA, FLUX Fill, RTX 4090 Laptop 16GB.

## Where to start

- `CLAUDE.md` — project instructions, SOP, technical context
- `PLAN.md` — active build roadmap (phases A–F)
- `FINDINGS.md` — empirical ground truth from testing
- `DECISIONS.md` — architectural decisions
- `PROJECT_LEDGER.md` — durable project history
- `SYSTEM_DESIGN.md` / `SYSTEM_DESIGN_R4.md` — design vision

## Running

```text
python -m pipeline.run_v1alpha [source_run_id] [--resolution WxH] [--hypothesis "..."]
```

Each invocation creates a new numbered run under `runs/experiments/v1alpha/`.
VLM evaluation output is advisory — conclusions are written only after human
review of the generated image.
