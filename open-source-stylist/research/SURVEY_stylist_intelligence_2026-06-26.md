# Survey — stylist intelligence, person evaluation, measurement & control/automation (2026-06-26)

Owner brief: survey the **non-rendering** layer — tools that **create the outfit, evaluate the person, pick
styles**, plus the **measurement / control / automation** instruments. (Companion to the rendering survey
`SURVEY_fashion_ai_landscape_2026-06-26.md`.) Maps to our stages [1] Person Analysis, [2] Stylist (V2/V3),
[6] Evaluation, and the orchestration backbone. Tags: `[OSS]` open · `[COM]` commercial-only · `[L]` local ·
`[clm]` search-claim · dates = freshness. 16 GB ceiling.

---

## A. Person evaluation (→ our PersonProfile, the "оцінити людину" layer)

### A1. Body shape / type classification
- Single-image **body-shape classification** (Apple / Hourglass / Inverted-Triangle / Rectangle / Triangle) from
  bust/waist/hip ratios. arXiv 2305.18480 (single image), **DL-EWF** (Grounded-SAM seg → shape class). Reported
  accuracy modest (~71 %) `[OSS-research]`. Practical for a coarse body-type label.
- **SMPL-X / PIXIE / ECON** (rendering survey §19) give parametric **shape params** (height/volume/proportions)
  from one RGB image → the rigorous body descriptor; heavier `[OSS]`.

### A2. Anthropometric measurement from photo
- **SizeYou** (front+side photos → real-time 3D anthropometrics) `[COM]`; Body-Measurements image datasets on
  Kaggle/Unidata `[OSS data]`; 2025 review "Inferring Body Measurements from 2D Images" (PMC12193998). Accuracy
  is application-dependent; good enough for sizing/relative proportions, not tailoring-grade.

### A3. Face shape + features
- Face-shape detection (oval/round/square/heart…) — mostly bundled in commercial color tools `[COM]`; can be
  built locally from **MediaPipe FaceMesh** landmark ratios (we already load FaceMesh for the identity/face path).

### A4. Personal color analysis (undertone / seasonal palette) — **honest gap**
- Strong consumer demand, many tools: Dressika/coloranalysis.app, Colorwise, Manus, Palette Hunt, Face Type
  Detector, ColorForMe — all `[COM]` / client-side closed. They derive **skin undertone + contrast + hair/eye
  colour → seasonal type (12-season) → flattering palette** (≈120 clothing colours).
- **No meaningful OSS model.** For local: build it ourselves — skin/hair/eye region sampling (our segmenter) →
  LAB/undertone + contrast features → rule-based or small classifier into the 12-season system, optionally a VLM
  cross-check. This is a **buildable custom instrument**, not an adopt-off-the-shelf.

## B. Outfit creation & compatibility (→ our Stylist [2], the "створення outfit" layer)

### B1. Compatibility / complementary-item models
- **Outfit Transformer** (Amazon Science) — outfit representations; generates a target-item embedding to retrieve
  compatible items; SOTA on **compatibility prediction**, **fill-in-the-blank (FITB)**, **complementary retrieval**.
  The canonical modern compatibility approach `[OSS-research]`.
- **Hybrid-Hierarchical Fashion Graph Attention Net** (2508.11105) — graph-based, compatibility + personalization.
- **TATTOO** (2509.23242, 2025) — **training-free aesthetic-aware** outfit recommendation (uses a frozen
  backbone) → attractive for us (no training).
- Type-aware compatibility (Polyvore lineage) — academic baseline.
- Practical pairing tool: **Marqo-FashionSigLIP** (rendering survey §8) for "find items like / compatible-with".

### B2. LLM/MLLM stylist reasoning (decide the outfit + explain)
- **FashionStylist** (2604.09249, ACM-MM 2026) — expert-knowledge multimodal **benchmark + dataset**: MLLM predicts
  **style / season / occasion** and **flags style-mismatched items**. A ready yardstick for "is this outfit
  coherent?" `[OSS-research]`.
- **Agentic Personalized Fashion Recommendation** (2508.02342) — agentic gen-AI rec: challenges, opportunities,
  evaluation. **Decoding Style** (2409.12150) — fine-tune an LLM for image-guided outfit rec with preference
  feedback. **DesignBridge** (2601.14639) — designer-expertise ↔ user-preference co-design.
- Pattern that fits us: local **MLLM (Qwen3-VL)** auto-tags garments → reasons style/season/occasion/body-type →
  ranks complementary items, with an explainable trace. Cold-start handled by LLM semantic reasoning.

## C. Garment / attribute recognition (the measurement of *what an item is*)
- **DeepFashion** (800K imgs, 50 cat, 1000 attrs, landmarks) / **DeepFashion2** (detect/pose/seg/re-id) /
  **Fashionpedia** (expert ontology + **Attribute-Mask-RCNN** joint seg + localized attributes) / iMaterialist —
  open datasets + trainable taggers `[OSS]`.
- **DETR-based layered clothing seg + fine-grained attributes** (2304.08107).
- **Practical no-train route: VLM zero-shot attribute labeling** (2601.15711, three-tier eval) — a VLM does
  multi-label category/colour/pattern/material/aesthetic tagging few/zero-shot (~0.80 weighted F1 on aesthetic
  labels). **Recommended:** use Qwen3-VL for attributes rather than training a tagger.
- Embedding/retrieval: **Marqo-FashionSigLIP / FashionCLIP** (Apache).

## D. Measurement / QA instruments (deterministic gates → our Evaluation [6])
What we already have stays the core: **identity** (ArcFace), **body proportions** (MediaPipe), **colour**
(CIEDE2000 solid + palette), **structure** (AnomalyDINO/DINOv2), **FashionSigLIP-sim**, **sanity guard**, VLM
presence/layering. Fresh additions worth wiring:
- **DISTS** — best single garment-similarity metric (rendering survey §9); add beside FashionSigLIP.
- **Attribute-match gate** — VLM/Fashionpedia attributes(reference) vs attributes(output) → catch wrong
  category/pattern/material that colour ΔE misses.
- **Outfit-coherence gate** — FashionStylist-style MLLM check: does the rendered look satisfy the requested
  style/season/occasion and contain no mismatched item.
- **Benches** for calibration: VTONQA, OpenVTON-Bench (2026-01).

## E. Control / automation backbone (the "автоматика" — make the pipeline reliable)
This is the layer that makes the contracts in SYSTEM_DESIGN §5 actually hold at runtime.
- **Structured output / constrained decoding** — guarantees every stage object is schema-valid:
  - **XGrammar** (default backend for **vLLM / SGLang / TensorRT-LLM** since 2026-03; <40 µs/token, near-zero
    overhead) — hard schema guarantee via `guided_json`. **XGrammar-2** (2601.04426) for agentic loops. `[OSS][L]`
  - **llguidance** (MS, Rust Earley ~50 µs) `[OSS]`; **Outlines** (FSM, slow on complex schemas) `[OSS]`.
  - **Instructor** (11K★, Pydantic validation + **auto-retry on validation failure** + streaming) `[OSS]` — the
    pragmatic wrapper around our PersonProfile / OutfitPackage / EvaluationVerdict JSON.
  - Our current **LM Studio** already supports JSON-schema `response_format`; **vLLM/SGLang + XGrammar** would give
    *hard* guarantees + speed if we move serving. `[L]`
- **Agent orchestration** — for V2/V3 the stylist becomes a multi-step agent (analyze → retrieve → reason →
  validate → render → evaluate → repair). Reference arches: Wardrowbe (Ollama/OpenAI-compatible, Docker),
  Fashion-Assistant (YOLO+CLIP+DINOv2+LLM), FitCheck.AI (LangChain+CLIP+Qwen). Keep deterministic gates as the
  agent's hard guardrails (the agent proposes, the gates + owner dispose).
- **VLM serving** — Qwen3-VL (ours) via LM Studio; alternatives InternVL3 / Molmo; vLLM/SGLang for throughput +
  constrained decoding.

---

## Synthesis — what to ADOPT vs BUILD for this layer (local-OSS first)
**Adopt (off-the-shelf / no-train):**
- Attribute tagging + outfit reasoning → **Qwen3-VL zero-shot** (no tagger training); benchmark coherence against
  **FashionStylist**.
- Compatibility/retrieval → **Marqo-FashionSigLIP**; **TATTOO** (training-free) for outfit-level aesthetic ranking.
- Contract reliability → **Instructor + (XGrammar via vLLM/SGLang)** for guaranteed-valid stage JSON.
- Body descriptor → **SMPL-X/PIXIE** (rigorous) or single-image shape-class (coarse).

**Build (no good OSS exists):**
- **Personal colour analysis** instrument (undertone/season → palette) — our own: segment skin/hair/eyes → LAB/
  contrast features → 12-season mapping (+ VLM cross-check). This is the clearest white-space; it also feeds the
  colour gate (palette the person *should* wear) and the no-text-colour rule.
- **Person→outfit fit rules** (body-shape → silhouette guidance) — encode as the Stylist's constraints; couples
  with the fit-aware rendering lever (Sapiens2 normals).

**Mapping to our stages:** A→[1] PersonProfile (add body-shape + colour-season fields); B→[2] Stylist (V2/V3
compatibility + MLLM reasoning); C→[5]/[6] attribute taggers feed gates; D→[6] add DISTS + attribute-match +
coherence gates; E→orchestrator backbone (constrained decoding + agent).

## Sources
Compatibility/rec: Outfit Transformer https://www.amazon.science/publications/outfit-transformer-outfit-representations-for-fashion-recommendation · Hybrid-Hier FGAN https://arxiv.org/pdf/2508.11105 · TATTOO https://arxiv.org/pdf/2509.23242
Stylist reasoning: FashionStylist https://arxiv.org/html/2604.09249v1 · Agentic Fashion Rec https://arxiv.org/html/2508.02342v1 · Decoding Style https://arxiv.org/html/2409.12150v1 · DesignBridge https://arxiv.org/pdf/2601.14639
Attributes/datasets: DeepFashion https://liuziwei7.github.io/projects/DeepFashion.html · DeepFashion2 https://arxiv.org/pdf/1901.07973 · Fashionpedia https://www.researchgate.net/publication/340963101_Fashionpedia_Ontology_Segmentation_and_an_Attribute_Localization_Dataset · DETR attrs https://arxiv.org/pdf/2304.08107 · VLM zero-shot attrs https://arxiv.org/pdf/2601.15711
Person eval: body-shape single image https://arxiv.org/pdf/2305.18480 · DL-EWF https://arxiv.org/pdf/2404.04891 · 2D body measurement review https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12193998/ · SizeYou https://www.sizeyou.it/en
Colour analysis (commercial): https://coloranalysis.app/ · https://colorwise.me/ · https://www.palettehunt.com/
Control/automation: XGrammar-2 https://arxiv.org/pdf/2601.04426 · JSONSchemaBench https://arxiv.org/pdf/2501.10868 · vLLM structured https://docs.vllm.ai/en/v0.8.2/features/structured_outputs.html · Instructor (structured outputs guides) https://techsy.io/en/blog/llm-structured-outputs-guide
Agents: Wardrowbe https://wardrowbe.com/blog/wardrowbe-ios-android-open-source-2026/ · Fashion-Assistant https://github.com/SkalskiP/fashion-assistant
