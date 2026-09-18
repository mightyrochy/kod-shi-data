"""E-014 autonomous pre-OmniTry pipeline — ONE command, runs itself, stops when ready for OmniTry.

    python experiments/014_full_pipeline_3item/pipeline.py

Stages (no manual steps between them):
  0. build the reduced 3-item board (blouse + skirt[continuous] + wedge sandals)
  1. QIE holistic try-on of the three garments (logical untucked prompt)
  2. CLEAN checks — ATR human-parsing garment masks (skin-excluded) vs isolated references
     (FashionSigLIP sim + DISTS + CIEDE2000); texture recorded but NOT gated on
  3. FitDiT repair IF NEEDED — any FitDiT-repairable garment (skirt) failing the check is repaired
     locally (skirt mask minus belt, hi-res) and re-checked
  4. STOP — print the report; the image is ready for the OmniTry accessory stage (belt + earrings)

Needs ComfyUI live (:8000) with QIE + FitDiT, and the local Leffa ATR parser (system.segmentation.parsing).
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from system.clients.comfyui import ComfyUIClient
from system.gates.garment_fidelity import measure_garment_correspondence
from system.segmentation.parsing import garment_masks
from system.workflows import fill_workflow, load_template

A = ROOT / "assets/outfits/outfit_001"
E001 = ROOT / "experiments/001_segmentation_masks/results"
OUT = Path(__file__).parent / "results"
PERSON = ROOT / "assets/person/person_front.png"
BOARD = A / "reference_boards/garments3_hybrid.png"
GARMENT_SKIRT = A / "crops/skirt_front_continuous.png"
SEED, GEN_RES, CANON_AREA = 42, "1152x1536", 1152 * 1536

PROMPT = (
    "Keep this exact person: face, hair, skin tone, body proportions, pose, and background unchanged. "
    "Using the reference board (image 2), re-dress them in the outfit shown. The board shows labeled "
    "garments: blouse, skirt, and wedge sandals. Dress the person in a blouse, a maxi skirt, and wedge "
    "sandals. The blouse is worn UNTUCKED — its hem hangs loose over the skirt waistband, not tucked "
    "in. The skirt is high-waisted and falls to the ankles. The wedge sandals are on the feet, visible "
    "below the skirt hem. Take all garment appearance from the board only."
)
# garment -> (ATR region, isolated reference image, reference mask). FitDiT-repairable: skirt.
ITEMS = {
    "blouse": ("upper", A / "blouse_front.webp", A / "reference_masks/blouse_front_buttons.png"),
    "skirt":  ("skirt", A / "skirt_front.webp", E001 / "outfit_001_skirt_front/skirt.png"),
    "shoes":  ("shoes", A / "shoes_wedge.webp", E001 / "outfit_001_shoes_wedge/shoes.png"),
}
SIM_OK = 0.85  # calibrated 2026-06-21


def _download(client, outputs, prefix, dst):
    for no in outputs.values():
        for im in no.get("images", []):
            if im.get("filename", "").startswith(prefix):
                dst.write_bytes(client.download(im["filename"], im.get("subfolder", ""), im.get("type", "output")))
                return dst
    raise RuntimeError(f"no output with prefix {prefix!r}")


def stage_qie(client) -> Path:
    wf = fill_workflow(load_template("qie2511_vton"), {
        "__PERSON_IMAGE__": client.upload_image(PERSON), "__REF_IMAGE__": client.upload_image(BOARD),
        "__POSITIVE_PROMPT__": PROMPT, "__NEGATIVE_PROMPT__": "", "__CFG__": 4.0,
        "__SAMPLER__": "euler", "__SCHEDULER__": "simple", "__SEED__": SEED, "__STEPS__": 20,
        "__OUTPUT_PREFIX__": "e014_qie", "__DENOISE__": 1.0,
    })
    out = _download(client, client.poll(client.submit(wf), timeout=600), "e014_qie", OUT / "e014_qie.png")
    client.free()
    return out


def check(image_path: Path) -> dict:
    """ATR-parse the image and run the clean garment-correspondence check for each item."""
    masks = garment_masks(image_path, [v[0] for v in ITEMS.values()])
    report = {}
    for name, (region, ref_img, ref_mask) in ITEMS.items():
        m = masks[region]
        if (m > 127).sum() < 200:
            report[name] = {"verdict": "TOO_SMALL", "coverage_px": int((m > 127).sum())}
            continue
        r = measure_garment_correspondence(str(image_path), m, str(ref_img), str(ref_mask))
        sim = r["identity"]["siglip_sim"]
        colour = r["colour"]["verdict"]
        ok = sim is not None and sim >= SIM_OK and colour != "FAIL"
        report[name] = {"verdict": "PASS" if ok else "CHECK", "sim": sim, "match": r["identity"]["match"],
                        "dists": r["structure"].get("score"), "dE": r["colour"].get("delta_e_mean"),
                        "colour": colour, "weave_recorded": r["texture"]["texture_ratio"]}
    return report


def stage_fitdit_skirt(client, base: Path) -> Path:
    """Local, belt-preserving FitDiT skirt repair on `base` at the canonical 1.77 MP (run_e013_hires logic)."""
    from system.segmentation.grounded_sam import segment
    from system.segmentation.prompts import generated_prompts
    img = cv2.imread(str(base)); h, w = img.shape[:2]
    ar = w / h
    cw, ch = round(math.sqrt(CANON_AREA * ar) / 16) * 16, round(math.sqrt(CANON_AREA / ar) / 16) * 16
    base_hi = cv2.resize(img, (cw, ch), interpolation=cv2.INTER_LANCZOS4)
    base_hi_p = OUT / "e014_base_hi.png"; cv2.imwrite(str(base_hi_p), base_hi)
    base_ref, garm_ref = client.upload_image(base_hi_p), client.upload_image(GARMENT_SKIRT)

    def fl(node):
        return {"class_type": "FitDiTLoader", "inputs": {"device": "cuda", "with_fp16": False,
                "with_offload": True, "with_aggressive_offload": False}}
    mg = {"1": fl(1), "2": {"class_type": "LoadImage", "inputs": {"image": base_ref, "upload": "image"}},
          "3": {"class_type": "FitDiTMaskGenerator", "inputs": {"model": ["1", 0], "vton_image": ["2", 0],
                "category": "Lower-body", "offset_top": 0, "offset_bottom": 0, "offset_left": 0, "offset_right": 0}},
          "4": {"class_type": "SaveImage", "inputs": {"images": ["3", 1], "filename_prefix": "e014_fdmask"}},
          "5": {"class_type": "SaveImage", "inputs": {"images": ["3", 2], "filename_prefix": "e014_fdpose"}}}
    mo = client.poll(client.submit(mg), timeout=900)
    mask = _download(client, mo, "e014_fdmask", OUT / "e014_fdmask.png")
    pose = _download(client, mo, "e014_fdpose", OUT / "e014_fdpose.png")
    ti = {"1": fl(1), "2": {"class_type": "LoadImage", "inputs": {"image": base_ref, "upload": "image"}},
          "3": {"class_type": "LoadImage", "inputs": {"image": garm_ref, "upload": "image"}},
          "4": {"class_type": "LoadImage", "inputs": {"image": client.upload_image(mask), "upload": "image"}},
          "5": {"class_type": "LoadImage", "inputs": {"image": client.upload_image(pose), "upload": "image"}},
          "6": {"class_type": "FitDiTTryOn", "inputs": {"model": ["1", 0], "vton_image": ["2", 0],
                "garm_image": ["3", 0], "mask": ["4", 0], "pose_image": ["5", 0], "n_steps": 20,
                "image_scale": 2.0, "seed": SEED, "num_images": 1, "resolution": GEN_RES}},
          "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "e014_fdtry"}}}
    fit = _download(client, client.poll(client.submit(ti), timeout=900), "e014_fdtry", OUT / "e014_fdtry.png")
    sk = segment(str(fit), generated_prompts("bottom"), client, OUT / "e014_segfit")["bottom"]
    be = segment(str(base_hi_p), generated_prompts("belt"), client, OUT / "e014_segbelt")["belt"]
    client.free()
    fit_img = cv2.resize(cv2.imread(str(fit)), (cw, ch))
    skm = cv2.resize(cv2.imread(sk, 0), (cw, ch), interpolation=cv2.INTER_NEAREST)
    bem = cv2.resize(cv2.imread(be, 0), (cw, ch), interpolation=cv2.INTER_NEAREST)
    bed = cv2.dilate((bem > 127).astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    region = ((skm > 127) & ~(bed > 127)).astype(np.float32)
    alpha = cv2.GaussianBlur(region, (0, 0), 5.0)[..., None]
    out = (fit_img * alpha + base_hi * (1 - alpha)).clip(0, 255).astype(np.uint8)
    dst = OUT / "e014_skirt_repaired.png"; cv2.imwrite(str(dst), out)
    return dst


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    print("[0] board ..."); subprocess.run([sys.executable, str(A / "build_reduced_board.py")], check=True)
    client = ComfyUIClient()
    print("[1] QIE holistic ..."); image = stage_qie(client)
    print("[2] clean checks (ATR parsing) ..."); rep = check(image)
    repaired = False
    for name, res in rep.items():
        flag = res["verdict"] not in ("PASS", "TOO_SMALL")
        print(f"    {name:7} {res['verdict']:9} sim={res.get('sim')} colour={res.get('colour')} "
              f"dE={res.get('dE')} weave(rec)={res.get('weave_recorded')}")
        if flag and name == "skirt":
            print("[3] skirt below check -> FitDiT local repair ...")
            client = ComfyUIClient()
            image = stage_fitdit_skirt(client, image)
            rep["skirt_after_fitdit"] = check(image)["skirt"]
            repaired = True
    final = OUT / "e014_ready_for_omnitry.png"; final.write_bytes(image.read_bytes())
    manifest = {"final_image": str(final.relative_to(ROOT)), "repaired_with_fitdit": repaired,
                "checks": rep, "seconds": round(time.monotonic() - t0, 1)}
    (OUT / "pipeline_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[4] STOP — ready for OmniTry: {final.relative_to(ROOT)}  ({manifest['seconds']}s)")
    print("    next stage (not run): OmniTry adds belt + earrings.")


if __name__ == "__main__":
    main()
