# System Audit - 2026-06-08

## Summary

This machine is a strong local AI workstation and does not need a full reset.
The useful path is to keep the working ComfyUI/Qwen setup, avoid overbuilding
from the older experiments, and focus the next milestone on a small controlled
loop:

```text
manual outfit package -> Qwen 2511 edit -> evaluation -> masked/local repair
```

## Hardware

- OS: Windows 10 Pro, x64.
- CPU: 13th Gen Intel Core i9-13980HX, 24 cores / 32 logical processors.
- RAM: 32 GB.
- GPU: NVIDIA GeForce RTX 4090 Laptop GPU.
- VRAM: 16 GB total.
- NVIDIA driver: 610.47.
- CUDA UMD reported by NVIDIA-SMI: 13.3.
- Disk: C: has about 480 GB free.

## Current Runtime State

- ComfyUI is running locally at `http://127.0.0.1:8000`.
- LM Studio is running locally at `http://127.0.0.1:1234`.
- Ollama is not running / not installed.
- Docker is not installed.
- Git is installed.
- Python 3.10.11 is installed globally.
- ComfyUI uses its own Python 3.12.11 environment with PyTorch 2.10.0+cu130.

Current GPU/RAM note:

- ComfyUI and LM Studio were both active during inspection.
- NVIDIA-SMI showed about 16 GB VRAM total and about 4-6 GB free depending on the moment.
- For Qwen generation, unload or close large LM Studio models first.

## Installed AI Tools

Installed:

- ComfyUI Desktop.
- LM Studio.
- Git.
- Python.

Not found:

- Docker Desktop.
- Ollama.
- Conda/Miniconda.
- Normal standalone Node/npm. The visible `node` command points to Codex's internal app runtime and returned access denied.

## ComfyUI Models Found

Important models already present:

- `C:\Users\Admin\ComfyUI\models\unet\qwen_image_edit_2511_fp8mixed.safetensors`
- `C:\Users\Admin\ComfyUI\models\unet\qwen_image_edit_2511_bf16.safetensors`
- `C:\Users\Admin\ComfyUI\models\vae\qwen_image_vae.safetensors`
- `C:\Users\Admin\ComfyUI\models\text_encoders\qwen_2.5_vl_7b_fp8_scaled.safetensors`
- `C:\Users\Admin\ComfyUI\models\loras\Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors`
- `C:\Users\Admin\ComfyUI\models\diffusion_models\flux1-fill-dev.safetensors`
- `C:\Users\Admin\ComfyUI\models\sams\sam_vit_h_4b8939.pth`
- `C:\Users\Admin\ComfyUI\models\sams\sam_vit_l_0b3195.pth`
- `C:\Users\Admin\ComfyUI\models\grounding-dino\groundingdino_swint_ogc.pth`

Missing or empty areas:

- `C:\Users\Admin\ComfyUI\models\upscale_models` is empty.
- `C:\Users\Admin\ComfyUI\models\controlnet` is empty.
- No local Qwen InstantX inpainting ControlNet model was found.

## ComfyUI Custom Nodes

Found:

- `comfyui_controlnet_aux`
- `comfyui_segment_anything`
- `comfyui-idm-vton`
- `comfyui-impact-pack`

This is enough for segmentation experiments and some older VTON tests.

## LM Studio

LM Studio API is active and reports:

- `qwen3-vl-8b-instruct`
- `qwen3-vl-8b-instruct:2`
- `text-embedding-nomic-embed-text-v1.5`

This is useful for person/reference analysis, evidence planning, and evaluator JSON.

## Older Project Material Found

Useful previous folders:

- `C:\Users\Admin\OneDrive\Документы\ComfyUI\COTS\outfit_pipeline`
- `C:\Users\Admin\OneDrive\Документы\ComfyUI\COTS\outfit_transfer_adapter`
- `C:\Users\Admin\OneDrive\Документы\ComfyUI\COTS\qwen_tests`
- `C:\Users\Admin\OneDrive\Рабочий стол\проект\CONTROLLED_AI_STYLING_SYSTEM`
- `C:\Users\Admin\OneDrive\Документы\Велика Ціль`

Useful ideas from old work:

- Keep stylist logic separate from adapter logic.
- Use structured outfit JSON.
- Build visual reference boards.
- Use evidence tiles for details.
- Keep prompt generation inspectable.
- Save every run folder with inputs, prompts, manifests, and outputs.

Main old-work caution:

- The older pipeline appears to have grown complex before the core edit/repair loop was reliable.
- Treat it as a source of parts and lessons, not as the foundation to continue blindly.

## Known Failure From Old Qwen Test

Previous Qwen 2511 test result:

- Qwen 2511 ran successfully.
- It preserved face/background reasonably.
- It captured garment color and silhouette partially.
- It failed to fully replace the old outfit: old top/jeans remained visible.

Interpretation:

- The main bottleneck is not model availability.
- The next problem to solve is edit-region control: masks, local inpainting, and repair passes.

## Recommended Next Milestone

Do not start with wardrobe/catalog or full stylist automation.

Start with:

1. One person image.
2. One manually written outfit package.
3. One Qwen 2511 generation through ComfyUI.
4. One evaluator report through LM Studio.
5. One local repair pass for a specific failed garment/detail.

Success means the system can complete one inspectable run and explain what passed,
what failed, and what the next repair should target.

