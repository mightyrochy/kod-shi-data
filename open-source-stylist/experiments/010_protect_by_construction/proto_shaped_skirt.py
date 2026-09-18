"""E-010 — shaped skirt-mask test.

Owner hypothesis: the generic full-leg rectangle mask is too coarse — it does not tell
FitDiT the skirt's shape/length, so FitDiT fills the whole leg region and (with the slit)
reads as pants. This builds a SKIRT-SILHOUETTE mask from pose keypoints (a body-hugging
trapezoid, waist→ankle, slight A-line) and runs one FitDiT pass with it.

If it renders a skirt → the mask shape was the lever. If still pants → confirms FitDiT
re-synthesis cannot honour the garment shape → warping engine for the lower garment.

    python experiments/010_protect_by_construction/proto_shaped_skirt.py [--offload]
ComfyUI must be live on :8000; FitDiT installed. cv2/numpy/mediapipe in system Python.
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
POSE_MODEL = ROOT / "system/gates/models/pose_landmarker_full.task"
OUT = Path(__file__).parent / "results" / "proto_chain"
RES = "768x1024"
SEED = 42
TIMEOUT = 900.0


def skirt_silhouette_mask(person_path: Path, out_path: Path) -> Path:
    """Trapezoid skirt silhouette from pose: waist (hips) → ankle, body-hugging, slight A-line."""
    import mediapipe as mp
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision

    img = cv2.imread(str(person_path))
    h, w = img.shape[:2]
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    opts = vision.PoseLandmarkerOptions(
        base_options=mp_tasks.BaseOptions(model_asset_path=str(POSE_MODEL)),
        running_mode=vision.RunningMode.IMAGE, num_poses=1)
    res = vision.PoseLandmarker.create_from_options(opts).detect(
        mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb)))
    lm = res.pose_landmarks[0]

    def px(i):  # MediaPipe: 23/24 hips, 27/28 ankles
        return (lm[i].x * w, lm[i].y * h)

    lhip, rhip = px(23), px(24)
    lank, rank = px(27), px(28)
    cx = (lhip[0] + rhip[0]) / 2.0
    hip_w = abs(lhip[0] - rhip[0])
    waist_y = (lhip[1] + rhip[1]) / 2.0        # top of skirt at the hips
    hem_y = (lank[1] + rank[1]) / 2.0          # maxi length → ankle
    top_hw = hip_w * 0.70                       # hug the hips (NOT the splayed-leg width)
    bot_hw = hip_w * 1.00                       # slight A-line flare

    poly = np.array([[cx - top_hw, waist_y], [cx + top_hw, waist_y],
                     [cx + bot_hw, hem_y], [cx - bot_hw, hem_y]], dtype=np.int32)
    mask = np.zeros((h, w), np.uint8)
    cv2.fillPoly(mask, [poly], 255)
    cv2.imwrite(str(out_path), mask)
    print(f"  shaped mask: hips@y={int(waist_y)} ankles@y={int(hem_y)} hip_w={int(hip_w)} -> {out_path.name}")
    return out_path


def _maskgen_wf(person_ref, prefix, offload):
    return {
        "1": {"class_type": "FitDiTLoader", "inputs": {"device": "cuda", "with_fp16": False,
              "with_offload": offload, "with_aggressive_offload": False}},
        "2": {"class_type": "LoadImage", "inputs": {"image": person_ref, "upload": "image"}},
        "3": {"class_type": "FitDiTMaskGenerator", "inputs": {"model": ["1", 0], "vton_image": ["2", 0],
              "category": "Lower-body", "offset_top": 0, "offset_bottom": 0, "offset_left": 0, "offset_right": 0}},
        "4": {"class_type": "SaveImage", "inputs": {"images": ["3", 2], "filename_prefix": prefix + "_pose"}},
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

    mask_path = skirt_silhouette_mask(PERSON, OUT / "shaped_skirt_mask.png")

    client = ComfyUIClient()
    person_ref = client.upload_image(PERSON)
    skirt_ref = client.upload_image(SKIRT_REF)
    mask_ref = client.upload_image(mask_path)

    print("  getting pose ...")
    mg = client.submit(_maskgen_wf(person_ref, "proto_shaped", args.offload))
    pose_path = _download(client, client.poll(mg, timeout=TIMEOUT), "proto_shaped_pose", OUT / "shaped_skirt_pose.png")
    pose_ref = client.upload_image(pose_path)

    print("  try-on with shaped mask ...")
    t0 = time.monotonic()
    ti = client.submit(_tryon_wf(person_ref, skirt_ref, mask_ref, pose_ref, "proto_shaped_tryon", args.offload))
    result = _download(client, client.poll(ti, timeout=TIMEOUT), "proto_shaped_tryon", OUT / "shaped_skirt_result.png")
    client.free()
    print(f"  done {round(time.monotonic()-t0,1)}s -> {result.relative_to(ROOT)}")
    print("\nOWNER CHECKPOINT: shaped_skirt_result.png — skirt now, or still pants?")
    print("  (compare mask shaped_skirt_mask.png vs the earlier full-rectangle skirt_automask.png)")


if __name__ == "__main__":
    main()
