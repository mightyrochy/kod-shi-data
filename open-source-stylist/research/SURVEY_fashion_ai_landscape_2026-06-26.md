# Fresh full survey — fashion + AI-image systems & tools (2026-06-26)

Owner brief: set our QIE+FitDiT design aside; survey *everything* useful for fashion / AI-image work, fresh as of
today, **local open-source or free cloud first**, verify availability. This is a landscape map, not a plan.

**Verification tags:** `[L]` local-runnable · `[C]` cloud/API · `[~XGB]` approx VRAM · `[CUI]` ComfyUI node exists
· `[lic:…]` license · `[ver]` I confirmed via fetch/primary page · `[clm]` search-claim, not independently
confirmed · dates = release/freshness. 16 GB = our ceiling (RTX 4090 Laptop).

---

## 1. Base image-EDITING engines (the "editing-first" spine)
The strongest current direction for our task is instruction/reference image-editing, not dedicated warping VTON
(see §13). Candidates that run locally on 16 GB:

| Model | VRAM | License | Edit? | Notes |
|---|---|---|---|---|
| **Qwen-Image-Edit-2511** (ours) | fp8 ~16 GB `[L]` | Apache-2.0 `[clm]` | yes, multi-ref | Accepts person + up to 3 garment images → reference panel → places garments following pose/lighting/identity; most *consistent*, follows prompts literally. Weakness: can look **smoothed/soft** on fine fabric. `[CUI]` |
| **FLUX.1 Kontext [dev]** | ~16–24 GB (fp8/GGUF fits) `[L]` | **Non-Commercial** v2.0 `[clm]` | yes, in-context | **Retains finer fabric/texture detail than Qwen/Nano-Banana** — directly addresses our cuff-softness complaint. NC license blocks commercial V2/V3. `[CUI]` |
| **FLUX.2 [klein] 4B** | **~13 GB** `[L]` | **Apache-2.0** `[ver]` (9B = NC) | yes, unified T2I+edit+multi-ref | Launched 2026-01-15; 4-step distilled; commercial-OK at 4B. Newest BFL open option that fits us. `[CUI]` emerging |
| **Z-Image (Tongyi)** Turbo/Edit | **12–16 GB** `[L]` | **Apache-2.0 (all variants)** `[ver]` | Edit variant *planned, not yet released* as of survey | 6B, sub-second, bilingual; fully-commercial Apache. **Watch for Z-Image-Edit** — Apache instruction-edit at our VRAM would be a strong base. |
| **Step1X-Edit v1p2** | ~16–24 GB `[L]` | check `[clm]` | yes, **reasoning** edits | "Thinks through" complex edits. Heavier; verify VRAM/license before adoption. |
| **Nano Banana** = Gemini 2.5 Flash Image | n/a `[C]` | proprietary | yes, clothes-change | **FREE 500 img/day @1024² via Google AI Studio, no card** (§12). Good at outfit swaps; less fine-texture than Kontext. Best *free-cloud* editor. |

**Takeaway:** editing-first is sound; the open question is texture fidelity (Kontext best, NC) vs commercial
license + VRAM (Qwen/FLUX.2-klein/Z-Image Apache). Z-Image-Edit is the one to watch.

## 2. Dedicated virtual try-on (VTON) models
| Model | VRAM/fit | Code/CUI | Quality notes |
|---|---|---|---|
| **CatVTON** | **<8 GB**, 1024×768 ~35 s `[L][CUI]` | yes | Lightweight inpaint-concat; best VRAM/speed; "good-enough" baseline. |
| **IDM-VTON** | higher `[L][CUI]` | yes | Higher realism/fidelity, heavier; dual-encoder. |
| **Leffa** (ours) | dual-UNet, heavy `[L]` | yes | Flow-in-attention (CVPR'25); strong texture, but **darker tone**; densepose-hard on skirts. |
| **FitDiT** (ours) | `[L]` | `[CUI]` | DiT VTON; **literature-confirmed: distorts body shape + brighter garments** — the source of our seams/proportion drift. |
| **Kolors-VTON** | `[L]` | — | **Fails skirt texture**, distorts some outfits `[clm]`. |
| **OmniVTON++** | training-free `[C/L]` 2026-02 | paper | Structured Garment Morphing + Principal Pose Guidance; SOTA cross-dataset; structure-preserving. |
| **UniFit** | 2025-11-19 **code** | paper+code | MLLM-guided semantic alignment; universal. |
| **Voost** | 2025-08-06 | paper | One DiT does **VTON+VTOFF bidirectionally**; flexible direction/category conditioning. |
| **MFP-VTON / JCo-MVTON** | 2025 | paper | **Mask-free** DiT → no mask, no composite seam (preserves original detail). |
| **PROMO** | 2026 | paper | Promptable outfitting, efficient high-fidelity. |
| **FitControler** | 2025-12 | paper | **Fit plug-in via ControlNet** for existing VTON — body-proportion control (our exact gap). |

Common 2026 finding: inpaint-warp VTON "neglects physical garment sizing" → texture preserved, **fit/shape
distorted**. Mask-free + fit-aware are the two corrective trends.

## 3. Virtual try-OFF (garment extraction from worn photos) — strategic for V2/V3
Reconstruct a clean flat-lay garment from a catalog/worn photo → produces **clean garment references with no
model body** = directly solves our board-contamination problem and feeds V2 retrieval.
- **TryOffDiff** (SigLIP-conditioned), **TryOffAnyone** (tiled) — foundational.
- **Voost**, **Any2AnyTryOn** (2025-01, **code**, 1st unified VTON+VTOFF) — DiT, task-aware.
- **cat-try-off-flux** + **ComfyUI-Flux-TryOff** `[CUI]` — FLUX.1-dev + CatVTON try-off, **runnable in ComfyUI now**.
- **AlignVTOFF** (2026), **BridgeDiff** (2026), **MGT**, **Dress-ED** (instruction-guided VTON+VTOFF) — newest.

## 4. Segmentation / parsing (masks) — see also research/RESEARCH_masks_seamless_2026-06-25.md
- **Sapiens2** (Meta, 2026-04-24) `[L][CUI via wrapper]` — 1K ViT/1B images; pixel-accurate body+**clothing
  items**+hair+earrings; also outputs **normals/depth** (feeds §6 fit). Current quality ceiling.
- **SegFormer-Clothes (ATR-18) / Fashion (b3)** via **ComfyUI-RMBG** `[L][CUI]` — semantic per-garment masks
  (upper-clothes≠skirt) → kills the "blouse mask eats skirt" bleed; tiny models.
- **BiRefNet / SDMatte** (in ComfyUI-RMBG) `[L][CUI]` — alpha-matte soft edges → seam-free composite boundaries.
- **SCHP/ATR-18** (we have in Python), **SAM2/SAM3** (RMBG/easy-sam3), **DensePose** (controlnet_aux). Note:
  DensePose distorts on long/loose skirts (avoid as skirt geometry source).

## 5. Identity preservation
- **ArcFace** (eval, we use) — keep as the identity gate.
- **InfiniteYou (InfU)** `[L]` FLUX — best ID-similarity + text-alignment, fewer copy-paste artifacts.
- **PuLID-FLUX II** `[L][CUI]`, **IP-Adapter-FaceID**, **WithAnyone** (2025-10) — ID-consistent generation.
- For **Qwen** the ID-adapter ports are **emerging/unverified** (PuLID-II/InfiniteYou/Redux-Qwen status open).
- Face restore: **GFPGAN / CodeFormer / ReActor** `[L][CUI]` — only when ArcFace gate drops (our shell already
  scoped this conditional).

## 6. Structure / body control (the fit lever)
- **Qwen-Image ControlNet-Union (InstantX)** + **Union DiffSynth control-LoRA** (we use) — canny/softedge/depth/
  pose/**normal**/openpose. `[L][CUI]`
- **FLUX ControlNet Union (InstantX)** + **Jasperai normal/depth** `[L][CUI]`.
- **Redux / IP-Adapter** — image-prompt conditioning (style/garment reference without text).
- **Fit insight (2026):** surface **normal maps are the geometry-preserving bridge** that keeps body shape;
  **Sapiens2 emits normals** → feed as a `normal` ControlNet to hold the base body shape during any repair. This
  is the concrete, local realization of FitControler/FIT's idea.

## 7. Seamless assembly / harmonization (anti-"stitched")
- **Differential Diffusion** (native ComfyUI) — gradient mask → per-pixel denoise → no hard seam; works through
  any checkpoint (so through QIE/FLUX directly → same tone as base).
- **BrushNet / PowerPaint / Fooocus-Inpaint** `[CUI]` — plug-and-play inpaint (SD/SDXL-side); context-aware.
- **Soft-matte edges** (SDMatte/BiRefNet) + **final low-denoise harmonization pass** (img2img ~0.2–0.3 over the
  whole frame) → melts residual seams + fixes tonal mismatch.
- Research: HarmonPaint (training-free soft-attention), Blend-Aware Latent Diffusion, PCT-Net/libcom harmonizers.

## 8. Fashion retrieval / embeddings
- **Marqo-FashionSigLIP / FashionCLIP** (150M, **Apache-2.0**, +57% over FashionCLIP-2.0; GCL over 7 fashion
  aspects) `[L]` — **already our eval embedding; confirmed current SOTA open**. Use for V2 retrieval too.

## 9. Evaluation metrics
- **DISTS** — most reliable single metric for **garment image similarity** (perceptual+structural); add it.
- SSIM/LPIPS (paired) + FID/KID (unpaired) — standard but **weakly correlated with human perception**.
- New benches: **VTONQA** (2026-01), **OpenVTON-Bench** (2026-01), reference-free IQA via human feedback (2026).
- VLM-judge (Qwen3-VL) advisory; **owner eye = final** (our existing stance holds).

## 10. Stylist agent (V2/V3 — outfit decision + retrieval)
- **Wardrowbe** (OSS wardrobe app; **Ollama / OpenAI-compatible**, Docker, runs on Pi5) — reference arch for
  local wardrobe + suggestions.
- **Fashion-Assistant** (SkalskiP) — YOLO + CLIP + DINOv2 features → LLM querying.
- **FitCheck.AI** — Streamlit + LangChain + CLIP + Qwen auto-tagging + recommendations.
- Pattern: VLM auto-tag garments → LLM compatibility reasoning → FashionSigLIP retrieval → try-off to clean refs.

## 11. Toolkits / frameworks
- **OpenTryOn** (tryonlabs) `[ver]` — **CC BY-NC-4.0 (non-commercial)**; *local* parts = U2Net seg + OpenPose +
  TryOnDiffusion (dual-UNet) + FLUX.1-dev LoRA; FLUX.2/Nano-Banana/Kling/Nova only as **paid API wrappers**.
  Useful as a *structure/reference* (it codifies seg→parse→pose→try-on), but its local models are **weaker** than
  Sapiens2/SegFormer + our QIE. NC license matters if we ever go commercial.
- **ComfyUI** — our spine; CES-2026 NVIDIA update gives up to 3× speedups + NVFP4/FP8 quant.
- Serving: **LM Studio** (ours), **Ollama**, **vLLM** for the LLM/VLM side.

## 12. Free / cheap cloud (priority per brief)
- **Google AI Studio — Nano Banana (Gemini 2.5 Flash Image): FREE 500 images/day @1024², no credit card** `[ver-ish]`
  → best free-cloud image editor for outfit swaps; good for rapid iteration / a cloud fallback engine.
- **HF Spaces ZeroGPU** — H200/RTX-Pro-6000, **free 3.5 GPU-min/day** (PRO: $1 / 10 min) → run heavy OSS models
  (Sapiens2, FLUX.2-9B, VTON) we can't fit at 16 GB, for free in small bursts.
- **Google Colab** (free T4 ~16 GB), **Kaggle** (free **30 GPU-h/week**, dual T4) → notebook runs of any OSS model.
- Paid-cheap: **Imagen-4 Fast $0.02/img**, Nano-Banana $0.039, Nano-Banana-Pro $0.134; 3rd-party (Kie.ai/Pixazo)
  cheaper; **Batch API −50%**. fal.ai / Replicate / Modal — credit-based, no durable free tier for image gen.

---

## 13. Synthesis for OUR case (local-OSS first), not anchored to the old design
Three coherent fresh architectures, each evaluated on our 4 axes (identity / presence / layering / colour-texture)
+ 16 GB + license + seam-free:

**Path A — Editing-first, fully local, seam-free (recommended primary).**
QIE-2511 (or FLUX.2-klein-4B Apache, or Z-Image-Edit when out) holistic edit = one coherent, seam-free image →
**semantic mask** (SegFormer-Clothes / Sapiens2) gates each garment → repair only failures via **Differential
Diffusion inside the same model** with a **soft matte edge** + **Sapiens2-normal ControlNet** to hold body shape →
**one low-denoise harmonization pass**. No FitDiT, one tone, fit-preserving. Everything local, mostly Apache.
Texture-fidelity risk on QIE → consider FLUX.1-Kontext for the repair pass (NC license caveat).

**Path B — Free-cloud accelerant / oracle.**
Use **Nano Banana free tier** (500/day) and **HF ZeroGPU / Kaggle** to (1) get a high-quality reference/oracle to
benchmark our local output against, and (2) run models too big for 16 GB (Sapiens2-2B, FLUX.2-9B) in bursts. Keeps
the product local while using free cloud for evaluation headroom and heavy preprocessing.

**Path C — Adopt a fit-aware / mask-free VTON instead of editing.**
Track **UniFit / Voost / OmniVTON++ / FitControler** — mask-free + fit-aware are the literature's answer to exactly
our seam + body-distortion problems. Mostly research-stage (verify code/license/VRAM); revisit when a CUI-ready,
16 GB-fitting release lands.

**Cross-cutting upgrades regardless of path:** masks → Sapiens2/SegFormer-Clothes + matte; seams → Differential
Diffusion + harmonize; fit → normal-map conditioning; eval → add **DISTS** beside FashionSigLIP; V2 ingestion →
**try-off (Any2AnyTryOn / ComfyUI-Flux-TryOff)** to make clean garment refs from catalog photos.

---

## ADDENDUM B (2026-06-26) — gap-fill after self-audit (owner flagged the first pass as too quick)
Eight high-relevance areas the first pass missed or skimmed. Several are **more impactful for us than anything
above** (esp. §14 quantization and §17 OmniGen2).

### 14. Quantization for 16 GB — Nunchaku / SVDQuant  ★ highest-impact miss
- **SVDQuant** (ICLR'25): 4-bit (INT4/NVFP4) PTQ, absorbs outliers via low-rank branch, ~**75 % size cut, minimal
  quality loss**; FLUX 3.5× less memory; INT4 **3× faster than NF4 on RTX 4090 (laptop incl.)**.
- **ComfyUI-nunchaku v1.0** `[L][CUI]` supports **Qwen-Image**; with **async offload Qwen runs in ~3 GiB VRAM,
  no perf loss**; bundles ControlNet-Union-Pro 2.0 + initial **PuLID**.
- **Why it matters:** our suspected base non-determinism came from co-loading QIE+FitDiT+SAM+GDINO on 16 GB.
  Nunchaku-Qwen at ~3 GB **dissolves the VRAM pressure** → co-load masks+control+identity comfortably, or run a
  bigger engine. This is the single most useful infra find.

### 15. Reference / subject injection (garment-ref without training)
- **ACE++** (ali-vilab) `[CUI]` — reference-image subject/portrait generation **without LoRA training**; pairs with
  **FLUX.1-Fill + Redux**. **Redux** = image-prompt FLUX with one+ images. Use to inject a garment reference as a
  conditioning image rather than a board panel. (OmniControl/USO/EasyControl exist but thin sourcing — verify later.)

### 16. Relighting / harmonization — IC-Light  ★ direct tonal-seam fix
- **IC-Light** (lllyasviel) `[L][CUI]` — FG/BG-conditioned relighting; **harmonizes foreground+background
  lighting**; consistent enough that relightings merge as normal maps. Concrete tool to **relight a composited/
  repaired region to match the base tone** — addresses the FitDiT "brighter garment" seam directly. (SD1.5-based;
  used as a post-harmonization step.) See also UniLight (2025-12), Relightful Harmonization.

### 17. More unified editing engines (real QIE alternatives)
- **OmniGen2** `[L][CUI]` **~8 GB, runs on 16 GB** — **SOTA open instruction-edit**: highest Perceptual Quality
  (7.94) + 2nd Semantic Consistency on GEdit-Bench; **precise localized edits without disturbing the rest**; beats
  BAGEL, Flux-Kontext, some GPT-4o cases. **Strong candidate to A/B against QIE for our localized-repair need.**
- **HiDream-O1-Image (8B)** — natively unified pixel-level transformer, open-sourced 2026-05 (distilled+undistilled).
- **BAGEL** — unified but weaker at editing than OmniGen2.

### 18. Fine-tuning / LoRA (the kill-criterion escalation, now concrete & local)
- **AI-Toolkit (Ostris)** — primary for FLUX.2 / Z-Image / **Qwen-Image** training; **OneTrainer**, **SimpleTuner**
  (bghira), **Kohya SS**, **Musubi Tuner** (1-click presets for **Qwen-Image-Edit**, FLUX-Klein/2, Z-Image).
- **Qwen-Image-Edit LoRA + full fine-tune is possible LOCALLY from ~6 GB VRAM** → we can domain-adapt the editor on
  outfit data **on our own 16 GB machine**, not only cloud. Cloud option: RunPod/Massed-Compute $0.5–2.7/hr;
  Shakker AI = web UI, no local GPU. This makes BUILD_PLAN's escalation path actionable without leaving local.

### 19. 3D body / avatar (hard fit-preservation anchor)
- **SMPL-X** (body+hands+face, shape params encode height/volume/proportions), **PIXIE** (predicts SMPL-X from RGB),
  **ECON** (single-view 3D human, SMPL-X + **normal-map integration** for clothes), **MExECON** (multi-view).
  Heavier, ComfyUI integration thin. The "hard" route to lock proportions vs the lighter Sapiens2-normal-ControlNet
  (§6). Most useful via their **normal maps**, which converge with §6's fit lever.

### 20. Upscale / detail / face-restore (against QIE softness)
- **SUPIR** `[L][CUI]` (kijai wrapper) — diffusion super-res; recovers texture detail while "preserving softness
  where appropriate"; Noise-Setting ~1.001 = minimal deviation. + ESRGAN upscalers (**4x-UltraSharp**, **Foolhardy
  Remacri**), **Face Detailer** for faces, **SeedVR2** for video. → final detail pass to counter QIE's soft fabric.

### 21. Video / multi-view try-on (V2/V3, dual-view)
- **ViViD** (video VTON, large dataset), **Fashion-VDM** (Google; 64-frame single-pass 512px, split-CFG, identity+
  motion preserving). Research-stage, heavy → future dual-view / animation, not V1.

### 22. Commercial quality bar (reference target)
- **Google's production try-on = "Nano Banana"** custom model — understands **fabric draping + body geometry** over
  billions of items. (The same model we can hit **free 500/day** — strong signal it's genuinely good at our task.)
- FASHN.ai (cheap dev API), Camclo3D (claims 0.98 SSIM), Nightjar, Kling, Kolors. Industry-wide hard cases match
  ours: small text/logos, sheer fabrics, **layered outfits**.

### Addendum-B effect on the synthesis (§13)
- **Adopt Nunchaku** regardless of path → removes the 16 GB co-load ceiling (infra win, do early).
- **A/B OmniGen2 vs QIE** as the local edit engine for the repair step.
- **IC-Light** = the concrete tonal-harmonization tool for Path A's finish.
- **SUPIR + Face Detailer** = final detail pass for QIE softness.
- **Local Qwen-Edit fine-tune (AI-Toolkit/Musubi, ~6 GB)** makes the kill-criterion escalation reachable on-machine.

## Sources
Engines: BentoML guide https://www.bentoml.com/blog/a-guide-to-open-source-image-generation-models · FLUX.2 klein
https://bfl.ai/models/flux-2-klein , https://huggingface.co/black-forest-labs/FLUX.2-klein-4B , license
https://bfl.ai/licensing · Z-Image https://zimage.design/blog/z-image-vs-flux-comparison/ · SiliconFlow on-device
https://www.siliconflow.com/articles/en/best-open-source-AI-for-on-device-image-editing · Qwen vs Kontext vs Nano
https://medium.com/diffusion-doodles/qwen-image-edit-vs-flux-1-kontext-vs-nano-banana-93fba1348a77 , https://myaiforce.com/nano-banana-vs-kontext-vs-qwen/
VTON: comparison https://miragic.ai/company/blogs/top-4-open-source-virtual-try-on-viton-models-compared , https://opencreator.io/blog/ai-virtual-try-on-models ·
Awesome-Try-On https://github.com/Zheng-Chong/Awesome-Try-On-Models · UniFit https://arxiv.org/html/2511.15831 ·
Voost https://arxiv.org/pdf/2508.04825 · OmniVTON++ https://arxiv.org/html/2602.14552v2 · MFP-VTON https://arxiv.org/pdf/2502.01626 ·
JCo-MVTON https://arxiv.org/pdf/2508.17614 · PROMO https://arxiv.org/html/2603.11675 · FitControler https://arxiv.org/abs/2512.24016 · FIT https://arxiv.org/abs/2604.08526
Try-off: awesome-vtoff https://github.com/rizavelioglu/awesome-virtual-try-off · Any2AnyTryOn, TryOffDiff https://arxiv.org/abs/2411.18350 ·
ComfyUI-Flux-TryOff https://www.runcomfy.com/comfyui-nodes/ComfyUI-Flux-TryOff
Masks: Sapiens2 https://github.com/facebookresearch/sapiens2 · ComfyUI-RMBG https://github.com/1038lab/ComfyUI-RMBG · SCHP https://ar5iv.labs.arxiv.org/html/1910.09777
Identity: InfiniteYou https://arxiv.org/html/2503.16418v1 · PuLID-Flux https://www.runcomfy.com/comfyui-workflows/pulid-flux-ii-in-comfyui-consistent-character-ai-generation · WithAnyone https://arxiv.org/html/2510.14975v1
Control: Qwen ControlNet-Union https://huggingface.co/InstantX/Qwen-Image-ControlNet-Union , https://blog.comfy.org/p/comfyui-now-supports-qwen-image-controlnet · FLUX CN https://comfyui-wiki.com/en/resource/controlnet-models/controlnet-flux-1
Seams/inpaint: ComfyUI-BrushNet https://github.com/nullquant/ComfyUI-BrushNet · differential diffusion https://www.promptingpixels.com/tutorial/soft-inpainting-in-comfyui · HarmonPaint https://arxiv.org/html/2507.16732v1
Retrieval: Marqo-FashionCLIP https://github.com/marqo-ai/marqo-FashionCLIP , https://huggingface.co/Marqo/marqo-fashionSigLIP
Eval: VTONQA https://arxiv.org/html/2601.02945v1 · OpenVTON-Bench https://arxiv.org/pdf/2601.22725 · TryOff dual-UNet (DISTS) https://arxiv.org/html/2604.08716
Agent: Wardrowbe https://wardrowbe.com/blog/wardrowbe-ios-android-open-source-2026/ · Fashion-Assistant https://github.com/SkalskiP/fashion-assistant
Toolkit: OpenTryOn https://github.com/tryonlabs/opentryon , docs https://tryonlabs.github.io/opentryon/
Free cloud: ZeroGPU https://huggingface.co/docs/hub/en/spaces-zerogpu · Colab/Kaggle https://iotbyhvm.ooo/best-free-cloud-gpu-platforms-in-2026-google-colab-kaggle-and-more/ · Gemini free https://www.aifreeapi.com/en/posts/gemini-image-generation-free-api · NVIDIA CES2026 https://developer.nvidia.com/blog/open-source-ai-tool-upgrades-speed-up-llm-and-diffusion-models-on-nvidia-rtx-pcs/
Addendum B: Nunchaku/SVDQuant https://github.com/nunchaku-ai/nunchaku , ComfyUI plugin https://github.com/nunchaku-ai/ComfyUI-nunchaku , Qwen build https://huggingface.co/nunchaku-ai/nunchaku-qwen-image · ACE++ https://github.com/ali-vilab/ACE_plus · FLUX Redux https://comfyui-wiki.com/en/tutorial/advanced/image/flux/flux-1-redux-dev · IC-Light https://github.com/lllyasviel/IC-Light , ComfyUI https://www.runcomfy.com/comfyui-nodes/ComfyUI-IC-Light · OmniGen2 https://arxiv.org/html/2506.18871v4 , ComfyUI https://docs.comfy.org/tutorials/image/omnigen/omnigen2 · HiDream-O1 https://arxiv.org/html/2605.11061v1 · Training: AI-Toolkit/Musubi https://github.com/bghira/simpletuner , Qwen-Edit training https://github.com/FurkanGozukara/Stable-Diffusion/wiki/Qwen-Image-Models-Training-0-to-Hero-Level-Tutorial-LoRA-and-Fine-Tuning-Base-and-Edit-Model · Body: ECON/SMPL-X/PIXIE (mesh survey) https://arxiv.org/html/2402.18844v1 · Upscale: SUPIR https://github.com/kijai/ComfyUI-SUPIR · Video: ViViD https://arxiv.org/pdf/2405.11794 , Fashion-VDM https://arxiv.org/abs/2411.00225 · Commercial: try-on tools 2026 https://nightjar.so/blog/best-tools-ai-virtual-try-on
