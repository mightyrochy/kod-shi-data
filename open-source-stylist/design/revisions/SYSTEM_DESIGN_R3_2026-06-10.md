# System Design — AI Stylist Pipeline
**Revision 3** — deep-research pass: research foundation added, operating principles reframed,
restoration shell introduced, candidate architectures expanded to three, bench-off protocol defined.

> Design vision across V1/V2/V3 with candidate architectures for the generation core.
> Covers: research grounding, operating principles, each subsystem's role, concrete tool
> candidates, and the interfaces — what data flows between stages and how.
>
> Not a fixed spec. FINDINGS.md and actual code override this document.

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
- **Models load/unload in sequence** — the orchestrator schedules this. A 20B-class image
  editor (fp8), a 7B VLM, and segmentation models cannot all be resident at once.
- Segmentation/landmark tools (SAM, Grounding DINO, MediaPipe) are small (≤2GB) and cheap
  to keep around; the big swaps are the image editor and the VLM.

---

## 2. Research foundation (what the field knows — June 2026)

Each item below is tagged **[R]** = published research / documented community knowledge,
or **[E]** = our own empirical finding (from runs in this project).

1. **[R] Outfit-level try-on is an open research problem.** Garments2Look (CVPR 2026) is the
   first large benchmark for full-outfit try-on with layering (3–12 reference items per look).
   Its conclusion: current methods struggle with complete outfits — misalignment, artifacts,
   incorrect layering. Documented failure modes include wrong button counts, distorted stripe
   density, lost details on inner layers — the exact failures we observe.
   → We are not misusing a solved technology; we are at the frontier. Expectations and
   architecture must account for this.

2. **[R] General editing models beat dedicated VTON models on layered outfits.**
   In the Garments2Look user study, FastFit (the leading multi-reference dedicated VTON)
   scored *lowest* on layering quality — it processes a single layer. Editing models
   (Qwen-Image-Edit class) can parse layering instructions. → Our empirical preference for
   Qwen over IDM-VTON/CatVTON **[E]** now has benchmark-level support.

3. **[R] Control degrades as the number of simultaneous reference items grows.**
   Documented in Garments2Look. → Argues for limiting simultaneous references:
   grouped or sequential dressing is a legitimate architectural response, not a hack.

4. **[R] Fine-tuning the editor on outfit data is a documented high-impact lever.**
   QIE-2509 fine-tuned on a small subset of Garments2Look improved layering preference
   0.41 → 0.627. The dataset is open (80K outfit-to-look pairs). → A future Qwen-2511 LoRA
   trained on this data is a realistic mid-term upgrade. (Training a 20B model is not
   feasible on a 16GB laptop — this is a future cloud-GPU-rental decision, deferred.)

5. **[R] Lightning/speed LoRAs trade fidelity for speed.** Documented guidance for Qwen 2511:
   avoid lightning variants when likeness/detail is the KPI. Same-seed comparisons show
   texture loss at Lightning-4 vs full 40 steps (no LoRA).
   **[E] Our "40 steps was worse" test almost certainly ran WITH Lightning still enabled**
   (outside its trained regime). The correct comparison — {4 + Lightning} vs {20–40, no
   Lightning} — has not been run yet. **Priority experiment.**

6. **[R] Color shift in clothing-swap edits is a known community problem** for Qwen-Image-Edit
   class models (dedicated articles exist on fixing it). → Color fidelity must be solved
   deterministically, not hoped for.

7. **[R] Deterministic identity restoration is an established pipeline pattern.**
   Documented approach: detect facial landmarks (MediaPipe FaceMesh) on the edited image,
   align the ORIGINAL face region via piecewise affine warp, merge with Poisson blending.
   Result: the final image provably carries the person's real face. The same logic applies
   to background. → Identity preservation stops being generative luck.

8. **[R] Text-prompted segmentation (Grounded-SAM / Grounded-SAM-2) yields precise
   per-garment masks** from prompts like "blouse", "skirt", "belt" — demonstrated down to
   the level of buttons and zippers. Open source, small models. → Enables per-region
   evaluation, per-region color correction, and targeted repair masks.

9. **[E] Prompt influence is weak; the model follows the reference panel.** Invest in panel
   construction, not wording.

10. **[E] Dual-view (front+side in one canvas) breaks outfit coherence between views.**

11. **[E] Qwen-2511 holds identity and layout acceptably on single frontal view at
    Lightning-4; detail/color drift is the main quality gap.**

---

## 3. Operating principles

**P1 — Minimize the trusted-generation surface.**
Split every output image into three zones with different handling:
- **Must-not-change** (face, background, hair, body proportions): do not trust the generator —
  restore deterministically (masks + composite original pixels back, Poisson blending).
- **Must-match-reference** (garment color, texture): correct deterministically
  (per-region histogram/LAB matching toward the reference garment).
- **Must-be-generated** (garment shape, drape, fit, shadows, layering): the only zone where
  the generator is trusted — and evaluated.

**P2 — Reference panel > prompt.** (From [E]9.) The adapter's main lever is panel layout.

**P3 — Deterministic where possible, generative only where necessary.**
Every problem solved with plain Python (compositing, color matching, mask math) is a problem
that can never regress, costs no VRAM, and needs no evaluation.

**P4 — Per-region evaluation, hybrid methods.**
Whole-image "does it look right" verdicts hide failures. Evaluate per garment region:
VLM for semantics (presence, layering), pixel math for color (ΔE in LAB vs reference),
detector for countable details (buttons via Grounding DINO). Identity needs no evaluation
if P1 composites the original face back.

**P5 — Cheap drafts, expensive finals.**
Lightning-4 is a search tool: generate K candidate drafts fast, auto-rank them, then re-generate
the winner (same seed/composition) at full quality without Lightning. Speed finding **[E]**
and fidelity finding **[R]5** stop contradicting each other — they serve different phases.

**P6 — Everything inspectable and resumable.** Every stage writes its inputs/outputs to the
run folder. Any stage can be re-run in isolation.

**P7 — VRAM sequencing is the orchestrator's job.** Explicit load → use → unload steps.

---

## 4. Data flow — objects and transport

Structured objects (JSON on disk + in memory), one per stage boundary:

```
PersonProfile      ← [1] Person Analysis
OutfitPackage      ← [2] Stylist
GenerationRequest  ← [3] Outfit Adapter
GenerationResult   ← [4] Try-On Engine (per candidate)
RegionMap          ← [5] Segmentation        (NEW: per-garment masks + face + background)
EvaluationVerdict  ← [6] Evaluation (per region; + RepairPlan if failing)
FinalOutput        ← [7] Restoration Shell + re-check
```

Transport:
- **ComfyUI** `localhost:8188` — generation. Orchestrator POSTs workflow JSON (image paths,
  prompt, params filled in), polls `/history`, reads output from disk.
- **LM Studio** `localhost:1234` — VLM/LLM via OpenAI-compatible `/v1/chat/completions`;
  images base64; structured output enforced by JSON schema validation.
- **Local Python** — segmentation (Grounded-SAM-2), landmarks (MediaPipe), compositing,
  color math. No server needed; runs in the orchestrator process.
- Stage-to-stage: JSON objects + file paths. Images pass by path, never embedded
  (except base64 to the VLM).

---

## 5. Stages: roles, tools, interfaces

### [1] Person Analysis
- **Role:** structured description of what must be preserved — proportions, hair, skin tone,
  accessories, photo format. Changes nothing.
- **Tool:** Qwen2.5-VL-7B (LM Studio). Schema-validated JSON out.
- **In:** photo. **Out:** `PersonProfile`.

### [2] Stylist — varies by version (see V1/V2/V3)
- **Out:** `OutfitPackage` = items (type, description, reference image path each) +
  `layout_logic` (layering order, what stays visible).

### [3] Outfit Adapter
- **Role:** pure formatting — build the composite reference panel + prompt + params for the
  chosen engine. No styling decisions.
- **Tool:** deterministic Python (panel compositing); Qwen3 14B only for prompt phrasing.
- **In:** `OutfitPackage`. **Out:** `GenerationRequest`.
- Panel-construction discipline (from P2): consistent item placement, labels, per-item crops;
  this is a first-class engineering artifact, version it like code.

### [4] Try-On Engine — see candidate architectures (§6)
- **In:** `GenerationRequest`. **Out:** K × `GenerationResult` (drafts), then 1 final.
- Two-tier generation per P5: Lightning-4 drafts → full-step final (no Lightning).

### [5] Segmentation (NEW stage)
- **Role:** produce `RegionMap` on BOTH the input photo and the generated image:
  face mask, hair mask, background mask, one mask per garment ("blouse", "skirt", "belt",
  "shoes", "earrings" — prompts come from `OutfitPackage`).
- **Tool:** Grounded-SAM-2 (Grounding DINO + SAM-2), local, small. MediaPipe FaceMesh for
  face landmarks.
- **Why it's a stage, not a utility:** every downstream step (evaluation, color correction,
  face restore, targeted repair) consumes `RegionMap`. One computation, many consumers.

### [6] Evaluation — per-region, hybrid
- **Identity:** not evaluated — guaranteed by restoration shell (P1). (Optionally a sanity
  landmark-distance check post-composite.)
- **Per-garment presence & structure:** VLM on the cropped garment region vs its reference
  image ("same item? same closure type? sleeve shape?").
- **Layering:** VLM on the whole image against `layout_logic`.
- **Color/texture:** deterministic — mean/percentile ΔE (LAB) between generated garment
  region and reference garment region; texture similarity (e.g. LBP/FFT stats) as a
  secondary signal. Hard thresholds, no VLM opinion.
- **Countable details:** Grounding DINO detection on crops ("button", "buckle") — count match
  vs reference.
- **Out:** `EvaluationVerdict` per region + `RepairPlan` (region, defect type, target) for
  failures. Pass = all criteria pass or user explicitly accepts.

### [7] Restoration Shell (replaces "Postproduction" as a concept)
Ordered sub-steps, deterministic first:
1. **Face restore (deterministic):** FaceMesh landmarks on generated image → piecewise affine
   warp of ORIGINAL face region → Poisson blend. Identity becomes an engineering guarantee.
2. **Background restore (deterministic):** background mask from `RegionMap` → composite
   original background back (when the request doesn't ask to change it).
3. **Color correction (deterministic):** per garment region, histogram/LAB matching toward
   the reference garment; bounded strength to avoid flattening shading.
   (`tools/postproduction_color_repair.py` exists but is UNTESTED — written by a degraded
   agent; validate or rewrite before relying on it.)
4. **Structural repair (generative, targeted, last resort):** only for defects the evaluator
   flagged that deterministic steps can't fix (missing buckle, wrong collar): masked inpaint
   with FLUX Fill (locality already proven: 0.048% outside mask) or Qwen-with-mask
   (untested — open question). Tight masks from `RegionMap`. Re-evaluate after.
- **In:** final `GenerationResult` + `RegionMap` + `RepairPlan`. **Out:** `FinalOutput`
  (image + per-criterion report + retry count). Retries capped.

---

## 6. Candidate architectures for the generation core

All three share stages [1][2][3][5][6][7]. They differ in how [4] produces the dressed person.

### Architecture A — Holistic edit + restoration shell  *(evolved current approach)*
- One Qwen-2511 pass generates the fully dressed person from the reference panel.
- Lightning-4 for K drafts → rank (auto-eval) → full-step final without Lightning.
- Shell then restores face/background, corrects color, repairs structure if flagged.
- **Strengths:** best documented layering ability; one generation; matches our experience.
- **Risks:** detail fidelity within garments still generator-dependent; color shift known
  (mitigated by shell step 3).

### Architecture B — Dedicated multi-reference VTON + shell
- FastFit as the engine (open source, ComfyUI workflow exists, handles tops/bottoms/shoes/bags
  simultaneously). Newer papers (DiT-VTON, Voost, OmniTry, JCo-MVTON) are candidates ONLY if
  released weights fit 16GB — verify before testing.
- **Strengths:** detail transfer designed-in (reference feature injection).
- **Risks (documented):** worst-in-class layering; background-transition artifacts;
  multi-item ≠ layered. Likely loses on our layered outfits — but one honest bench run is
  cheap and settles it.

### Architecture C — Sequential layered dressing + shell
- Dress in passes following `layout_logic`: base layer → outer layer → shoes → accessories.
  Each pass is a small, controlled edit (Qwen with a region mask, or a per-category engine),
  with few simultaneous references (responds directly to [R]3).
- Inter-pass mini-evaluation (cheap: presence + color only).
- **Strengths:** each item gets focused reference fidelity; layering is explicitly
  constructed, not hoped for; failures are localized to a pass.
- **Risks:** cumulative drift across passes (face drift neutralized by shell step 1;
  garment drift remains), N× generation time, compounding masks.
- **Status:** hypothesis. Worth a small pilot after A is benched.

**Decision = bench-off (§7), not assumption.** A is the default favorite on current evidence;
B must be disproven honestly; C is the fallback if single-pass detail fidelity stays
insufficient even with the shell.

---

## 7. Engine bench-off protocol (Open Question #1 — highest priority)

- **Fixed inputs:** the existing run-000001 assets (person photo, reference board,
  layout text) + one new harder outfit (more layers, patterned fabric).
- **Matrix:**
  1. Qwen-2511, Lightning, 4 steps (current baseline)
  2. Qwen-2511, NO Lightning, 20 steps
  3. Qwen-2511, NO Lightning, 40 steps
  4. FastFit (if weights run in 16GB)
  5. (optional) one newer VTON if weights available
- **K=5 seeds each**, same seeds across rows.
- **Metrics (per P4):** per-garment ΔE vs reference; VLM presence/layering checklist;
  button/buckle count match; face landmark distance (pre-shell); wall-clock time.
- **Output:** FINDINGS.md entry + the architecture decision for V1.
- This bench also answers [R]5/**[E]** Lightning question as a side effect (rows 1–3).

---

## 8. V1 — Closed local loop

**Goal:** one orchestrator script runs [1]→[7] end-to-end on a single frontal photo with a
manual `OutfitPackage`. Fragile is fine; closed is mandatory.

- Stylist = manual (owner assembles reference board + layout text; Qwen3 14B may help
  structure the text).
- Orchestrator: Python; ComfyUI client (submit/poll/fetch), LM Studio client, local
  segmentation/compositing/color modules; explicit VRAM sequencing (P7);
  run folder per execution (P6).
- **Build order inside V1:**
  1. ComfyUI client + LM Studio client (plumbing)
  2. Segmentation stage + RegionMap (enables everything)
  3. Deterministic shell steps 1–3 (face, background, color) — immediate quality win,
     zero generative risk
  4. Evaluation per-region
  5. Bench-off (§7) → engine decision
  6. Close the loop with the winning engine; structural repair (shell step 4) last
- **Excludes:** dual-view, complex poses, real backgrounds, retrieval, wardrobe.

### Dual-view (deferred, sharpened hypothesis)
Generate and finalize the front view first; then generate the side view with the finalized
front as an additional reference ("same person, same outfit, side view"); composite the two
finished singles into one canvas deterministically. Never ask the model to hold coherence
across views in one canvas (failed empirically).

---

## 9. V2 — Real garment retrieval

V1 unchanged except Stylist:
- **Stylist reasoning:** LLM turns `PersonProfile` + style request into an outfit concept
  with per-item descriptions. Candidate: Qwen3 14B local; escalate to a stronger model only
  if styling judgment proves weak (Open Q).
- **Garment retrieval:** per-item description → embedding → nearest-neighbor in a local
  catalog index.
  - Embeddings: **FashionCLIP** or **Fashion-SigLIP** (fashion-pretrained; SigLIP-class
    models tend to win on fine attributes — bench on the real catalogs).
  - Vector DB: **Qdrant** (local, open source).
  - Indexing offline: catalog images → embeddings + metadata (name, price, URL).
- Retrieved product images become the `OutfitPackage` reference board automatically.
  Stages [3]–[7] untouched.

## 10. V3 — Wardrobe + product stage

- **Wardrobe:** user's own garments photographed once → VLM-attributed → embedded → separate
  per-user Qdrant index. Stylist searches catalog + wardrobe, can prefer either.
- **Product stage (only if it becomes a product):** generation moves to rented GPU inference,
  indices and orchestrator become services. Multi-user serving makes cloud non-optional here.
  Architecture stays portable (stages = services talking JSON) so this is a re-deploy,
  not a rewrite.
- **Mid-term quality lever:** LoRA fine-tune of the editor on Garments2Look-style outfit data
  (documented large gains). Requires cloud GPU rental → deferred until the project earns it.

---

## 11. Open questions (re-prioritized)

1. **Engine bench-off (§7)** — decides architecture; also settles the Lightning question. *(highest)*
2. **Restoration shell validation** — does deterministic face/background/color restore
   produce seamless results on our photos? (Poisson blending edge cases, lighting mismatch.)
3. **Qwen-with-mask structural repair** — viable, or is FLUX Fill the only option for shell
   step 4? (Only matters where the shell's deterministic steps aren't enough.)
4. **Sequential dressing pilot (Architecture C)** — only if A's per-garment fidelity stays
   insufficient after the shell.
5. **Dual-view composite approach** (§8) — after V1 closes.
6. **Stylist-reasoning quality** — is Qwen3 14B enough? (V2)
7. **FashionCLIP vs Fashion-SigLIP** on real catalogs. (V2)
8. **VRAM sequencing timings** — measure load/unload overhead; confirm the 16GB plan holds.

---

## 12. Verified vs hypothesis ledger

| Claim | Status |
|---|---|
| Qwen-2511 + Lightning-4 best-so-far on layered single-view | [E] verified in our runs |
| 40 steps worse than 4 | [E] but confounded — Lightning was likely on; re-test (§7 rows 1–3) |
| General editors > dedicated VTON for layering | [R] benchmark + [E] trend |
| Detail/color drift is architectural in semantic editing | [R] documented |
| Deterministic face-back restore works | [R] pattern documented; [hypothesis] for our photos until tested |
| Grounded-SAM gives usable garment/detail masks | [R] documented; [hypothesis] on our images until tested |
| color_repair tool works | UNTESTED — validate or rewrite |
| FastFit weak at layering | [R] documented (benchmark user study) |
| Sequential dressing (C) viable | hypothesis |
| LoRA fine-tune big gains | [R] for QIE-2509; [hypothesis] for 2511 |
