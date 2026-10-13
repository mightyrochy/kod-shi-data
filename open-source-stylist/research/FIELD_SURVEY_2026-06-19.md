# Field survey — image generation, editing, VTON, fashion AI, tooling (broad scan, 2026-06-19)

A broad scan of the field **beyond the project's current stack**, per owner request: "everything about
image generation, style and fashion, AI tools, research — not only what we already use." Goal: surface
options/ideas we have NOT considered. Each item tagged with **[relevance]** to this project. Companion to
`DEEP_RESEARCH_2026-06-19.md` (which is the focused mechanism/architecture analysis); this file is the
wide net. Sources inline. Status: research notes, not decisions (METHODOLOGY §1 — Observations).

---

## 1. Foundation image-generation models (2026), local-16 GB lens

| Model | Type / license | 16 GB local? | Note | [relevance] |
|---|---|---|---|---|
| **Qwen-Image / -2.0 / -2512** (Alibaba) | DiT flow-match, **Apache-2.0** | fp8 yes | our spine's base family; bilingual text, photoreal; QIE-2511 is the edit variant | **HIGH — current spine** |
| **FLUX.1 [dev]** + **Kontext [dev]** | DiT, **non-commercial dev** | fp8 ~16 GB; GGUF Q8→12 GB | Kontext = multimodal **instruction editing**, runs on 16 GB | HIGH — edit alt / repair |
| **FLUX.1 Fill [dev]** | inpaint, NC | yes (we use it) | our skin/repair inpaint executor | HIGH — in use |
| **HiDream-I1** | DiT, open | full ~20 GB; **fp8/nf4 ~16 GB** | strong open T2I; HiDream-E1 = its instruction-edit | MED — bench candidate |
| **SANA** (NVIDIA, linear-attention DiT) | open | **0.6B <1 s on 16 GB laptop**, 4K | efficiency king; deep-compression autoencoder | MED — drafts/speed |
| **Z-Image-Turbo** | open, distilled | yes, very fast | speed/cost king for high-volume | MED — drafts |
| **Hunyuan-Image-3** (Tencent) | open | heavy | open quality leader | LOW — VRAM |
| **SDXL / SD3.5** | open | yes | mature LoRA/ControlNet ecosystem; the assembly base (ENGINE_LANDSCAPE Family 5) | MED — control assembly |
| **Seedream 4.5/5.0** (ByteDance) | **closed/cloud** | — | photoreal, rivals frontier; **"Universal Reference" = character/object consistency WITHOUT fine-tune/LoRA** | NOTE — identity-consistency pattern; cloud ceiling |

**Takeaways we hadn't logged:** (a) **fp8/GGUF/nf4 quantization** makes nearly every modern DiT fit 16 GB
— VRAM is rarely the blocker now, quality-at-quant is the question. (b) **SANA / Z-Image** are real fast
draft engines (P5 cheap-drafts). (c) **Seedream's "Universal Reference"** (identity/object consistency
without LoRA) is the exact capability our identity-preservation needs — a pattern to watch even though
it's cloud.

## 2. Unified instruction-editing & understanding-generation models (2026)

The hot frontier: **one model that both understands and edits**. Could in principle do person-analysis +
try-on in a single model.

- **OmniGen2** (open): instruction-aligned multimodal gen; **GenEval 0.95** > UniWorld-V1 0.84 > BAGEL 0.88.
  Strong on compositional prompts. arXiv 2506.18871.
- **BAGEL**, **Step1X-Edit** (full-DiT fine-tune), **Emu-Edit**, **Query-Kontext** (2509.26641), **Skywork
  UniPic 2.0** (Kontext + online RL, 2509.04548), **MammothModa2** (AR+diffusion unified, 2511.18262).
- **ICEdit** — MoE layers inside LoRA → **lightweight** instruction editing (cheap to train/run).
- **UniWorld-V1** — open, inherits ImgEdit-E1, trained on 700K ImgEdit subset.
- Datasets/benchmarks: **ImgEdit / ImgEditBench** (NeurIPS 2025, PKU), **X2Edit** (self-constructed
  arbitrary-instruction data). Region-aware mask-free local editing (2604.23763).

**[relevance] MED-HIGH:** a unified open editor (OmniGen2 / Step1X-Edit / FLUX-Kontext-dev) is a credible
**alternative spine or repair engine** to QIE-2511 — worth a bench row. ICEdit's MoE-in-LoRA is a cheap
fine-tune pattern for an outfit-edit LoRA. The unified understanding+generation direction could later
collapse our 3-subsystem split.

## 3. Frontier closed models (the quality ceiling / fallback)

- **Nano Banana Pro** (Google, Gemini-image): **#1 globally**; 4K; micro-detail (skin/fabric/light) "nearly
  indistinguishable from photos". Native VTON in Google Shopping.
- **Seedream 5.0** (ByteDance): search-augmented, "Universal Reference" consistency.
- **GPT Image 2** (OpenAI): reasoning-driven editing; faithful text/logo reproduction.
- Compare hubs: artificialanalysis.ai/image, Atlas Cloud 2026 benchmark, WaveSpeed.

**[relevance]:** the **cloud ceiling** (design sanctions it for the full hard case / V3). Nano Banana
Pro's native VTON + photoreal fabric is the bar local must approach; GPT-image's logo/text fidelity is
the detail ceiling. Use as the upper anchor in any bench, and as the immediate full-outfit fallback.

**Sources (§1-3):** siliconflow/bentoml/pixazo open-model guides 2026 · SANA https://nvlabs.github.io/Sana/ ·
HiDream ComfyUI https://comfyui-wiki.com/en/tutorial/advanced/image/hidream/i1-t2i · OmniGen2
https://arxiv.org/abs/2506.18871 · ImgEdit https://github.com/PKU-YuanGroup/ImgEdit · UniPic2
https://arxiv.org/pdf/2509.04548 · leaderboards https://artificialanalysis.ai/image/explore ·
Atlas 2026 benchmark (GPT-Image-2 / Nano-Banana-Pro / Seedream-5).

---

## 4. Virtual try-on frontier beyond our stack (2026) — directions we under-weighted

### 4.1 MASK-FREE VTON is the big 2026 trend (directly sidesteps OUR failure)
The agnostic-mask requirement is exactly what broke our skirt (incorrect mask → hallucination,
DEEP_RESEARCH §1.3). A whole 2026 line removes the mask:
- **OmniDiT** — one mask-free DiT unifying model-based VTON + model-free VTON + try-off, 380k pairs.
- **JCo-MVTON** (2508.17614) — jointly-controllable multi-modal DiT, **mask-free**.
- **OutfitAnyone** — ultra-high-quality, any clothing / any person.
- **OmniTry** — mask-free anything (but 28 GB).
**[relevance] HIGH:** mask-free methods avoid the agnostic-mask-hallucination class entirely. If we keep
a dedicated VTON anywhere, prefer **mask-free** over agnostic-mask (CatVTON/Leffa/IDM-VTON). A real
direction we had not logged.

### 4.2 Pose-robust & unified VTON+try-off
- **Voost** (2508.04825) — single DiT, **bidirectional try-on AND try-off**, robust across poses /
  garments / backgrounds / lighting. Already in design sources; now confirmed as a top pose-robust option.
- **CatV2TON** — image **and video** try-on, single DiT, temporal concat.
- **TED-VITON / ITVTON / Dress-ED (instruction) / Tstars-Tryon 1.0** — DiT+flow-matching VTON family.
- Warping-free via modified attention is now the norm; multi-view from a single frontal (WACV 2026).

### 4.3 Multi-garment / coordinated outfit (OUR core gap)
- **MuGa-VTON** (2508.08488) — multi-garment via DiT + prompt customization: coordinated **upper+lower**
  in one model — the exact "coordinated outfit" gap the survey says single-garment methods can't do.
- **MV-VTON** (multi-view), **AnyDressing** (parallel multi-garment, NC).
**[relevance] HIGH:** MuGa-VTON / AnyDressing are the *multi-garment-native* candidates vs our
chain-of-single-garment plan. A bench row.

### 4.4 Virtual TRY-OFF — a tool we hadn't considered for building clean references
**Try-off = reconstruct the canonical (flat) garment FROM a worn/on-model photo.** TryOffDiff
(2411.18350), **MGT** (multi-garment try-off, 2504.13078), Voost/OmniDiT (bidirectional), "What Matters
in Try-Off" (Dual-UNet, ICPR 2026). **[relevance] MED-HIGH:** this is a *better* way to build the
**GarmentEvidencePack / canonical front** (IMPLEMENTATION_BLUEPRINT §5) from a model-worn product photo
than segmentation — it removes the model and recovers a clean, frontal, deformation-free garment. Directly
useful for §6a garment isolation and for our own on-model crops. `awesome-virtual-try-off` (rizavelioglu).

### 4.5 Body-shape / occlusion robustness (the rejected-defect axis)
- **PROMO** (2603.11675) — *the* long-skirt answer: DensePose distorts on loose garments → EOMT +
  iterative training → occlusion-robust pose/shape; preserves the **real (non-idealised) figure**. No code.
- **Depth-map conditioning** (Sci. Reports 2025, s41598-025-18107-6) — spatial awareness for occlusion +
  alignment; a lever **beyond densepose** we hadn't listed.
- **SMPL + OpenPose shape guidance** to replicate exact body shape across body types; **ClothWild**
  (weak-sup 2D-cloth-seg + densepose loss) for clothed-human reconstruction.
**[relevance]:** body preservation under loose garments is a *named open problem*; the robust answers are
no-code (PROMO) or heavy (SMPL); **depth-conditioning** is the cheapest unconsidered lever to test.

**Sources (§4):** Awesome-Try-On-Models https://github.com/Zheng-Chong/Awesome-Try-On-Models · Voost
https://arxiv.org/abs/2508.04825 · OmniDiT / JCo-MVTON (2508.17614) · MuGa-VTON
https://arxiv.org/abs/2508.08488 · TryOffDiff https://arxiv.org/abs/2411.18350 · MGT (2504.13078) ·
awesome-virtual-try-off https://github.com/rizavelioglu/awesome-virtual-try-off · PROMO
https://arxiv.org/abs/2603.11675 · OutfitAnyone https://arxiv.org/abs/2407.16224 · Inverse-VTON (ICLR 2026).

---

## 5. Human / body / garment perception & 3D tooling (infrastructure beyond our SCHP/DWPose/MediaPipe)

### 5.1 Sapiens / Sapiens2 (Meta) — SOTA human perception, but license-blocked for our product
- **Sapiens** (ECCV 2024, 2408.12569): one human foundation model for **pose + body-part segmentation
  (parsing) + depth + surface-normal**, native 1K, trained on 300M human images; beats prior SOTA on all
  four. **Sapiens2** (2026): 1B images, 0.4B–5B params, +pointmap +albedo, 4K; Sapiens2-5B > DINOv3-7B.
- **[relevance] HIGH but BLOCKED:** Sapiens is *the* best replacement for our SCHP parser + DWPose +
  MediaPipe + a densepose alternative (one model, all four) — but **its licence forbids biometric/deepfake
  use** (IMPLEMENTATION_BLUEPRINT §3.3), which is exactly identity-preserving generation. So: usable for
  *research/prototype* parsing/depth, **not shippable** in the product. Real tension to flag; for product,
  stay on SCHP/DWPose/MediaPipe or find a permissive parser.

### 5.2 3D garment reconstruction / sewing patterns / physical drape (the principled body+fit answer)
A whole paradigm we list but don't use (ENGINE_LANDSCAPE Family 6), now more accessible:
- **NGL-Prompter** (2602.20700, **training-free**): single image → VLM identifies garments → GarmentCode
  params → 2D **sewing pattern** → 3D garment → **cloth sim (CLO3D/ContourCraft)** → draped reconstruction.
- **Dress-1-to-3** (2502.03449): single image → sewing pattern → **differentiable physics** sim → drape on
  posed human → animatable 3D rest shape.
- **AIpparel** (2412.03937, multimodal digital-garment foundation), **GarmentCrafter**, **GarmentCode**,
  curation: `Awesome-3D-Garments`.
- **[relevance] MED (long-term):** this is the *principled* answer to "exact body shape + physically
  correct drape + occlusion" — body is exact because it's 3D; garments drape by simulation, not guesswork.
  Heavy/research-grade for V1, but the right endgame for fit fidelity, and NGL-Prompter (training-free,
  VLM-driven) is the most adoptable entry. Worth a spike, not a V1 dependency.

### 5.3 Depth / normal conditioning — the cheap unconsidered body/drape lever
- **Depth Anything (v2)** (2401.10891) — robust monocular depth, beats MiDaS; **Depth Pro** (Apple,
  2410.02073) sharp metric depth <1 s; **Marigold** (diffusion depth/normal); ControlNet **depth/normal**;
  unified conditioning **UniCon / OmniControlNet**; "editing models are strong dense perceivers"
  (Edit2Perceive 2511.18673).
- **[relevance] MED-HIGH:** depth/normal maps as ControlNet conditioning pin **3D body structure + garment
  drape under clothing** without densepose/SMPL — the cheapest lever for the body-preservation defect and
  for occlusion robustness (Batch-2 depth finding). A concrete, light experiment vs the heavy SMPL path.

**Sources (§5):** Sapiens https://arxiv.org/abs/2408.12569 · Sapiens2
https://www.marktechpost.com/2026/04/27/meta-ai-releases-sapiens2-... · repo
https://github.com/facebookresearch/sapiens · NGL-Prompter https://arxiv.org/abs/2602.20700 ·
Dress-1-to-3 https://dress-1-to-3.github.io/ · AIpparel https://arxiv.org/abs/2412.03937 ·
Awesome-3D-Garments https://github.com/Shanthika/Awesome-3D-Garments · Depth Anything
https://arxiv.org/abs/2401.10891 · Depth Pro https://arxiv.org/abs/2410.02073.

---

## 6. Fashion-AI stack — recommendation, compatibility, fashion LLMs, design (the V2/V3 product side)

### 6.1 Outfit recommendation & compatibility (validates + sharpens the V2 Stylist)
- **Agentic** is the modern pattern: **AMMR** (Agentic Mixed-Modality Refinement) = multimodal encoders +
  **agentic LLM planner** + **dynamic retrieval**, constraint-aware; "Agentic Personalized Fashion
  Recommendation in the Age of Generative AI" (2508.02342, already in CONCEPT_REVIEW).
- **Mixed-modality refinement** = combine an **image anchor + textual constraints** → *exactly* our input
  (photo + short request). Named as the critical real-world capability.
- Compatibility learning: multimodal fusion + Bayesian Personalized Ranking on +/- outfit pairs;
  **Hybrid-Hierarchical Fashion Graph Attention Net** (2508.11105); **History-aware Transformers**
  (2407.00289); LLM+KG+RAG outfit Q&A; **Diffusion for generative outfit recommendation** (2402.17279).
- Documented limits to avoid: over-reliance on purchase history, item-not-outfit focus, weak trend
  adaptation. **[relevance] HIGH (V2):** confirms the blueprint's planner + per-slot retrieval +
  constraint-solver; upgrade the *plan* step to an **agentic planner + dynamic retrieval** loop; the input
  is the named "mixed-modality (image anchor + text)" case.

### 6.2 Fashion multimodal LLMs (could upgrade our person/garment semantics)
- **FashionGPT / Fashion-GPT** — fashion-tuned LVLM (understanding + retrieval integration).
- **AIpparel** (120K garments; text+image+**sewing-pattern** annotations; SOTA text→garment, image→garment;
  interactive garment editing) — bridges 2D understanding ↔ the 3D-garment paradigm (§5.2).
- **VLG / Vision-Language-Garment** (synthesize garments from text+image); **GarmentSketch** dataset;
  garment-attribute manipulation; **BridgeDiff** (try-off: human obs → flat garment).
- **[relevance] MED:** a fashion-tuned VLM beats generic Qwen3-VL for the §6 garment checklist + §6a
  attribute extraction; AIpparel is the most complete garment-foundation candidate (but heavy). For V1,
  generic Qwen3-VL is fine; note FashionGPT-class as the upgrade path.

### 6.3 Generative fashion design / virtual photoshoot (adjacent; competitor + validation)
- Textile/print generation (seamless tileable print-res); **Textile-IR** physics-aware fashion CAD
  (2601.02792); **Style3D** pattern-making; knitted-textile generative design.
- **On-model imagery** (Vue.ai): on-model product photos at ~1/4 cost, 5× speed — the commercial form of
  our visualization subsystem; AI trend-forecasting (Heuritech, Style3D, 6–24-mo).
- Commercial AI stylists (The New Black, Alta, Stylegen, Glance AI…); AI-fashion-design market ≈ **$450 M
  (2026)**. **[relevance] LOW-MED:** adjacent; on-model-imagery tools are the closest commercial analog to
  our exact-visualization goal (validation of demand + the bar).

**Sources (§6):** Agentic fashion rec https://arxiv.org/abs/2508.02342 · Fashion-graph-attn
https://arxiv.org/abs/2508.11105 · History-aware https://arxiv.org/abs/2407.00289 · generative outfit rec
https://arxiv.org/abs/2402.17279 · FashionGPT (Springer 978-3-031-72344-5_21) · AIpparel
https://georgenakayama.github.io/AIpparel/ · VLG https://arxiv.org/abs/2506.05210 · Textile-IR
https://arxiv.org/abs/2601.02792 · Vue.ai on-model · Heuritech trend-forecasting.

---

## 7. Controllable / identity conditioning, evaluation, efficiency (levers we have but haven't wired)

### 7.1 Identity & subject conditioning (lock the face on an editing spine — axis #2)
- **PuLID** (insightface + Eva-CLIP face embed; "pure & lightning ID"); **InstantID** (zero-shot ID from
  ONE ref, ControlNet+IP-Adapter IdentityNet, keeps text-editability); **IP-Adapter / IP-Adapter-FaceID**;
  **InfiniteYou** (2503.16418, identity-preserving recrafting); **OminiControl** (unified subject+spatial
  control, +0.1% params, base preserved). FLUX integrations: **FLUX-Kontext-PuLID**, **FLUX-PuLID via
  nunchaku** (SVDQuant → 16 GB).
- **[relevance] HIGH:** these are the concrete tools to **pin identity** if the QIE/editing spine drifts
  (design P1, ENGINE_LANDSCAPE Family 5). We have them in the landscape but never wired one. FLUX-PuLID-
  nunchaku fits 16 GB. A real, scoped experiment for the identity axis.

### 7.2 Human-preference / alignment reward models (augment, don't replace, the owner)
- **ImageReward** (137 k expert comparisons), **PickScore** (Pick-a-Pic), **HPSv2.1/HPSv3**, **MPS**
  (multi-dimensional), **VQAScore** ("Does this figure show {text}?" via a VQA model), **GenEval**
  (compositional).
- **[relevance] MED:** good for ranking *drafts* (P5) and general realism/prompt-alignment, and **VQAScore**
  is a clean **item-presence** check (≈ our VLM presence gate). **Caveat:** they score general human
  preference / prompt-alignment, NOT garment-SKU identity — so they **complement** DISTS+retrieval-rank+
  owner, never replace them (METHODOLOGY: instruments + owner). A cheap evaluation augmentation worth adding.

### 7.3 Efficiency — quantization makes "heavy" models 16 GB-reachable
- Quant: **GGUF Q4_K > NF4** at equal size; **FP8 PTQ** near-lossless; **SVDQuant/nunchaku** (absorb
  outliers → FLUX-class + PuLID on 16 GB); FP4 DiT (HQ-DiT, FP4DiT); "FP8 quality ceiling at INT8/GGUF for
  consumer GPUs" (Ideogram-4, 2606.12280). Distill: SDXL-Turbo, **LCM**, **Lightning**, **DMD**.
- **[relevance] MED:** confirms our QIE-fp8 + Lightning path is standard, and — combined with §13 (local
  QIE LoRA from ~6 GB) — means **VRAM is rarely the real blocker**: FLUX-Kontext, fine-tuned QIE,
  PuLID-FLUX, even multi-garment DiTs are reachable at fp8/SVDQuant on the 16 GB 4090. The blocker is
  **quality-at-quant** and **engineering**, not VRAM. This reframes the "16 GB constraint" the whole
  project assumes.

## 8. Synthesis — what this broad scan genuinely adds (actionable, not in the repo before)

Ranked by leverage for THIS project; all are Observations to protocol, not decisions:
1. **Mask-free VTON exists and sidesteps OUR exact failure.** If a dedicated VTON is used at all, prefer
   **mask-free** (OmniDiT / JCo-MVTON / OutfitAnyone) over agnostic-mask (CatVTON/Leffa/IDM-VTON) — the
   incorrect-agnostic→hallucination class disappears (§4.1). Big, previously-unlogged direction.
2. **Multi-garment-native DiTs** (MuGa-VTON, AnyDressing) target our coordinated-upper+lower gap directly,
   vs our chain-of-single-garment plan — a bench row (§4.3).
3. **Try-off** (TryOffDiff/MGT/Voost) is the right tool to build clean **GarmentEvidencePacks / canonical
   fronts** from model-worn photos — better than segmentation for §6a (§4.4).
4. **Depth/normal conditioning** (Depth Anything → ControlNet-depth) is the cheap, unconsidered lever for
   **body-shape + occlusion under loose garments** — lighter than SMPL, no densepose (§5.3, §4.5).
5. **Identity adapters** (PuLID/InstantID/IP-Adapter, FLUX-PuLID-nunchaku at 16 GB) are the concrete,
   never-wired lever to lock identity on the editing spine (§7.1).
6. **Local QIE-2511 LoRA fine-tune from ~6 GB** (DiffSynth) makes the Garments2Look-style outfit-LoRA a
   LOCAL experiment, not rented-GPU — lowers the blueprint's WP7 cost (DEEP_RESEARCH §13.3).
7. **Quantization reframes the "16 GB constraint":** most heavy models (FLUX-Kontext, multi-garment DiTs,
   PuLID-FLUX, fine-tuned QIE) are reachable at fp8/SVDQuant — the real limits are quality-at-quant +
   engineering, not VRAM (§7.3).
8. **Unified editing models** (OmniGen2/Step1X-Edit/FLUX-Kontext) are credible **alternative spines** and
   could later collapse the 3-subsystem split (§2).
9. **Agentic mixed-modality recommendation** (planner + dynamic retrieval, image-anchor+text) is the modern
   V2 Stylist pattern — sharpens the blueprint's planner step (§6.1).
10. **3D-garment/sewing-pattern + physics drape** (NGL-Prompter, Dress-1-to-3) is the principled endgame
    for exact body+fit; a long-term spike, not V1 (§5.2).
11. **Sapiens** is the best human parser/pose/depth but **license-forbids our product** — prototype-only;
    keep SCHP/DWPose/MediaPipe for shippable (§5.1).
12. **Cloud ceiling** (Nano-Banana-Pro native VTON 4K, Seedream-5 "Universal Reference", GPT-Image-2,
    FASHN/Kling) — the bar to approach and the immediate full-outfit fallback (§3, DEEP_RESEARCH §13.4).

**Net:** none of this overturns the recommended spine (QIE editing + repair + gates), but it adds a
concrete **menu of levers** the project had not catalogued — most importantly **mask-free VTON**,
**try-off for evidence**, **depth-conditioning for body**, **identity adapters**, and **local fine-tune** —
each a small protocolled experiment, none a foregone conclusion.

**Sources (§7):** PuLID/InstantID/IP-Adapter/OminiControl/InfiniteYou (repos + 2503.16418) · ImageReward,
PickScore, HPSv3, VQAScore, GenEval (reward-model literature) · SVDQuant/nunchaku, GGUF, FP8/FP4 quant
(2606.12280, 2503.15465, 2405.19751) · LCM/Turbo/Lightning/DMD distillation.
