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

    import open_clip
    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name="ViT-B-16-SigLIP",
        pretrained=str(weights_path),
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
