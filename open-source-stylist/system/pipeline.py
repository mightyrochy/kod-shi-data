"""Universal pre-OmniTry try-on pipeline — ONE wired system, input-driven, not outfit-specific.

Input: a person image, an outfit layout (text), and the ORIGINAL image of each garment with its TYPE.
The system reacts to the input — it does not expect any particular garment:

  garment.classify() maps any garment LABEL -> {atr region, segmentation term, FitDiT category, holistic
  vs accessory} by keyword, with a safe default for unknown labels. "holistic" garments (tops/bottoms/
  dresses/footwear) go through the QIE board+holistic pass; "accessory" garments (belt/earrings/bag/...)
  are deferred to the OmniTry stage (NOT run here).

Stages (autonomous, stops before OmniTry; every artifact saved under outdir):
  1-2. board.build() isolates each holistic garment (human-parsing when clean, else GroundingDINO+SAM),
     makes single-piece silhouettes continuous, and assembles the combined (mask + crop) board. A garment
     that fails the gross-error guard stops the run for owner review.
  3. build the QIE prompt from the layout (literal layering).
  4. QIE holistic try-on.
  5. checks per garment (ATR parse region): identity (ArcFace, whole image), colour (CIEDE2000),
     structure (AnomalyDINO), texture (recorded, non-gating) + a Qwen3-VL judge (multi-image,
     error-enumeration). A garment fails if structure/colour/VLM flag it.
  6. repair: a failing garment with a FitDiT category is re-rendered (FitDiT) and composited locally
     (its mask minus neighbours), then re-checked. Shoes/anything without a FitDiT category -> flag only.
  7. stop, write the manifest; list the accessory garments deferred to OmniTry.

Needs ComfyUI (:8000, QIE+FitDiT+GroundingDINO/SAM), the Leffa ATR parser, DINOv2-small, LM Studio
(Qwen3-VL @ :1234). All local.
"""
from __future__ import annotations

import base64
import json
import math
import re
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np

from system.board import build as build_board
from system.clients.comfyui import ComfyUIClient
from system.garment import GarmentSpec, classify
from system.gates import color as color_gate
from system.gates import structure as structure_gate
from system.gates import texture as texture_gate
from system.gates.identity import compare_faces
from system.segmentation.parsing import garment_masks
from system.workflows import fill_workflow, load_template

ROOT = Path(__file__).resolve().parents[1]
CANON_AREA = 1152 * 1536
VLM_URL = "http://localhost:1234/v1/chat/completions"
VLM_MODEL = "qwen3-vl-8b-instruct"

# Per-garment behaviour is derived by system.garment.classify (no per-outfit table here).


# ── helpers ───────────────────────────────────────────────────────────────
def _download(client, outputs, prefix, dst):
    for no in outputs.values():
        for im in no.get("images", []):
            if im.get("filename", "").startswith(prefix):
                dst.write_bytes(client.download(im["filename"], im.get("subfolder", ""), im.get("type", "output")))
                return dst
    raise RuntimeError(f"no output with prefix {prefix!r}")


def build_prompt(layout_text: str, holistic_labels: list[str], deferred_labels: tuple[str, ...] = ()) -> str:
    """A concrete instruction for THIS pass only — render exactly the holistic items, with just the layout
    lines that concern them. QIE does not need the system plan: lines mentioning a deferred accessory (and
    the build-order line that names them) are dropped, so QIE is not told to render belt/earrings/etc. it
    must not add yet."""
    stems = {w[:-1] if w.endswith("s") else w
             for lbl in deferred_labels for w in re.findall(r"[a-z]+", lbl.lower()) if len(w) >= 3}
    layering = "\n".join(ln for ln in layout_text.splitlines()
                         if not (stems and any(re.search(r"\b" + s, ln.lower()) for s in stems))).strip()
    items = ", ".join(holistic_labels)
    return (f"Keep this exact person (face, hair, skin tone, body proportions, pose, and background) "
            f"unchanged. Using only the reference board (image 2), dress them in exactly these items: {items}. "
            "Render only the items listed above and nothing else: no other garments or accessories. Take all "
            "colour and texture from the board.\n"
            "How these items are worn:\n" + layering)


def vlm_judge(out_img: Path, refs: list[tuple[str, Path]], holistic_types: list[str]) -> dict:
    def b64(p, mx=768):
        im = cv2.imread(str(p)); h, w = im.shape[:2]; s = min(1.0, mx / max(h, w))
        if s < 1.0:
            im = cv2.resize(im, (int(w * s), int(h * s)))
        return "data:image/png;base64," + base64.b64encode(cv2.imencode(".png", im)[1]).decode()
    types = ", ".join(holistic_types)
    prompt = (f"STRICT QA for a virtual try-on. Image 1 = generated result. The next images are the "
              f"reference garments, in order: {types}. The person should wear ONLY these; any other "
              "garment/accessory must be ABSENT. Look ONLY at what is actually in image 1. Reply strictly "
              'as JSON {"defects":[{"item":..,"defect":..,"severity":"low|med|high"}], '
              '"all_present":true/false, "extra_items":true/false}.')
    content = [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": b64(out_img)}}]
    for _, r in refs:
        content.append({"type": "image_url", "image_url": {"url": b64(r)}})
    body = {"model": VLM_MODEL, "messages": [{"role": "user", "content": content}], "temperature": 0.1, "max_tokens": 500}
    try:
        req = urllib.request.Request(VLM_URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        txt = json.loads(urllib.request.urlopen(req, timeout=300).read())["choices"][0]["message"]["content"]
        try:
            return {"ok": True, **json.loads(txt[txt.find("{"):txt.rfind("}") + 1])}
        except Exception:
            return {"ok": True, "raw": txt}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_garment(out_img: Path, gtype: str, ref_tile: Path, out_mask: np.ndarray) -> dict:
    if (out_mask > 127).sum() < 200:
        return {"verdict": "TOO_SMALL", "coverage_px": int((out_mask > 127).sum())}
    full = np.full(cv2.imread(str(ref_tile)).shape[:2], 255, np.uint8)
    colour = color_gate.compare_regions(str(out_img), out_mask, str(ref_tile), full)
    de = colour.get("delta_e_mean")
    colour_verdict = "INVALID" if de is None else ("PASS" if de <= 3 else "WARN" if de <= 5 else "FAIL")
    struct = structure_gate.structure_score(str(out_img), out_mask, str(ref_tile), full)
    tex = texture_gate.compare_texture(str(out_img), str(ref_tile), out_mask, None)
    fails = (struct["verdict"] == "STRUCTURE_OFF") or (colour_verdict == "FAIL")
    return {"verdict": "CHECK" if fails else "PASS", "structure": struct, "colour_verdict": colour_verdict,
            "dE": de, "texture_recorded": tex["texture_ratio"]}


def repair_fitdit(out_img: Path, spec: GarmentSpec, ref_tile: Path, client, outdir: Path) -> Path:
    """Re-render one body garment with FitDiT at canonical res and composite ONLY its region back."""
    key = re.sub(r"[^a-z0-9]+", "_", spec.label.lower()).strip("_") or "garment"
    img = cv2.imread(str(out_img)); h, w = img.shape[:2]; ar = w / h
    cw, ch = round(math.sqrt(CANON_AREA * ar) / 16) * 16, round(math.sqrt(CANON_AREA / ar) / 16) * 16
    base_hi = cv2.resize(img, (cw, ch), interpolation=cv2.INTER_LANCZOS4)
    base_hi_p = outdir / f"repair_{key}_base.png"; cv2.imwrite(str(base_hi_p), base_hi)
    base_ref, garm_ref = client.upload_image(base_hi_p), client.upload_image(ref_tile)
    fl = {"class_type": "FitDiTLoader", "inputs": {"device": "cuda", "with_fp16": False, "with_offload": True, "with_aggressive_offload": False}}
    mg = {"1": fl, "2": {"class_type": "LoadImage", "inputs": {"image": base_ref, "upload": "image"}},
          "3": {"class_type": "FitDiTMaskGenerator", "inputs": {"model": ["1", 0], "vton_image": ["2", 0], "category": spec.fitdit_category,
                "offset_top": 0, "offset_bottom": 0, "offset_left": 0, "offset_right": 0}},
          "4": {"class_type": "SaveImage", "inputs": {"images": ["3", 1], "filename_prefix": f"rp_{key}_m"}},
          "5": {"class_type": "SaveImage", "inputs": {"images": ["3", 2], "filename_prefix": f"rp_{key}_p"}}}
    mo = client.poll(client.submit(mg), timeout=900)
    mask = _download(client, mo, f"rp_{key}_m", outdir / f"repair_{key}_agn.png")
    pose = _download(client, mo, f"rp_{key}_p", outdir / f"repair_{key}_pose.png")
    ti = {"1": fl, "2": {"class_type": "LoadImage", "inputs": {"image": base_ref, "upload": "image"}},
          "3": {"class_type": "LoadImage", "inputs": {"image": garm_ref, "upload": "image"}},
          "4": {"class_type": "LoadImage", "inputs": {"image": client.upload_image(mask), "upload": "image"}},
          "5": {"class_type": "LoadImage", "inputs": {"image": client.upload_image(pose), "upload": "image"}},
          "6": {"class_type": "FitDiTTryOn", "inputs": {"model": ["1", 0], "vton_image": ["2", 0], "garm_image": ["3", 0],
                "mask": ["4", 0], "pose_image": ["5", 0], "n_steps": 20, "image_scale": 2.0, "seed": 42, "num_images": 1, "resolution": "1152x1536"}},
          "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": f"rp_{key}_t"}}}
    fit = _download(client, client.poll(client.submit(ti), timeout=900), f"rp_{key}_t", outdir / f"repair_{key}_fit.png")
    region_mask = garment_masks(str(fit), [spec.atr_region])[spec.atr_region]
    region_mask = cv2.resize(region_mask, (cw, ch), interpolation=cv2.INTER_NEAREST)
    fit_img = cv2.resize(cv2.imread(str(fit)), (cw, ch))
    alpha = cv2.GaussianBlur((region_mask > 127).astype(np.float32), (0, 0), 5.0)[..., None]
    out = (fit_img * alpha + base_hi * (1 - alpha)).clip(0, 255).astype(np.uint8)
    dst = outdir / f"repaired_{key}.png"; cv2.imwrite(str(dst), out); return dst


def run_pipeline(person: Path, layout_path: Path, garments: list[dict], outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    layout = Path(layout_path).read_text(encoding="utf-8")
    specs = [(classify(g["type"]), Path(g["image"])) for g in garments]
    holistic = [(s, img) for s, img in specs if s.holistic]
    accessory = [s.label for s, _ in specs if not s.holistic]
    holistic_labels = [s.label for s, _ in holistic]
    regions = {s.label: s.atr_region for s, _ in holistic if s.atr_region}

    print("[1-2] build board ...")
    client = ComfyUIClient()
    bd = build_board(holistic, client, outdir)
    client.free()
    (outdir / "board_report.json").write_text(json.dumps(bd["report"], indent=2) + "\n", encoding="utf-8")
    if bd["flags"]:
        print(f"[STOP] isolation guard flagged {bd['flags']} — review {outdir / 'isolate'} and board.png")
        manifest = {"stopped": "board_guard", "flags": bd["flags"], "deferred_to_omnitry": accessory,
                    "board": str(bd["board"].relative_to(ROOT)) if bd["board"] else None,
                    "report": bd["report"], "seconds": round(time.monotonic() - t0, 1)}
        (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
        return manifest
    board, mask_cells = bd["board"], bd["mask_cells"]

    print("[3] prompt + [4] QIE ...")
    prompt = build_prompt(layout, holistic_labels, tuple(accessory)); (outdir / "prompt.txt").write_text(prompt, encoding="utf-8")
    client = ComfyUIClient()
    wf = fill_workflow(load_template("qie2511_vton"), {
        "__PERSON_IMAGE__": client.upload_image(person), "__REF_IMAGE__": client.upload_image(board),
        "__POSITIVE_PROMPT__": prompt, "__NEGATIVE_PROMPT__": "", "__CFG__": 4.0, "__SAMPLER__": "euler",
        "__SCHEDULER__": "simple", "__SEED__": 42, "__STEPS__": 20, "__OUTPUT_PREFIX__": "pl_qie", "__DENOISE__": 1.0})
    image = _download(client, client.poll(client.submit(wf), timeout=600), "pl_qie", outdir / "qie.png")
    client.free()

    print("[5] checks ...")
    parsed = garment_masks(str(image), sorted(set(regions.values()))) if regions else {}
    identity = compare_faces(str(image), str(person))
    report = {"identity_cosine": identity.get("cosine")}
    for s, _ in holistic:
        if s.atr_region in parsed:
            report[s.label] = check_garment(image, s.label, mask_cells[s.label], parsed[s.atr_region])
        else:
            report[s.label] = {"verdict": "NO_PARSE_REGION"}
    report["vlm"] = vlm_judge(image, [(lbl, p) for lbl, p in mask_cells.items()], holistic_labels)

    print("[6] repair if needed ...")
    for s, _ in holistic:
        if report.get(s.label, {}).get("verdict") == "CHECK" and s.fitdit_category:
            print(f"    {s.label}: CHECK -> FitDiT repair")
            client = ComfyUIClient()
            image = repair_fitdit(image, s, mask_cells[s.label], client, outdir); client.free()
            parsed = garment_masks(str(image), sorted(set(regions.values())))
            report[f"{s.label}_after_repair"] = check_garment(image, s.label, mask_cells[s.label], parsed[s.atr_region])

    final = outdir / "ready_for_omnitry.png"; final.write_bytes(image.read_bytes())
    manifest = {"final": str(final.relative_to(ROOT)), "holistic": holistic_labels,
                "deferred_to_omnitry": accessory, "report": report, "seconds": round(time.monotonic() - t0, 1)}
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"[7] STOP — ready for OmniTry ({accessory}): {final.relative_to(ROOT)}  ({manifest['seconds']}s)")
    return manifest
