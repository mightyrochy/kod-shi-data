# Try-on engine landscape — local-first, all families (2026-06-16)

Research note for E-010. Goal: on **RTX 4090 Laptop 16 GB**, achieve exact try-on of a
**multi-item outfit (blouse + skirt + belt + earrings + wedge sandals)** on the SAME person,
preserving **identity + a non-idealised body** and **exact garment detail**. License matters for a
real product. This is a literature/landscape survey from sources — it narrows candidates; it does
NOT prove any works on our case. Only prototyping (E-010) decides.

**Headline:** a dedicated VTON model ≈ "inpaint + body-control in one" (agnostic mask keeps the
person's pixels; DensePose/pose keeps the body shape; garment enters as an image). Several fit 16 GB.
**But:** no single local open model cleanly covers {multi-item + accessories + non-idealised body +
exact detail} today — each family trades something. The choice is a staged bet, possibly an assembly,
possibly cloud for parts.

**Priority correction (2026-06-16):** garment exact-fidelity is product axis #1 (showing the SPECIFIC
item); body morphology is secondary. So the families that keep the **real garment pixels** —
**warping / high-res feature injection** (FitDiT, DiffFit, GP-VTON) and **per-item high-res references +
single-item local repair** — lead for our goal; pure generative VTON (re-synthesises → detail drift)
ranks below them on the garment axis. Read this survey through that lens. Chosen generation tools:
`GEN_INSTRUMENTS.md`; measurement: `EVAL_INSTRUMENTS.md`; experiment spec: `protocol.md`.

---

## Family 1 — Single-garment all-in-one VTON (mature, lightest)

| Model | VRAM | License | Body/ID | Multi-item | Notes |
|---|---|---|---|---|---|
| **Leffa** (Meta) | **~4 GB** | **MIT — commercial OK** | DensePose pose+shape | 1 garment/pass | lightest + only permissive license; also does pose control; ComfyUI node exists |
| **CatVTON** (ICLR25) | <8 GB | CC-BY-NC-SA | SCHP+DensePose agnostic | 1/pass | fast, strong on consumer GPU; ComfyUI node |
| **IDM-VTON** (ECCV24) | ~15 GB | CC-BY-NC-SA | densepose+agnostic | 1/pass (tops auto-mask) | best texture (SDXL), slower, 3:4 aspect; community ComfyUI node |
| OOTDiffusion | consumer | — | dual-UNet | no lower-body | slow (~46s), demo stale |

Body preservation is **by construction** (DensePose carries the source body), but VTON typically
does **one garment per pass** → our outfit needs **sequential passes** (blouse → skirt), and
**accessories (belt/earrings/shoes) are out of scope** for plain garment VTON.

## Family 2 — Multi-item / accessory all-in-one

| Model | Covers | License | Code | VRAM | Notes |
|---|---|---|---|---|---|
| **OmniTry** (NeurIPS25) | clothes **+ shoes + jewelry + belts + bags + glasses + ties** | **CC-BY-SA — commercial OK** | "will be released" (repo not found yet) | undisclosed (likely FLUX-class → needs fp8/quant for 16 GB) | mask-free, ID-preserving; the purpose-built answer for our accessories. Verify release + VRAM. |
| **AnyDressing** | multi-garment combos | — | yes | — | GarmentsNet + DressingNet |
| **OmniVTON++** | outfit-level multi-garment | — | — | — | extends OmniVTON to outfit level |

## Family 3 — Training-free (no fine-tune; light base)

| Model | Base | VRAM | License | Notes |
|---|---|---|---|---|
| **OmniVTON** | **SD 1.5 / SD 2.0 inpaint** | fits 16 GB easily | **CC-BY-NC-4.0** | training-free, DDIM-inversion body alignment + boundary stitching; single-garment (++ for multi) |

Attractive (no training, light, runs anywhere) but non-commercial and SD-1.5/2.0-era quality.

## Family 4 — Body-shape-specialised (our long-skirt problem)

- **PROMO** (CVPR26, arXiv 2603.11675): **FLUX.1-dev + LoRA**, an EOMT pose/shape estimator **robust
  to clothing occlusion** — explicitly notes *"DensePose produces distorted results on loose-fitting
  garments like long skirts"* (our exact failure) and preserves the **real figure, not idealised**.
  **BUT no code released** (trained on 16×H800). → a direction/inspiration, not locally usable now;
  reproducing needs cloud fine-tune.
- **SMPL-shape conditioning**: keep the source SMPL **shape** params fixed, drive generation with an
  SMPL-depth/normal control → body shape by construction. Open SMPL estimators exist (SMPLer-X etc.),
  but monocular shape is ill-posed (HumanGPS) and this is a heavy assembly.
- **Odo** (2508.13065): depth-guided identity-preserving body reshaping — related building block.

## Family 5 — Assembled pipeline (max control, max work, VRAM-tight)

Base diffusion (**SDXL** lighter, or **FLUX** at fp8/quant — FLUX multi-control wants ~24 GB) +:
- **inpaint** (clothing mask) — protect unclothed pixels;
- **ControlNet** pose (DWPose) + depth/normal or **DensePose/SMPL-depth** — pin body shape under clothes;
- **IP-Adapter / FLUX Redux** on the board / per-garment crops — garment-from-image;
- **PuLID** (94-96% ID; ~12 GB fp8 on FLUX) or **InstantID** — lock the face;
- **OmniTry** pass for accessories; **DiffFit / FitDiT** warping for exact garment detail; face restore.

This is the only path that, in principle, hits every axis locally — but it is a large multi-stage
build, VRAM-tight on 16 GB, and may still not beat a single dedicated model + cloud for parts.

## Family 6 — 3D / SMPL reconstruct → redress → render → refine

Monocular **SMPL/SMPL-X fit** → lock the body shape (the source body, exactly) → repose/redress (3D
garment drape or VTON) → render → diffusion refine. Solves body **exactly** (3D body = source), and
is the principled answer to "preserve morphology under clothing". But: monocular fit is **ill-posed**
(HumanGPS), garment draping is fragile, and the pipeline is heavy/research-grade. High risk, high
reward; not a V1 path.

## Family 7 — Cloud (pragmatic for the full hard case)

- **APIs**: FASHN (**$0.075/img**, →$0.04 at volume; API-first; full outfit + accessories), **Kling**
  (photorealistic draping), Google Vertex AI, Kolors. These already do **multi-item outfit +
  accessories** at high quality, cheaply — the fastest way to a working full result if local quality
  is insufficient. (Closed; per-image cost; data leaves the machine.)
- **GPT-4o native image**: reportedly reproduces sleeve/neckline/logos/typography/gradient faithfully
  — a detail-fidelity ceiling, closed.
- **Rented GPU** (24–80 GB): run the heavy open models (OmniTry, CatVTON-FLUX 40 GB, PROMO-style) or
  **fine-tune** on **Garments2Look** (CVPR26 multi-reference outfit dataset) — the blueprint's WP7.
  Inference can return local after a LoRA is trained.

---

## Honest read for OUR case

- **Body (the rejected defect):** preserved *by construction* only where conditioning encodes the
  source shape. DensePose-based VTON helps but **distorts on long skirts** (PROMO's own finding —
  exactly our skirt). The robust answers (PROMO, SMPL-shape) are either **no-code** or a **heavy
  assembly**. So "off-the-shelf local fixes the body" is **not guaranteed** — this stays a real
  kill-criterion risk.
- **Accessories (belt/earrings/shoes):** plain garment VTON ignores them; **OmniTry** is the only
  purpose-built open answer (commercial-OK license) but its **release + 16 GB feasibility is unverified**.
- **Exact detail:** warping (DiffFit/FitDiT) or multi-reference; cloud (Kling/GPT-4o) is the current ceiling.
- **License:** of the local options, only **Leffa (MIT)** and **OmniTry (CC-BY-SA)** are commercial-OK;
  CatVTON/IDM-VTON/OmniVTON are non-commercial (fine for a V1 prototype, blocked for launch).

## Recommendation (staged, for E-010)

1. **Prototype the main garments locally** with **Leffa** (MIT, ~4 GB) and/or **CatVTON** — sequential
   blouse→skirt passes. Measure body (`body_pose`) + identity (ArcFace) + garment (colour/detail) on
   our person/outfit. This answers cheaply: does a dedicated VTON hold the figure and the items?
2. **Accessories:** evaluate **OmniTry** (verify release + quantised 16 GB); else inpaint/detail passes.
3. **If the body still drifts** (likely on the long skirt): add **SMPL/DensePose-shape conditioning**
   (assembly, Family 5/6) or accept that robust body needs **PROMO-style fine-tune on rented GPU**.
4. **If local quality/coverage is insufficient:** **cloud (FASHN/Kling)** for the full outfit is cheap
   and immediate — a legitimate V1 path, with the privacy/cost tradeoff stated.
5. The **full local assembly** (ControlNet + IP-Adapter + PuLID + OmniTry + warp) is the max-control
   endgame but a large build; pursue only if 1–3 prove a dedicated model + targeted parts can't.

**For E-010 Phase 0**, replace the single-engine pick with this matrix: prototype Leffa/CatVTON first,
measure on our gates, then decide local-dedicated vs assembly vs cloud per the evidence — do not commit
blind.

---

## Sources

- [Awesome-Try-On-Models](https://github.com/Zheng-Chong/Awesome-Try-On-Models) ·
  [OpenVTON-Bench](https://arxiv.org/pdf/2601.22725) ·
  [fashn.ai comparison](https://fashn.ai/blog/comparing-the-top-4-open-source-virtual-try-on-viton-models)
- Family 1: [Leffa (MIT)](https://huggingface.co/franciszzj/Leffa) ·
  [CatVTON](https://github.com/Zheng-Chong/CatVTON) · [IDM-VTON](https://github.com/yisol/IDM-VTON)
- Family 2: [OmniTry](https://omnitry.github.io/) ([paper](https://arxiv.org/abs/2508.13632)) ·
  [AnyDressing](https://crayon-shinchan.github.io/AnyDressing/) ·
  [OmniVTON++](https://arxiv.org/pdf/2602.14552)
- Family 3: [OmniVTON](https://github.com/Jerome-Young/OmniVTON) ([paper](https://arxiv.org/abs/2507.15037))
- Family 4: [PROMO](https://arxiv.org/pdf/2603.11675) · [Odo](https://arxiv.org/html/2508.13065)
- Family 5: [IP-Adapter try-on](https://huggingface.co/blog/tonyassi/virtual-try-on-ip-adapter) ·
  [PuLID-Flux ComfyUI](https://github.com/balazik/ComfyUI-PuLID-Flux) ·
  [catvton-flux (40 GB)](https://github.com/nftblackmagic/catvton-flux)
- Family 6: [SMPL 3D try-on patent](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11941770)
- Family 4/detail: [FitDiT](https://arxiv.org/html/2411.10499v1) · [DiffFit](https://arxiv.org/pdf/2506.23295) ·
  [Garments2Look](https://arxiv.org/abs/2603.14153)
- Family 7: [best VTON tools 2026](https://nightjar.so/blog/best-tools-ai-virtual-try-on) ·
  [Kling/FASHN APIs](https://www.pixazo.ai/blog/best-virtual-try-on-api)
