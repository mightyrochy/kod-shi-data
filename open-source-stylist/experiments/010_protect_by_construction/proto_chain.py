"""E-010 prototype — chained FitDiT on the SOURCE with our own occlusion-aware masks.

Tests two claims at once:
  1. A continuous skirt-silhouette mask (auto Lower-body mask, row-filled to close the
     leg gap) makes FitDiT render a SKIRT, not pants — without editing the garment crop.
  2. Layering emerges from pass order: skirt pass, then blouse pass on that result, with
     the blouse mask extended down over the skirt waist → blouse over skirt.

Per garment pass we do TWO ComfyUI calls:
  a) FitDiTMaskGenerator → save its auto mask + pose; download them;
  b) modify the mask in numpy (skirt: row-fill; blouse: dilate downward);
  c) FitDiTTryOn(person, OUR mask, garment, pose) → the garment rendered into OUR mask.

Run (ComfyUI must be live on :8000; FitDiT node installed):
    python experiments/010_protect_by_construction/proto_chain.py            # full chain
    python experiments/010_protect_by_construction/proto_chain.py --skirt-only
Add --offload if VRAM OOM. Identity gate needs system Python (insightface).
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
CROPS = ROOT / "assets/outfits/outfit_001/crops"
SKIRT_REF = CROPS / "skirt_front_fitdit.png"
BLOUSE_REF = CROPS / "blouse_front_fitdit.png"
OUT = Path(__file__).parent / "results" / "proto_chain"
RES = "768x1024"
SEED = 42
TIMEOUT = 900.0


def _maskgen_wf(person_ref: str, category: str, prefix: str, offload: bool) -> dict:
    return {
        "1": {"class_type": "FitDiTLoader",
              "inputs": {"device": "cuda", "with_fp16": False,
                         "with_offload": offload, "with_aggressive_offload": False}},
        "2": {"class_type": "LoadImage", "inputs": {"image": person_ref, "upload": "image"}},
        "3": {"class_type": "FitDiTMaskGenerator",
              "inputs": {"model": ["1", 0], "vton_image": ["2", 0], "category": category,
                         "offset_top": 0, "offset_bottom": 0, "offset_left": 0, "offset_right": 0}},
        "4": {"class_type": "SaveImage", "inputs": {"images": ["3", 1], "filename_prefix": prefix + "_mask"}},
        "5": {"class_type": "SaveImage", "inputs": {"images": ["3", 2], "filename_prefix": prefix + "_pose"}},
    }


def _tryon_wf(person_ref: str, garm_ref: str, mask_ref: str, pose_ref: str,
              prefix: str, offload: bool) -> dict:
    return {
        "1": {"class_type": "FitDiTLoader",
              "inputs": {"device": "cuda", "with_fp16": False,
                         "with_offload": offload, "with_aggressive_offload": False}},
        "2": {"class_type": "LoadImage", "inputs": {"image": person_ref, "upload": "image"}},
        "3": {"class_type": "LoadImage", "inputs": {"image": garm_ref, "upload": "image"}},
        "4": {"class_type": "LoadImage", "inputs": {"image": mask_ref, "upload": "image"}},
        "5": {"class_type": "LoadImage", "inputs": {"image": pose_ref, "upload": "image"}},
        "6": {"class_type": "FitDiTTryOn",
              "inputs": {"model": ["1", 0], "vton_image": ["2", 0], "garm_image": ["3", 0],
                         "mask": ["4", 0], "pose_image": ["5", 0],
                         "n_steps": 20, "image_scale": 2.0, "seed": SEED,
                         "num_images": 1, "resolution": RES}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": prefix}},
    }


def _download(client: ComfyUIClient, outputs: dict, prefix: str, dst: Path) -> Path:
    for node_out in outputs.values():
        for img in node_out.get("images", []):
            if img.get("filename", "").startswith(prefix):
                dst.write_bytes(client.download(img["filename"], img.get("subfolder", ""),
                                                img.get("type", "output")))
                return dst
    raise RuntimeError(f"no ComfyUI output with prefix {prefix!r}")


def _row_fill(mask_path: Path, out_path: Path) -> Path:
    """Close the leg gap: per row, fill from leftmost to rightmost foreground pixel."""
    m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    fg = m > 127
    out = np.zeros_like(m)
    for y in range(m.shape[0]):
        xs = np.where(fg[y])[0]
        if len(xs):
            out[y, xs.min():xs.max() + 1] = 255
    cv2.imwrite(str(out_path), out)
    return out_path


def _dilate_down(mask_path: Path, out_path: Path, px: int = 90) -> Path:
    """Extend the (blouse) mask downward by px so it overlaps the skirt waistband."""
    m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    fg = (m > 127).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 2 * px + 1))
    down = cv2.dilate(fg, kernel, anchor=(0, 0))  # anchor top → grows downward only
    cv2.imwrite(str(out_path), down)
    return out_path


def _pass(client, label, person_ref, garm_ref, category, mask_fn, person_path, offload):
    """One garment pass: maskgen → modify mask → tryon. Returns the result image path."""
    print(f"\n--- pass: {label} ({category}) ---")
    # a) auto mask + pose
    mg = client.submit(_maskgen_wf(person_ref, category, f"proto_{label}", offload))
    mg_out = client.poll(mg, timeout=TIMEOUT)
    auto_mask = _download(client, mg_out, f"proto_{label}_mask", OUT / f"{label}_automask.png")
    pose_img = _download(client, mg_out, f"proto_{label}_pose", OUT / f"{label}_pose.png")
    print(f"  auto mask + pose downloaded")
    # b) our mask
    our_mask = mask_fn(auto_mask, OUT / f"{label}_ourmask.png")
    mask_ref = client.upload_image(our_mask)
    pose_ref = client.upload_image(pose_img)
    # c) try-on with OUR mask
    t0 = time.monotonic()
    ti = client.submit(_tryon_wf(person_ref, garm_ref, mask_ref, pose_ref, f"proto_tryon_{label}", offload))
    ti_out = client.poll(ti, timeout=TIMEOUT)
    result = _download(client, ti_out, f"proto_tryon_{label}", OUT / f"{label}_result.png")
    print(f"  try-on {label}: {round(time.monotonic() - t0, 1)}s -> {result.relative_to(ROOT)}")
    return result


def main() -> None:
    ap = ArgumentParser()
    ap.add_argument("--skirt-only", action="store_true")
    ap.add_argument("--offload", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    client = ComfyUIClient()
    source_ref = client.upload_image(PERSON)
    skirt_ref = client.upload_image(SKIRT_REF)

    # Pass 1 — skirt on the SOURCE, mask = row-filled Lower-body (continuous silhouette)
    canvas1 = _pass(client, "skirt", source_ref, skirt_ref, "Lower-body", _row_fill, PERSON, args.offload)

    if not args.skirt_only:
        # Pass 2 — blouse on canvas1, mask = Upper-body dilated down over the skirt waist
        canvas1_ref = client.upload_image(canvas1)
        blouse_ref = client.upload_image(BLOUSE_REF)
        canvas2 = _pass(client, "blouse", canvas1_ref, blouse_ref, "Upper-body", _dilate_down, canvas1, args.offload)
        final = canvas2
    else:
        final = canvas1

    client.free()
    print(f"\nFINAL: {final.relative_to(ROOT)}")
    print(f"Intermediates in {OUT.relative_to(ROOT)}/ (automask, ourmask, result per pass)")
    print("\nOWNER CHECKPOINT:")
    print("  skirt_result.png  — does the row-filled mask render a SKIRT (not pants)?")
    if not args.skirt_only:
        print("  blouse_result.png — does the blouse layer OVER the skirt (pass order + mask overlap)?")
    print("  + identity preserved (run identity gate via system Python on the final image).")


if __name__ == "__main__":
    main()
