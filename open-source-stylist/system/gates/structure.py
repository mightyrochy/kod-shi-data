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
# provisional (2 anchors, narrow margin): no-slit worst_window 0.375 (FAIL) vs slit 0.406 (PASS).
WORST_WINDOW_OK = 0.39

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

    The verdict uses `worst_window` — the worst contiguous 3x3 patch region, AUTO-LOCALISED (the defect
    may be anywhere; no garment- or defect-specific region is hard-coded). A missing/wrong structural
    feature shows up as a low-correspondence blob wherever it sits. `lower_centre` is kept only as a
    diagnostic, not the gate.

    HONEST LIMITS: catches INTRA-garment structural defects (e.g. a missing slit) but NOT layering
    defects (e.g. a half-tucked blouse — that is a between-garment boundary problem, needs a separate
    check). The general signal is weaker than a region-tuned one (the slit margin shrinks ~0.03), and
    the threshold is provisional (2 anchors) — owner verdict decides. ADVISORY until broadly calibrated.
    """
    import torch
    ga = _grid(_bbox_crop(out_image, region_mask))
    gb = _grid(_bbox_crop(ref_image, ref_mask))
    cos = (ga * gb).sum(-1)
    n = cos.shape[0]
    worst_window = torch.nn.functional.avg_pool2d(cos[None, None], 3, stride=1).min()
    lc = cos[n // 2:, n // 4:(3 * n) // 4]
    mean, ww, lower_centre = round(cos.mean().item(), 3), round(worst_window.item(), 3), round(lc.mean().item(), 3)
    return {
        "mean": mean, "worst_window": ww, "lower_centre": lower_centre,
        "verdict": "OK" if ww >= WORST_WINDOW_OK else "STRUCTURE_OFF",
        "note": "ADVISORY (provisional, 2 anchors; weak general margin). worst_window = auto-localised "
                "worst 3x3 patch region vs reference; < threshold flags an intra-garment structural "
                "defect anywhere. Does NOT catch layering/tuck. DINOv2; owner verdict decides.",
    }
