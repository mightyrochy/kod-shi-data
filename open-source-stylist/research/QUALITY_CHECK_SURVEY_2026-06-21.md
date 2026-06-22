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
