# How the field checks generated-image fidelity / defects — broad survey (2026-06-21, pass 1)

Owner-directed: we were looking too narrowly (bespoke metrics per defect). Survey how the broader field
detects whether a generated image faithfully matches a reference and where it is defective — CV and
beyond. Lens: local on 16 GB, reference = the garment image, defects = missing slit, wrong layering (tuck),
texture/structure drift. **Pass 1 — web-search session limit hit (resets ~01:40 Kyiv) and arXiv PDFs
exceed the fetch size cap; this is the strong-signal first pass, more to mine after reset.**

## 1. The field's verdict: our metric class is known-insufficient
2025 VTON-evaluation work states plainly that pixel metrics (SSIM/PSNR) and distribution metrics
(FID/KID/LPIPS) — and by extension our global FashionSigLIP-sim / DISTS / CIEDE2000 — are **insufficient**:
they "reflect overall realism or low-level similarity and do NOT assess whether the specific reference
garment is faithfully transferred and plausibly worn"; they "overlook instance-level errors such as
distorted textures or incorrect patterns." That is exactly our missing-slit / half-tuck blind spot. So the
narrowness was real, and the field has moved on from these metrics.

## 2. Reference-based defect detection — the established taxonomy (from industrial anomaly detection)
(`github.com/m-3lab/awesome-industrial-anomaly-detection`.) These compare a test image to reference/normal
and LOCALISE defects — our exact shape of problem:
| Category | Representatives | Idea |
|---|---|---|
| **Memory-bank / feature-matching** | **PatchCore**, PNI | store reference patch features; test-patch distance to nearest reference patch = anomaly, localised |
| Teacher–student | Reverse Distillation | anomaly = teacher/student feature discrepancy |
| Normalizing flows | CFlow-AD, PyramidFlow | model normal feature distribution; deviation = anomaly |
| Reconstruction | DRAEM, RealNet | reconstruct from "normal"; reconstruction error = anomaly |
| **VLM zero-shot** | **AnomalyCLIP**, AnoVL | CLIP prompts localise anomalies, no training |
| **MLLM-based** | **AnomalyGPT**, AD-Copilot | a multimodal LLM REASONS about the anomaly (visual+text) |
The memory-bank / feature-matching / flow families "excel at comparing test garments to reference images …
ideal for quality control where reference standards exist."

## 3. VTON-specific evaluation (2025) — two threads
- **VLM/MLLM as judge with structured criteria.** Proposed protocol scores: **GTC** Garment-Transfer
  Consistency, **TAC** Textual-Attribute Consistency, **FPC** Fit-Pose Coherence. A VLM is asked, per
  criterion, whether the reference garment is faithfully transferred and plausibly worn.
- **Decomposed garment-preservation** into **Size-Fitness** + **Texture-Fidelity** with perceptual-aligned
  metrics; correspondence-alignment (CORAL) for try-on; benchmarks OpenVTON-Bench, VTBench, VQualA-2025
  (LMMs reasoning about visual-quality differences).

## 4. The two strongest fits for us — and they answer "CV vs something else"
### A. CV: PatchCore-style feature anomaly detection (the RIGHT form of what we attempted)
Our DINOv2 aligned-grid was on the right track but confounded by framing/alignment (we saw it). The
established fix is **PatchCore**: a **memory bank** of the reference garment's patch features (DINOv2/any
pretrained encoder) + **nearest-neighbour distance** in feature space (NO grid alignment) → a per-patch
anomaly map that LOCALISES where the output garment diverges (a missing slit = a blob of high-distance
patches, wherever it sits). Universal, reference-based, local-runnable (DINOv2 features + a NN index).
This is the principled, general version of our structure gate.

### B. "Something else": VLM-as-JUDGE (local VLM, we already have one)
A multimodal LLM is asked structured yes/no questions against the reference + layout: "Is the blouse tucked
in or hanging over the skirt? Does the skirt have a front slit? Is each garment the same as its reference?"
It REASONS about structure AND layering (the tuck — which no metric caught) and generalises to arbitrary
defects. We have a **local VLM (LM Studio)**. NOTE the tension: METHODOLOGY §1 said "VLM output is never
decision-grade." The field now uses VLMs as evaluators — so reframe the VLM not as the final verdict but as
a **defect FLAGGER** that triggers a repair or an owner look (observations that ROUTE work, exactly the
allowed role). This is the most universal checker available to us.

## 5. Recommendation (pass 1)
Pursue BOTH, complementary:
1. **PatchCore + DINOv2** as the localized structural/appearance anomaly check (memory bank of reference
   patches, NN distance, anomaly map) — replaces the brittle aligned-grid; validate on the slit case.
2. **Local VLM-as-judge** with GTC/TAC/FPC-style criteria — catches layering/tuck and arbitrary defects;
   used as a flagger (routes repair/owner), per METHODOLOGY's observation role.
Both are local-runnable. Pass 2 (after the search limit resets) should mine: PatchCore-for-fashion specifics,
AnomalyGPT/AnomalyCLIP details, the exact VTON VLM-eval prompts, and dense-correspondence (DIFT/SD-DINO/CORAL).

## PASS 2 (limits reset) — the CV answer is named, and the VLM criteria are concrete

### CV: **AnomalyDINO** (WACV 2025, arXiv 2405.14529) — exactly the right tool, training-free
This is the principled, validated form of what we hand-rolled:
- **Patch-level deep nearest-neighbour** with **DINOv2** patch features (we already have DINOv2 loaded).
- **Memory bank** of the reference garment's patches + **nearest-neighbour distance via Faiss** — NO grid
  alignment (this fixes the framing/alignment confound that broke our aligned-grid version).
- Gives BOTH an image-level score (anomaly = "mean of top 1%" of patch distances) AND **pixel-level
  localisation** (bilinear-Gaussian upsampling) → a heat-map of WHERE the output garment diverges (the
  missing slit lights up wherever it is).
- **Training-free, few-shot** (a single reference garment is enough). Directly implementable locally.
This replaces our brittle `structure.py` with the established method. Related: AnomalyCLIP (ICLR 2024,
object-agnostic zero-shot prompts), CLIP-DINOv2 fusion, "Foundation-Model-Based Industrial Defect
Detection" survey (arXiv 2502.19106).

### Dense correspondence (alternative / complement)
DIFT (emergent diffusion-feature correspondence, training-free) and **SD-DINO** ("A Tale of Two Features",
NeurIPS 23): DINOv2 gives sparse accurate matches, Stable-Diffusion features add spatial density; fused +
nearest-neighbour for zero-shot part matching. Heavier than AnomalyDINO; keep as a fallback.

### VLM-as-judge — concrete criteria that catch OUR defects (incl. the tuck)
The field's VTON VLM rubrics name exactly our blind spots:
- GTC / TAC / FPC (Garment-Transfer / Textual-Attribute / Fit-Pose Consistency).
- A 5-dim set: Background Consistency, Person Identity & Body Consistency, **Texture Fidelity**, **Shape
  Preservation (geometric correctness)**, Overall Realism.
- Garment-transfer priorities: correct placement, **sleeve & hem length**, collar/neckline, pattern
  orientation; drape/physical realism; lighting; source integrity.
**"hem length / placement"** is the half-tuck; **"shape preservation / geometric correctness"** is the
missing slit — both are standard VLM-judge criteria. Field impls use GPT-4o; we use the local LM Studio
VLM as a **flagger**. Note "When Rubrics Fail: Error Enumeration as Reward" (arXiv 2603.05659): for VTON,
asking the model to ENUMERATE errors beats fixed rubrics — a good local-VLM prompt pattern.

## Sharpened recommendation
1. **Replace `structure.py` with an AnomalyDINO-style check** — DINOv2 patch features + NN memory bank of
   the reference garment + top-1% anomaly score + localisation map. Universal, training-free, no alignment.
   Validate on the slit case (no-slit should anomaly-score high, slit low).
2. **Add a local VLM-as-judge flagger** — error-enumeration prompt against the reference + layout
   ("list anything wrong: hem/tuck, missing slit, wrong placement, …"). Routes repair/owner (observation
   role, METHODOLOGY-compatible). Catches layering the metric can't.
Both local. Together: AnomalyDINO localises structural/appearance anomalies; the VLM reasons about layering
and arbitrary defects. That is the breadth we were missing.
