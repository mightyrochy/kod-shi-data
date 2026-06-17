# Drape synthesis — universal garment placement & correspondence (2026-06-16)

Design note for E-010. How to place **any** outfit element (tops, bottoms, dresses, AND
accessories) on **any** body **automatically** — not hand-tuned per item. Grounded in the
E-010 FitDiT runs. Companion to protocol.md / GEN_INSTRUMENTS.md / ENGINE_LANDSCAPE.md / EVAL_INSTRUMENTS.md.

## 1. Problem (evidenced)

- Per-item hand-tuning (row-fill, hand trapezoids, manual slit-fill) does not scale.
- Two distinct axes (do not conflate): **placement/length** (the mask) and **fidelity** (the engine).
- A garment crop has **no absolute scale** — the same item shot zoomed-in vs out has the same
  proportions but different pixels, so **pixel proportions cannot give real placement** (our
  pixel-ratio length heuristic undershot a maxi skirt to mid-calf).
- **Topology** matters: a through-gap in the silhouette (slit cut to background) → FitDiT renders
  pants; a continuous silhouette with the slit kept as a line → a skirt. Generalises: every
  element's silhouette must be represented **as worn** (continuous where continuous), not as a
  cut-out artifact.

## 2. Universal principle

```
placement(element, person) = a BODY-RELATIVE measurement taken on the element's on-model photo,
                             transferred to the TARGET person's pose.
```
Body-relative fractions are **scale-invariant** (independent of photo zoom). This holds for **every
element** — each anchored to its own body landmarks. No per-item hardcoding.

## 3. Per-element anchoring (the generalisation — NOT skirt-specific)

| Element class | Anchor landmark(s) | Extent measured on-model (fraction) | Engine |
|---|---|---|---|
| Top (shirt/blouse/sweater/jacket) | shoulders + neckline | shoulder→hem as fraction of shoulder→hip (cropped/regular/tunic/longline); sleeves follow arms | FitDiT Upper-body |
| Skirt | waist/hip line | hip→hem as fraction of hip→ankle (mini/knee/midi/maxi); **continuous column** silhouette | FitDiT Lower-body |
| Pants | waist/hip line | hip→hem fraction of hip→ankle; legs follow leg keypoints | FitDiT Lower-body |
| Dress | shoulders | shoulder→hem fraction to ankle | FitDiT Dresses |
| Belt | waist line | thin band over the top layer | OmniTry / inpaint |
| Shoes | ankles / feet | foot region | OmniTry |
| Earrings | ears (face landmarks) | ear region | OmniTry / detail inpaint |
| Bag | hand / shoulder | held/strap region | OmniTry |

Every row uses the SAME mechanism (on-model fraction → target landmark); only the anchor + body
span differ per class. Body landmarks for non-garment anchors (ears, feet) come from the same pose
+ face model.

## 4. The mechanism — catalog-time + runtime

**CATALOG-TIME (once per element) → `GarmentDescriptor`:**
1. **MediaPipe Pose (+ face)** on the on-model photo → model landmarks.
2. **GroundingDINO + SAM** segment the element on the model → its region.
3. Compute **body-relative descriptor**: anchor, `length_fraction = (hem−anchor)/(anchor−end span)`,
   `width_ratio = element_width/body_width`, top-anchor (waist vs hip), layer role.
4. Build the **continuous silhouette** of the isolated crop (interior gaps filled, slit/opening kept
   as a line) for the engine's garment input.

**RUNTIME (per element × person) → image:**
5. **MediaPipe Pose (+ face)** on the target → target landmarks/spans.
6. **DrapeSynthesizer**: for each element, `hem = anchor + length_fraction × body_span`,
   `width = width_ratio × body_width`, build a continuous silhouette mask, then
   **occlusion-subtract** the regions covered by higher layers per the **layer graph**.
7. Pose image for the engine (FitDiTMaskGenerator pose output / DWPose).
8. **Engine pass**: FitDiT (garments) or OmniTry (accessories), into the synthesized mask, with the
   continuous crop.
9. **Chain** in layer order on the running canvas (skirt → top → belt → accessories); layering
   emerges from pass order + mask overlap.

## 5. Descriptors

- **GarmentDescriptor** (per element): `element_class`, `anchor`, `length_fraction`, `width_ratio`,
  `silhouette`, `continuous_crop`, `features` (slit/neckline/closure/print), `layer_role`.
- **BodyModel** (per person): full pose keypoints + **face landmarks** (ears/feet anchors), body
  spans (shoulder→hip, hip→ankle, hip width, shoulder width).

## 6. Where placement data comes from (priority)

1. **On-model photo** (primary, automatic, exact) — measure body-relative fractions via pose +
   segmentation. Real catalogs ship on-model photos; outfit_001 has them.
2. **Catalog metadata** (`GarmentItem.length/dimensions`) — when present.
3. **VLM class** (Qwen-VL: length/fit class → landmark table) — fallback when no on-model photo.

## 7. Fidelity is a SEPARATE axis (all elements)

The placement mechanism is **engine-agnostic** — it feeds FitDiT (re-synthesis, approximate detail),
a **warping** engine (real-pixel detail), or OmniTry. Fidelity (exact item) is measured by
`EVAL_INSTRUMENTS` per element. Levels: **geometric** (placement only) → **warping** (placement +
real-pixel fidelity, mask becomes a byproduct) → **3D/SMPL** (general, heavy).

## 8. Evidenced from E-010 (skirt, but the lessons are general)

- Topology fixed by a **continuous silhouette** (slit as a line, not a through-gap) — applies to any
  element with openings/cut-outs.
- Length/placement must be **body-relative measured**, not pixel-ratio guessed (the latter undershot).
- Identity/body preserved by construction when the engine edits only the masked region.

## 9. Next steps
1. `measure_on_model(model_photo, element_class)` in `system/drape.py` → body-relative fractions
   (pose + GroundingDINO/SAM), per element class. Replace the pixel-ratio placeholder.
2. Generalise `DrapeSynthesizer` per element class (anchors/spans table above) + occlusion by layer graph.
3. Re-run the skirt on the **measured** length; then the chain (skirt → top → belt → accessories via OmniTry).
4. Fidelity: warping head-to-head (DiffFit/GP-VTON) + build the FashionSigLIP/DISTS calibration set.

*Written 2026-06-16. Universal across elements; on-model body-relative fraction transfer is the core,
scale-invariant placement mechanism.*
