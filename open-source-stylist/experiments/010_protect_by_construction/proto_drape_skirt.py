"""E-010 — drape-synthesizer skirt test (geometric level).

Uses system/drape.py to build, automatically:
  - garment_descriptor → continuous silhouette (gap filled, slit kept) + length ratio,
  - body_model → pose anchors,
  - skirt_agnostic_mask → mask whose HEM = hip_y + length_ratio*hip_width (garment length,
    not leg length), continuous.
Then one FitDiT pass. Tests whether the length is now correct (and topology stays a skirt).

    python experiments/010_protect_by_construction/proto_drape_skirt.py [--offload]
"""

from __future__ import annotations

import sys
import time
from argparse import ArgumentParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from system import drape
from system.clients.comfyui import ComfyUIClient

PERSON = ROOT / "assets/person/person_front.png"
SKIRT_REF = ROOT / "assets/outfits/outfit_001/crops/skirt_front_fitdit.png"
SKIRT_ON_MODEL = ROOT / "assets/outfits/outfit_001/skirt_front.webp"
OUT = Path(__file__).parent / "results" / "proto_chain"
RES = "768x1024"
SEED = 42
TIMEOUT = 900.0


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

    print("  body_model + garment_descriptor ...")
    body = drape.body_model(PERSON)
    desc = drape.garment_descriptor(SKIRT_REF, continuous_out=OUT / "drape_skirt_crop.png")
    print(f"    hip_y={int(body['hip_y'])} ankle_y={int(body['ankle_y'])} hip_w={int(body['hip_width'])}")
    print(f"    garment length_ratio={desc['length_ratio']:.2f} top_width={desc['top_width']}")

    client = ComfyUIClient()

    print("  measure_on_model (skirt on its on-model photo) ...")
    meas = drape.measure_on_model(SKIRT_ON_MODEL, "skirt", client, out_dir=OUT)
    print(f"    length_fraction={meas['length_fraction']:.3f} (of hip->ankle)  width_ratio={meas['width_ratio']:.2f}")

    person_ref = client.upload_image(PERSON)
    garm_ref = client.upload_image(OUT / "drape_skirt_crop.png")

    print("  auto mask + pose ...")
    mg_out = client.poll(client.submit(_maskgen_wf(person_ref, "proto_drape", args.offload)), timeout=TIMEOUT)
    auto_mask = _download(client, mg_out, "proto_drape_mask", OUT / "drape_skirt_automask.png")
    pose = _download(client, mg_out, "proto_drape_pose", OUT / "drape_skirt_pose.png")

    mask_path, hem_y = drape.agnostic_mask(auto_mask, body, meas["length_fraction"], OUT / "drape_skirt_mask.png")
    print(f"    HEM at y={hem_y} (measured frac {meas['length_fraction']:.2f}; target ankle={int(body['ankle_y'])})")

    mask_ref = client.upload_image(mask_path)
    pose_ref = client.upload_image(pose)

    print("  try-on (continuous crop + length-correct drape mask) ...")
    t0 = time.monotonic()
    result = _download(client, client.poll(
        client.submit(_tryon_wf(person_ref, garm_ref, mask_ref, pose_ref, "proto_drape_tryon", args.offload)),
        timeout=TIMEOUT), "proto_drape_tryon", OUT / "drape_skirt_result.png")
    client.free()
    print(f"  done {round(time.monotonic()-t0,1)}s -> {result.relative_to(ROOT)}")
    print("\nOWNER CHECKPOINT: drape_skirt_result.png — length correct now? still a skirt with slit?")
    print("  mask: drape_skirt_mask.png (hem from garment proportions) · crop: drape_skirt_crop.png")


if __name__ == "__main__":
    main()
