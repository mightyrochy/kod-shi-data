# Postproduction Strategy

Postproduction is a general repair layer, not a hand-tuned fix for one outfit.

The goal is to improve a single strong base generation with cheaper local
operations whenever possible.

Do not assume the product will generate 3-5 full Qwen candidates by default.
That is a research mode, not the default runtime path.

## Core Principle

Do not repair everything, and do not regenerate everything.

First decide:

```text
Is this failure repairable locally, or should the base generation be rejected?
```

Reject or regenerate when:

- identity is damaged;
- body anatomy is broken;
- garment fit is physically implausible;
- outfit structure is wrong at a large scale;
- the wrong main garment was generated;
- background/camera is badly changed.

Repair locally when:

- color/tone is off;
- a small detail is missing;
- an accessory is slightly wrong;
- a layer edge is too visible or not visible enough;
- old clothing remains in a small region;
- texture is simplified but the shape is correct.

## Failure Taxonomy

This taxonomy is provisional. A failure is only "repairable" if the
postproduction system has a module that can fix it without damaging more
important qualities such as identity, body anatomy, garment fit, or outfit
structure.

### 1. Layer Visibility Error

Examples:

- top hem should cover part of the skirt but does not;
- belt should be partial but becomes dominant;
- jacket should be open but becomes closed;
- blouse should be untucked but becomes tucked.

Repair type:

- local inpainting around the layer boundary;
- mask must include both overlapping garments;
- preserve body outline and adjacent garment silhouette.

### 2. Garment Shape Error

Examples:

- skirt silhouette changes from straight to flared;
- sleeve volume disappears;
- collar/neckline changes;
- shoe wedge becomes stiletto.

Repair type:

- usually hard;
- try local repair only for small shape errors;
- reject/regenerate if the main silhouette is wrong.

### 3. Color Or Tone Mismatch

Examples:

- generated garment has wrong hue or saturation;
- color varies too much between front and side views.

Repair type:

- mask-based color correction;
- histogram matching;
- low-denoise local image edit.

This is usually more repairable than shape or identity.

### 4. Texture Or Detail Loss

Examples:

- fabric texture becomes flat;
- buttons disappear;
- buckle is simplified;
- earring ridges are lost;
- shoe material texture disappears.

Repair type:

- local inpainting with detail crop/reference;
- deterministic sharpening/upscale only after semantic pass;
- reject if the missing detail changes the garment identity.

### 5. Accessory Scale Or Placement Error

Examples:

- earrings too large;
- belt too high;
- bag appears on wrong side;
- necklace appears when not requested.

Repair type:

- local inpainting;
- remove or resize only if the surrounding body/garment area stays stable.

### 6. Old Clothing Remnant

Examples:

- original jeans visible under skirt;
- socks remain with sandals;
- old sweater edge remains under blouse.

Repair type:

- local inpainting around remnant;
- if large region remains, reject/regenerate.

### 7. Identity Or Body Damage

Examples:

- face changes;
- hair changes strongly;
- glasses removed when they should remain;
- body proportions change unnaturally;
- hands/feet become broken.

Repair type:

- usually reject/regenerate;
- avoid face repair as a default because it can change identity more.

### 8. Background Damage

Examples:

- room changes;
- doors/walls/floor warp;
- camera crop changes unexpectedly.

Repair type:

- local background repair if small;
- reject/regenerate if global.

## Repair Policy

For each generated candidate:

1. Score hard-to-repair areas first:
   - identity;
   - body anatomy;
   - garment fit;
   - outfit structure;
   - main garment shapes.
2. If any hard-to-repair area fails badly, reject the candidate.
3. If the base passes, list repairable failures.
4. Choose one repair target at a time.
5. Use the smallest mask that includes enough context.
6. Re-evaluate after each repair.

## Default Runtime Flow

The product default should be:

```text
1. Generate one base image with Qwen.
2. Evaluate hard-to-repair qualities.
3. If hard failure: regenerate once with targeted prompt/workflow adjustment.
4. If base is usable: create repair plan.
5. Run one local repair pass.
6. Re-evaluate.
7. Stop, accept, or run one more local repair only if risk is low.
```

Multi-candidate generation is allowed only in research mode or when the user
explicitly asks for options.

## Postproduction System Shape

Inputs:

- source person image;
- generated candidate;
- outfit package;
- reference board or item references;
- original prompt/settings;
- evaluator findings.

Outputs:

- repaired image;
- repair plan JSON;
- repair mask(s);
- repair prompt(s);
- repair settings;
- evaluation after repair.

Modules:

### 1. Evaluator

Purpose:

- decide whether the base is usable;
- identify hard failures;
- identify local repair targets.

This can start manual, then become VLM-assisted through LM Studio.

### 2. Mask Planner

Purpose:

- choose the region to repair;
- keep the mask as small as possible while including enough context.

Possible tools:

- manual mask first;
- SAM/GroundingDINO later;
- human parsing later if needed.

### 3. Deterministic Color Repair

Purpose:

- adjust hue/tone/saturation inside a mask without changing structure.

Use for:

- color mismatch;
- front/side color mismatch;
- local material tone correction.

### 4. Local Inpainting Repair

Purpose:

- fix local structure/detail without regenerating the whole image.

Use for:

- old clothing remnants;
- layer boundary errors;
- missing buttons/buckles/straps;
- accessory placement/detail issues.

### 5. Reference-Guided Detail Repair

Purpose:

- restore a detail from a crop/reference image.

Use for:

- shoe texture;
- earring ridges;
- buttons;
- belt buckle;
- fabric texture.

### 6. Final Detail/Upscale

Purpose:

- improve final image quality only after semantic checks pass.

Do not upscale before evaluation, because it can make wrong details look more
finished.

## Budget Policy

Default budget per user request:

```text
1 base Qwen generation
1 evaluation
0-2 local repair passes
1 final evaluation
```

Regenerate only if the base has a hard failure:

- identity failure;
- broken anatomy;
- unusable garment fit;
- wrong main outfit structure;
- severe old clothing remnants;
- severe background/camera damage.

Do not spend full Qwen passes on repairable color/detail issues by default.

## First Practical Implementation

The first implementation should define the postproduction system contract before
trying to repair a specific image.

After that, it should produce a structured repair plan:

```json
{
  "candidate": "candidate_01.png",
  "base_verdict": "usable_for_repair",
  "reject_reasons": [],
  "repair_targets": [
    {
      "type": "layer_visibility_error",
      "region": "waist_layer_boundary",
      "priority": 1,
      "repair_method": "local_inpaint",
      "risk": "medium"
    }
  ]
}
```

The belt issue in `runs/000001` is only one example of
`layer_visibility_error`.
