# Postproduction Tool Research

Date: 2026-06-09

Scope:

This is a practical survey of current tools relevant to Open Source Stylist
postproduction. It focuses on tools that can repair a local clothing/accessory
region after a base generation, while preserving identity, body, garment
structure, and background.

This is not a generic image-editing leaderboard. The ranking is specific to our
system:

```text
manual outfit package
-> Qwen 2511 edit through ComfyUI
-> evaluator through LM Studio
-> targeted postproduction repair
-> repeatable run folder
```

## Evaluation Criteria

Postproduction executor candidates are ranked quality-first:

1. Output quality for clothing/accessory repair.
2. Locality: can edit only a mask/local region.
3. Preservation: keeps identity, body outline, background, and global outfit
   structure.
4. Clothing usefulness: handles layer boundaries, garment details, material,
   old-clothing remnants, and small shape/detail repair.
5. Reference use: can use outfit package evidence, reference board, or reference
   crops.
6. System compatibility: can cooperate with evaluator, planner, mask builder,
   references, protected regions, verifier, and run-folder logging.
7. Runtime fit: plausible for the default product budget.
8. Reproducibility: can save inputs, masks, settings, output, and verdict in a
   run folder.
9. Deployment fit: local/open-weight is preferred, but local availability is not
   proof of quality.

Local availability is a practical constraint, not a quality criterion. A tool
being installed locally only means it is easier to test. It does not make it a
better postproduction executor.

## Current Local Baseline

Already detected locally:

- ComfyUI Desktop backend at `http://127.0.0.1:8000`.
- Qwen-Image-Edit-2511 fp8mixed is already the main Try-On Engine.
- Qwen-Image-Edit-2511 bf16 is also available.
- FLUX.1 Fill dev.
- Qwen VAE.
- Qwen text encoders.
- Qwen Lightning LoRA.
- SAM.
- GroundingDINO.
- Existing workflow:
  `C:\Users\Admin\ComfyUI\user\default\workflows\flux_fill_inpaint_cots.json`.
- LM Studio at `http://127.0.0.1:1234`.

## Ranking Summary

### Tier 1 - Best Functional Fit For The Desired System

These are ranked highest because their function matches the desired
postproduction system: local semantic image repair with reference evidence,
mask/protected-region control, and strong preservation.

#### 1. Qwen-Image-Edit-2511

Role:

- established primary Try-On Engine for base generation, using
  `qwen_image_edit_2511_fp8mixed`;
- candidate local/masked semantic editor;
- candidate reference-aware outfit repair tool.

Why it matters:

- It is already the best observed base-generation direction for this project.
- The fp8mixed 2511 model is already used as the main Try-On Engine, so the
  system should keep that role stable.
- It understands image editing and outfit-level instructions better than
  classic inpaint-only models.
- It can use image references with text instructions, which matches outfit
  package + reference board workflows.

Risks:

- Mask behavior may be indirect or workflow-dependent.
- It may regenerate too much of the image if the workflow is not truly local.
- It can smooth or simplify textures.
- VRAM/runtime cost is higher than small inpaint tools.

Use first for:

- semantic clothing repair where instruction/reference understanding matters:
  layer boundary, missing local garment element, local outfit logic.

System compatibility:

- Strong with outfit package/reference evidence.
- Strong with evaluator/planner/verifier.
- Needs a reliable local-region mechanism: direct mask workflow, crop-based
  repair, or external compositing.
- Postproduction use must not blur the architectural distinction between base
  try-on generation and targeted local repair.

Sources:

- ComfyUI Qwen-Image-Edit-2511 workflow docs:
  https://docs.comfy.org/tutorials/image/qwen/qwen-image-edit-2511
- Qwen Image Edit model card:
  https://huggingface.co/qwen/qwen-image-edit

#### 2. FLUX.1 Fill dev

Role:

- primary local inpainting/outpainting candidate;
- likely best first test for pure masked fill behavior;
- useful for old-clothing remnants, local blending, background-safe masked
  repair, and simple structure completion.

Why it matters:

- FLUX.1 Fill is specifically an inpainting/outpainting model.
- It accepts conditioning image and mask.
- Its function maps cleanly to locality and protected-region testing.

Risks:

- It may not use outfit reference crops as strongly as Qwen.
- It may preserve image style but fail exact garment logic.
- It may need crop-and-stitch/composite handling to avoid whole-image
  degradation.

Use first for:

- locality proof;
- old clothing remnant removal;
- local masked repair where the instruction is simple and reference fidelity is
  less important.

System compatibility:

- Strong with mask builder and protected-region verifier.
- Medium with outfit/reference evidence because direct reference conditioning is
  weak or absent in the inspected workflow.
- Best as a local inpaint executor, not as the full semantic repair layer.

Sources:

- Black Forest Labs FLUX Fill docs:
  https://github.com/black-forest-labs/flux/blob/main/docs/fill.md
- ComfyUI FLUX.1 Fill dev docs:
  https://docs.comfy.org/tutorials/flux/flux-1-fill-dev
- BFL FLUX Tools API docs:
  https://docs.bfl.ai/flux_tools

#### 3. Mask Builder Stack: GroundingDINO + SAM / SAM2 / Fashion Parser

Role:

- not a repair executor;
- required support layer for reliable postproduction.

Why it matters:

- Bad masks make good models fail.
- Our previous color-repair failure was mostly mask/target process failure.
- For clothing repair, mask quality is as important as the generative model.

Recommended V1:

- manual masks for first controlled tests;
- SAM for object/part masks;
- GroundingDINO + SAM for text-located targets;
- fashion/human parsing for body/clothing classes.

Risks:

- SAM can segment visually coherent regions, not necessarily semantic garment
  classes.
- GroundingDINO can locate objects by text, but garment subparts may be
  ambiguous.
- Human/fashion parsers are useful but add another model family to manage.

Sources:

- SAM2 official Meta page:
  https://ai.meta.com/research/sam2/
- SAM2 paper:
  https://arxiv.org/abs/2408.00714
- GroundingDINO GitHub:
  https://github.com/IDEA-Research/GroundingDINO
- GroundingDINO paper:
  https://arxiv.org/abs/2303.05499
- FASHN human parser:
  https://github.com/fashn-AI/fashn-human-parser

#### 4. LM Studio VLM Evaluator / Verifier

Role:

- evaluator before repair;
- verifier after repair.

Why it matters:

- The system needs automatic under-the-hood decisions.
- Human validation is only an R&D safeguard.
- A VLM can fill structured JSON checks: target improved, identity preserved,
  background preserved, artifacts introduced.

Recommended starting model:

- Qwen2.5-VL-7B through LM Studio, because it is locally available in LM Studio
  ecosystem and supports structured visual understanding/localization.

Risks:

- VLMs can miss subtle garment fidelity issues.
- They need strict schema prompts and before/after comparisons.
- They should not be the only verifier; use image diff/protected-region checks
  too.

Sources:

- LM Studio Qwen2.5-VL page:
  https://lmstudio.ai/models/qwen/qwen2.5-vl-7b/
- Hugging Face Transformers Qwen2.5-VL docs:
  https://huggingface.co/docs/transformers/v4.50.0/model_doc/qwen2_5_vl
- InternVL3 overview:
  https://internvl.github.io/blog/2025-04-11-InternVL-3.0/

### Tier 2 - Strong Candidates, But Not First Integration

These are relevant, but should not replace the current stack until the local
Qwen/FLUX/SAM/LM Studio loop is proven.

#### 5. SDXL Inpainting

Role:

- reliable mature baseline for masked inpaint.

Why it matters:

- Stable, widely supported, easy to compare.
- Good control over mask/denoise/crop workflows.
- Could be useful as a conservative fallback.

Risks:

- Older visual quality compared with Qwen/FLUX.
- Weaker outfit-reference understanding.
- More likely to create generic garment details.

Source:

- SDXL Inpainting model card:
  https://huggingface.co/diffusers/stable-diffusion-xl-1.0-inpainting-0.1

#### 6. BrushNet

Role:

- plug-and-play image inpainting model for diffusion pipelines.

Why it matters:

- Designed to improve masked-image feature conditioning.
- Research-backed and open implementation.

Risks:

- Integration cost.
- Likely less direct ComfyUI/Desktop fit than already installed FLUX/Qwen.
- Not obviously better for fashion-specific reference fidelity without testing.

Sources:

- BrushNet GitHub:
  https://github.com/TencentARC/BrushNet
- BrushNet paper:
  https://arxiv.org/abs/2403.06976

#### 7. PowerPaint

Role:

- versatile inpainting: object insertion, object removal, shape-guided
  inpainting, outpainting.

Why it matters:

- Good conceptual fit for object-level local repair.
- Useful if we need one model for remove/insert/outpaint tasks.

Risks:

- Extra integration cost.
- May overlap with FLUX Fill without clear benefit for our first loop.

Source:

- PowerPaint GitHub:
  https://github.com/open-mmlab/PowerPaint

#### 8. HD-Painter

Role:

- high-resolution prompt-faithful inpainting.

Why it matters:

- Specifically targets higher-resolution inpainting and prompt fidelity.
- Could matter later for final-quality garment/detail repair.

Risks:

- Integration cost and possible dependency burden.
- Not needed before core local repair loop works.

Sources:

- HD-Painter GitHub:
  https://github.com/Picsart-AI-Research/HD-Painter
- HD-Painter paper:
  https://arxiv.org/abs/2312.14091

### Tier 3 - Reference-Guided / Specialized Tools

These are conceptually interesting for exact garment/detail transfer, but should
not be first-line V1 tools.

#### 9. Paint-by-Example

Role:

- exemplar/reference-guided image editing.

Why it matters:

- Matches the concept of "repair this region using this reference crop."

Risks:

- Older generation stack.
- Likely weaker than current Qwen/FLUX for photoreal outfit integration.
- Could be useful as a reference for design, not immediate integration.

Sources:

- Paint-by-Example GitHub:
  https://github.com/Fantasy-Studio/Paint-by-Example
- Paper:
  https://www.microsoft.com/en-us/research/wp-content/uploads/2023/06/Paint-by-Example.pdf

#### 10. AnyDoor / Object Insertion Family

Role:

- reference object placement into a scene.

Why it matters:

- Similar to garment/accessory transfer at the object level.

Risks:

- More object insertion than subtle outfit postproduction.
- Could disturb body/garment fit.
- Not the current core problem.

Source:

- AnyDoor project page:
  https://damo-vilab.github.io/AnyDoor-Page/

#### 11. CorrFill / TransRef / Reference-Guided Inpainting Research

Role:

- reference-based inpainting with stronger correspondence or embedding.

Why it matters:

- The exact weakness we care about is reference faithfulness.

Risks:

- Research/integration burden.
- Not yet clearly practical in ComfyUI.
- Better as a later research branch.

Sources:

- CorrFill GitHub:
  https://github.com/khliu0000/CorrFill
- TransRef paper:
  https://www.sciencedirect.com/science/article/pii/S0925231225004217

### Tier 4 - Cloud/API Benchmarks, Not Product Core

These may be useful for comparison but do not fit the current local/open-source
strategy as default executors.

#### 12. FLUX.1 Kontext

Role:

- high-quality image editing with context/reference understanding.

Why it matters:

- Strong benchmark for instruction-following image edits.
- Useful to understand what "good" can look like.

Risks:

- API/proprietary availability depending on variant.
- Not currently part of local ComfyUI stack.
- Product strategy is local/open-source first.

Sources:

- FLUX.1 Kontext paper:
  https://arxiv.org/abs/2506.15742
- BFL Kontext image editing docs:
  https://docs.us.bfl.ai/kontext/kontext_image_editing
- FLUX.1 Kontext dev Hugging Face:
  https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev

#### 13. Gemini 2.5 Flash Image / Nano Banana

Role:

- external benchmark for strong image editing and consistency.

Why it matters:

- Known for image generation/editing and consistency.

Risks:

- Cloud/API dependency.
- Not open/local.
- Harder to integrate into offline repeatable ComfyUI pipeline.

Source:

- Google Developers Blog:
  https://developers.googleblog.com/introducing-gemini-2-5-flash-image/

#### 14. OpenAI Image Edits

Role:

- API-based image editing with optional masks.

Why it matters:

- Useful as a cloud benchmark or fallback prototype.

Risks:

- Cloud/API dependency.
- Not local/open-source.
- Full-frame changes may need careful verification.

Sources:

- OpenAI Images API reference:
  https://platform.openai.com/docs/api-reference/images/overview
- OpenAI image generation guide:
  https://platform.openai.com/docs/guides/image-generation

#### 15. Adobe Firefly Fill

Role:

- commercial generative fill/inpaint reference.

Why it matters:

- Useful quality benchmark for product expectations.

Risks:

- Cloud/commercial.
- Not aligned with local open-source core.

Source:

- Adobe Firefly Fill Image API tutorial:
  https://developer.adobe.com/firefly-services/docs/firefly-api/guides/how-tos/firefly-fill-image-api-tutorial

## What Not To Prioritize Now

### Classic object removal tools such as LaMa / IOPaint

Useful for:

- removing unwanted objects;
- background cleanup.

Weak for:

- reference-faithful garment detail;
- outfit layer logic;
- semantic clothing repair.

Source:

- IOPaint GitHub:
  https://github.com/Sanster/IOPaint

### VTON-specific systems

Examples:

- IDM-VTON;
- CatVTON;
- FASHN VTON.

Reason:

- The user already tested VTON variants and found Qwen better for this use case.
- Postproduction should repair a usable base, not restart the try-on model
  comparison.

## Quality-First System Design

### V1 Core Toolchain

```text
Evaluator/verifier:
  LM Studio + Qwen2.5-VL or similar VLM

Mask builder:
  manual masks for R&D
  -> SAM / GroundingDINO + SAM
  -> later fashion/human parsing

Core repair executor candidates:
  1. Qwen-Image-Edit-2511 for semantic/reference-aware local repair, while
     keeping qwen_image_edit_2511_fp8mixed as the base Try-On Engine
  2. FLUX.1 Fill dev for strict masked inpaint/locality

Support executor:
  deterministic cleanup with Pillow/OpenCV

Logger:
  run-folder repair_request + masks + prompts + settings + outputs + verdict
```

### First Real Research Question

Do not ask:

```text
Does an inpaint workflow inpaint?
```

Ask:

```text
Which local executor is most suitable for outfit postproduction under our
constraints?
```

Evaluate candidates on:

- locality;
- preservation of protected regions;
- instruction following;
- reference/outfit evidence use;
- clothing/detail usefulness;
- runtime;
- failure modes.

### First Tool Comparison To Run Later

Before generation, inspect available workflows and write a comparison matrix
with quality/function/system-compatibility as the primary lens:

```text
Qwen 2511 masked/local edit
FLUX.1 Fill dev
SDXL inpaint baseline if easily available
```

Then run the same repair request through one or two candidates only if both are
available and the request is ready.

## Current Recommendation

For this project, the best next technical path is:

1. Keep `qwen_image_edit_2511_fp8mixed` as the main Try-On Engine.
2. Treat Qwen 2511 as the strongest semantic/reference repair candidate only if
   a reliable locality mechanism is defined.
3. Treat FLUX.1 Fill as the strongest strict-mask/locality candidate.
4. Treat mask building as a first-class subsystem.
5. Use LM Studio VLM as evaluator/verifier, supported by before/after and
   protected-region checks.
6. Keep BrushNet, PowerPaint, HD-Painter, Paint-by-Example, AnyDoor, and
   FLUX Kontext as later research/benchmark options.

The first proof should compare capabilities, not assume a workflow is good
because it already exists locally.
