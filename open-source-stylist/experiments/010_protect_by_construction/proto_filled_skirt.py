"""E-010 — filled-silhouette skirt test.

Root cause (owner-diagnosed): the skirt crop's slit is a THROUGH-gap in the silhouette
(cut to background), so both garment and mask are bifurcated → FitDiT draws pants. Even a
continuous auto mask gave culottes, so the GARMENT crop drives it.

Fix tested here: make the garment SILHOUETTE continuous (fill the interior gap with cloned
fabric) while keeping the slit as an internal dark line — i.e. remove the silhouette gap,
keep the slit feature. Then FitDiT + the (already continuous) auto mask should render a
SKIRT with a slit, not pants.

    python experiments/010_protect_by_construction/proto_filled_skirt.py [--offload]
"""

from __future__ import annotations

import sys
import time
from argparse import ArgumentParser
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from system.clients.comfyui import ComfyUIClient

PERSON = ROOT / "assets/person/person_front.png"
SKIRT_REF = ROOT / "assets/outfits/outfit_001/crops/skirt_front_fitdit.png"
OUT = Path(__file__).parent / "results" / "proto_chain"
RES = "768x1024"
SEED = 42
TIMEOUT = 900.0


def fill_slit_gap(crop: Path, out_path: Path) -> Path:
    """Close the interior through-gap with cloned fabric; keep a darkened slit line."""
    raw = cv2.imread(str(crop), cv2.IMREAD_UNCHANGED)
    if raw.ndim == 3 and raw.shape[2] == 4:
        alpha = raw[:, :, 3]
        bgr = raw[:, :, :3]
        fg = alpha > 10
        img = np.full_like(bgr, 255)
        img[fg] = bgr[fg]
    else:
        img = raw if raw.ndim == 3 else cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR)
        fg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) < 245
    out = img.copy()
    h, w = fg.shape
    filled_rows = 0
    for y in range(h):
        xs = np.where(fg[y])[0]
        if len(xs) < 5:
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        gap = [x for x in range(x0, x1 + 1) if not fg[y, x]]
        if not gap:
            continue
        filled_rows += 1
        for x in gap:
            l = x
            while l >= x0 and not fg[y, l]:
                l -= 1
            r = x
            while r <= x1 and not fg[y, r]:
                r += 1
            cl = img[y, l] if l >= x0 else img[y, r]
            cr = img[y, r] if r <= x1 else img[y, l]
            out[y, x] = ((cl.astype(int) + cr.astype(int)) // 2).astype(np.uint8)
        xc = int(np.mean(gap))
        out[y, max(0, xc - 1):min(w, xc + 2)] = (out[y, xc].astype(int) * 0.55).astype(np.uint8)
    cv2.imwrite(str(out_path), out)
    print(f"  filled slit gap on {filled_rows} rows -> {out_path.name}")
    return out_path


def _maskgen_wf(person_ref, prefix, offload):
    return {
        "1": {"class_type": "FitDiTLoader", "inputs": {"device": "cuda", "with_fp16": False,
              "with_offload": offload, "with_aggressive_offload": False}},
        "2": {"class_type": "LoadImage", "inputs": {"image": person_ref, "upload": "image"}},
        "3": {"class_type": "FitDiTMaskGenerator", "inputs": {"model": ["1", 0], "vton_image": ["2", 0],
              "category": "Lower-body", "offset_top": 0, "offset_bottom": 0, "offset_left": 0, "offset_right": 0}},
        "4": {"class_type": "SaveImage", "inputs": {"images": ["3", 1], "filename_prefix": prefix + "_mask"}},
        "5": {"class_type": "SaveImage", "inputs": {"images": ["3", 2], "filename_prefix": prefix + "_pose"}},
    }


def _tryon_wf(person_ref, garm_ref, mask_ref, pose_ref, prefix, offload):
    return {
        "1": {"class_type": "FitDiTLoader", "inputs": {"device": "cuda", "with_fp16": False,
              "with_offload": offload, "with_aggressive_offload": False}},
        "2": {"class_type": "LoadImage", "inputs": {"image": person_ref, "upload": "image"}},
        "3": {"class_type": "LoadImage", "inputs": {"image": garm_ref, "upload": "image"}},
        "4": {"class_type": "LoadImage", "inputs": {"image": mask_ref, "upload": "image"}},
        "5": {"class_type": "LoadImage", "inputs": {"image": pose_ref, "upload": "image"}},
        "6": {"class_type": "FitDiTTryOn", "inputs": {"model": ["1", 0], "vton_image": ["2", 0],
              "garm_image": ["3", 0], "mask": ["4", 0], "pose_image": ["5", 0],
              "n_steps": 20, "image_scale": 2.0, "seed": SEED, "num_images": 1, "resolution": RES}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": prefix}},
    }


def _download(client, outputs, prefix, dst):
    for node_out in outputs.values():
        for img in node_out.get("images", []):
            if img.get("filename", "").startswith(prefix):
                dst.write_bytes(client.download(img["filename"], img.get("subfolder", ""),
                                                img.get("type", "output")))
                return dst
    raise RuntimeError(f"no output with prefix {prefix!r}")


def main():
    ap = ArgumentParser()
    ap.add_argument("--offload", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    filled = fill_slit_gap(SKIRT_REF, OUT / "skirt_filled_crop.png")

    client = ComfyUIClient()
    person_ref = client.upload_image(PERSON)
    garm_ref = client.upload_image(filled)

    print("  auto mask + pose ...")
    mg = client.submit(_maskgen_wf(person_ref, "proto_filled", args.offload))
    mg_out = client.poll(mg, timeout=TIMEOUT)
    auto_mask = _download(client, mg_out, "proto_filled_mask", OUT / "skirt_filled_automask.png")
    pose = _download(client, mg_out, "proto_filled_pose", OUT / "skirt_filled_pose.png")
    mask_ref = client.upload_image(auto_mask)
    pose_ref = client.upload_image(pose)

    print("  try-on (filled crop + continuous auto mask) ...")
    t0 = time.monotonic()
    ti = client.submit(_tryon_wf(person_ref, garm_ref, mask_ref, pose_ref, "proto_filled_tryon", args.offload))
    result = _download(client, client.poll(ti, timeout=TIMEOUT), "proto_filled_tryon", OUT / "skirt_filled_result.png")
    client.free()
    print(f"  done {round(time.monotonic()-t0,1)}s -> {result.relative_to(ROOT)}")
    print("\nOWNER CHECKPOINT: skirt_filled_result.png — skirt with slit now, or still pants?")
    print("  compare crop: skirt_filled_crop.png (gap closed, slit line kept)")


if __name__ == "__main__":
    main()
