"""Reframe an in-the-wild person photo into the DressCode/VITON distribution Leffa expects:
segment the person (Leffa human-parsing), composite on a plain WHITE background, tight-crop to
the figure so it fills the frame. This is the fix for the skirt->trousers failure (the cause was
the in-the-wild full-body framing + room background, NOT the garment/mask).

    python reframe_person.py --src <person.png> --out <reframed.png>
"""
import argparse
import os
import sys

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
DENSEPOSE_PATH = os.path.join(ROOT, "detectron2_src", "projects", "DensePose")
if os.path.isdir(DENSEPOSE_PATH):
    sys.path.insert(0, DENSEPOSE_PATH)
CKPT = os.path.join(ROOT, "ckpts")

from preprocess.humanparsing.run_parsing import Parsing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--margin", type=float, default=0.06)
    args = ap.parse_args()

    parsing = Parsing(atr_path=f"{CKPT}/humanparsing/parsing_atr.onnx",
                      lip_path=f"{CKPT}/humanparsing/parsing_lip.onnx")

    src = Image.open(args.src).convert("RGB")
    W, H = src.size
    parse, _ = parsing(src.resize((384, 512)))
    pm = np.array(parse)
    mask = cv2.resize((pm > 0).astype(np.uint8) * 255, (W, H), interpolation=cv2.INTER_NEAREST)
    # clean tiny holes/specks
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    fg = mask > 127

    arr = np.array(src)
    white = np.full_like(arr, 255)
    comp = np.where(fg[..., None], arr, white)

    ys, xs = np.where(fg)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    mh, mw = int((y1 - y0) * args.margin), int((x1 - x0) * args.margin)
    y0, y1 = max(0, y0 - mh), min(H, y1 + mh)
    x0, x1 = max(0, x0 - mw), min(W, x1 + mw)
    crop = comp[y0:y1, x0:x1]

    # Center the tight crop on a 3:4 white canvas (DressCode aspect); person fills the height.
    ch, cw = crop.shape[:2]
    canvas_h = max(ch, int(cw * 4 / 3))
    canvas_w = int(canvas_h * 3 / 4)
    if cw > canvas_w:
        canvas_w = cw
        canvas_h = int(cw * 4 / 3)
    canvas = np.full((canvas_h, canvas_w, 3), 255, np.uint8)
    top, left = (canvas_h - ch) // 2, (canvas_w - cw) // 2
    canvas[top:top + ch, left:left + cw] = crop
    cv2.imwrite(args.out, cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
    print(f"SAVED {args.out}  ({canvas_w}x{canvas_h}, person bbox {x1-x0}x{y1-y0})")


if __name__ == "__main__":
    main()
