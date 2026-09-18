# Garment-fidelity verification instruments (2026-06-16)

The measurement stack for "is this the SAME item?" — the axis that was owner-eye-only (audit gap).
Garment fidelity is product axis #1. All of these are small models / CPU-cheap — far lighter than the
generator. They MEASURE the result; they do not produce it.

| Layer | Instrument | Catches | Class |
|---|---|---|---|
| 1 (headline) | **Retrieval-rank with decoys** via **Marqo-FashionSigLIP** (ViT-B-16, ~0.4 GB): embed generated garment crop, rank vs [target reference + visually-similar decoys] | "same SKU / item" — target should be top-1/top-K | deterministic, decision-relevant |
| 2 | **DISTS** (field-preferred garment-similarity metric: perceptual+structural, robust to legitimate spatial variation) + **DINOv2** features | texture / structure / cut similarity | deterministic |
| 3 | **hue/chroma CIEDE2000** (have) + **palette histogram/EMD** for patterns; **silhouette descriptors** from the garment mask (neckline/sleeve/hem/length); **PaddleOCR** + template-match for logo/print/text | colour, cut, print, logo | deterministic |
| 4 | **Qwen3-VL-8B** structured per-detail checklist on crop vs reference (V-neck? central button row? peplum? buckle gold? wedge shape?) | named critical details no metric sees | advisory (not decision-grade per METHODOLOGY) |
| 5 | **owner per-item verdict** | ground truth + calibration labels | human |

**Avoid as primary:** SSIM/PSNR (penalise legitimate variation), FID/KID alone (miss instance-level
errors — wrong pattern/distorted texture).

**Calibration (required, like colour):** a labelled set of garment crops — exact / acceptable /
wrong-colour / wrong-detail / wrong-SKU + hard decoys (~150–200) — to set retrieval-rank/DISTS
thresholds and confirm the instrument agrees with the eye. Uncalibrated numbers repeat the colour-gate
mistake.

**Core:** retrieval-rank (FashionSigLIP) + DISTS, wrapped with colour/silhouette/OCR + VLM checklist +
owner verdict, on a labelled calibration set.

Sources: [OpenVTON-Bench](https://arxiv.org/pdf/2601.22725) · [DISTS for try-on](https://arxiv.org/pdf/2504.00562) ·
[Marqo-FashionSigLIP](https://huggingface.co/Marqo/marqo-fashionSigLIP) ·
[marqo-FashionCLIP](https://github.com/marqo-ai/marqo-FashionCLIP) · [VTON survey](https://arxiv.org/pdf/2311.04811)
