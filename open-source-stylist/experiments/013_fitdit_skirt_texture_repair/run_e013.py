"""E-013 — FitDiT skirt-texture repair of the QIE holistic output.

Re-render the skirt region of the E-012 QIE output (right shape, FLAT texture) with FitDiT, using a
continuous-silhouette textured skirt reference at high resolution. Canonical FitDiT flow
(FITDIT_AUDIT_2026-06-21): native Lower-body mask + pose on the base, then FitDiTTryOn.

    python experiments/013_fitdit_skirt_texture_repair/run_e013.py [--res 1152x1536] [--no-offload]

ComfyUI must be live on :8000 with the FitDiT node + models.
"""

from __future__ import annotations

import sys
import time
from argparse import ArgumentParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from system.clients.comfyui import ComfyUIClient

BASE = ROOT / "experiments/012_holistic_workflow_fix/results/holistic_v1_fixed_graph.png"
GARMENT = ROOT / "experiments/010_protect_by_construction/results/proto_chain/skirt_filled_crop.png"
OUT = Path(__file__).parent / "results"
SEED = 42
TIMEOUT = 900.0


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


def main():
    ap = ArgumentParser()
    ap.add_argument("--res", default="1152x1536", choices=["768x1024", "1152x1536", "1536x2048"])
    ap.add_argument("--no-offload", action="store_true")
    args = ap.parse_args()
    offload = not args.no_offload
    OUT.mkdir(parents=True, exist_ok=True)

    client = ComfyUIClient()
    base_ref = client.upload_image(BASE)
    garm_ref = client.upload_image(GARMENT)

    print("  FitDiT Lower-body mask + pose on the QIE output ...")
    mg = client.poll(client.submit(_maskgen_wf(base_ref, "e013", offload)), timeout=TIMEOUT)
    mask = _download(client, mg, "e013_mask", OUT / "e013_skirt_mask.png")
    pose = _download(client, mg, "e013_pose", OUT / "e013_skirt_pose.png")
    mask_ref = client.upload_image(mask)
    pose_ref = client.upload_image(pose)

    print(f"  FitDiT try-on (skirt, {args.res}, offload={offload}) ...")
    t0 = time.monotonic()
    ti = client.submit(_tryon_wf(base_ref, garm_ref, mask_ref, pose_ref, "e013_skirt_repaired",
                                 args.res, offload))
    result = _download(client, client.poll(ti, timeout=TIMEOUT), "e013_skirt_repaired",
                       OUT / "e013_skirt_repaired.png")
    client.free()
    print(f"  done {round(time.monotonic()-t0,1)}s -> {result.relative_to(ROOT)}")
    print("\nOWNER CHECKPOINT: e013_skirt_repaired.png — skirt texture restored, still a skirt, rest preserved?")


if __name__ == "__main__":
    main()
