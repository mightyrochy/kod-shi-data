# Open Source Stylist

Open source pipeline for an automatic stylist and outfit transfer system.

The goal is not to generate a single prompt. The goal is a controlled workflow:

```text
user photo + style request
-> person analysis
-> stylist system
-> outfit adapter
-> Qwen Image Edit / ComfyUI
-> afterproduction
-> evaluation + retry
```

## MVP Stack

| Layer | Open source choice | Purpose |
| --- | --- | --- |
| Workflow runner | Python + FastAPI | API and orchestration |
| Image workflow | ComfyUI | Local node-based generation and image editing |
| Try-on/edit model | Qwen-Image-Edit-2511 | Identity-preserving outfit transfer |
| Vision analysis | Qwen2.5-VL, Florence-2, SAM2, OpenPose/DWPose | Describe person, pose, masks, photo constraints |
| Stylist reasoning | Qwen/Llama/Mistral via Ollama or vLLM | Pick outfit from structured constraints |
| Catalog search | Qdrant or FAISS | Retrieve garment candidates by style, season, color, budget |
| Storage | MinIO + Postgres | Images, runs, structured results |
| Evaluation | CLIP/SigLIP + VLM checklist | Identity, item presence, outfit logic, detail preservation |

## What Is In This Starter

- [docs/architecture.md](./docs/architecture.md) - build plan and module boundaries.
- [schemas/outfit_layout.schema.json](./schemas/outfit_layout.schema.json) - contract between stylist and adapter.
- [configs/pipeline.example.yaml](./configs/pipeline.example.yaml) - example local configuration.
- [prompts/](./prompts) - first-pass prompts for person analysis, stylist, adapter, and evaluator.

## First Practical Milestone

Build a local CLI/API that accepts:

- one person image;
- one style request;
- 3-8 garment reference images;
- constraints such as season, budget, colors, and dislikes.

It should output:

- `person_analysis.json`;
- `outfit_layout.json`;
- `qwen_edit_prompt.txt`;
- generated image;
- `evaluation.json`.

The important discipline: every module emits structured data, not loose prose.

