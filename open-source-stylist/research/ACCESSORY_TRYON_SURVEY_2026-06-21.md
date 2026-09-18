# Accessory / mask-free "try-on anything" survey + OmniTry verification (2026-06-21)

Owner-directed: verify OmniTry (the accessory executor named in SYSTEM_DESIGN/BUILD_PLAN) and deep-search
all similar solutions. Lens: **local on a 16 GB RTX 4090 laptop**, accessory coverage (our outfit has
earrings + a belt), and license.

## 1. OmniTry — VERIFIED (and our docs were partly wrong)

**Source of truth:** repo `github.com/Kunbyte-AI/OmniTry`, paper arXiv **2508.13632** (NeurIPS 2025),
project `omnitry.github.io`, HF `huggingface.co/Kunbyte/OmniTry` (+ Space). Kunbyte AI + Zhejiang Univ.

- **CORRECTION:** `audit/IMPLEMENTATION_BLUEPRINT_2026-06-15.md:1080` lists the wrong URL
  (`KiseKloset/OmniTry`). The real repo is **`Kunbyte-AI/OmniTry`**. Flag, don't trust the old link.
- **Architecture — it's a LoRA, not a full model.** OmniTry is a **LoRA on FLUX.1-Fill-dev**. Two weights:
  `omnitry_v1_unified.safetensors` (any wearable) and `omnitry_v1_clothes.safetensors` (clothes only).
  **We already have the base (`flux1-fill-dev.safetensors`) and the fp8 ComfyUI infra from the FLUX Fill
  audit (2026-06-21).**
- **Method:** mask-FREE. Two-stage — (1) repurpose the inpainting model to auto-place the object given an
  EMPTY mask (learned localisation from unpaired portraits); (2) paired fine-tune for appearance fidelity.
  Input = person image + object image; no manual mask.
- **Categories:** 12 wearable classes on OmniTry-Bench — bags, belts, hats, glasses, sunglasses, ties +
  jewelry (bracelets, **earrings**, necklaces, rings) + clothing/shoes. **Covers our earrings + belt.**
- **VRAM:** authors state **≥28 GB at torch.bfloat16**, "will continue to decrease". No fp8/offload in
  their docs. BUT — it is a FLUX.1-Fill-dev LoRA, and **FLUX fp8 runs on 16 GB in ComfyUI** (confirmed; we
  already run FLUX Fill fp8). So **16 GB via fp8/offload is PLAUSIBLE** — the "not local" verdict in our
  docs is a bf16 figure and should be revised to **"plausible via fp8, needs an empirical test."**
- **License:** **Apache-2.0** (code; weights repo also apache-2.0, model-card README empty). Permissive —
  no NC block (unlike AnyDressing/Sapiens).
- **Run:** `gradio_demo.py` (diffusers + FLUX). No official ComfyUI node, but a FLUX-Fill LoRA is
  ComfyUI-loadable via a LoRA loader (may need a diffusers→ComfyUI key conversion).

**Verdict:** OmniTry is the **best-fit accessory executor** AND more accessible than our docs claimed. Next
step = empirically confirm 16 GB: download the (Apache-2.0) LoRA, load on our fp8 FLUX Fill (ComfyUI) or run
its gradio with fp8, try one accessory (earrings/belt), judge.

## 2. The FLUX.1-Fill-dev mask-free family (most accessible — we own the base + fp8 infra)
- **OmniTry** (above) — any wearable, accessories. Best fit.
- **MFP-VTON** (arXiv 2502.01626) — mask-free person-to-person VTON on FLUX-Fill-dev. Garment-focused.
- **JCo-MVTON** (arXiv 2508.17614) — mask-free, jointly-controllable MM-DiT VTON.
Because we just audited+fixed FLUX Fill, this whole family is the cheapest path to try.

## 3. FLUX in-context object insertion (general, ComfyUI-ready, we have FLUX)
- **FLUX Kontext** (in-context edit/insert) + **FLUX "in-context LoRA" try-on** (OpenArt workflow exists).
- **IC-Custom** (arXiv 2507.01926), **In-Context Brush** (arXiv 2505.20271) — zero-shot subject insertion
  via in-context latent manipulation. Could place an earring/belt from a reference, mask-free-ish.

## 4. General object insertion (older / mask-based — fallbacks)
- **AnyDoor** (`ali-vilab/AnyDoor`, SD2.1 + ControlNet, **MIT**) — zero-shot object insertion; demonstrates
  try-on but **requires a target mask** and is older/lower-fidelity than FLUX. Usable fallback.

## 5. Research-only / no usable release
- **GlamTry** (arXiv 2409.14553) — VITON-HD + MediaPipe Hand Landmarker for jewelry/watches; tiny dataset,
  **no code/weights released**. Concept only.
- **Style-Instructed Mask-Free VTON** (arXiv 2603.29587, 2026) — recent mask-free; check for release.

## 6. Adjacent / datasets (not executors)
- **Garments2Look** (CVPR 2026) — multi-reference dataset for outfit-level try-on **with clothing AND
  accessories**; useful for eval/fine-tune, not an executor.
- **Stable-Hair** (AAAI 2025), **Stable-Makeup** (SIGGRAPH 2025) — hair/makeup transfer; adjacent, not
  accessories.

## 7. Commercial AR (NOT local, not for our pipeline) — for reference only
Camweara, Kivisense, Bandy AI, SellerPic, PicCopilot — browser/AR jewelry-glasses try-on; closed, not
local diffusion.

## Bottom line for our pipeline
1. **OmniTry is the accessory tool to test** — accessory-trained, mask-free, Apache-2.0, and a LoRA on the
   FLUX Fill we already run. The 28 GB scare is bf16; fp8 likely fits 16 GB (empirical test pending).
2. The accessible alternatives are the **other FLUX-Fill mask-free models** (MFP-VTON, JCo-MVTON) and
   **FLUX in-context insertion** — all reuse the FLUX base we have.
3. AnyDoor is the mask-based fallback; GlamTry/commercial AR are not usable locally.
4. Action: correct the blueprint URL; then a timeboxed empirical run of OmniTry's LoRA on fp8 FLUX Fill to
   settle the 16 GB yes/no (this is BUILD_PLAN's "OmniTry on 16 GB" gating test, now de-risked).
