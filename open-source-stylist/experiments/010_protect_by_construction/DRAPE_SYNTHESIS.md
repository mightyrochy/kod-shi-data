# Drape synthesis — intelligent garment placement & correspondence (2026-06-16)

Design note for E-010. How to build the "complex mask / worn shape" for ANY garment
automatically, instead of hand-tuning a mask per item. Grounded in the E-010 FitDiT runs.

## 1. Problem (evidenced, not theorised)

Per-item hand-tuning (row-fill, hand trapezoids, manual slit-gap fill) does not scale. And the
skirt run isolated TWO distinct remaining problems with FitDiT + a generic mask:
- **Length** — the auto Lower-body mask runs waist→ankle (the LEG length), not the SKIRT length →
  wrong hem. This is a **placement/mask** problem.
- **Fidelity (<100%)** — FitDiT **re-synthesises** the garment → approximate detail. This is an
  **engine/pixels** problem; the mask cannot fix it.

Also evidenced: topology (pants↔skirt) is driven by the garment **silhouette continuity** (a
through-gap in the crop → pants; a filled silhouette + slit-line → skirt), not by the mask alone.

## 2. Principle

A garment's worn placement is a **function of measurable inputs**, so it should be **computed**:
```
worn_placement(garment, person) = f( garment_proportions , body_landmarks , layer_graph )
```
Nothing here needs hand-drawing — garment proportions come from the reference, body landmarks from
pose/parsing, layering from the outfit definition.

## 3. Framework — 3 reusable artifacts + a synthesizer

| Artifact | Computed | Contents |
|---|---|---|
| **GarmentDescriptor** | once per garment (catalog-time) | category; silhouette type; **length ratio** (h:w); features (slit, neckline, sleeve); continuous-silhouette (interior gaps filled, slit kept as a marked line) |
| **BodyModel** | once per person | pose keypoints + parsing; anchor lines (waist/hip/knee/ankle/shoulder); body scale |
| **DrapeSynthesizer** | per (garment × person) | anchor + **hem = anchor + length_ratio × body_scale** (← fixes length) + silhouette projected on the body + **occlusion-subtraction by layer_graph** → the agnostic mask (and optionally a warped garment) |

This is the "intelligent complex mask": automatic, parameterised by the **actual** garment + body,
occlusion-aware for the chain. It fixes **length, shape, and layering** by construction.

## 4. Levels of realisation

| Level | Solves | Fidelity? | Cost |
|---|---|---|---|
| **Geometric** (pose + proportions + rules) | placement / length / shape / occlusion → a correct mask for FitDiT | NO (FitDiT still re-synthesises) | light, V1 |
| **Warping / correspondence** (TPS / dense flow; DiffFit / GP-VTON) | placement / length / shape **+ real-pixel detail**; mask becomes a byproduct of the warp | **YES** | medium; realised by existing warping VTON engines, not a from-scratch build |
| **3D / SMPL drape** | any pose, full generality | yes | heavy, fragile |

## 5. Mapping the two remaining issues

- **Length** → fixed at the **geometric** level (hem from the garment's length ratio, not the leg).
- **Fidelity** → fixed only at the **warping** level (deform real garment pixels). The mask paradigm
  (FitDiT) cannot close it; warping can, AND it gives correct length/shape at the same time.

So the two problems point in one direction: **garment→body correspondence (warping)** subsumes the
complex-mask problem AND closes fidelity. The geometric synthesizer is the lighter option that fixes
length within FitDiT but leaves fidelity approximate.

## 6. Recommendation — where to start

**Target the warping level; first concrete step = evaluate a warping VTON (DiffFit / GP-VTON) on the
skirt**, because it is the level that addresses **both** remaining issues (length via the garment's own
warped length; fidelity via real pixels) and makes the complex mask a byproduct.

- If warping is viable locally (16 GB, license, our skirt) → it becomes the lower-garment engine;
  the geometric synthesizer is no longer the bottleneck.
- If warping is NOT viable locally → fall back to the **geometric DrapeSynthesizer + FitDiT**: fixes
  length/shape/occlusion now; fidelity stays approximate (a known limit, re-open with warping/cloud).

**Shared foundation regardless of level:** `BodyModel` (pose/landmarks) and `GarmentDescriptor`
(continuous silhouette + proportions + features) are reusable inputs for both FitDiT and warping, and
for the garment-fidelity evaluator. Build these first — they are not wasted on either path.

## 7. Next steps
1. Build `BodyModel` + `GarmentDescriptor` extractors (light, reusable; pose we already have, garment
   silhouette/continuity we prototyped in `proto_filled_skirt.py`).
2. Head-to-head **warping VTON vs FitDiT+geometric-mask** on the skirt → decide the lower-garment engine.
3. Wire the chosen path into the chain (skirt → blouse, occlusion-aware) + accessories (OmniTry).
4. Fidelity remains owner-eye until the FashionSigLIP+DISTS calibration set is built.

*Written 2026-06-16. Companion to protocol.md / GEN_INSTRUMENTS.md / ENGINE_LANDSCAPE.md / EVAL_INSTRUMENTS.md.*
