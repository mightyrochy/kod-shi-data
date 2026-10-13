"""Trimmed Leffa virtual try-on (DressCode branch only) for the E-010 skirt head-to-head.

Standalone (official franciszzj/Leffa, MIT). Loads ONLY the DressCode try-on model + the
preprocessors it needs (humanparsing, openpose, densepose) — skips the VITON-HD and the
SDXL pose-transfer models to save VRAM and ~7GB of downloads.

    python leffa_skirt.py --src <person.png> --ref <skirt.png> --out <result.png> \
                          --garment lower_body --step 30 --scale 2.5 --seed 42

Run from the Leffa repo root with the venv that has torch+cu, detectron2, densepose.
"""

import argparse
import os
import sys

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
# densepose lives in the detectron2 source tree (projects/DensePose); allow override via env.
DENSEPOSE_PATH = os.environ.get(
    "DENSEPOSE_PATH", os.path.join(ROOT, "detectron2_src", "projects", "DensePose"))
if os.path.isdir(DENSEPOSE_PATH):
    sys.path.insert(0, DENSEPOSE_PATH)

# Use the Windows trust store for SSL (venv certifi can't verify the cert chain here).
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from huggingface_hub import snapshot_download

CKPT = os.path.join(ROOT, "ckpts")

# Only the DressCode try-on branch + its preprocessors (no SDXL pose-transfer, no VITON-HD weights).
ALLOW = [
    "stable-diffusion-inpainting/*",
    "virtual_tryon_dc.pth",
    "densepose/*",
    "schp/*",
    "humanparsing/*",
    "openpose/*",
    "examples/*",
]


def ensure_ckpts():
    snapshot_download(repo_id="franciszzj/Leffa", local_dir=CKPT, allow_patterns=ALLOW)


def align_mask(mask_path, tw=768, th=1024):
    """Bring an external mask (original-person coords) into the resize_and_center frame:
    same aspect-fit + centering as the person, padded with 0 (white = inpaint region)."""
    m = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    h, w = m.shape
    scale = min(th / h, tw / w)
    nh, nw = int(h * scale), int(w * scale)
    r = cv2.resize(m, (nw, nh), interpolation=cv2.INTER_NEAREST)
    canvas = np.zeros((th, tw), np.uint8)
    top, left = (th - nh) // 2, (tw - nw) // 2
    canvas[top:top + nh, left:left + nw] = r
    return Image.fromarray((canvas > 127).astype(np.uint8) * 255)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mask", default=None,
                    help="optional external mask (e.g. the continuous drape skirt mask); "
                         "overrides Leffa's leg-split auto mask to enforce a skirt silhouette")
    ap.add_argument("--garment", default="lower_body",
                    choices=["upper_body", "lower_body", "dresses"])
    ap.add_argument("--step", type=int, default=30)
    ap.add_argument("--scale", type=float, default=2.5)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    ensure_ckpts()

    from leffa.inference import LeffaInference
    from leffa.model import LeffaModel
    from leffa.transform import LeffaTransform
    from leffa_utils.densepose_predictor import DensePosePredictor
    from leffa_utils.utils import get_agnostic_mask_dc, resize_and_center
    from preprocess.humanparsing.run_parsing import Parsing
    from preprocess.openpose.run_openpose import OpenPose

    parsing = Parsing(atr_path=f"{CKPT}/humanparsing/parsing_atr.onnx",
                      lip_path=f"{CKPT}/humanparsing/parsing_lip.onnx")
    openpose = OpenPose(body_model_path=f"{CKPT}/openpose/body_pose_model.pth")
    densepose = DensePosePredictor(
        config_path=f"{CKPT}/densepose/densepose_rcnn_R_50_FPN_s1x.yaml",
        weights_path=f"{CKPT}/densepose/model_final_162be9.pkl")
    model = LeffaModel(
        pretrained_model_name_or_path=f"{CKPT}/stable-diffusion-inpainting",
        pretrained_model=f"{CKPT}/virtual_tryon_dc.pth", dtype="float16")
    inference = LeffaInference(model=model)

    src_image = resize_and_center(Image.open(args.src).convert("RGB"), 768, 1024)
    ref_image = resize_and_center(Image.open(args.ref).convert("RGB"), 768, 1024)
    src_arr = np.array(src_image)

    if args.mask:
        mask = align_mask(args.mask)
    else:
        model_parse, _ = parsing(src_image.resize((384, 512)))
        keypoints = openpose(src_image.resize((384, 512)))
        mask = get_agnostic_mask_dc(model_parse, keypoints, args.garment).resize((768, 1024))

    iuv = densepose.predict_iuv(src_arr)[:, :, 0:1]
    densepose_img = Image.fromarray(np.concatenate([iuv] * 3, axis=-1))

    data = LeffaTransform()({
        "src_image": [src_image], "ref_image": [ref_image],
        "mask": [mask], "densepose": [densepose_img]})
    output = inference(data, num_inference_steps=args.step,
                       guidance_scale=args.scale, seed=args.seed)
    output["generated_image"][0].save(args.out)
    mask.save(args.out.replace(".png", "_mask.png"))
    densepose_img.save(args.out.replace(".png", "_densepose.png"))
    print(f"SAVED {args.out}")


if __name__ == "__main__":
    main()
