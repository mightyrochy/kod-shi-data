# ComfyUI Update Safety Snapshot

Date: 2026-06-09

Purpose:

Record the currently detected ComfyUI setup before any Comfy Desktop update or
migration. This is a safety snapshot only. No update was run.

## Detected Comfy Paths

Likely active ComfyUI workspace:

```text
C:\Users\Admin\ComfyUI
```

Related paths:

```text
C:\Users\Admin\ComfyUI-Shared
C:\Users\Admin\AppData\Local\Programs\ComfyUI
C:\Users\Admin\OneDrive\Документы\ComfyUI
```

`C:\Users\Admin\AppData\Local\Programs\ComfyUI` appears to contain the Comfy
Desktop application binaries.

`C:\Users\Admin\ComfyUI` contains the working ComfyUI data/runtime folders:

```text
.venv
custom_nodes
input
models
output
temp
user
```

## Existing Workflows

Detected workflow files:

```text
C:\Users\Admin\ComfyUI\user\default\workflows\flux_fill_inpaint_cots.json
C:\Users\Admin\ComfyUI\user\default\workflows\vton.json
```

`flux_fill_inpaint_cots.json` may be useful for the first masked local
generative edit proof.

## Custom Nodes

Detected custom node folders:

```text
C:\Users\Admin\ComfyUI\custom_nodes\.disabled
C:\Users\Admin\ComfyUI\custom_nodes\comfyui-idm-vton
C:\Users\Admin\ComfyUI\custom_nodes\comfyui-impact-pack
C:\Users\Admin\ComfyUI\custom_nodes\comfyui_controlnet_aux
C:\Users\Admin\ComfyUI\custom_nodes\comfyui_segment_anything
```

## Key Model Folders

Detected model folders include:

```text
models\diffusion_models
models\unet
models\vae
models\loras
models\text_encoders
models\sams
models\grounding-dino
```

Detected key files:

```text
models\diffusion_models\flux1-fill-dev.safetensors
models\diffusion_models\qwen_image_edit_2509_fp8_e4m3fn.safetensors
models\unet\qwen_image_edit_2511_bf16.safetensors
models\unet\qwen_image_edit_2511_fp8mixed.safetensors
models\vae\ae.safetensors
models\vae\qwen_image_vae.safetensors
models\loras\Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors
models\loras\Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors
models\text_encoders\clip_l.safetensors
models\text_encoders\qwen_2.5_vl_7b_fp8_scaled.safetensors
models\text_encoders\qwen_3_4b.safetensors
models\text_encoders\t5xxl_fp16.safetensors
models\sams\sam_vit_h_4b8939.pth
models\sams\sam_vit_l_0b3195.pth
models\grounding-dino\GroundingDINO_SwinT_OGC.cfg.py
models\grounding-dino\groundingdino_swint_ogc.pth
```

## Safety Notes

Do not update or migrate blindly if the updater intends to overwrite:

- `C:\Users\Admin\ComfyUI\.venv`
- `C:\Users\Admin\ComfyUI\custom_nodes`
- `C:\Users\Admin\ComfyUI\models`
- `C:\Users\Admin\ComfyUI\user\default\workflows`
- `C:\Users\Admin\ComfyUI\user\default\comfy.settings.json`

Before accepting migration/update, confirm whether Comfy Desktop will:

- reuse `C:\Users\Admin\ComfyUI`;
- copy assets into a new workspace;
- overwrite the existing workspace;
- change Python dependencies in `.venv`;
- change custom node versions;
- keep model paths intact.

## Recommended Update Approach

Preferred safe path:

1. Keep `Local` selected.
2. Disable `Express Install` unless the next screen clearly shows it will not
   overwrite the existing working setup.
3. Use migration only if it points to the expected workspace and preserves the
   existing models/workflows/settings.
4. After any update, verify:
   - ComfyUI starts;
   - `flux_fill_inpaint_cots.json` opens;
   - Qwen 2511 models are visible;
   - FLUX Fill model is visible;
   - SAM and GroundingDINO nodes/models are visible;
   - generation still writes to the expected output folder.

## Current Verdict

The existing environment appears valuable and should be treated as working
state. The update can be attempted only with clear migration behavior and a
post-update verification checklist.

## Post-Migration Check

After migration, Comfy Desktop showed an instance named `ComfyUI` and its
console prompt was:

```text
C:\Users\Admin\ComfyUI-Installs\ComfyUI
```

Local API check at `http://127.0.0.1:8000/system_stats` confirmed the running
backend still uses the original working folders:

```text
--base-directory C:\Users\Admin\ComfyUI
--user-directory C:\Users\Admin\ComfyUI\user
--database-url sqlite:///C:\Users\Admin\ComfyUI\user\comfyui.db
--extra-model-paths-config C:\Users\Admin\AppData\Roaming\Comfy Desktop\shared_model_paths.yaml
--input-directory C:\Users\Admin\ComfyUI\input
--output-directory C:\Users\Admin\ComfyUI\output
--port 8000
```

Detected runtime:

```text
ComfyUI version: 0.24.1
Frontend package: 1.44.19
Workflow templates: 0.9.98
Python: 3.12.11
PyTorch: 2.10.0+cu130
GPU: NVIDIA GeForce RTX 4090 Laptop GPU
```

Interpretation:

The Desktop instance is a launcher-managed entry, while the backend still points
to the existing `C:\Users\Admin\ComfyUI` workspace. This is good. Do not press
`Desktop Update Ready` until the post-migration model/workflow checks are done.

## Post-Restart Check

After the user pressed `Restart`, the local API at
`http://127.0.0.1:8000/system_stats` still responds.

The backend still uses:

```text
--base-directory C:\Users\Admin\ComfyUI
--user-directory C:\Users\Admin\ComfyUI\user
--input-directory C:\Users\Admin\ComfyUI\input
--output-directory C:\Users\Admin\ComfyUI\output
--extra-model-paths-config C:\Users\Admin\AppData\Roaming\Comfy Desktop\shared_model_paths.yaml
```

`shared_model_paths.yaml` includes:

```text
C:\Users\Admin\ComfyUI\models
C:\Users\Admin\ComfyUI-Shared\models
```

Existing workflows are still present:

```text
C:\Users\Admin\ComfyUI\user\default\workflows\flux_fill_inpaint_cots.json
C:\Users\Admin\ComfyUI\user\default\workflows\vton.json
```

Post-restart verdict:

The migration/restart preserved the key workspace paths. The next check should
be inside ComfyUI itself: open the inpaint workflow or blueprint and confirm the
required models/nodes are selectable.
