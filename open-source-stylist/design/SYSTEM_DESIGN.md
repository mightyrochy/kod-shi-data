# System Design — AI Stylist Pipeline (canonical)

**Consolidated 2026-06-10** from revisions R2/R3/R4 (preserved in `design/revisions/`).
This is the single canonical design document. Changes are appended as dated revision
notes at the bottom; the body is updated only with owner approval.

> Design vision across V1/V2/V3. Covers: research grounding, operating principles,
> every subsystem's role, concrete tool candidates, and the interfaces — what data
> flows between stages and how.
>
> Not a fixed spec. `knowledge/verified.md` and actual code override this document.
> **Important:** all empirical findings of the previous implementation attempt are
> downgraded to hypotheses (owner decision, 2026-06-10). They live in
> `knowledge/hypotheses.md` and must be re-verified under METHODOLOGY.md rules
> before any decision rests on them.

---

## 1. Design constraints

- **Local-first.** All core processing on the local machine.
- **Open source only.** No paid/closed models for core functionality.
- **No upfront investment.** Learning project that may become a product.
- **Cloud only later** (V3 product stage), and only where it gives real advantage.
- Owner is not a programmer; system is built with AI agents.

### Hardware reality
- RTX 4090 **Laptop** = **16GB VRAM** (not the desktop 24GB), i9, 32GB RAM.
- VRAM is shared between image-generation models and language models.
- **Models load/unload in sequence** — the orchestrator schedules this. A 20B-class
  image editor (fp8), an 8B VLM, and segmentation models cannot all be resident at once.
- Segmentation/landmark tools (SAM, MediaPipe) are small (≤2GB) and cheap to keep
  resident; the big swaps are the image editor and the VLM.
- Concrete unload levers: ComfyUI `POST /free`; LM Studio REST v1
  `POST /api/v1/models/unload` + per-request TTL.

---

## 2. The core problem

Image generation already works. The hard parts, in order:

1. **Detail & color fidelity.** A styling system must show specific garments accurately
   (exact color, texture, material). Approximations fail the product goal.
2. **Consistency.** Same input → different output each run; worse on multi-view.
3. **Closing the loop automatically** — evaluation that can actually be trusted, then retry.
4. **Sourcing real garments** (V2+).

### Critical insight on detail loss
Detail loss is **architectural, not a post-processing accident**. Models that condition
on garments via semantic understanding (editing models) preserve overall color/texture
but lose fine detail — a documented limitation. The design answer is layered:
minimize what generation is trusted with (P1), measure what it did (per-region gates),
restore/repair deterministically where possible (restoration shell).

### Critical insight on evaluation (hard lesson, 2026-06-10)
A closed loop is only as good as its measurement. The previous attempt closed the loop
around a VLM evaluator that hallucinated, and around subjective AI visual comparison that
proved unreliable on three consecutive reviews of the same image. **Neither a VLM nor an
AI assistant's eyes are measurement instruments.** Deterministic gates (pixel math,
embeddings, masks) plus final human judgment are the measurement core; VLM output is
advisory until its agreement with human verdicts is itself measured.

---

## 3. Research foundation (June 2026, verified against primary sources in R4)

Status per claim: **[R-verified]** = checked against primary sources;
**[hypothesis]** = plausible, not proven for our case.

1. **[R-verified] Outfit-level try-on is an open research problem.** Garments2Look
   (CVPR 2026, arXiv 2603.14153): first large outfit-level benchmark, 80K outfit→look
   pairs, 3–12 refs/look, 40 categories; current methods fail at full outfits —
   misalignment, artifacts, wrong layering, lost inner-layer detail. We are at the
   frontier, not misusing a solved technology. Dataset open; no fine-tuned checkpoint
   released (training = cloud GPU, deferred).
2. **[R-verified] General editing models beat dedicated VTON on layered outfits.**
   In the Garments2Look user study FastFit (leading multi-reference VTON) scored lowest
   on layering. Editing models parse layering instructions.
3. **[R-verified] Control degrades as simultaneous reference count grows** (Garments2Look).
   → Limiting simultaneous references (grouping, sequential passes) is a legitimate
   architectural response, not a hack.
4. **[R-verified] Industrial SOTA converged on our direction.** Tstars-Tryon 1.0
   (Alibaba/Taobao, arXiv 2604.19748): multi-reference *editing-model* architecture with
   engineered identity + background control, up to 6 refs. Weights closed; benchmark open.
   Validates the architecture class.
5. **[R-verified] Fine-tuning the editor on outfit data is a high-impact lever.**
   QIE-2509 + Garments2Look subset: layering preference 0.41 → 0.627. Deferred (cloud GPU).
6. **[hypothesis] Lightning LoRA trades fidelity for speed.** Official LightX2V claims
   quality is preserved at 4 steps; no rigorous public same-seed comparison exists.
   Bench-off rows 1–3 decide. No architecture decision may pre-assume the answer.
7. **[R-verified] Color shift in clothing-swap edits is a known community problem** for
   the Qwen-Image-Edit class. → Color fidelity must be solved deterministically.
8. **[R-verified] Deterministic identity restoration is an established pattern:**
   facial landmarks (MediaPipe FaceMesh) → piecewise affine warp of the ORIGINAL face
   region → Poisson blend. [hypothesis] that it is seam-free on our photos.
9. **[R-verified] Text-prompted segmentation gives per-garment masks.** Meta **SAM 3**
   (Nov 2025) does open-vocabulary text-prompted segmentation natively; maintained
   ComfyUI node packs exist, including a low-VRAM variant. Grounded-SAM-2 is the fallback.
   [hypothesis] that masks are usable on our images.
10. **[R-verified] QIE-2511 masked repair workflows exist and are mature** (crop-and-stitch:
    `InpaintCropImproved`/`InpaintStitchImproved` + `TextEncodeQwenImageEditPlus`).
    The repair executor is imported and validated, not invented (P8).
11. **[R-verified] OmniTry** (NeurIPS 2025): mask-free try-on of any wearable incl.
    jewelry; open weights; a LoRA on FLUX.1-Fill-dev. Official requirement 28GB bf16 —
    [hypothesis] that fp8/offload fits 16GB. Gating test required.
12. **Watch item:** Qwen-Image-2.0 (7B unified gen+edit, #1 AI Arena editing) — weights
    NOT open as of June 2026. If opened: candidate engine row in the bench.

### Prior-attempt observations (now hypotheses — see knowledge/hypotheses.md)
The previous attempt produced observations: prompt influence weak vs reference panel;
dual-view breaks coherence; 4-step-vs-40-step confound; color text in prompts overrides
visual references; body proportions pulled toward reference-photo models; VLM unreliable
at low resolution. None of these is hard proof. Each is listed in
`knowledge/hypotheses.md` with what it would take to verify it.

---

## 4. Operating principles

**P1 — Minimize the trusted-generation surface.** Split every output into three zones:
- *Must-not-change* (face, background, hair, body proportions): never trust the
  generator — restore deterministically (composite original pixels back) in holistic
  passes, or exclude by mask construction in repair passes.
- *Must-match-reference* (garment color, texture): correct deterministically
  (per-region LAB matching toward the reference).
- *Must-be-generated* (garment shape, drape, fit, shadows, layering): the only zone
  where the generator is trusted — and it is measured there.

**P2 — Reference panel > prompt.** [hypothesis from prior attempt, high plausibility]
The adapter's main lever is panel construction, not wording. QIE-2511 official
multi-image input is 1–3 images; person + 5 items requires compositing or grouping.

**P3 — Deterministic where possible, generative only where necessary.** Every problem
solved with plain Python (compositing, color matching, mask math) can never regress,
costs no VRAM, and needs no evaluation.

**P4 — Per-region evaluation, hybrid methods, instruments before opinions.**
Whole-image "looks right" verdicts hide failures. Per garment region: deterministic
gates (ΔE color in LAB, ArcFace identity cosine, mask-derived proportion ratios) decide
what they can measure; VLM covers semantics only (presence, layering) and is advisory
until calibrated against human verdicts; the owner's verdict is final for visual quality.

**P5 — Cheap drafts, expensive finals.** [hypothesis] Generate K fast drafts, rank,
re-generate winner at full quality. Same seed across configs does NOT replay the same
image; draft-rank → full-quality correlation is unverified. Correlation test required
before relying on this.

**P6 — Everything inspectable and resumable.** Every stage writes inputs/outputs to the
experiment folder. Any stage can be re-run in isolation.

**P7 — VRAM sequencing is the orchestrator's job.** Explicit load → use → unload.

**P8 — Adopt before building.** For any capability, first look for a maintained
community workflow/node; import, validate on our cases, only then build custom.

**P9 — Measurement before generation experiments.** (New — from the 2026-06-10 lesson.)
No generation experiment is run before the instruments that will judge it are themselves
validated on controlled cases. Un-measured experiments produce noise, not knowledge.

---

## 5. Data flow — objects and transport

One structured JSON object per stage boundary, written to disk and passed in memory:

```
PersonProfile      ← [1] Person Analysis
OutfitPackage      ← [2] Stylist
GenerationRequest  ← [3] Outfit Adapter
GenerationResult   ← [4] Try-On Engine (per candidate)
RegionMap          ← [5] Segmentation (masks: person, face, hair, background, per-garment)
EvaluationVerdict  ← [6] Evaluation (per region; + RepairPlan if failing)
FinalOutput        ← [7] Restoration Shell + re-check
```

All seven objects get JSON schemas in `system/contracts/` **before** the orchestrator
is built. Stages never reach into each other's internals — any stage is swappable.

Transport:
- **ComfyUI** — image generation server. Port: `:8000` on this machine per local
  verification 2026-06-10 (docs elsewhere say `:8188`; re-verify at plumbing time).
  Orchestrator POSTs workflow JSON (API format, image names + prompt + params filled),
  polls `/history/{prompt_id}`, downloads outputs via `/view`. `POST /free` unloads models.
- **LM Studio** `:1234` — VLM/LLM. OpenAI-compatible `/v1/chat/completions` for inference
  (images base64; structured output via JSON-schema response format) + native REST v1
  (`/api/v1/models`, `/api/v1/models/unload`) for explicit lifecycle control.
- **Local Python** — segmentation, landmarks, compositing, color math, gates. In-process.
- Stage-to-stage: JSON + file paths. Images pass by path, never embedded (except base64
  to the VLM).

---

## 6. Stages: roles, tools, interfaces

### [1] Person Analysis
- **Role:** structured description of what must be preserved — proportions, hair, skin
  tone, accessories, photo format (front/side/dual/full-partial). Changes nothing.
- **Tool:** Qwen3-VL-8B via LM Studio, schema-validated JSON output.
- **In:** photo. **Out:** `PersonProfile`.

### [2] Stylist — varies by version
- **Role:** decide the outfit; produce concrete items + reference images + layout logic.
- **V1:** manual — owner assembles reference images + layout text (an LLM may help
  structure the text, no retrieval). **V2:** LLM reasoning + retrieval (§10).
  **V3:** + wardrobe (§11).
- **Out:** `OutfitPackage` = items (type, description, reference image paths,
  visibility priority) + `layout_logic` (layering order, what stays visible)
  + negative constraints.

### [3] Outfit Adapter
- **Role:** pure formatting — build the composite reference panel + prompt + params for
  the chosen engine. **No styling decisions.** Prompt carries structure and layout;
  color/texture/material come exclusively from reference images
  (text color labels are forbidden — hypothesis H-COLOR, treat as rule until re-tested).
- **Tool:** deterministic Python (panel compositing); a small LLM only for prompt phrasing.
- **In:** `OutfitPackage`. **Out:** `GenerationRequest`.
- Panel construction is a first-class engineering artifact: consistent placement,
  per-item crops, versioned like code. Garment references should be cropped to the
  garment itself — bodies/shoes/competing items visible in product photos contaminate
  conditioning (hypothesis H-REF-CONTAMINATION, from run-000003 observation).

### [4] Try-On Engine
- **Default engine:** Qwen-Image-Edit-2511 (fp8mixed on 16GB) via ComfyUI; native
  multi-image nodes (`TextEncodeQwenImageEditPlus`). Generation strategies in §7;
  decision by bench-off (§8).
- **In:** `GenerationRequest`. **Out:** K × `GenerationResult` (drafts) or 1 final.

### [5] Segmentation
- **Role:** produce `RegionMap` for BOTH input photo and generated image: person, face,
  hair, background masks + one mask per garment (text prompts from `OutfitPackage`).
- **Tool:** SAM 3 (text-prompted, ComfyUI nodes, low-VRAM variant preferred);
  MediaPipe FaceMesh for face landmarks; Grounded-SAM-2 as fallback.
  (V1 as-built: GroundingDINO+SAM1 accepted per E-001; SAM3 deferred behind a
  dependency blocker — see BUILD_PLAN Stage 1 notes.)
- **Why a stage, not a utility:** evaluation gates, color correction, face restore, and
  repair masks all consume `RegionMap`. One computation, many consumers.
- **Mask sanity guard (added 2026-06-12 after two silent-mask-corruption incidents
  in E-005):** deterministic plausibility checks on every produced mask before any
  consumer sees it — area fraction within bounds for the region type, positional
  priors (footwear in the lower band, top in the upper half), garment masks ⊂ person
  mask. Violations FLAG the mask for owner review; they do not auto-fail. Masks are
  a single point of failure for every downstream measurement — they must not fail
  silently.

### [6] Evaluation — per-region, hybrid (P4)
- **Deterministic gates (decide):**
  - *Color:* per-region comparison between garment region (output) and reference
    garment region, designed around three findings from gate calibration
    (experiments/002, 2026-06-11):
    (a) **Metric: CIEDE2000, not CIE76.** CIE76 mean ΔE compresses differences on
    dark/desaturated colors — the same perceptual hue shift measured ~2 on navy vs
    ~5 on brown, so no universal CIE76 threshold exists.
    (b) **Lightness normalization before comparison** (align region L* means, or
    compare hue/chroma distributions): most of the photo-pair noise is lighting/
    shade/drape, not color. Natural variation between two photos of the SAME garment
    measured ΔE 4.0–5.2 while two different dark items measured 7.5 — the raw signal
    window is too narrow without normalization.
    (c) **Two modes, auto-selected by the reference region's own color distribution:**
    `solid` — unimodal reference → mean ΔE; `palette` — multimodal reference
    (patterned/multi-color garment) → dominant-color palette extraction (k-means)
    with weight-aware matching, or histogram EMD. Mean ΔE is blind on patterns: a
    red/white striped shirt and a pink shirt share the same regional mean.
    *Thresholds:* three zones PASS/WARN/FAIL; WARN goes to owner review. Per-item
    adaptive baseline where multi-view reference photos exist (ΔE(front,back) =
    that item's own noise). All thresholds are **provisional until the generator
    noise floor exists** (E-005) — the gate's real operating distribution is
    generated-vs-reference, which product-photo pairs only proxy.
  - *Identity:* ArcFace embedding cosine between input face and output face.
  - *Body proportions:* shoulder/waist/hip pixel widths (from person masks) normalized
    by person height; threshold on relative change, calibrated against natural
    run-to-run variance so noise is not flagged.
- **VLM checks (advise):** per-garment presence and structure (cropped region vs
  reference), layering vs `layout_logic`. Qwen3-VL-8B, schema JSON. Advisory until the
  VLM's agreement rate with human verdicts is measured (calibration experiment).
- **Countable details** (buttons, buckles): SAM3 instance counts — advisory in V1.
- **Texture & pattern spatial structure:** advisory only in V1 (drape vs flat product
  photo is not reliably measurable). Explicit boundary: the color gate's `palette`
  mode measures a pattern's **color composition** (which colors, in what proportions);
  the pattern's **spatial structure** (stripe width, print scale, motif placement)
  is texture-land — a documented open problem industry-wide (Garments2Look reports
  stripe-density distortion as an unsolved failure mode). In V1 it is covered by VLM
  semantics + owner's eyes only. Known limitation; revisit in V2.
- **Human verdict:** final authority on visual quality (SOP). The system's job is to
  bring the owner a measured, per-region report — not to replace the owner's eyes.
- **Out:** `EvaluationVerdict` per region + `RepairPlan` (region, defect type, target)
  for failures.

### [7] Restoration Shell
Ordered sub-steps, deterministic first:
1. **Face restore — conditional, not default (revised 2026-06-12):** triggered only
   when the ArcFace gate scores a run below threshold. E-005 measured identity as
   the generator's strongest property (cosine 0.776–0.874 vs threshold 0.57, all
   seeds); compositing into already-good faces adds Poisson-seam risk for no gain.
   Mechanism unchanged: FaceMesh landmarks → piecewise affine warp of ORIGINAL
   face → Poisson blend; ArcFace validates the result.
2. **Background restore:** composite original background back (when unchanged by request).
3. **Color correction:** per garment region, bounded histogram/LAB matching toward the
   reference (bounded strength — do not flatten shading).
4. **Structural repair (generative, targeted, last resort):** only for evaluator-flagged
   defects the deterministic steps can't fix. Executor: QIE-2511 + crop-and-stitch
   inpaint (imported community workflow), mask from `RegionMap`, **single garment
   reference** (fewer simultaneous refs = better control, per research item 3).
   FLUX Fill: text-only conditioning → architecturally incapable of reference-faithful
   repair; keep only for reference-free structural fixes. OmniTry: candidate accessory
   executor if it fits 16GB (gating test).
- Identity strategy is mode-split: holistic pass → restore-after (steps 1–2);
  repair pass → protect-by-construction (mask excludes face/background; no restore).
- **In:** `GenerationResult` + `RegionMap` + `RepairPlan`. **Out:** `FinalOutput`
  (image + per-criterion report + retry count). Retries capped.

---

## 7. Generation strategies for stage [4]

All share stages [1][2][3][5][6][7]. Decision by bench-off (§8), not assumption.

- **A — Holistic QIE-2511 pass + shell** *(default favorite: best documented layering,
  industrial precedent via Tstars-Tryon)*. One edit generates the dressed person;
  shell restores/corrects; repair pass fixes flagged regions.
- **B — FastFit + shell.** Open, fast, multi-reference VTON. Documented worst-in-class
  layering. One honest bench row to disprove or surprise.
- **C — Hybrid sequential: holistic clothing pass + per-item accessory passes.**
  Clothing layers in one Qwen pass (layering is where editors win); accessories (belt,
  shoes, earrings) added by separate masked local passes (repair executor, or OmniTry).
  Responds directly to reference-count degradation; drift outside masks is zero by
  construction. Cost: +N generations.
  **Measured motivation (2026-06-12, E-005):** the holistic baseline systematically
  distorts body proportions on every seed (waist −4…−11%, shoulders +4…+16%) and
  fails shoes both in color and stability. Masked passes physically cannot alter
  pixels outside their masks — protect-by-construction is currently the only
  architectural answer to proportion distortion, because the shell has no
  deterministic body-restore step (the garment legitimately changes the silhouette).
  This makes the proportion gate the primary discriminating metric between A and C
  in the bench-off.
- **D — Look compilation (pilot hypothesis).** (1) compile the outfit board into ONE
  coherent worn-look image; (2) transfer that single look onto the person. Compresses
  5 refs → 1. Risk: detail loss compounds across two generations. Cheap pilot only if
  A/C underperform on layering coherence.

---

## 8. Engine bench-off protocol

Runs only after measurement gates are validated (P9) — metrics, not eyeballing.

- **Fixed inputs:** assets outfit_001 (person photo, garment references, layout text)
  + one harder outfit (more layers, patterned fabric) — assembled before the bench.
  Assembling the patterned outfit triggers the color gate's `palette`-mode calibration
  (E-013): the gate must be able to measure patterned garments before the bench
  judges them.
- **Matrix:**
  | Row | Config | Answers |
  |---|---|---|
  | 1 | QIE-2511 + Lightning, 4 steps, 720×1024 | baseline |
  | 2 | QIE-2511, no Lightning, 20 steps, 720×1024 | Lightning-fidelity question |
  | 3 | QIE-2511, no Lightning, 40 steps, 720×1024 | (with row 2) |
  | 3b | QIE-2511, no Lightning, 40 steps, **1120×1600 (High+)** | resolution-ceiling question (added 2026-06-12) |
  | 4 | FastFit | strategy B |
  | 5 | Strategy C (holistic + accessory passes) | hybrid sequential |
  | 6 | OmniTry, accessories only, fp8 | accessory executor + VRAM fit |

  **Row 3b rationale (2026-06-12, from E-006):** color ΔE improved monotonically with
  resolution (High+ best: top 1.54, bottom 1.65 — below the E-005 noise floor), but
  every non-baseline tier failed *identity* via head-cropping, which O-RES-002
  attributes to the Lightning LoRA being tuned near 720–1024px. If that interpretation
  holds, a no-Lightning model at High+ may keep the color gain without the identity
  failure — potentially the best-color config in the whole matrix. One row settles it.
  Cost: +5 generations (40 steps, so the slowest row — schedule as a background batch).
- **K=5 seeds per row, same seeds across rows.** Natural per-seed variance must be
  measured first (variance baseline) so differences can be attributed.
- **P5 correlation side-test:** rank 5 Lightning drafts by gates; regenerate each seed
  full-step; check rank stability.
- **Metrics:** per-garment ΔE; ArcFace cosine; proportion deltas (**primary
  discriminator between strategies A and C** — see §7); advisory texture indicator
  (high-frequency energy ratio of garment region vs reference — added 2026-06-12:
  owner observed texture flatness dominates perceived difference at ΔE 3–5, and a
  ΔE-only bench could pick a flat-texture winner); VLM presence/layering checklist
  (advisory); wall-clock; VRAM peak. Owner review remains a mandatory bench input —
  no engine decision on numbers alone.
- **Output:** knowledge entry + engine/strategy decision recorded with data.

---

## 9. V1 — Closed local loop

**Goal:** one orchestrator runs [1]→[7] end-to-end on a single frontal photo with a
manual `OutfitPackage`, producing a final image + measured per-region report.
Success bar: closed, measured, reproducible.

- Stylist = manual. Orchestrator = Python. Explicit VRAM sequencing.
  Experiment folder per execution.
- Assembly order, stage contracts, and per-stage acceptance criteria: `BUILD_PLAN.md`.
- **Excludes:** dual-view, complex poses, real backgrounds, retrieval, wardrobe.

### Dual-view (deferred, sharpened hypothesis)
Generate and finalize the front view first; then generate the side view with the
finalized front as an additional reference; composite the two finished singles
deterministically. Never ask the model to hold coherence across views in one canvas.

---

## 10. V2 — Real garment retrieval

V1 unchanged except Stylist:
- **Stylist reasoning:** LLM turns `PersonProfile` + style request into an outfit
  concept with per-item descriptions. Candidate: Qwen3 14B local; escalate to a stronger
  (possibly cloud) LLM only if local styling judgment proves weak — the one place cloud
  may earn its keep pre-V3.
- **Garment retrieval subsystem:**
  - *Indexing (offline, once per catalog):* garment images → **FashionCLIP** or
    **Fashion-SigLIP** embeddings → **Qdrant** (local, open source) with metadata
    (name, price, URL, image path).
  - *Query (per outfit item):* item description (text and/or sample image) → same
    embedding model → nearest-neighbor → top-K real product candidates.
  - Embedding choice benchmarked on the real target catalogs (SigLIP-class tends to win
    on fine attributes — verify).
- Retrieved product images become the `OutfitPackage` reference board automatically.
  Stages [3]–[7] untouched.

---

## 11. V3 — Wardrobe + product stage

- **Personal wardrobe:** user's garments photographed once → VLM-attributed → embedded
  (same model as V2) → separate per-user Qdrant index. Stylist searches catalog (buy) +
  wardrobe (own), can prefer either.
- **Product stage (only if it becomes a product):** generation moves to rented GPU
  inference; indices and orchestrator become services. Multi-user serving makes cloud
  non-optional here. Architecture stays portable (stages = services talking JSON) so
  this is a re-deploy, not a rewrite.
- **Mid-term quality lever:** LoRA fine-tune of the editor on Garments2Look-style outfit
  data (documented large gains for QIE-2509). Requires cloud GPU rental → deferred.
- Quality bar rises: V3 inherits V1's fidelity/consistency solutions — which is why
  solving them properly in V1 matters.

---

## 12. Open questions (priority order)

1. **Measurement-gate calibration** — do ΔE / ArcFace / proportion gates produce stable,
   human-agreeing verdicts on controlled cases? (Everything downstream depends on this.)
2. **Engine bench-off (§8)** — engine/strategy decision + Lightning question.
3. **Repair executor validation** — imported QIE-2511 crop-and-stitch inpaint on a real
   documented failure: reference-faithful? local?
4. **OmniTry on 16GB** (fp8/offload) — yes/no gating test.
5. **Restoration-shell seams** — Poisson blend quality on our photos; ArcFace thresholds.
6. **P5 draft-rank correlation** — does Lightning-draft ranking predict full-step quality?
7. **VLM calibration** — agreement rate of Qwen3-VL-8B semantic checks vs human verdicts;
   at what image resolution does it become usable?
8. **Dual-view composite approach** — after V1 closes.
9. **Qwen-Image-2.0 weights** — watch monthly; if open, bench row 7.
10. **V2 questions** (stylist LLM quality, FashionCLIP vs Fashion-SigLIP) — deferred.

---

## 13. Sources

- Garments2Look: https://arxiv.org/abs/2603.14153 · https://github.com/ArtmeScienceLab/Garments2Look
- Tstars-Tryon 1.0: https://arxiv.org/abs/2604.19748
- OmniTry: https://arxiv.org/abs/2508.13632 · https://github.com/Kunbyte-AI/OmniTry
- FastFit: https://arxiv.org/abs/2508.20586 · https://github.com/Zheng-Chong/FastFit
- Voost: https://arxiv.org/abs/2508.04825 · https://github.com/nxnai/Voost
- Qwen-Image-2.0 tech report: https://huggingface.co/papers/2605.10730
- Qwen-Image-Edit-2511: https://qwen.ai/blog?id=qwen-image-edit-2511
- QIE-2511 Lightning: https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning
- QIE-2511 inpaint workflows: https://openart.ai/workflows/makisekurisu/inpainting-for-qwen-image-edit-2511/AYcG8mrxUuvwk1BUbEMT · https://github.com/axiomgraph/ComfyUIWorkflow
- SAM 3 ComfyUI: https://github.com/PozzettiAndrea/ComfyUI-SAM3 · https://github.com/yolain/ComfyUI-Easy-Sam3
- Qwen3-VL-8B in LM Studio: https://lmstudio.ai/models/qwen/qwen3-vl-8b
- LM Studio model mgmt API: https://lmstudio.ai/docs/developer/rest/unload · https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict
- Awesome-Try-On-Models: https://github.com/Zheng-Chong/Awesome-Try-On-Models

---

## Revision notes (append-only)

- **2026-06-10** — canonical consolidation of R2 (2026-06-09), R3 (2026-06-10),
  R4 (2026-06-10). Key consolidation decisions: R4's research verification and P8
  adopted; R3's stage descriptions and restoration shell adopted; R2's V2/V3 detail and
  transport description adopted; new P9 (measurement before generation experiments)
  added from the evaluation-reliability lesson; all prior-attempt [E] findings
  downgraded to hypotheses per owner decision.
- **2026-06-12** — post-E-005 architecture review (owner-approved): face restore in
  the shell becomes conditional (ArcFace-triggered) — identity measured as the
  generator's strongest property; strategy C gains measured motivation (systematic
  proportion distortion in holistic passes has no shell remedy — protect-by-
  construction is the only architectural answer); proportion gate named primary
  A-vs-C bench discriminator; advisory texture indicator added to bench metrics;
  mask sanity guard added to stage [5] after two silent-mask-corruption incidents.
- **2026-06-12 (E-006 closed)** — bench matrix gains row 3b (no-Lightning, 40 steps,
  1120×1600): E-006 found color ΔE best at High+ but Lightning failed identity there
  via head-cropping (LoRA tuned ~720–1024px), so a full model at High+ may keep the
  color gain without the identity loss. V-RES-001 (720×1024) is therefore scoped to
  the Lightning config only, not generalized until row 3b runs.
- **2026-06-11** — color gate redesigned on E-002 calibration data (experiments/002):
  CIE76 → CIEDE2000; lightness normalization added; two modes (solid/palette)
  auto-selected by reference distribution — mean ΔE is blind on multi-color patterns;
  per-item adaptive baseline from multi-view reference photos; PASS/WARN/FAIL zones
  with WARN → owner; thresholds provisional until E-005 generator noise floor.
  Texture note sharpened: palette mode measures pattern color composition only;
  pattern spatial structure stays advisory (known V1 limitation). Bench-off inputs
  note: patterned-outfit assembly triggers palette-mode calibration (E-013).
