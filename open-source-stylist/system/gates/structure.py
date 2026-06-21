"""Structural-correspondence gate (DINOv2) — catches MAJOR structural defects that the global
FashionSigLIP sim / DISTS / colour gates miss, e.g. a skirt rendered WITHOUT its front slit.

Mechanism: the output garment region and its reference are each encoded into a DINOv2 patch grid;
the grids are compared patch-by-patch (aligned). A missing structural feature (a slit over half the
skirt) shows up as LOW patch-correspondence, strongest in the sub-region where the feature lives
(the lower-centre, for a front slit).

Validated 2026-06-21 on the owner-labelled skirt cases — the correct direction (FashionSigLIP patches
were backwards):
    no-slit QIE skirt (owner FAIL): mean 0.524, lower_centre 0.496
    slit  FitDiT skirt (owner PASS): mean 0.587, lower_centre 0.611
Provisional threshold from these two anchors: lower_centre >= 0.55 -> OK (PROVISIONAL, 2 anchors only).

DINOv2-small weights live in system/gates/models/dinov2-small (downloaded via PowerShell; the venv has
SSL trouble). Runs on CPU. ADVISORY until calibrated on a labelled set.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

MODEL_DIR = Path(__file__).parent / "models" / "dinov2-small"
LOWER_CENTRE_OK = 0.55  # provisional (2 anchors); structural-correspondence floor

_MODEL = None
_PROC = None


def _load():
    global _MODEL, _PROC
    if _MODEL is None:
        from transformers import AutoImageProcessor, AutoModel
        _PROC = AutoImageProcessor.from_pretrained(str(MODEL_DIR))
        _MODEL = AutoModel.from_pretrained(str(MODEL_DIR)).eval()
    return _MODEL, _PROC


def _bbox_crop(image, mask) -> np.ndarray:
    img = cv2.imread(str(image)) if isinstance(image, (str, Path)) else image
    if mask is None:
        return img
    m = cv2.imread(str(mask), cv2.IMREAD_GRAYSCALE) if isinstance(mask, (str, Path)) else mask
    if (m.shape[1], m.shape[0]) != (img.shape[1], img.shape[0]):
        m = cv2.resize(m, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
    ys, xs = np.where(m > 127)
    if ys.size == 0:
        raise ValueError("empty region mask")
    return img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def _grid(bgr: np.ndarray):
    import torch
    from PIL import Image
    model, proc = _load()
    rgb = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    inp = proc(images=rgb, return_tensors="pt")
    with torch.no_grad():
        tok = model(**inp).last_hidden_state[0, 1:, :]  # drop CLS
    n = int(tok.shape[0] ** 0.5)
    g = tok[:n * n].reshape(n, n, -1)
    return torch.nn.functional.normalize(g, dim=-1)


def structure_score(out_image, region_mask, ref_image, ref_mask=None) -> dict:
    """Aligned DINOv2 patch-correspondence between the output garment region and its reference.

    Returns mean / lower_centre / worst_20pct correspondence and an ADVISORY verdict. Higher = the
    output reproduces the reference structure; a low `lower_centre` flags a missing lower-centre feature
    (e.g. a front slit). Thresholds are provisional (2 anchors) — owner verdict decides.
    """
    import torch
    ga = _grid(_bbox_crop(out_image, region_mask))
    gb = _grid(_bbox_crop(ref_image, ref_mask))
    cos = (ga * gb).sum(-1)
    n = cos.shape[0]
    lc = cos[n // 2:, n // 4:(3 * n) // 4]
    worst = torch.sort(cos.flatten())[0][:n * n // 5].mean()
    mean, lower_centre, worst20 = round(cos.mean().item(), 3), round(lc.mean().item(), 3), round(worst.item(), 3)
    return {
        "mean": mean, "lower_centre": lower_centre, "worst_20pct": worst20,
        "verdict": "OK" if lower_centre >= LOWER_CENTRE_OK else "STRUCTURE_OFF",
        "note": "ADVISORY (provisional, 2 anchors). lower_centre < 0.55 flags a missing structural "
                "feature (e.g. skirt slit). DINOv2 patch-correspondence; owner verdict decides.",
    }
