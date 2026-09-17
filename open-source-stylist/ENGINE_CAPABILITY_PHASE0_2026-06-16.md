# Engine Capability Phase 0

Date: 2026-06-16  
Verifier: `system/engine_capability_phase0.py`  
ComfyUI endpoint: `http://127.0.0.1:8000/object_info`  
Node count: 1034

## Purpose

Engine selection is now gated by support for all three required channels:

1. garment/reference image conditioning;
2. masked edit / inpaint;
3. body/pose control.

Text-only image editing is disqualified for the product visualization path. A candidate
engine does not enter Phase 1 unless `/object_info` proves the necessary nodes and local
weights are present.

## Current Result

No current candidate passes Phase 0 in the local ComfyUI environment.

```text
python system/engine_capability_phase0.py --comfyui http://127.0.0.1:8000
```

### qwen_image_edit_2511_local: FAIL

Pass:

- Qwen Image Edit 2511 weights are visible:
  - `qwen_image_edit_2511_bf16.safetensors`
  - `qwen_image_edit_2511_fp8mixed.safetensors`
- `TextEncodeQwenImageEditPlus` exposes optional image inputs:
  - `image1`
  - `image2`
  - `image3`
- `QwenImageDiffsynthControlnet` has the right kind of signature:
  - required `image`
  - optional `mask`

Fail:

- `ModelPatchLoader.name` has 0 options.
- Therefore no usable local Qwen control/model patch weight is currently visible.

Interpretation:

Qwen has garment-image conditioning, and there is a possible masked/control node shape,
but the local environment does not yet prove a working combined path:

```text
garment image + mask + body/pose control
```

### flux_fill_local: FAIL

Pass:

- `flux1-fill-dev.safetensors` is visible in `UNETLoader.unet_name`.
- Local masked-edit primitives exist:
  - `InpaintModelConditioning`
  - `VAEEncodeForInpaint`
  - `ConditioningSetMask`
- Pose/depth preprocessors exist:
  - `OpenposePreprocessor`
  - `DensePosePreprocessor`
  - `DepthAnythingV2Preprocessor`

Fail:

- `ControlNetLoader.control_net_name` has 0 options.
- `CLIPVisionLoader.clip_name` has 0 options.
- The only obvious IP-Adapter node found is `ImpactIPAdapterApplySEGS`, but it requires
  an `IPADAPTER_PIPE`; the local loader/weights for that pipe are not proven by
  `/object_info`.

Interpretation:

Local FLUX is the strongest direction for masked edit because `flux1-fill-dev` is
installed, but it does not yet prove the full triad. It needs local body/pose ControlNet
weights and a real garment-image adapter path visible in `/object_info`.

### bfl_partner_api_flux: FAIL for local-open product constraint

Pass:

- `FluxVTONode` is a BFL API node with `person` + `garment`.
- `FluxProFillNode` is a BFL API node with `image` + `mask`.

Fail:

- These are partner/API nodes, not local open-source inference.
- No BFL API node in the current `/object_info` exposes body/pose control input.

Interpretation:

BFL API nodes can be useful for capability comparison, but they do not satisfy the
local-open constraint and do not currently prove all three required channels together.

## Phase 0 Pass Rule

A candidate engine passes only if all are true:

```text
garment_image_conditioning == true
masked_edit == true
body_pose_control == true
local_weights_visible == true
non_text_only == true
```

The first passing candidate then enters Phase 1, where it must run a tiny non-text-only
proof:

```text
person image + garment image + mask + pose/body control
-> output image
```

Phase 1 is still not a quality benchmark. It only proves the graph executes and all
channels are actually consumed.

## Immediate Actions

1. For FLUX local:
   - install or expose FLUX-compatible pose/body ControlNet weights;
   - install or expose a real FLUX-compatible image adapter / reference conditioning path;
   - rerun `system/engine_capability_phase0.py`.
2. For Qwen local:
   - locate/install Qwen model patch/control weights compatible with
     `QwenImageDiffsynthControlnet`;
   - prove the graph can combine image references, mask and control image;
   - rerun Phase 0.
3. Do not run text-only Fill/Inpaint as evidence for product suitability.
4. Do not promote API-only BFL nodes unless the local-open constraint is explicitly changed.

## Architectural Implication

The engine bench-off should move behind this gate. Sampler, cfg, steps and prompt wording
are secondary. The primary question is now:

> Which engine can accept concrete garment visual evidence, edit only the intended region,
> and obey body/pose control in the same local workflow?

Until at least one engine passes Phase 0, further try-on quality experiments risk tuning
the wrong abstraction.
