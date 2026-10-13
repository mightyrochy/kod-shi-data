# E-010 — Garment-faithful try-on (garment fidelity is axis #1)

**Status:** UPDATED 2026-06-16 (owner-directed reprioritisation: garment accuracy > body). Approved
direction; generation engine selected in Phase 0. Execute in a separate session — see `STARTER.md`.
Not yet run.
**Supersedes** the earlier body-first / inpaint+body-control framing of this protocol.
**Companion docs:** `ENGINE_LANDSCAPE.md` (engine survey), `GEN_INSTRUMENTS.md` (generation tools),
`EVAL_INSTRUMENTS.md` (measurement). **Governed by:** METHODOLOGY.md §2; design §5/§7; follows E-009.

---

## 1. Decision history that produced this protocol

1. The earlier FLUX-Fill Phase-0 build (`system/workflows/flux_fill_inpaint.json`) is **text-only**
   (person + mask + text, **no board image**). With our colour-less prompt it invents generic clothes →
   **fails garment fidelity by construction**. **Disqualified** (kept only as a body-only control).
   The engine MUST condition the garment on an **image**, never text.
2. We first reframed toward inpaint + body-control. Then the owner corrected the **priority**:
   **garment accuracy is the product** (showing the SPECIFIC item). Body morphology (the E-009 ~9 %
   hip slim) matters but is **secondary** — a recognisable person in the EXACT outfit beats a perfect
   body in an approximate one.
3. Garment exact-reproduction from a reference is the genuine product frontier: generic VTON
   re-synthesises → detail drift. The fidelity tools **keep the real garment pixels** (warping /
   high-res feature injection).

## 2. Axes, in priority order

1. **Garment fidelity (axis #1, HARD gate).** Per item: "is this the same item?" — measured by the
   `EVAL_INSTRUMENTS` stack (retrieval-rank vs decoys via FashionSigLIP; DISTS; colour hue/chroma +
   palette; silhouette descriptors; OCR for logo/print; Qwen-VL detail checklist; owner per-item verdict).
2. **Identity (axis #2).** ArcFace face cosine ≥ 0.57 and not below baseline; (hair/skin owner-checked).
3. **Body morphology (axis #3, secondary).** `body_pose` skeletal hip/shoulder; protect-by-construction
   (source pixels outside the clothing) + optional DensePose/SMPL-shape. Measured and reported, but it
   does **not** block acceptance unless the body is grossly wrong — the ~9 % slim is polish.

## 3. Generation instruments (see GEN_INSTRUMENTS.md)

Core garment-transfer chosen for detail: **FitDiT** (DiT, high-res garment feature injection, ComfyUI)
primary; **DiffFit / GP-VTON** warping fallback. Plus **per-item high-res reference conditioning** (the
hybrid board's per-item crops, not the 768 tiled board), **high-res single-item local repair** per
garment (design §5), and **OmniTry** for accessories (belt/earrings/shoes). Identity (PuLID/InstantID)
and body (DensePose/SMPL) ride along as secondary.

## 4. Engine selection — Phase 0 (garment-first; see ENGINE_LANDSCAPE.md)

Pick the stack by, in order: (a) **garment exact-fidelity** on our specific items; (b) coverage of
**multi-item + accessories**; (c) 16 GB local feasibility; (d) license (Leffa MIT / OmniTry CC-BY-SA
commercial-OK; CatVTON/IDM-VTON NC = prototype only); identity/body secondary.

Candidate cores: **FitDiT** (detail), **DiffFit/GP-VTON** (warping), **IDM-VTON** (best texture, NC),
**Leffa** (MIT, light) — single-garment, applied **per garment** (blouse → skirt); **OmniTry** for
accessories. **Cloud (FASHN/Kling/GPT-4o)** is the detail ceiling and a legitimate V1 fallback.

Phase 0 procedure: query the live ComfyUI `/object_info`; for the top garment-fidelity candidate
produce ONE output and review at an **owner checkpoint** against the EVAL stack. If no local stack
reproduces our items acceptably → escalate to cloud or a Garments2Look-style fine-tune (rented GPU),
do not force a weak local engine.

## 5. Method (A/B)

| Arm | Path |
|-----|------|
| A — baseline | current full-regen (QIE Lightning, E-009 R1) — approximate garment, ~9 % body slim |
| B — garment-first | FitDiT/warping core (per garment) + per-item high-res refs + single-item local repair + OmniTry accessories |

Fixed: `person_front.png`; `outfit_001`; per-item references from `hybrid_mask_crop` crops (SHA-verified);
seeds [42, 123].

## 6. Acceptance (fixed before results)

- **Garment (axis #1, HARD gate):** for every required item, target ranks top-K in retrieval (vs decoys),
  DISTS/colour/silhouette/detail not worse than A, owner per-item detail verdict **not worse**. This is
  the PASS axis. Calibration set required (see EVAL_INSTRUMENTS).
- **Identity:** face cosine ≥ 0.57 and not below A.
- **Body (secondary):** measured + reported; blocks only if grossly wrong; the ~9 % slim is acceptable
  for V1 unless owner says otherwise. Body refinement is a later lever (DensePose/SMPL or fine-tune).
- No aggregate score; owner verdict per axis is the acceptance.

## 7. Honest unknowns

- Exact-item reproduction (buttons / exact shade / wedge geometry) is the real frontier; even SOTA
  approximates; cloud is the ceiling.
- No single LOCAL open model cleanly covers {multi-item + accessories + exact detail + non-idealised
  body} — likely a small pipeline (FitDiT + local repair + OmniTry) or cloud. This is a kill-criterion check.
- FitDiT/OmniTry exact VRAM + license + whether they handle OUR multi-item outfit must be verified in Phase 0.
- The garment-fidelity instrument itself needs a labelled calibration set before its numbers are trusted.

## 8. Cost

Phase 0 engine selection + 1 test output per candidate: 1–2 sessions. Build EVAL stack (FashionSigLIP +
DISTS + calibration): ~1 session. Phase 1 A/B + measurement: GPU batches. Local repair / OmniTry: +1–2 sessions.

---

## Owner sign-off

- [x] Garment fidelity is axis #1 (HARD gate); identity #2; body #3 (secondary, non-blocking unless gross).
- [x] Generation core = detail-preserving (FitDiT/warping) + per-item high-res + local repair + OmniTry;
      text-only / generic re-synthesis disqualified for garment.
- [x] Engine selected in Phase 0 from ENGINE_LANDSCAPE (garment-first); cloud is a legitimate fallback.
- [x] Garment-fidelity instrument (EVAL_INSTRUMENTS) must be built + calibrated to make axis #1 measurable.

**Signed:** owner, 2026-06-16 (directed this reprioritisation). Execution delegated to a separate session.

---

## Addendum 2026-06-16 — FitDiT execution results + architecture refinement

### Results so far (Arm B = FitDiT, per-garment)
- **Blouse: PASS** (owner "добре") — lemon colour, buttons, silhouette correct. Identity 0.97.
- **Skirt: FAIL** (owner "схожа на штани") — the crop's central front **slit** + FitDiT's Upper/Lower-body-only
  parsing → read as two legs → pants. Deterministic by input, both seeds.
- **Identity preserved 0.97–0.98** across all FitDiT runs — FitDiT only edits the masked garment region
  (face/body untouched) → protect-by-construction works for identity.
- **Garment axis #1 is still owner-eye-only** — FashionSigLIP gate PENDING_CALIBRATION (no labelled set);
  garment verdict = None in manifests.
- **These are SINGLE-garment runs, NOT the full outfit** — blouse run keeps the original jeans; skirt run
  keeps the original sweater. The assembled multi-item outfit is not yet produced.

### Architecture decision: V1 = chained FitDiT on the SOURCE; QIE dropped
QIE's holistic "composer" is **redundant for V1**: the outfit's **layer order is KNOWN a priori** (it is in the
outfit definition / layout — "blouse over skirt, belt over blouse"). We do not need a holistic model to
discover the composition. The V1 garment pipeline is:

```
canvas = source photo (real body, original clothes)
for each garment, bottom-up in the KNOWN layer order:
    M_g = agnostic mask for g  (from FitDiT parsing + the layer graph;
          a higher layer's mask overlaps the lower garment at the seam)
    canvas = FitDiT(canvas, M_g, exact_reference_g)   # only the mask changes; the rest is preserved
+ accessories (belt buckle / earrings / shoes) via OmniTry or targeted inpaint
```
**Layering emerges from pass order + mask overlap** (a later garment's mask covers the lower garment at the
seam → it is drawn on top). Body/face stay source by construction. **QIE/holistic is deferred to V2/V3**, where
the outfit logic is *unknown* (the stylist invents the outfit and how it is worn) and a holistic composer earns
its place. The real hard parts are therefore **mask construction** (peplum extent, belt band, occlusion seams),
**seam blending** (feather), and **FitDiT category limits** (Upper/Lower only; slit skirts; no accessories) —
NOT "obtaining outfit logic".

### What FitDiT already provides (component map)
FitDiT bundles much of the needed machinery: garment feature extractor (`transformer_garm`), **human parsing**
(`parsing_*.onnx` → per-garment regions / agnostic maps), **pose** (`dwpose` + `pose_guider`). FashionSigLIP
(our eval encoder) is also loaded. **Missing / to wire:** the layer-graph + occlusion orchestration (chaining),
**OmniTry** for accessories, the FashionSigLIP **calibration set** + DISTS, and (secondary) SMPL body-shape control.

### Engine comparison (see ENGINE_LANDSCAPE.md addendum)
- **Garment detail (axis #1): FitDiT is the strongest open model** (beats IDM-VTON/CatVTON/Leffa on
  VITON-HD/DressCode) → keep as the per-garment detail core.
- **Multi-item one-pass (our chaining concern): AnyDressing** — parallel multi-garment + **plug-in composable
  with ControlNet/IP-Adapter/LoRA** (a slot for body/pose + face-identity control). Strongest architectural fit
  for our multi-item outfit, but **non-commercial license** (prototype only) and detail-vs-FitDiT unverified.
  Alternatives: OmniVTON++ (training-free, NC), MuGa-VTON.
- **Accessories: OmniTry** (mask-free; jewellery/belts/shoes; CC-BY-SA commercial-OK) — complement, release/VRAM
  unverified. **Skirt slit** is a masking/category issue, not a model choice.
- Commercial-OK local options remain sparse: **Leffa (MIT)**, **OmniTry (CC-BY-SA)**; FitDiT/AnyDressing/
  IDM-VTON/CatVTON are prototype-only or unverified license.

### Open decision (skirt) + next steps
1. **Skirt:** Variant 1 (closed-slit crop → regenerate; loses the slit detail → owner judges) OR Variant 2
   (accept FitDiT slit-skirt limitation). The skirt is one garment in the chain regardless.
2. **Build the chained-FitDiT-on-source pipeline** (skirt → blouse) to verify layering emerges from pass order.
3. **Head-to-head: AnyDressing vs FitDiT** on our items (detail + multi-item) — decides single-model vs chain.
4. **Build + calibrate the garment-fidelity instrument** (FashionSigLIP retrieval-rank + DISTS + labelled set)
   so axis #1 is measurable, not owner-eye-only.
5. Accessories via OmniTry (verify release/VRAM).

### Universal placement (2026-06-16) — applies to ALL elements, not just the skirt
Mask/placement is computed, not hand-tuned: **measure each element's body-relative fraction on its
on-model photo (MediaPipe pose + GroundingDINO/SAM), transfer to the target's pose** — scale-invariant,
per-element anchored (waist/shoulders/ears/feet…), occlusion-subtracted by the layer graph. This is the
universal drape mechanism for every garment AND accessory; full spec + per-element table in
`DRAPE_SYNTHESIS.md`. It is engine-agnostic (feeds FitDiT / OmniTry / warping). Placement (this) and
fidelity (engine) are the two separate axes.

## Addendum 2026-06-18 — measure_on_model implemented + chain verified

**Universal measurement built.** `system/drape.py::measure_on_model(model_photo, prompt, client, anchor, end)`
measures an element's placement on its own on-model photo (MediaPipe pose + GroundingDINO/SAM segmentation)
as **scale-invariant body-relative fractions** (`length_fraction`, `top_offset_frac`, `width_ratio`),
transferable to any target body. `skirt_agnostic_mask` generalised to `agnostic_mask(...)`:
`hem_y = anchor_y + length_fraction·(end_y − anchor_y)`. Skirt measured `length_fraction = 0.917`
(maxi, hem near ankle) — fixes the pixel-ratio undershoot (mid-calf). Owner accepted the re-run length +
topology ("більш менш"); colour (olive vs brown) and silhouette stay on the engine fidelity axis.

**Chained FitDiT on the SOURCE verified** (`proto_chain.py`, skirt → blouse, outfit_001 layer order):
- **Layering emerges from pass order + mask overlap** — the blouse painted last over its native Upper-body
  mask (which already covers torso→hip and overlaps the skirt waist) sits OVER the skirt. No holistic composer
  needed (confirms the V1 "QIE dropped" decision).
- **Identity survives the chain** — ArcFace cosine: skirt-only 0.976, chain final 0.929 (≥ 0.57 threshold).
  Each pass edits only its mask → face/body preserved by construction; chaining costs a small, non-blocking drop.
- **Bug + lesson:** the blouse needs NO mask dilation. The first chain run corrupted the face because
  `_dilate_down` (cv2.dilate, (1,181) kernel, anchor=(0,0)) grew the mask UPWARD into the neck/chin, not
  downward — FitDiT then re-synthesised the lower face. Removed; blouse uses the native mask.
- **Still single-source artifacts:** jeans show below the skirt hem (no bottom-layer cleanup yet); accessories
  (belt/earrings/shoes via OmniTry) not added; garment-fidelity instrument still PENDING_CALIBRATION.

Next (in order): garment-fidelity instrument build+calibration (make axis #1 measurable, not owner-eye-only);
warping (DiffFit/GP-VTON) head-to-head for fidelity; accessories via OmniTry (install/VRAM/license verify).

**Axis #1 first numbers (2026-06-18, `proto_fidelity.py`, ADVISORY — uncalibrated):** rendered skirt + blouse
cropped from the chain final via the per-pass region masks (no ComfyUI), scored vs their reference + the other
outfit items as decoys. Both rank **#1/5** (recognisable as their targets). Blouse DISTS 0.211 / sim 0.925
(≈ calibrated "same garment, other view" 0.21; margin 0.253) — strong. Skirt DISTS 0.319 / sim 0.823 (between
"same" 0.21 and "different" 0.37; margin 0.086 over the belt) — the weaker item, matching the olive-vs-brown +
narrow-silhouette eye verdict → the skirt is the target for warping/fidelity. Still needs a labelled
calibration set before decision-grade.

**Warping head-to-head — arm B (geometric warp, 2026-06-18, `proto_warp.py`):** the cheapest arm —
non-parametric silhouette warp of the REAL brown skirt pixels into the drape mask (exact colour by
construction, pure CPU, no model/ComfyUI). Result: **LOSES to FitDiT.** DISTS 0.41 (FitDiT arm A 0.319),
sim 0.700 (FitDiT 0.823). The naive per-row stretch looks pasted/flat — a boxy slab with a hard horizontal
waist seam, no body contour, no pose shading — and the structural distortion costs more than FitDiT's colour
drift gains. Conclusion: keeping exact pixels via a dumb paste is NOT the win; the "keep pixels" thesis needs
an INTELLIGENT (flow-field + shading-aware) warp = a model. Survey of model-based warp: "DiffFit" is a
diffusion fine-tuning method, not a VTON (doc misnomer); **GP-VTON** (Local-Flow, supports skirts/dresses,
preserves pixels) is NC-licensed + no ComfyUI node + research-grade studio-trained setup (heavy, generalisation
risk); **SAL-VTON** (ComfyUI, GPL) needs a white background + is upper-only-ish (poor fit); **Leffa** (MIT,
flow-field, separates top/bottom) is the best LOCAL model fit if a ComfyUI wrapper exists; cloud (FASHN/Kling)
is the fidelity ceiling. Cheap non-warp alternative for FitDiT's only flaw (colour): reference-image colour
transfer onto FitDiT's well-integrated skirt (keeps shading, corrects hue). Open: model-warp arm needs
ComfyUI + an engine/license decision.

**Warping head-to-head — arm C (Leffa, model-based flow-field, 2026-06-18):** owner chose Leffa (MIT). Installed
official `franciszzj/Leffa` standalone (external dir `C:\Users\Admin\Leffa`, NOT in this repo; runner copied here as
`leffa_skirt_runner.py` for provenance). Install recipe that worked on this Windows box (no MSVC/CUDA toolkit):
dedicated py3.10 venv → torch 2.6.0+cu124 → **prebuilt detectron2** `0.6+fd27788 pt2.6.0cu124 cp310 win` (miropsota
index, no source build) → densepose from `facebookresearch/detectron2` source on PYTHONPATH → diffusers/transformers
(latest, imports OK) → `truststore.inject_into_ssl()` for HF downloads (venv certifi can't verify the chain here) →
trimmed ckpts (DressCode branch only, ~8 GB, skipped the SDXL pose-transfer). Result: **Leffa renders TROUSERS, not
a skirt** — both with its own DressCode `lower_body` agnostic mask AND with our continuous drape mask fed in (the
saved mask confirmed continuous). Cause: Leffa conditions on **densepose IUV**, which encodes the two legs as
separate parts; the flow-field reconstructs the garment along that leg structure → leg-split trousers regardless of
the mask. Colour is browner than FitDiT, but **topology is a hard fail for a skirt** → **disqualified**. General
insight: VTON models hard-conditioned on densepose/parsing (Leffa; likely GP-VTON too) enforce leg topology for the
lower body → a skirt that bridges the legs is structurally hard for them. **FitDiT + our continuous drape mask
remains uniquely suited** for the skirt (its custom IMAGE mask dominates; no per-leg densepose prior).

### Head-to-head verdict (skirt, axis #1)
| Arm | Topology | Colour | DISTS | Verdict |
|-----|----------|--------|-------|---------|
| A — FitDiT (+drape mask) | skirt ✓ | olive drift | 0.319 | **best** |
| B — geometric warp | flat/pasted slab | exact | 0.41 | loses (pasted) |
| C — Leffa (DressCode) | trousers ✗ | browner | n/a | disqualified (topology) |

Neither warp arm beats FitDiT for the skirt. FitDiT stays the skirt engine; its only flaw is colour drift → cheapest
fix = reference-image colour transfer onto FitDiT's skirt (keeps topology+shading, corrects hue); ceiling = cloud.
Warping for the skirt is closed as a negative result.

### CORRECTION + deep investigation (2026-06-18) — "Leffa can't do skirts" was WRONG
Owner challenged the arm-C conclusion. A proper isolation study (one variable at a time) overturns the
"VTON structurally can't do skirts" claim. Scripts: `leffa_skirt_runner.py` (+ `reframe_person.py` in the
external Leffa dir). Tests (DressCode model, seed 42, step 30, scale 2.5):
- **Sanity** (Leffa example tee + example person): PERFECT transfer (colour + print + stripes) → **the install is
  correct**, Leffa transfers garments faithfully.
- **T3** (our clean skirt + a DressCode full-body example person): renders a **proper SKIRT** → **Leffa CAN do
  skirts**. Disproves the "fundamental limitation".
- **T2** (example tee + OUR person): blue + print transferred (slightly blended) → our person is ~usable for upper.
- **T1** (our blouse cut-out + example person): correct DESIGN (peplum/buttons) but washed colour → our garment
  *cut-outs* (styled, not flat-product) degrade fidelity.
- **T4** (clean skirt + our person reframed to DressCode style: segmented, white bg, tight frame): **trousers**
  (colour now correctly brown) → reframing transfers colour but NOT topology.
- **T5** (T4 + our continuous drape mask forcing a skirt silhouette): **trousers** (narrow, matching the mask
  width) → the inpaint mask constrains the REGION but does NOT dictate topology.

**Real root cause:** Leffa conditions topology on the **densepose IUV of the target body**, and that conditioning
**dominates the inpaint mask** (T5 proof). For our in-the-wild person standing legs-together in jeans, the
conditional strongly favours trousers; for an in-distribution DressCode person (studio, dynamic pose, bare legs)
it drapes a skirt (T3). So the failure is **person-distribution + densepose-dominant conditioning**, NOT a
fundamental VTON limit, NOT the install, NOT diffusers (0.31 == 0.38), NOT the mask alone. **Why FitDiT succeeds on
the SAME person:** FitDiT lets the **custom IMAGE mask + garment** dominate topology → it obeys our continuous
drape mask; Leffa lets densepose dominate → legs. That is the true engine difference.

**Fixes, by robustness:** (1) our pipeline → **FitDiT+drape** (robust skirt on our person; already works) — Leffa
isn't worth the fight for the skirt; (2) **cloud** (FASHN/Kling, diverse-data, robust to in-the-wild person +
skirts) = ceiling; (3) Leffa only if the person is brought FULLY in-distribution (studio + skirt-amenable pose +
clean flat-product skirt image without a slit) — reframing alone is insufficient, costly/brittle. Leffa stays
installed (a working local VTON for in-distribution cases).
