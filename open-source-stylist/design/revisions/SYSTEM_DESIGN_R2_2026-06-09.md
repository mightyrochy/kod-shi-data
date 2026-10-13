# System Design — AI Stylist Pipeline

> Complete design vision across three versions (V1, V2, V3), with two candidate
> architectures for the generation core (to be decided by testing).
> Covers: each subsystem's role, the concrete tool candidates, and — importantly —
> how data flows between stages (the interfaces).
>
> This is a design vision, not a fixed spec. FINDINGS.md and the actual code override it.

---

## Design constraints (from project owner)

- **Local-first.** All core processing on the local machine.
- **Open source only.** No paid/closed models for core functionality.
- **No upfront investment.** Learning project that may become a product.
- **Cloud only later** (V3 product stage), and only where it gives a real advantage.
- Owner is not a programmer; system is built with AI agents.

### Hardware reality (must be respected in architecture)
- RTX 4090 **Laptop** = **16GB VRAM** (NOT the 24GB of the desktop 4090), i9, 32GB system RAM.
- 16GB VRAM is shared between language models and image-generation models.
- **Consequence: large models cannot all stay resident at once.** The orchestrator must
  load/unload models in sequence (e.g. run VLM analysis → unload → load generation model →
  generate → unload → load evaluator). This sequencing is a core architectural requirement,
  not an afterthought.
- Practical model ceiling: ~14B LLM at Q5/Q8, or a 7B VLM, OR an image-gen model — not all together.

---

## The core problem

Image generation already works. The hard parts, in order:

1. **Detail & color fidelity.** A styling system must show specific garments accurately
   (exact color, texture, material). Approximations fail the product goal.
2. **Consistency.** Same input → slightly different output each run; worse on multi-view.
3. **Closing the loop automatically** with evaluation and retry.
4. **Sourcing real garments** (V2+).

### Critical insight about detail loss (from research)
Detail loss is likely **architectural, not a post-processing problem**. Models that condition
on a garment via CLIP-style embeddings preserve overall color/texture but lose fine detail —
this is a known, documented limitation of that approach. Dedicated VTON models attack this at
the source (garment warping / reference-only feature injection) rather than repainting after.

This is why the generation core is presented below as **two candidate architectures**, not one.
The current Qwen approach repairs detail after losing it; the alternative avoids losing it.

---

## Data flow — the shared interface model

Every stage is a function: it receives one structured object and returns one structured object.
Stages never reach into each other's internals. This makes any stage swappable.

The objects (JSON) that flow through the pipeline:

```
PersonProfile      ← produced by Person Analysis
OutfitPackage      ← produced by Stylist
GenerationRequest  ← produced by Outfit Adapter
GenerationResult   ← produced by Try-On Engine
EvaluationVerdict  ← produced by Evaluation
RepairPlan         ← produced by Evaluation (if verdict fails)
FinalOutput        ← produced by Postproduction + Re-evaluation
```

Transport between stages:
- **Local model calls** go over HTTP to two local servers:
  - **ComfyUI** on `localhost:8188` — image generation. The orchestrator POSTs a workflow JSON
    (with prompt + input image paths filled in), polls the `/history` endpoint for completion,
    then reads the output image from disk.
  - **LM Studio** on `localhost:1234` — LLM and VLM, via an OpenAI-compatible `/v1/chat/completions`
    endpoint. For VLM calls, images are sent base64-encoded in the message; structured output is
    enforced by asking for JSON and validating against a schema.
- **Between stages**, data is passed as JSON objects in memory by the orchestrator, and also
  written to the run folder (`/runs/NNNNNN/`) as files, so every step is inspectable and resumable.
- **Images** are passed by file path, not embedded, except when sent to a VLM (base64) — keeps
  memory low and every intermediate image saved to disk.

---

## Shared pipeline stages

```
User input (photo + style request)
        │  →  raw photo file + free-text request
        ▼
[1] Person Analysis
        │  →  PersonProfile (JSON)
        ▼
[2] Stylist
        │  →  OutfitPackage (JSON: items + reference images + layout logic)
        ▼
[3] Outfit Adapter
        │  →  GenerationRequest (JSON: composite reference panel path + prompt + params)
        ▼
[4] Try-On Engine   ◄── this is where the two architectures differ
        │  →  GenerationResult (JSON: output image path + metadata)
        ▼
[5] Evaluation
        │  →  EvaluationVerdict (+ RepairPlan if failed)
        ▼
[6] Postproduction   (only if needed — and possibly removed in Architecture B)
        │  →  repaired image path
        ▼
[7] Re-evaluation / retry
        │  →  FinalOutput (image + report)
        ▼
Output
```

---

## Stage-by-stage: roles, tools, and interfaces

### [1] Person Analysis
- **Role:** describe the person to preserve — proportions, hair, face, accessories, skin tone, photo format (front / side / dual-view / full or partial body). Changes nothing.
- **Tool:** **Qwen2.5-VL-7B** via LM Studio (already in use; strong open VLM at 7B, fits 16GB alone).
- **Input:** raw photo (base64 to VLM).
- **Output → PersonProfile:** JSON with fields like `identity_attributes`, `body_shape`, `hair`, `skin_tone`, `accessories`, `photo_format`. Schema-validated.
- **Talks to:** LM Studio `/v1/chat/completions` (vision). Hands PersonProfile to Stylist.

### [2] Stylist  — *differs by version, see V1/V2/V3 below*
- **Role:** decide the outfit; produce concrete items + reference images + layout logic.
- **Output → OutfitPackage:** JSON listing each item (type, description, reference image path) plus `layout_logic` (what is worn over what, what stays visible).

### [3] Outfit Adapter
- **Role:** translate OutfitPackage into exactly what the chosen engine consumes. Makes NO styling decisions — pure formatting for stable, lossless generation.
- **Tool:** deterministic Python (image compositing for the reference panel) + a small local LLM (Qwen3 14B) only for phrasing the prompt.
- **Key finding respected:** prompt influence is weak; the model leans on the reference panel. So the adapter's main lever is the **composite panel layout**, not wording.
- **Input:** OutfitPackage. **Output → GenerationRequest:** composite reference panel image (path) + final prompt + generation params (steps, CFG, seed, LoRA flags).
- **Talks to:** filesystem (writes panel), passes GenerationRequest to the engine.

### [4] Try-On Engine — **TWO CANDIDATE ARCHITECTURES**

#### Architecture A — Qwen-Image-Edit (current)
- **Tool:** Qwen-Image-Edit-2511 + Lightning LoRA, 4 steps, via ComfyUI.
- **How it conditions:** the composite reference panel + prompt; the model re-generates the dressed person from semantic understanding of the references.
- **Findings respected:** 4 steps > 40; Lightning LoRA required at low steps.
- **Known weakness:** semantic re-generation loses fine detail and exact color → REQUIRES stage [6] postproduction to repair.
- **Interface:** orchestrator POSTs the Qwen workflow JSON (panel path + prompt + params) to ComfyUI `:8188`, polls, retrieves output image.

#### Architecture B — Dedicated VTON model (to be tested)
- **Candidates:** DiT-VTON, Voost, OmniTry (mask-free), or a Qwen try-on LoRA.
- **How it conditions:** garment warping / reference-only feature injection — designed to carry the actual garment pixels, preserving detail at the source.
- **Potential payoff:** if detail is preserved during generation, **stage [6] postproduction may be unnecessary**, simplifying the whole system and removing the exact part where work previously stalled.
- **Cost:** new model integration; must verify it runs within 16GB VRAM; must verify it handles "full outfit" (multi-garment) not just single-garment try-on.
- **Interface:** same pattern — a ComfyUI workflow (or standalone inference script) the orchestrator calls; output image to disk.

> **Decision is made by the engine bench-off (see Open Questions #1), not assumed.**
> Both architectures share stages [1][2][3][5][7]; they differ only at [4] and whether [6] exists.

### [5] Evaluation
- **Role:** judge GenerationResult against the four criteria; emit a structured verdict and, if failing, a repair plan.
- **Tools (hybrid — important):**
  - **Qwen2.5-VL-7B** for semantic checks (identity present? all items present? layering correct?) — schema-driven JSON output.
  - **Deterministic color/texture check** (Python): sample regions in the output, compare to reference hex/texture stats. VLMs are weak at precise color judgment, so this criterion is NOT left to the VLM.
- **Input:** GenerationResult + the original PersonProfile + OutfitPackage (to know what *should* be there).
- **Output → EvaluationVerdict** (pass/fail per criterion) **+ RepairPlan** (which regions, what target color/detail) if failing.
- **Talks to:** LM Studio (vision) + local Python; hands verdict to orchestrator.

### [6] Postproduction  *(central in Architecture A; possibly absent in Architecture B)*
- **Role:** repair detail/color the engine lost.
- **Tools:**
  - **Deterministic color repair** — `tools/postproduction_color_repair.py` (already built): masked HSV correction toward target hex. Good for flat color shifts.
  - **FLUX Fill** (ComfyUI) for masked semantic repair (confirmed tight locality: 0.048% outside mask) — for restoring lost structure (buttons, buckles).
- **Open blocker (Architecture A):** FLUX Fill proved locality but not reliable semantic repair; Qwen-with-mask as repair executor was never properly tested. This is the V1 blocker for Architecture A — and the reason Architecture B is worth testing first.
- **Input:** GenerationResult + RepairPlan. **Output:** repaired image path.
- **Talks to:** ComfyUI `:8188` (FLUX Fill workflow) and/or local Python (color tool).

### [7] Re-evaluation / retry
- **Role:** re-run [5] on the repaired image; if still failing, retry (new seed) or flag for manual review. Caps retries to avoid loops.
- **Output → FinalOutput:** final image + a report (which criteria passed, what was repaired, retry count).

---

# V1 — Closed local loop

**Goal:** prove the loop runs end-to-end on a controlled, simple case. Single frontal photo, manually specified outfit, automated generation + evaluation.

Deliberately simple inputs (plain pose, plain background, hand-picked garments) to isolate the core problems before adding real-world complexity.

### Stylist in V1 (manual)
- Outfit specified by hand: a reference board of real garment images + an outfit-layout description. This is the current working approach.
- Tool: Qwen3 14B (in LM Studio) only to help *structure* the layout text, or fully manual. No retrieval.
- **OutfitPackage** is assembled by the owner; the rest of the pipeline is automated.

### V1 orchestration
- One Python orchestrator running stages [1]→[7] in sequence.
- Needs: a **ComfyUI API client** (submit workflow, poll, fetch image) and an **LM Studio client** (OpenAI-compatible).
- Must **load/unload models in sequence** (16GB constraint): VLM for [1], unload; generation model for [4], unload; VLM for [5]. The orchestrator owns this scheduling.
- "Fragile but closed" is the success bar.

### V1 work order — two paths to choose between (resolved by testing, not assumed)
- **Path A (loop-first):** close the simplest loop on Qwen now; do the engine bench-off later.
  - Pro: a working end-to-end loop sooner. Con: risk of rebuilding [4]/[6] if Architecture B wins.
- **Path B (engine-first):** run the engine bench-off first (Qwen vs DiT-VTON/Voost/OmniTry on identical inputs), pick the winner, then build the loop around it.
  - Pro: builds the loop on the right foundation; may delete [6] entirely. Con: delays a working loop.
- The owner's decision: **describe and keep both; the engine bench-off determines which we continue with.**

### V1 excludes
Dual-view, complex poses, real backgrounds, garment retrieval, wardrobe.

### Note on dual-view (from prior testing)
Dual-view (front+side in one image) broke consistency badly (e.g. blouse color flipped between views). Open question #3: solve by generating two single views separately and compositing, rather than one dual-view generation.

---

# V2 — Real garment retrieval

Everything from V1 stays. The change is stage [2] plus a new retrieval subsystem feeding it.

### Stylist in V2 (agent + retrieval)
- **Role:** given PersonProfile + style request, decide the outfit concept and per-item descriptions, then retrieve real matching products.
- **Two sub-roles and how they talk:**
  1. **Stylist reasoning** — an LLM produces an outfit concept: a list of needed items with text descriptions (e.g. "ivory loose V-neck blouse", "brown midi pencil skirt", "green wedge sandals"). Candidate: Qwen3 14B locally; OR a stronger cloud LLM if local styling judgment proves weak (one place cloud may earn its keep — see Open Q #4).
  2. **Garment retrieval** — turns each item description into a query and returns real product images.

### New subsystem: Garment Retrieval — and its data flow
- **Indexing (offline, once per catalog):**
  - garment images → **FashionCLIP** or **Fashion-SigLIP** embedding model → vectors → stored in **Qdrant** (local, open-source vector DB) with product metadata (name, price, url, image path).
- **Query (per outfit item):**
  - item description (text) [and/or a sample image] → same embedding model → query vector →
    Qdrant nearest-neighbor search → top-K real product candidates (image + metadata).
- **Output:** the retrieved product images become the **OutfitPackage** reference board that V1 built by hand. Stages [3]–[7] are unchanged.
- **Embedding choice (Open Q #5):** FashionCLIP vs Fashion-SigLIP — SigLIP tends to win on fine attribute discrimination (neckline, texture); to be benchmarked on the real target catalogs.

### V2 stays local
FashionCLIP/SigLIP, Qdrant, engine, evaluation, postproduction — all local. Only stylist-reasoning LLM is a cloud candidate.

---

# V3 — Wardrobe + product-grade

Everything from V2 stays. Additions:

### Personal wardrobe
- **Role:** user uploads their own garments once; system indexes them; stylist can build outfits mixing owned items with new purchasable ones.
- **Data flow:** each wardrobe item → analyzed (category, color, attributes by the VLM) → embedded (same model as V2) → stored in a **separate per-user Qdrant index**.
- **Stylist now searches two sources:** catalog index (buy) + wardrobe index (own), and can be told to prefer one. Same query mechanism as V2, two indices.

### Cloud architecture (product stage only)
- A multi-user product cannot run on one local GPU.
- **What moves to cloud:** generation engine (GPU inference as a service), catalog index, per-user wardrobe storage, orchestrator as a backend service.
- This is the one place cloud is **not optional** — multi-user serving requires it. It's a deployment decision made only if the project becomes a product.
- **Keep the architecture portable** (stages as independent services talking via JSON) so this move is a re-deployment, not a rewrite.

### Quality bar rises
Reliable consistency, fast turnaround, accurate detail/color — exactly what V1 solves. V3 inherits V1's solutions, which is why solving them properly now matters.

---

## Cross-version principles
- **Each stage is an independent, swappable function** communicating via JSON objects + files on disk. A better engine swaps stage [4] without touching the rest.
- **Reference panel > prompt** (empirical). Invest effort there.
- **Evaluation is hybrid:** VLM for semantics, pixel math for color.
- **Solve fidelity & consistency in V1;** later versions inherit them.
- **Models load/unload in sequence** because of the 16GB VRAM limit — the orchestrator schedules this.
- **Keep it portable** for an eventual cloud move.

---

## Open questions — resolved by testing, in priority order

1. **(HIGHEST) Engine bench-off.** Test Qwen-Image-Edit-2511 (Architecture A) vs DiT-VTON / Voost / OmniTry / Qwen-try-on-LoRA (Architecture B) on identical inputs. The prior "Qwen is best" conclusion was based on old models (IDM-VTON, CatVTON) and few tests; newer VTON models were never tried. **This decides whether postproduction [6] is even needed.**
2. Can Qwen-with-mask do reliable semantic repair, or is FLUX Fill / hybrid needed for [6]? (Only matters if Architecture A wins.)
3. Dual-view: generate two single views separately and composite, instead of one dual-view generation? (Prior testing showed dual-view breaks consistency.)
4. Is local stylist-reasoning (Qwen3 14B) good enough, or is this the one role needing a stronger/cloud LLM?
5. FashionCLIP vs Fashion-SigLIP — which retrieves more accurately on the target catalogs?
6. Does the 16GB VRAM limit force any chosen model out, especially when a generation model and a VLM are both needed in one run? (Validate load/unload timings.)

---

## Review notes — 2026-06-10

<!-- PATH A vs B IS NOT A REAL FORK
     Stages [1][2][3][5][7], the ComfyUI client, LM Studio client, run-I/O, and
     VRAM sequencer are identical regardless of which engine wins.
     Stage [4] is a clean interface. Build the shared backbone first;
     the bench-off then becomes a plugin swap, not a strategic decision. -->

<!-- ARCHITECTURE B WILL NOT ELIMINATE POSTPRODUCTION
     Classical VTON models (DiT-VTON, Voost, IDM-VTON) handle one garment,
     torso/legs focus. A 5-item outfit with accessories still needs Qwen or
     postproduction for belt, shoes, earrings.
     OmniTry is the exception — test it specifically on accessories, not just clothing.
     The bench-off MUST use a multi-item outfit with accessories as the test case.
     A single-garment test will give Architecture B a false advantage. -->

<!-- EVALUATOR NEEDS SEGMENTATION TO MEASURE COLOR
     "Sample regions" requires knowing where each garment is in the output image.
     That means SAM/GroundingDINO segmentation before the color check.
     This is a required sub-step, not an implied one. -->

<!-- TEXTURE IN V1 PASS/FAIL IS NOISE
     Color (mean HSV in a region) is a robust metric.
     Texture across garment drape vs flat product photo is not reliably measurable.
     Recommendation: make texture advisory only in V1; gate on identity / item
     presence / layering / color. Revisit in V2. -->

<!-- postproduction_color_repair.py IS NOT RELIABLE
     Tested and failed as a repair tool. Do not treat it as a working component.
     Deterministic color correction is not the right approach for this problem. -->

<!-- VRAM SEQUENCING NEEDS CONCRETE MECHANISM
     ComfyUI: POST to /free to unload models.
     LM Studio: uses TTL-based unload (no explicit API call); keep TTL short.
     Loading Qwen-Image-Edit from disk is slow (tens of seconds) — accepted cost for V1,
     but must be measured and documented as part of the first end-to-end run. -->

<!-- CONTRACT NAMES ARE INCONSISTENT
     SYSTEM_DESIGN names 7 objects (PersonProfile, OutfitPackage, GenerationRequest,
     GenerationResult, EvaluationVerdict, RepairPlan, FinalOutput).
     Existing schemas use different names (outfit_layout, evaluation_and_repair_plan).
     PersonProfile, GenerationRequest, GenerationResult have no schemas yet.
     Resolve naming and write missing schemas before building the orchestrator — these
     are the interfaces everything else depends on. -->
