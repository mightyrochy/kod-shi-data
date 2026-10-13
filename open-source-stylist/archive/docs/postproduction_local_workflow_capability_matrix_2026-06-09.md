# Local Workflow Capability Matrix

Date: 2026-06-09

Purpose:

Compare currently accessible ComfyUI workflow candidates, but judge them by
postproduction quality/function/system compatibility first.

Local availability is recorded only as an integration fact. It is not the main
reason to choose a tool.

No generation was run. No image was edited.

## Checked Environment

ComfyUI API:

```text
http://127.0.0.1:8000
```

Runtime still points to:

```text
C:\Users\Admin\ComfyUI
```

Shared model paths include:

```text
C:\Users\Admin\ComfyUI\models
C:\Users\Admin\ComfyUI-Shared\models
```

## Local Candidates

Checked workflow files:

```text
C:\Users\Admin\ComfyUI\user\default\workflows\flux_fill_inpaint_cots.json
C:\Users\Admin\ComfyUI-Installs\ComfyUI\ComfyUI\blueprints\Image Edit (Qwen 2511).json
C:\Users\Admin\ComfyUI-Installs\ComfyUI\ComfyUI\blueprints\Image Inpainting (Qwen-image).json
C:\Users\Admin\ComfyUI-Installs\ComfyUI\ComfyUI\blueprints\Image Inpainting (Flux.1 Fill Dev).json
```

Checked model availability:

```text
models\diffusion_models\flux1-fill-dev.safetensors
models\unet\qwen_image_edit_2511_bf16.safetensors
models\unet\qwen_image_edit_2511_fp8mixed.safetensors
models\vae\qwen_image_vae.safetensors
models\text_encoders\qwen_2.5_vl_7b_fp8_scaled.safetensors
models\text_encoders\qwen_3_4b.safetensors
models\text_encoders\clip_l.safetensors
models\text_encoders\t5xxl_fp16.safetensors
models\vae\ae.safetensors
```

Not detected locally:

```text
SDXL inpaint checkpoint
Qwen-Image-InstantX-ControlNet-Inpainting.safetensors
Qwen-Image-Lightning-4steps-V1.0.safetensors
```

Note:

Qwen 2511 Lightning LoRA exists locally under a different filename:

```text
models\loras\Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors
```

## Capability Matrix

| Candidate | Local status | Image input | Mask input | Text instruction | Reference evidence | Required model status | Quality/function fit | System compatibility | Main risk | Recommended role |
|---|---:|---:|---:|---:|---:|---|---|---|---|---|
| Qwen 2511 Image Edit blueprint | Available | Yes | No explicit mask in inspected blueprint | Yes | Yes, up to image1/image2/image3 through `TextEncodeQwenImageEditPlus` | Qwen 2511 + Qwen VAE/text encoder available | Highest for semantic/reference outfit repair | Strong with outfit package, reference board, evaluator/verifier; needs separate locality control | May edit too broadly without mask/crop/composite control | Primary semantic/reference repair candidate |
| FLUX.1 Fill dev blueprint | Available | Yes through subgraph inputs | Yes | Yes | No direct reference input found | FLUX Fill + CLIP/T5 + AE available | High for strict masked inpaint/locality; medium for outfit semantics | Strong with mask builder and protected-region verifier; weak/medium with reference evidence | May not follow outfit reference/details strongly | Primary locality/preservation candidate |
| Existing `flux_fill_inpaint_cots.json` | Available | Yes, includes `LoadImage` | Yes, includes mask input | Yes | No direct reference input found | Same FLUX Fill stack available | Same as FLUX Fill; existing file is convenience only | Good for testing local inpaint path if UI inspection passes | Existing workflow may be example/tutorial-shaped | Concrete FLUX workflow candidate, not chosen merely because it exists |
| Qwen-image inpainting blueprint | Blueprint available | Yes | Yes | Yes | Weak/indirect | Required ControlNet inpainting model not detected | Potentially high if model exists, because it combines Qwen + mask path | Could be strong if dependency is resolved | Currently blocked by missing model file | Park until required model is installed or path is found |
| SDXL inpaint | Not detected | Would be yes | Would be yes | Yes | No direct reference | SDXL inpaint checkpoint not detected | Mature but likely lower outfit/reference quality than Qwen; useful as baseline | Easy to integrate if installed, but weaker strategic fit | Adds another model without clear quality upside | Benchmark/fallback only |

## Detailed Notes

### Qwen 2511 Image Edit Blueprint

Inspected workflow:

```text
Image Edit (Qwen 2511).json
```

Relevant nodes:

```text
UNETLoader
CLIPLoader
TextEncodeQwenImageEditPlus
FluxKontextMultiReferenceLatentMethod
FluxKontextImageScale
VAEEncode
KSampler
VAEDecode
VAELoader
```

Important capability:

`TextEncodeQwenImageEditPlus` exposes:

```text
prompt
image1
image2
image3
vae
```

This is valuable for reference/outfit evidence. It can condition on the base
image and reference board/crops.

Limitation:

The inspected blueprint does not expose a direct edit mask input. That makes it
less suitable for the first locality proof. It may still be the better semantic
repair tool if a local/masked variant is built or if crop-based repair is used.

Verdict:

Strong semantic/reference candidate. Not the cleanest first test for masked
locality.

### FLUX.1 Fill Dev Blueprint

Inspected workflow:

```text
Image Inpainting (Flux.1 Fill Dev).json
```

Relevant nodes:

```text
UNETLoader
DualCLIPLoader
VAELoader
InpaintModelConditioning
DifferentialDiffusion
FluxGuidance
KSampler
VAEDecode
```

Node availability checked through API:

```text
InpaintModelConditioning: OK
DifferentialDiffusion: OK
FluxGuidance: OK
DualCLIPLoader: OK
UNETLoader: OK
VAELoader: OK
KSampler: OK
```

Important capability:

This workflow is explicitly mask-driven through `InpaintModelConditioning`.

Limitation:

No direct reference image/crop input was found. It is more suitable for testing
locality and basic inpainting than exact garment-reference fidelity.

Verdict:

Best first candidate for a locality/preservation proof.

### Existing `flux_fill_inpaint_cots.json`

Inspected workflow:

```text
C:\Users\Admin\ComfyUI\user\default\workflows\flux_fill_inpaint_cots.json
```

Relevant nodes:

```text
LoadImage
UNETLoader
DualCLIPLoader
VAELoader
InpaintModelConditioning
DifferentialDiffusion
FluxGuidance
KSampler
VAEDecode
SaveImage
```

Important capability:

It appears to be a ready FLUX Fill inpaint workflow with image + mask path.

Limitation:

It also contains tutorial/report text, so it should be inspected in UI before
being used as a production-style request template. It does not appear to add
reference-image conditioning beyond text.

Verdict:

Useful concrete local FLUX workflow. Candidate for first locality proof, but not
because it already exists; because it has the explicit mask/inpaint path.

### Qwen-image Inpainting Blueprint

Inspected workflow:

```text
Image Inpainting (Qwen-image).json
```

Relevant nodes:

```text
UNETLoader
CLIPLoader
CLIPTextEncode
ControlNetLoader
ControlNetInpaintingAliMamaApply
ImageToMask
GrowMask
ImageBlur
MaskPreview
SetLatentNoiseMask
VAEEncode
KSampler
VAEDecode
```

Node availability checked through API:

```text
ControlNetInpaintingAliMamaApply: OK
```

Blocking issue:

The workflow references:

```text
Qwen-Image-InstantX-ControlNet-Inpainting.safetensors
```

This file was not found in local model folders.

Verdict:

Interesting future candidate, but not ready for the first proof unless the
missing ControlNet inpainting model is installed or already exists in another
path.

### SDXL Inpaint

No SDXL inpaint checkpoint was found in local `models\checkpoints` or matching
model paths.

Verdict:

Do not include in the first local proof. It would add setup work without clear
benefit over installed Qwen/FLUX.

## Ranking By Function

### Semantic/reference outfit repair

1. Qwen 2511 Image Edit.
2. Qwen-image inpainting if the missing ControlNet model is resolved.
3. FLUX Fill only for simpler text-guided local fill, not exact reference
   fidelity.

### Strict masked locality/preservation

1. FLUX.1 Fill dev.
2. Qwen-image inpainting if the missing ControlNet model is resolved.
3. Qwen 2511 Image Edit only if we add a reliable locality mechanism such as
   crop-mask-composite or a true masked workflow.

### Baseline/fallback

1. SDXL inpaint if installed later.

## Ranking For First Proof

### 1. FLUX.1 Fill Dev / Existing FLUX Fill Workflow

Best for proving:

- mask locality;
- protected-region preservation;
- basic local inpaint behavior;
- old-clothing remnant or local blending repair.

Weak for:

- exact reference-detail fidelity;
- complex outfit logic.

### 2. Qwen 2511 Image Edit

Best for proving:

- reference/outfit evidence use;
- semantic instruction following;
- garment logic/detail edits.

Weak for first masked-locality proof because:

- inspected blueprint does not expose direct mask control.

### 3. Qwen-image Inpainting

Potentially useful because:

- combines Qwen image generation with inpaint/control mask path.

Blocked because:

- required Qwen inpainting ControlNet model is not currently detected.

### 4. SDXL Inpaint

Parked because:

- local model not detected;
- lower strategic fit than Qwen/FLUX.

## Recommended Next Step

First proof should use FLUX Fill only for a narrow locality/preservation test:

```text
Can a local inpaint executor change one masked non-face region while preserving
the rest of the image?
```

This proof should not claim reference-faithful outfit repair.

After that, run a separate Qwen 2511 semantic/reference proof:

```text
Can Qwen 2511 use outfit/reference evidence for a local semantic repair without
changing protected regions?
```

Those are different questions and should be tested separately.
