# Reference matrix — system stage → tool → adopt/build → priority (2026-06-26)

Single anchor consolidating the two surveys:
- Rendering layer: `research/SURVEY_fashion_ai_landscape_2026-06-26.md` (+ Addendum B)
- Stylist-intelligence layer: `research/SURVEY_stylist_intelligence_2026-06-26.md`
- Masks/seams deep-dive: `research/RESEARCH_masks_seamless_2026-06-25.md`

This is a decision-support map; **priorities are my recommendation, the owner decides direction**. Stages follow
SYSTEM_DESIGN §6. Legend — **A**=adopt off-the-shelf · **B**=build ourselves · **A/B**=adopt base, build glue.
Avail: `[L]`local `[C]`cloud `[~XG]`VRAM `[Apache]`/`[NC]`/`[CC-NC]` license. Prio: **P0** unblock-now ·
**P1** core-V1-quality · **P2** V2/V3-or-later.

---

## Recommended first moves (the P0 spine, in order)
1. **Nunchaku 4-bit Qwen** → frees VRAM (Qwen ~3 GB) → kills the 16 GB co-load pressure (suspected base-nondeterminism cause).
2. **Semantic masks** (SegFormer-Clothes / Sapiens2 + matte) → kills "blouse-mask-eats-skirt" + crude edges.
3. **Seam-free assembly** (Differential Diffusion + soft matte + IC-Light / harmonize pass) → kills the "stitched" look.
4. **Constrained decoding** (Instructor + XGrammar) → contracts always schema-valid → the closed loop can actually be assembled.
These four are infrastructure/quality unblockers; everything else sits on top.

---

## Stage [1] Person Analysis  (→ PersonProfile)
| Need | Tool | A/B | Avail | Prio | Solves |
|---|---|---|---|---|---|
| Attribute/feature extraction | **Qwen3-VL** zero-shot (ours) | A | `[L]` | P1 | photo→structured profile, no training |
| Body-shape class (coarse) | single-image shape-class / DL-EWF | A | `[L][OSS]` | P2 | apple/hourglass label for silhouette rules |
| Body shape (rigorous) | **SMPL-X / PIXIE / ECON** | A | `[L]` heavy | P2 | parametric shape params + normals (also fit lever) |
| Face shape | MediaPipe FaceMesh ratios (ours) | B | `[L]` | P2 | face-shape from landmarks we already compute |
| **Personal colour (undertone/season)** | none good OSS | **B** | — | P2 | **white-space build**: skin/hair/eye LAB+contrast→12-season→palette; feeds colour gate |

## Stage [2] Stylist  (→ OutfitPackage; V2/V3 brain)
| Need | Tool | A/B | Avail | Prio | Solves |
|---|---|---|---|---|---|
| Outfit reasoning (style/season/occasion) | **Qwen3-VL**; bench vs **FashionStylist** | A | `[L]` | P2 | decide + explain the look |
| Compatibility / complementary | **Outfit Transformer**; **TATTOO** (training-free) | A | `[L][OSS]` | P2 | which items go together (FITB/complementary) |
| Item retrieval (V2 catalog) | **Marqo-FashionSigLIP** | A | `[L][Apache]` | P2 | find/compatible-with garments |
| Person→silhouette rules | encode from body-shape+colour | B | — | P2 | "what suits this body" constraints |

## Stage [3] Outfit Adapter  (→ GenerationRequest)
| Need | Tool | A/B | Avail | Prio | Solves |
|---|---|---|---|---|---|
| Clean garment refs from catalog photos | **try-off**: Any2AnyTryOn / **ComfyUI-Flux-TryOff** | A | `[L][CUI]` | P1 | flat-lay garment w/o model body → kills board contamination + powers V2 |
| Garment-ref injection (no panel) | **ACE++ / Redux** | A | `[L][CUI]` | P2 | inject garment as conditioning image |

## Stage [4] Try-On / Edit Engine
| Need | Tool | A/B | Avail | Prio | Solves |
|---|---|---|---|---|---|
| Primary editor (current) | **Qwen-Image-Edit-2511** | A | `[L][Apache][~16/3 w-Nunchaku]` | P1 | our spine; consistent multi-ref edits |
| **A/B alternative** | **OmniGen2** | A | `[L][CUI][~8G]` | P1 | SOTA localized instruction-edit; test vs QIE for repair |
| Commercial/Apache options | FLUX.2-klein-4B `[Apache~13G]`, Z-Image-Edit (pending) `[Apache]`, FLUX.1-Kontext `[NC, best texture]` | A | `[L]` | P2 | license-clean or texture-better fallbacks |
| Free-cloud oracle/engine | **Nano-Banana** (Gemini 2.5 Flash Image) | A | `[C] free 500/day` | P1 | quality oracle + cloud fallback (= Google's prod try-on model) |
| Fit / body-shape preservation | **Sapiens2 normals → `normal` ControlNet** | A/B | `[L][CUI]` | P1 | hold base body shape during edit/repair |
| Dedicated VTON (alt path) | CatVTON `[<8G]`; track UniFit/Voost/OmniVTON++/FitControler | A | `[L]` | P2 | mask-free/fit-aware corrective trend |

## Stage [5] Segmentation / masks  (→ RegionMap)
| Need | Tool | A/B | Avail | Prio | Solves |
|---|---|---|---|---|---|
| **Semantic garment masks** | **SegFormer-Clothes (ATR-18)** via ComfyUI-RMBG | A | `[L][CUI] tiny` | **P0** | upper-clothes≠skirt → kills mask bleed |
| Quality ceiling masks + normals | **Sapiens2** | A | `[L][CUI]` | P1 | pixel-accurate parts + normals for fit |
| Soft edges (anti-seam) | **BiRefNet / SDMatte** | A | `[L][CUI]` | P0 | alpha-matte composite edges |
| Open-vocab fallback | SAM2/SAM3 (RMBG) | A | `[L][CUI]` | P2 | cleaner than our GDINO+SAM-HQ |

**Masks: ONE engine, three jobs — NOT a tool per mask (clarified 2026-06-26).** The board, measurement, and repair
masks are the same operation (segment garment regions on a person image), so a **single semantic clothes parser**
(SegFormer-Clothes; escalate to Sapiens2 where needed) serves **all three**. The rows above are *options*, not
one-tool-per-job. Two genuine additions are different *operations*, not extra parsers: **soft matte**
(BiRefNet/SDMatte) is an **edge-refinement on top** of the same mask, used **only where we composite** (repair),
not for measurement; **try-off** (§stage [3]) is a different operation — **garment reconstruction from a flat /
product photo** — used only when a board reference is not a person photo. Net: one parser + matte-for-composite +
try-off-for-catalog. Keeps it simple, one model loaded, low VRAM.

## Stage [6] Evaluation  (gates → EvaluationVerdict)
| Need | Tool | A/B | Avail | Prio | Solves |
|---|---|---|---|---|---|
| Identity / proportions / colour / structure | ours (ArcFace, MediaPipe, CIEDE2000, AnomalyDINO) | — keep | `[L]` | P1 | core deterministic gates |
| Garment similarity | **+ DISTS** beside FashionSigLIP | A | `[L]` | P1 | best garment-sim metric |
| Attribute match | VLM / Fashionpedia attrs(ref vs out) | A/B | `[L]` | P1 | wrong category/pattern/material ΔE misses |
| Outfit coherence | FashionStylist-style MLLM check | A/B | `[L]` | P2 | style/season/occasion + mismatch flag |

## Stage [7] Restoration / finish
| Need | Tool | A/B | Avail | Prio | Solves |
|---|---|---|---|---|---|
| Seam-free repair | **Differential Diffusion** (native) + soft matte | A | `[L][CUI]` | **P0** | per-pixel blend inside same model, no hard seam |
| Tonal harmonization | **IC-Light** relight region→base tone; or low-denoise harmonize pass | A | `[L][CUI]` | P0 | fixes "brighter region" tonal seam |
| Detail / softness | **SUPIR + Face Detailer** (+4x-UltraSharp) | A | `[L][CUI]` | P1 | counters QIE soft fabric; face polish |
| Face restore (conditional) | GFPGAN/CodeFormer (ArcFace-gated) | A | `[L][CUI]` | P2 | only when identity gate drops |

## Cross-cutting — infra / control / automation
| Need | Tool | A/B | Avail | Prio | Solves |
|---|---|---|---|---|---|
| **VRAM headroom** | **Nunchaku / SVDQuant 4-bit** (Qwen ~3 GB) | A | `[L][CUI]` | **P0** | co-load all models on 16 GB; 3× faster; removes nondeterminism pressure |
| **Schema-valid stage outputs** | **Instructor** (+ **XGrammar** via vLLM/SGLang) | A | `[L][OSS]` | **P0** | contracts never break → closed loop assemblable |
| Agent orchestration (V2/V3) | ref: Wardrowbe / Fashion-Assistant; gates = guardrails | A/B | `[L]` | P2 | analyze→reason→render→evaluate→repair |
| Domain fine-tune (kill-criterion) | **AI-Toolkit / Musubi** (Qwen-Edit LoRA from ~6 GB) | A | `[L]` | P2 | on-machine escalation if local-open stalls |
| Free heavy-model bursts | HF ZeroGPU / Kaggle / Colab | A | `[C] free` | P2 | run >16 GB models (Sapiens2-2B, FLUX.2-9B) free |

---

## P0 install-feasibility verification (2026-06-26, read-only env check)
Env confirmed: ComfyUI `.venv`, **Python 3.12.11, torch 2.10.0+cu130 (CUDA 13)**, transformers 5.9.0,
diffusers 0.28.2, protobuf 7.35.0, onnxruntime-gpu 1.26.0, iopath 0.1.10, decord/ftfy/timm present.
- **Nunchaku (#1): model exists** (`nunchaku-ai/nunchaku-qwen-image-edit`, Edit-2511 INT4) **but backend NOT
  installable clean on our stack** (verified 2026-06-26). No prebuilt wheel for **cu130 + torch2.10 + cp312**
  anywhere: official stable 1.2.1 = cu12.8 only; community (Wildminder) cu130 wheels are **torch2.9** only
  (`nunchaku-1.0.1+cu130torch2.9-cp312-win`), wrong torch-minor (per-torch ABI) + old nunchaku that may lack
  Edit-2511 support; build bug for cp312+cu130 (issue #789). **Reliable route = realign torch to 2.10+cu128**
  (whole-stack change; official `cu12.8torch2.10-cp312-win` wheel then works + supports Edit-2511) — a deliberate
  env decision, not a drop-in. **Recommendation: DEFER Nunchaku**; rely on ComfyUI native offload/sequencing for
  VRAM until an exact cu130/torch2.10 wheel lands or a planned env refresh. The other 3 P0s are unaffected.
- **ComfyUI-RMBG (#2): installable with care.** Most deps already present; only add `transparent-background`,
  `hydra-core`, `omegaconf` (light). One conflict: RMBG pins `protobuf<6` vs our 7.35 — install the node WITHOUT
  the blind `pip -r` protobuf downgrade; test SegFormer-Clothes in isolation. Low–moderate risk.
- **Differential Diffusion (#3): native in ComfyUI, zero new deps → safest first move.**
- **Instructor (#4): pure-Python, outside ComfyUI, zero risk to the generation env.**
- **Revised P0 order:** #3 → #4 (both ~zero risk) → #2 (careful, no protobuf downgrade) → #1 (gated on cu130 wheel).

## How this changes our default pipeline (vs the QIE+FitDiT path)
Drop FitDiT from the default (literature + our data: distorts body + brighter tone). New default skeleton:
`Qwen-Edit (Nunchaku) holistic → semantic SegFormer/Sapiens2 mask + matte → gate each garment →
repair only failures via Differential-Diffusion inside Qwen + Sapiens2-normal ControlNet → IC-Light/harmonize →
SUPIR detail → gates (incl. DISTS/attribute/coherence) → owner`. All local, mostly Apache, seam-free, fit-aware,
VRAM-comfortable. Stylist brain (Qwen3-VL + Outfit Transformer/TATTOO + FashionSigLIP) and personal-colour build
are P2/V2 additions on top. Open decision for the owner: confirm this default direction (vs keeping/parallel-
tracking a dedicated VTON), and which P0 to start with.
