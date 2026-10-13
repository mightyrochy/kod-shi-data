# Verified tool survey — primary-source grounded (2026-06-26)

Supersedes the reputation-based `SURVEY_fashion_ai_landscape_2026-06-26.md` / `REFERENCE_MATRIX_2026-06-26.md`
for any capability claim. Method change forced by the Kontext miss (see
`experiments/017_editor_fidelity_benchoff/` + memory `feedback-read-capability-docs-before-install`).

## Method (the bar every entry must clear)
For each tool, verified against the AUTHORITATIVE source (model card / paper / official docs), not a blog:
1. **Specific capability** — does the primary source document the exact thing we need
   (multi-image reference → transfer a specific garment onto a person), not just "image editing"?
2. **License** — Apache/MIT (clean) vs Non-Commercial (eval-only).
3. **VRAM** — does a real variant fit our **16 GB** (fp8/quant counts; offload counts).
4. **Install path** — official ComfyUI / Comfy-Org repackaged (low risk) vs community node vs torch-pin conflict on our py3.12 / torch 2.10 / cu130 stack.
5. **Freshness** — mid-2026 current, weights actually released.

Legend: ✅ verified-pass · ⚠️ partial/needs-test · ❌ verified-fail · 🔬 capability class documented but garment-specific must be proven by a run.

---

## STAGE 4 — Edit / try-on engine (THE crux: faithful garment transfer). Deep pass.

### The gate that matters
We need: **multi-image input** + **take a specific garment from a reference and put it on the person**,
local, ≤16 GB, open license. "Best texture" reputation is NOT this capability — that conflation is what
cost us 12 GB on Kontext.

### Verified shortlist — legitimate local-open multi-reference transfer engines (test these in E-017)
| Engine | Capability (primary source) | License | VRAM (fits 16 GB?) | ComfyUI | Status |
|---|---|---|---|---|---|
| **Qwen-Image-Edit-2511** (incumbent) | multi-image edit (1–3 imgs), transfers full outfit (proven in E-017) | Apache-2.0 | fp8mixed, yes | native | ✅ transfers; **fidelity below owner bar** |
| **OmniGen2** | "combine diverse inputs — humans, reference objects, scenes"; *"the X from image 1 onto … image 2"* | Apache-2.0 | ~9–11 GB (offload/INT8) | **official** (`omnigen2` type in our build) | 🔬 downloading/testing now |
| **HiDream-O1-Image-Dev (fp8)** | multi-reference **subject-driven personalization, up to ~10–12 ref images**, "preserving exact identity"; 8B | **MIT** | **~10 GB** fp8, 28 steps | official | 🔬 strong new candidate (specs cleanest) |
| **FLUX.2-klein-4B** | "single- and **multi-reference** editing / composition", "character, object, style reference" | **Apache-2.0** (4B only) | **~13 GB** (4B + 8B Qwen3 text enc, fp8) | official | 🔬 strong; heavier than above |

All four pass capability-class + license + VRAM by primary source. **Which one clears the fidelity bar is now
the only open question — that is exactly what E-017 must decide empirically** (not from reputation).

### Eliminated by primary source (do NOT spend on these for our need)
| Engine | Why out |
|---|---|
| **FLUX.1-Kontext [dev]** | ❌ card: **single image + text instruction**; multi-image is a ComfyUI workaround. Tested in E-017: both official workarounds fail to transfer (generic white blouse / no change). NC license too. |
| **Step1X-Edit (v1p2)** | ❌ card: **one image + text**, no multi-ref transfer. Apache, but fp8+offload **18 GB** (over budget); recommends 80 GB. |
| **FLUX.2-dev** | ⚠️ HAS multi-reference (real), but **Non-Commercial** + **32B** params (4-bit rec.; 16 GB very tight once the large text encoder loads). Eval-only, heavy. Klein-4B is the usable cut. |
| **Z-Image-Edit** | ❌ not released yet (base Z-Image is Apache; watch for the edit variant). |

### Dedicated VTON (purpose-built person+garment) — secondary track
Literature (re-confirmed) keeps showing the same failure modes that pushed us off them:
- **FitDiT** — texture ok but **distorts body shape** (our own finding + lit).
- **Leffa** — better texture but **darker output + flattened patterns** in complex regions (matches our skirt result).
- **CatVTON / IDM-VTON** — **lose fine-grained texture** on complex garments.
- **Voost** (arXiv 2508.04825) — benchmark **SOTA on try-on + try-off**, but the abstract does **not** confirm a
  weight release / license / VRAM → **not adoptable until the project page confirms open weights.** Watch.
- DS-VTON, shape-guided-warping papers — research, no clean local release verified.
Verdict: VTON stays a *secondary* track; editing-model-first (the shortlist above) remains the spine. Re-open VTON
only if all four editors miss the fidelity bar AND a 2026 VTON ships open weights + no body distortion.

### Free-cloud oracle — CORRECTION (was stale in memory)
**Nano-Banana / Gemini 3 Pro Image ("Nano Banana Pro")**: the "free 500/day" in old notes is **stale**. As of
Feb 2026: **no free API tier**; consumer app = **~2 images/day @1K**, then falls back to base Nano Banana. Paid API
~$0.134/img (1–2K). Supports up to 14 ref images, strong consistency. → **cloud quality-oracle only** (occasional
benchmark), not a pipeline engine, and the free budget is now tiny. Local-first rule unchanged.

---

## STAGE 5 — Masks (carried from verified prior pass; stable, freshness-checked)
- **SegFormer-Clothes (ATR-18)** via ComfyUI-RMBG — semantic garment parse (upper≠skirt) → kills mask bleed. ✅
- **Sapiens2** — quality-ceiling parts + **normal maps** (also the fit lever). ✅
- **BiRefNet / SDMatte** — soft alpha matte, edge-refinement **only where we composite** (repair). ✅
- One parser serves board/measurement/repair; matte is an add-on op, not a second parser.

## STAGE 6 — Evaluation (carried; stable)
- ArcFace (identity), MediaPipe (proportions), CIEDE2000 (colour), AnomalyDINO (structure) — core gates. ✅
- **+ DISTS** beside Marqo-FashionSigLIP for garment similarity (FashionSigLIP still current SOTA-open). ✅
- VLM attribute-match (Qwen3-VL) + outfit-coherence — record-only support.

## STAGE 7 — Finish (carried; stable)
- **Differential Diffusion** (native) — seam-free per-pixel repair blend. ✅
- **IC-Light** — tonal harmonization (kills "brighter region" seam). ✅
- **SUPIR + Face Detailer** — detail/softness recovery, face polish. ✅

## STAGE 3 — Adapter / clean garment refs (raised in priority by E-017)
- **try-off** (Any2AnyTryOn / ComfyUI-Flux-TryOff) → flat garment from a worn/product photo. ✅
- **E-017 evidence:** feeding engines a *collage board* hurt transfer badly; a **clean single-garment reference**
  is materially better. → clean per-garment refs are a cross-cutting quality lever for ALL engines, not optional.

## STAGE 1–2 — Person analysis + stylist brain (V2/V3; carried)
- Qwen3-VL zero-shot (attributes, outfit reasoning); Outfit Transformer / TATTOO (compatibility); FashionSigLIP (retrieval); SMPL-X/PIXIE (body). ✅
- **Personal colour** — still essentially **BUILD**, but **DSCAS** (`mrcmich/deep-seasonal-color-analysis-system`,
  classical colour-harmony + DL segmentation, selfie→12-season palette→clothing retrieval) is a usable **OSS
  scaffold** to start from rather than nothing. ⚠️ reference-grade, not production.

## Cross-cutting — infra / contracts (carried)
- **Nunchaku 4-bit** — still **gated on our stack** (no cu130/torch2.10 wheel; needs torch→cu128 realign). Deferred. With HiDream-O1-Dev/OmniGen2 already ~10 GB, the VRAM pressure that motivated Nunchaku is lower now.
- **Instructor + XGrammar** — schema-valid stage outputs for the closed loop. ✅

---

## What changed vs the reputation survey
1. **Engine shortlist is now capability-verified, not texture-reputation.** Four legitimate local-open candidates
   (QIE, OmniGen2, HiDream-O1-Dev, FLUX.2-klein-4B); Kontext/Step1X/FLUX.2-dev eliminated on hard grounds.
2. **HiDream-O1-Image-Dev (fp8)** surfaced as arguably the best-spec'd new candidate (8B, ~10 GB, **MIT**, multi-ref
   subject-driven up to ~10–12 imgs, official ComfyUI) — was absent from the prior survey.
3. **FLUX.2-klein-4B** is the usable Apache cut of FLUX.2 (multi-ref, ~13 GB) — dev (32B/NC) is not.
4. **Nano-Banana free tier collapsed** (500/day → ~2/day, no free API). Oracle-only.
5. **Clean garment refs** promoted to a first-class quality lever (E-017 evidence).

## Corrected E-017 scope (the decision this unblocks)
Bench the **four** verified engines on the SAME clean garment reference + person, native multi-ref mode each,
owner's eye on fidelity (primary) + identity/proportions/DISTS/FashionSigLIP/CIEDE2000 (record-only):
**QIE-2511 vs OmniGen2 vs HiDream-O1-Image-Dev(fp8) vs FLUX.2-klein-4B.** First one to clear the owner's fidelity
bar sets the base engine; if none do, re-open the VTON track (Voost weight-release) + domain LoRA on the best base.
