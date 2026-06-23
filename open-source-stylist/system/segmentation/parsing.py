"""Human-parsing garment masks (ATR) — clean per-garment regions that separate clothing from skin,
unlike GroundingDINO (which grabs the V-neck skin / floor and gives noisy checks).

Wraps the ATR+LIP ONNX parser from the local Leffa checkout (CPU). Used for decision-grade garment
checks and agnostic masks. Set LEFFA_PATH to override the checkout location.

ATR label map: 0 bg, 1 hat, 2 hair, 3 sunglasses, 4 upper-clothes, 5 skirt, 6 pants, 7 dress, 8 belt,
9 left-shoe, 10 right-shoe, 11 face, 12 left-leg, 13 right-leg, 14 left-arm, 15 right-arm, 16 bag, 17 scarf.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

LEFFA = Path(os.environ.get("LEFFA_PATH", r"C:/Users/Admin/Leffa"))

ATR_REGIONS: dict[str, list[int]] = {
    "upper": [4], "skirt": [5], "pants": [6], "dress": [7], "belt": [8], "shoes": [9, 10],
    "hat": [1], "hair": [2], "face": [11], "arms": [14, 15], "legs": [12, 13], "bag": [16],
}

_PARSER = None


def _parser():
    global _PARSER
    if _PARSER is None:
        sys.path.insert(0, str(LEFFA))
        sys.path.insert(0, str(LEFFA / "preprocess/humanparsing"))
        from preprocess.humanparsing.run_parsing import Parsing  # noqa: E402
        _PARSER = Parsing(atr_path=str(LEFFA / "ckpts/humanparsing/parsing_atr.onnx"),
                          lip_path=str(LEFFA / "ckpts/humanparsing/parsing_lip.onnx"))
    return _PARSER


def parse_label_map(image_path) -> np.ndarray:
    """ATR label map (H=512, W=384) of class indices for the image."""
    img = Image.open(str(image_path)).convert("RGB").resize((384, 512))
    parse, _ = _parser()(img)
    return np.array(parse)


def garment_masks(image_path, regions, out_size=None) -> dict[str, np.ndarray]:
    """{region: uint8 mask (255=fg)} for ATR regions, resized to out_size=(W,H) or the image's native size."""
    arr = parse_label_map(image_path)
    if out_size is None:
        im = cv2.imread(str(image_path))
        out_size = (im.shape[1], im.shape[0])
    out = {}
    for r in regions:
        m = np.isin(arr, ATR_REGIONS[r]).astype(np.uint8) * 255
        out[r] = cv2.resize(m, out_size, interpolation=cv2.INTER_NEAREST)
    return out


def garment_mask(image_path, region, out_size=None) -> tuple[np.ndarray, float]:
    """One region's mask plus its DOMINANCE = region pixels / all parsed-foreground pixels.

    Dominance says whether the region is the SUBJECT of the image (a product/on-model photo of that
    garment -> high) or whether ATR, a full-body parser, mis-parsed a close-up and the target is a sliver
    of a garbage body parse (-> low). It is scale-free, so it discriminates without a tuned area threshold.
    """
    arr = parse_label_map(image_path)
    fg = int((arr > 0).sum())
    region_lab = np.isin(arr, ATR_REGIONS[region])
    dominance = (int(region_lab.sum()) / fg) if fg else 0.0
    if out_size is None:
        im = cv2.imread(str(image_path))
        out_size = (im.shape[1], im.shape[0])
    mask = cv2.resize(region_lab.astype(np.uint8) * 255, out_size, interpolation=cv2.INTER_NEAREST)
    return mask, round(dominance, 3)
