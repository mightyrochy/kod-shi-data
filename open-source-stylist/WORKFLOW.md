# WORKFLOW — current pipeline state

Last updated: 2026-06-10.

## Executable pipeline (V1-alpha)

```text
python -m pipeline.run_v1alpha [source_run_id] [--resolution WxH] [--hypothesis "..."]
```

Steps performed per invocation:

1. Locate source run (`runs/experiments/v1alpha/NNNNNN` or legacy `runs/NNNNNN`).
2. Create a new numbered run folder under `runs/experiments/v1alpha/`.
3. Copy inputs (person image, outfit package, prompt, reference board) into `input/`.
4. Write `experiment/config.json` (model, LoRA, steps, cfg, sampler, resolution, hypothesis).
5. Free VRAM (`POST /free`), build the QIE-2511 workflow from
   `pipeline/workflows/qie2511_vton.json`, submit to ComfyUI.
6. Download the generated image to `output/output.png`.
7. Free VRAM, run VLM evaluation (qwen3-vl-8b via LM Studio), save raw result
   to `conclusion/evaluation.json`, unload the VLM.
8. Print VLM observations to terminal and stop.

## Evaluation discipline

- `conclusion/evaluation.json` is **raw VLM output** — experiment data, not a verdict.
- VLM observations are advisory only (documented hallucinations at low resolution).
- Conclusions are written to `conclusion/notes.md` and FINDINGS.md **only after
  human review** of the output image. No commit of conclusions before that.
- Final quality verdict belongs to the owner (CLAUDE.md SOP).

## Run folder layout

```text
runs/experiments/v1alpha/NNNNNN/
  input/        person image, outfit_package.json, prompt.txt, reference board
  output/       output.png
  experiment/   config.json, workflow_submitted.json
  conclusion/   evaluation.json (raw VLM), notes.md (human)
  run.log       timestamped execution log
```

## Modules

| File | Role |
|---|---|
| `pipeline/run_v1alpha.py` | orchestrator (closed loop) |
| `pipeline/outfit_adapter.py` | reference panel, prompt build, workflow fill |
| `pipeline/comfyui_client.py` | ComfyUI REST client (submit, poll, download, /free) |
| `pipeline/lmstudio_client.py` | LM Studio REST client (chat, vision, unload) |
| `pipeline/evaluator.py` | 4-criterion VLM evaluation (advisory) |
| `pipeline/run_io.py` | numbered run folder creation, logging |
| `pipeline/confirm_run.py` | append human review notes to a run |
| `pipeline/smoke_test.py` | environment smoke test (8 checks) |
| `tools/upscale.py` | standalone AI/LANCZOS upscaler |
| `tools/postproduction_color_repair.py` | standalone color repair (legacy, working) |

## Known constraints

- Generation: QIE-2511 fp8mixed + Lightning LoRA, 4 steps, cfg 1.0 — do not
  raise steps with LoRA enabled (40 steps confirmed worse).
- Colors must come from reference images, never from prompt text.
- VRAM 16GB: generation and VLM are sequenced via /free + unload, never resident together.
- Working resolution: under evaluation (Phase A1; 928×1344 tested in run 000003).
