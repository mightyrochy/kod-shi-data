"""Garment-fidelity measurement gates (EVAL_INSTRUMENTS.md Layers 1-2).

Layer 1 — FashionSigLIP retrieval-rank:
    Embed the generated garment crop and rank it against [target reference + decoys].
    Target should be top-1 or top-K.

Layer 2 — DISTS:
    Perceptual + structural similarity between generated crop and reference.
    Field-preferred metric for garment similarity; robust to legitimate spatial variation.

Both layers require a calibration set (~150-200 labeled crops) before thresholds
are decision-grade (EVAL_INSTRUMENTS.md: "Uncalibrated numbers repeat the colour-gate
mistake"). For Phase 0 they produce advisory numbers only; owner verdict is primary.

Model download:
    Run  python system/gates/garment_fidelity.py --download
    or   powershell C:\\path\\to\\download_fashionsiglip.ps1
    Model is saved to  system/gates/models/marqo-fashionSigLIP/
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = Path(__file__).parent / "models" / "marqo-fashionSigLIP"


# ── Model loading (FashionSigLIP via open_clip) ───────────────────────────

def _load_model():
    """Load FashionSigLIP. Raises FileNotFoundError with download instruction if absent."""
    config_path = MODEL_DIR / "open_clip_config.json"
    weights_path = MODEL_DIR / "open_clip_pytorch_model.bin"

    if not config_path.is_file() or not weights_path.is_file():
        raise FileNotFoundError(
            f"FashionSigLIP model not found at {MODEL_DIR}.\n"
            "Download with:\n"
            "  python -m system.gates.garment_fidelity --download\n"
            "or run:  system/gates/download_fashionsiglip.ps1"
        )

    with config_path.open() as fh:
        cfg = json.load(fh)

    model_cfg     = cfg["model_cfg"]
    preprocess_cfg = cfg.get("preprocess_cfg", {})

    import open_clip
    # Register the custom architecture from the downloaded config.
    # marqo-fashionSigLIP uses a timm-based vision encoder with embed_dim=768
    # (distinct from standard ViT-B-16-SigLIP) — must inject config before loading.
    _name = "marqo-fashionSigLIP-local"
    open_clip.factory._MODEL_CONFIGS[_name] = model_cfg

    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name=_name,
        pretrained=str(weights_path),
        image_mean=preprocess_cfg.get("mean"),
        image_std=preprocess_cfg.get("std"),
        image_interpolation=preprocess_cfg.get("interpolation"),
        image_resize_mode=preprocess_cfg.get("resize_mode"),
    )
    model.eval()
    return model, preprocess


def _embed_images(image_paths: Sequence[Path | str], model=None, preprocess=None) -> np.ndarray:
    """Return (N, D) unit-normalised embeddings for a list of image paths."""
    import torch
    from PIL import Image

    if model is None:
        model, preprocess = _load_model()

    tensors = []
    for p in image_paths:
        img = Image.open(p).convert("RGB")
        tensors.append(preprocess(img))

    batch = torch.stack(tensors)
    with torch.no_grad():
        features = model.encode_image(batch)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.cpu().numpy()


# ── Layer 1: retrieval-rank ───────────────────────────────────────────────

def retrieval_rank(
    generated_crop: Path | str,
    target_reference: Path | str,
    decoys: Sequence[Path | str],
) -> dict:
    """Embed generated_crop and rank it against [target] + decoys.

    Returns:
        rank        : int, 1-based rank of target (1 = perfect)
        top_k_hit   : bool, target is in top-3
        sim_target  : float, cosine similarity to target
        sim_decoys  : list[float], cosine similarities to each decoy
        verdict     : "PASS" | "WARN" | "FAIL" | "MISSING_MODEL"
    """
    try:
        model, preprocess = _load_model()
    except FileNotFoundError as e:
        return {"verdict": "MISSING_MODEL", "note": str(e)}

    all_paths = [generated_crop, target_reference, *decoys]
    try:
        embs = _embed_images(all_paths, model, preprocess)
    except Exception as e:
        return {"verdict": "ERROR", "error": str(e)}

    query   = embs[0]        # generated crop
    gallery = embs[1:]       # [target, decoy_0, ..., decoy_N]

    sims = (gallery @ query).tolist()          # cosine (unit-normalised)
    target_sim = sims[0]
    decoy_sims = sims[1:]

    # rank = 1 + number of decoys with higher similarity than the target
    rank = 1 + sum(d > target_sim for d in decoy_sims)
    top_k = rank <= 3

    verdict = "PASS" if rank == 1 else ("WARN" if top_k else "FAIL")

    return {
        "verdict":     verdict,
        "rank":        rank,
        "top_k_hit":   top_k,
        "sim_target":  round(float(target_sim), 4),
        "sim_decoys":  [round(float(s), 4) for s in decoy_sims],
        "n_decoys":    len(decoys),
        "note":        ("Uncalibrated — thresholds require labelled calibration set "
                        "(EVAL_INSTRUMENTS.md). Advisory only until calibrated."),
    }


# ── Layer 2: DISTS ────────────────────────────────────────────────────────

def dists_score(
    generated_crop: Path | str,
    reference_crop: Path | str,
) -> dict:
    """Compute DISTS between generated and reference garment crops.

    Lower is better. Field-preferred for garment similarity (robust to legitimate
    spatial variation unlike SSIM/PSNR). No hard threshold until calibrated.
    Returns:
        score   : float (0=identical, higher=more different)
        verdict : "MEASURED" | "ERROR"
    """
    try:
        import torch
        from PIL import Image
        from torchvision import transforms
        from DISTS_pytorch import DISTS

        to_tensor = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
        ])

        img_gen = to_tensor(Image.open(generated_crop).convert("RGB")).unsqueeze(0)
        img_ref = to_tensor(Image.open(reference_crop).convert("RGB")).unsqueeze(0)

        metric = DISTS()
        with torch.no_grad():
            score = float(metric(img_gen, img_ref).item())

        return {
            "verdict": "MEASURED",
            "score":   round(score, 4),
            "note":    ("No calibrated threshold yet. Lower = more similar. "
                        "Build calibration set before treating this as decision-grade."),
        }
    except Exception as e:
        return {"verdict": "ERROR", "error": str(e)}


# ── Combined gate ─────────────────────────────────────────────────────────

def measure_garment_fidelity(
    generated_crop: Path | str,
    reference_crop: Path | str,
    decoys: Sequence[Path | str] = (),
) -> dict:
    """Run Layers 1-2 on a generated garment crop vs its reference.

    generated_crop : path to the garment region cropped from the generated image
    reference_crop : path to the target reference crop (e.g. blouse front crop.png)
    decoys         : list of visually similar but different-SKU garments for ranking
    """
    result = {}

    if decoys:
        result["retrieval_rank"] = retrieval_rank(generated_crop, reference_crop, decoys)
    else:
        result["retrieval_rank"] = {
            "verdict": "SKIP_NO_DECOYS",
            "note": "Provide decoy garments to enable retrieval ranking.",
        }

    result["dists"] = dists_score(generated_crop, reference_crop)
    return result


# ── One-to-one garment correspondence (deformation-aware, all axes) ───────

def siglip_similarity(crop_a, crop_b) -> float | None:
    """FashionSigLIP cosine similarity between two garment crops (no decoys needed).
    Deformation-robust: the learned fashion embedding compares garment IDENTITY, not pixels.
    Returns None if the model is unavailable."""
    try:
        model, preprocess = _load_model()
        embs = _embed_images([crop_a, crop_b], model, preprocess)
    except Exception:
        return None
    return round(float(embs[0] @ embs[1]), 4)


def _region_to_temp(image, mask, dst: Path) -> Path:
    """Bounding-box crop of the masked garment -> dst. image/mask = path or array (BGR / gray)."""
    import cv2
    img = cv2.imread(str(image)) if isinstance(image, (str, Path)) else image
    if mask is None:
        cv2.imwrite(str(dst), img)
        return dst
    m = cv2.imread(str(mask), cv2.IMREAD_GRAYSCALE) if isinstance(mask, (str, Path)) else mask
    if (m.shape[1], m.shape[0]) != (img.shape[1], img.shape[0]):
        m = cv2.resize(m, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
    ys, xs = np.where(m > 127)
    if ys.size == 0:
        raise ValueError("empty region mask")
    cv2.imwrite(str(dst), img[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
    return dst


def measure_garment_correspondence(out_image, region_mask, reference_image,
                                   reference_mask=None, decoys=(), workdir=None) -> dict:
    """One-to-one garment correspondence (deformation-AWARE): is the worn garment region the SAME
    item as the reference, allowing for shape change from how it drapes on the body?

    Four deformation-ROBUST axes (pixel-aligned metrics — SSIM/PSNR/MSE — are deliberately excluded;
    they break under draping/occlusion):
      - identity  : FashionSigLIP cosine sim (+ retrieval-rank if decoys) — learned fashion embedding,
                    pose/drape-invariant; the PRIMARY "same item?" signal.
      - structure : DISTS — texture+structure statistics, robust to legitimate spatial variation.
      - colour    : CIEDE2000 hue/chroma (system.gates.color) — spatial-agnostic.
      - texture   : HF energy + chroma/lum spread ratio (system.gates.texture), scale-normalised.

    out_image / reference_image : path or BGR array.  region_mask : the garment's mask in the OUTPUT.
    reference_mask : the garment's mask in the reference (None = reference is already a garment crop).
    decoys : other-SKU garment crops to enable retrieval-rank (rank 1 = reference ranks first).
    Returns a per-axis report + an ADVISORY overall (calibration pending → owner verdict decides).
    """
    import tempfile
    from system.gates import color as color_gate
    from system.gates import texture as texture_gate

    import cv2

    def _full_mask(image):
        img = cv2.imread(str(image)) if isinstance(image, (str, Path)) else image
        return np.full(img.shape[:2], 255, np.uint8)

    tmp = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="garm_corr_"))
    tmp.mkdir(parents=True, exist_ok=True)
    out_crop = _region_to_temp(out_image, region_mask, tmp / "out_crop.png")
    ref_crop = _region_to_temp(reference_image, reference_mask, tmp / "ref_crop.png")

    sim = siglip_similarity(out_crop, ref_crop)
    # Match-strength bands calibrated on the 2026-06-21 skirt triplet (CALIBRATION_2026-06-21.md):
    # good (owner-accepted) sim 0.922, flat 0.845 -> >=0.90 strong, 0.85-0.90 acceptable, <0.85 low.
    match = None if sim is None else ("strong" if sim >= 0.90 else "acceptable" if sim >= 0.85 else "low")
    identity = {"siglip_sim": sim, "match": match}
    if decoys:
        identity["retrieval"] = retrieval_rank(out_crop, ref_crop, decoys)

    # The colour gate needs an explicit region mask; when none is given the (already-cropped) image
    # IS the garment, so use a full-frame mask.
    eff_region = region_mask if region_mask is not None else _full_mask(out_image)
    eff_ref = reference_mask if reference_mask is not None else _full_mask(reference_image)

    colour = color_gate.compare_regions(out_image, eff_region, reference_image, eff_ref)
    # compare_regions reports delta_e; derive the verdict here (run_slice thresholds: PASS<=3, FAIL>5).
    de = colour.get("delta_e_mean")
    colour["verdict"] = "INVALID" if de is None else ("PASS" if de <= 3.0 else "WARN" if de <= 5.0 else "FAIL")

    report = {
        "identity": identity,
        "structure": dists_score(out_crop, ref_crop),
        "colour": colour,
        "texture": texture_gate.compare_texture(out_image, reference_image, region_mask, reference_mask),
    }

    # The texture sub-report is kept for DATA COLLECTION only — it is NOT counted in the verdict
    # (owner decision 2026-06-21: the texture measure is too weak/noisy to gate on; let it run quietly
    # and accumulate numbers, but the system ignores it). Identity (sim) + colour (CIEDE2000) gate.
    flags = []
    if sim is not None and sim < 0.85:   # calibrated 2026-06-21 (was 0.80)
        flags.append("IDENTITY_LOW")
    if report["colour"]["verdict"] == "FAIL":
        flags.append("COLOUR_OFF")
    report["texture"]["gating"] = False  # informational only; excluded from overall
    report["overall"] = {
        "flags": flags,
        "verdict": "REVIEW" if flags else "OK",
        "note": "ADVISORY — thresholds uncalibrated (no labelled set). FashionSigLIP sim is the primary "
                "deformation-robust 'same item' signal; owner verdict is the decider (METHODOLOGY §1). "
                "TEXTURE is recorded but NOT gated on (owner 2026-06-21).",
    }
    return report


# ── Model download helper ─────────────────────────────────────────────────

def download_model() -> None:
    """Print PowerShell commands to download FashionSigLIP via Invoke-WebRequest.

    System Python has SSL issues with the corporate cert; use PowerShell instead.
    """
    model_dir = MODEL_DIR.as_posix()
    hf_base   = "https://huggingface.co/Marqo/marqo-fashionSigLIP/resolve/main"
    files     = ["open_clip_config.json", "open_clip_pytorch_model.bin"]

    print(f"# Download FashionSigLIP to {MODEL_DIR}")
    print(f"New-Item -ItemType Directory -Force -Path '{MODEL_DIR.as_posix()}' | Out-Null")
    for f in files:
        dest = (MODEL_DIR / f).as_posix()
        print(
            f"if (-not (Test-Path '{dest}')) {{\n"
            f"    Invoke-WebRequest -Uri '{hf_base}/{f}' "
            f"-OutFile '{dest}' -UseBasicParsing\n"
            f"}}"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Garment fidelity gate")
    parser.add_argument("--download", action="store_true",
                        help="print PowerShell download commands for FashionSigLIP model")
    parser.add_argument("--test-dists", nargs=2, metavar=("GEN", "REF"),
                        help="quick DISTS test on two image paths")
    args = parser.parse_args()

    if args.download:
        download_model()
    elif args.test_dists:
        result = dists_score(args.test_dists[0], args.test_dists[1])
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()
