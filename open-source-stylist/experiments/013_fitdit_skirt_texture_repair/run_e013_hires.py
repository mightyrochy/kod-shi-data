"""E-013 hi-res — resolution-correct, belt-preserving FitDiT skirt repair.

Fixes the two issues the owner flagged on the first E-013 run:
  1. RESOLUTION: FitDiT resizes its output back to the input size, so feeding it the ~1MP QIE base threw
     away the 1152x1536 detail. Fix = upscale the base to the canonical 1.77 MP (aspect-preserved) FIRST,
     so FitDiT's output stays hi-res.
  2. BELT VANISHED: FitDiT regenerates the whole lower body (not local), erasing the waist belt. Fix =
     composite ONLY the skirt fabric (skirt mask MINUS the belt) back into the base — belt + blouse +
     face + background stay byte-identical from the base; only the skirt carries the new hi-res texture.

    python experiments/013_fitdit_skirt_texture_repair/run_e013_hires.py
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from system.clients.comfyui import ComfyUIClient
from system.segmentation.grounded_sam import segment
from system.segmentation.prompts import generated_prompts

BASE = ROOT / "experiments/012_holistic_workflow_fix/results/holistic_v1_fixed_graph.png"
GARMENT = ROOT / "experiments/010_protect_by_construction/results/proto_chain/skirt_filled_crop.png"
OUT = Path(__file__).parent / "results"
CANON_AREA = 1152 * 1536            # canonical 1.77 MP target (owner-chosen)
GEN_RES = "1152x1536"              # FitDiT generation budget
SEED = 42
TIMEOUT = 900.0


def _canonical_size(w: int, h: int) -> tuple[int, int]:
    """1.77 MP preserving the input aspect ratio, rounded to /16 (FitDiT-friendly)."""
    ar = w / h
    cw = round(math.sqrt(CANON_AREA * ar) / 16) * 16
    ch = round(math.sqrt(CANON_AREA / ar) / 16) * 16
    return cw, ch


def _maskgen_wf(base_ref, prefix, offload):
    return {
        "1": {"class_type": "FitDiTLoader", "inputs": {"device": "cuda", "with_fp16": False,
              "with_offload": offload, "with_aggressive_offload": False}},
        "2": {"class_type": "LoadImage", "inputs": {"image": base_ref, "upload": "image"}},
        "3": {"class_type": "FitDiTMaskGenerator", "inputs": {"model": ["1", 0], "vton_image": ["2", 0],
              "category": "Lower-body", "offset_top": 0, "offset_bottom": 0,
              "offset_left": 0, "offset_right": 0}},
        "4": {"class_type": "SaveImage", "inputs": {"images": ["3", 1], "filename_prefix": prefix + "_mask"}},
        "5": {"class_type": "SaveImage", "inputs": {"images": ["3", 2], "filename_prefix": prefix + "_pose"}},
    }


def _tryon_wf(base_ref, garm_ref, mask_ref, pose_ref, prefix, res, offload):
    return {
        "1": {"class_type": "FitDiTLoader", "inputs": {"device": "cuda", "with_fp16": False,
              "with_offload": offload, "with_aggressive_offload": False}},
        "2": {"class_type": "LoadImage", "inputs": {"image": base_ref, "upload": "image"}},
        "3": {"class_type": "LoadImage", "inputs": {"image": garm_ref, "upload": "image"}},
        "4": {"class_type": "LoadImage", "inputs": {"image": mask_ref, "upload": "image"}},
        "5": {"class_type": "LoadImage", "inputs": {"image": pose_ref, "upload": "image"}},
        "6": {"class_type": "FitDiTTryOn", "inputs": {"model": ["1", 0], "vton_image": ["2", 0],
              "garm_image": ["3", 0], "mask": ["4", 0], "pose_image": ["5", 0],
              "n_steps": 20, "image_scale": 2.0, "seed": SEED, "num_images": 1, "resolution": res}},
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


def _to_size(mask_path, cw, ch):
    m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if (m.shape[1], m.shape[0]) != (cw, ch):
        m = cv2.resize(m, (cw, ch), interpolation=cv2.INTER_NEAREST)
    return m


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base = cv2.imread(str(BASE))
    h, w = base.shape[:2]
    cw, ch = _canonical_size(w, h)
    base_hi = cv2.resize(base, (cw, ch), interpolation=cv2.INTER_LANCZOS4)
    base_hi_path = OUT / "base_canonical_1p77.png"
    cv2.imwrite(str(base_hi_path), base_hi)
    print(f"  base {w}x{h} -> canonical {cw}x{ch} ({cw*ch/1e6:.2f} MP)")

    client = ComfyUIClient()
    base_ref = client.upload_image(base_hi_path)
    garm_ref = client.upload_image(GARMENT)

    print("  FitDiT mask + pose on the canonical base ...")
    mg = client.poll(client.submit(_maskgen_wf(base_ref, "e013hi", True)), timeout=TIMEOUT)
    mask = _download(client, mg, "e013hi_mask", OUT / "e013hi_agnosticmask.png")
    pose = _download(client, mg, "e013hi_pose", OUT / "e013hi_pose.png")

    print(f"  FitDiT try-on (skirt, gen {GEN_RES}, hi-res base) ...")
    t0 = time.monotonic()
    ti = client.submit(_tryon_wf(base_ref, garm_ref, client.upload_image(mask),
                                 client.upload_image(pose), "e013hi_tryon", GEN_RES, True))
    fit = _download(client, client.poll(ti, timeout=TIMEOUT), "e013hi_tryon", OUT / "e013hi_fitdit_raw.png")
    print(f"  FitDiT done {round(time.monotonic()-t0,1)}s")

    print("  segment skirt (FitDiT result) + belt (base) for the local composite ...")
    skirt_m = _to_size(segment(fit, generated_prompts("bottom"), client, OUT / "seg_fit")["bottom"], cw, ch)
    belt_m = _to_size(segment(base_hi_path, generated_prompts("belt"), client, OUT / "seg_base")["belt"], cw, ch)
    client.free()

    fit_img = cv2.imread(str(fit))
    if fit_img.shape[:2] != (ch, cw):
        fit_img = cv2.resize(fit_img, (cw, ch), interpolation=cv2.INTER_LANCZOS4)

    if (belt_m > 127).sum() < 50:
        print("  WARNING: belt mask is ~empty — belt may not be protected.")
    belt_d = cv2.dilate((belt_m > 127).astype(np.uint8) * 255,
                        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    region = ((skirt_m > 127) & ~(belt_d > 127)).astype(np.float32)
    alpha = cv2.GaussianBlur(region, (0, 0), 5.0)[..., None]
    out = (fit_img.astype(np.float32) * alpha + base_hi.astype(np.float32) * (1 - alpha)).clip(0, 255).astype(np.uint8)
    final = OUT / "e013hi_final.png"
    cv2.imwrite(str(final), out)
    print(f"  -> {final.relative_to(ROOT)} ({cw}x{ch})")
    print("\nOWNER CHECKPOINT: e013hi_final.png — hi-res skirt texture, belt restored, rest intact?")


if __name__ == "__main__":
    main()
