"""Structural-correspondence gate — AnomalyDINO-style (WACV 2025, arXiv 2405.14529).

Catches MAJOR structural defects the global FashionSigLIP-sim / DISTS / colour gates miss (e.g. a skirt
rendered WITHOUT its front slit). Method: DINOv2 patch features + **bidirectional nearest-neighbour**
between the output garment patches and the reference garment patches (NO grid alignment — this fixes the
framing confound; no garment/defect-specific region is hard-coded):

  forward  = output patches with no good match in the reference  -> output has EXTRA/wrong stuff
  reverse  = reference patches with no good match in the output   -> output is MISSING reference features
                                                                     (this is what catches a dropped slit)

Each direction aggregates the top-5% worst (1 - best cosine). `anomaly` = max(forward, reverse); lower is
better. Reference garment = the "normal" memory bank (few-shot: one reference is enough).

Validated 2026-06-22 on owner-labelled skirt cases (correct direction, wider margin than the old
aligned-grid):
    no-slit QIE skirt (owner FAIL): forward 0.555, reverse 0.515  -> anomaly 0.555 STRUCTURE_OFF
    slit  FitDiT skirt (owner PASS): forward 0.433, reverse 0.434  -> anomaly 0.434 OK

HONEST LIMITS: catches INTRA-garment structure/appearance defects; does NOT catch layering defects
(half-tuck — a between-garment problem; use the VLM-judge / owner for that). Threshold provisional
(2 anchors). DINOv2-small runs on CPU; ADVISORY until broadly calibrated.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

MODEL_DIR = Path(__file__).parent / "models" / "dinov2-small"
# provisional (2 anchors): no-slit anomaly 0.555 (FAIL) vs slit 0.434 (PASS).
ANOMALY_OK = 0.48

_MODEL = None
_PROC = None


def _load():
    global _MODEL, _PROC
    if _MODEL is None:
        from transformers import AutoImageProcessor, AutoModel
        _PROC = AutoImageProcessor.from_pretrained(str(MODEL_DIR))
        _MODEL = AutoModel.from_pretrained(str(MODEL_DIR)).eval()
    return _MODEL, _PROC


def _garment_patches(image, mask):
    """Normalised DINOv2 patch features for the garment only (bbox crop + patch-level mask). -> (Ng, D)."""
    import torch
    from PIL import Image
    img = cv2.imread(str(image)) if isinstance(image, (str, Path)) else image
    m = cv2.imread(str(mask), cv2.IMREAD_GRAYSCALE) if isinstance(mask, (str, Path)) else mask
    if (m.shape[1], m.shape[0]) != (img.shape[1], img.shape[0]):
        m = cv2.resize(m, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
    ys, xs = np.where(m > 127)
    if ys.size == 0:
        raise ValueError("empty region mask")
    crop = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    mcrop = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    model, proc = _load()
    inp = proc(images=Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)), return_tensors="pt")
    with torch.no_grad():
        tok = model(**inp).last_hidden_state[0, 1:, :]
    n = int(tok.shape[0] ** 0.5)
    g = torch.nn.functional.normalize(tok[:n * n].reshape(n, n, -1), dim=-1)
    keep = cv2.resize(mcrop, (n, n), interpolation=cv2.INTER_NEAREST) > 127
    sel = g[torch.from_numpy(keep)]
    return sel if sel.shape[0] >= 4 else g.reshape(-1, g.shape[-1])  # fallback if mask too small at patch res


def structure_score(out_image, region_mask, ref_image, ref_mask=None) -> dict:
    """Bidirectional DINOv2 patch nearest-neighbour anomaly between the output garment and its reference.

    Returns forward / reverse / anomaly (max) and an ADVISORY verdict. anomaly < threshold -> OK; a high
    `reverse` flags a MISSING reference feature (e.g. a dropped slit), a high `forward` flags wrong/extra
    content. Owner verdict decides; provisional threshold.
    """
    import torch
    tp = _garment_patches(out_image, region_mask)
    rp = _garment_patches(ref_image, ref_mask if ref_mask is not None else np.full(
        cv2.imread(str(ref_image)).shape[:2], 255, np.uint8))
    sim = tp @ rp.T
    fwd = 1 - sim.max(1).values
    rev = 1 - sim.max(0).values

    def top5(v):
        k = max(1, len(v) // 20)
        return round(torch.sort(v, descending=True)[0][:k].mean().item(), 3)
    forward, reverse = top5(fwd), top5(rev)
    anomaly = max(forward, reverse)
    return {
        "forward": forward, "reverse": reverse, "anomaly": anomaly,
        "verdict": "OK" if anomaly < ANOMALY_OK else "STRUCTURE_OFF",
        "note": "ADVISORY (provisional, 2 anchors). AnomalyDINO bidirectional patch-NN; high reverse = "
                "missing reference feature (e.g. slit), high forward = wrong/extra content. Catches "
                "intra-garment structure, NOT layering/tuck. owner verdict decides.",
    }
