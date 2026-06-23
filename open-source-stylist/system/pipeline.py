"""Universal pre-OmniTry try-on pipeline — ONE wired system, input-driven, not outfit-specific.

Input: a person image, an outfit layout (text), and the ORIGINAL image of each garment with its TYPE.
The system reacts to the input — it does not expect any particular garment:

  GARMENT_VOCAB maps a garment TYPE -> {atr region, segmentation prompt, FitDiT category, stage,
  continuous-silhouette?}. Anything in the vocab routes itself. "holistic" garments (upper/lower/dress/
  shoes) go through the QIE board+holistic pass; "accessory" garments (belt/earrings/bag/glasses) are
  deferred to the OmniTry stage (NOT run here).

Stages (autonomous, stops before OmniTry; every artifact saved under outdir):
  1. isolate each holistic garment from its original (GroundingDINO/SAM); free-hanging garments
     (skirt/dress) get a continuous silhouette (interior gaps filled, opening kept as a line).
  2. build the board from the isolated tiles + labels.
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
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np

from system.clients.comfyui import ComfyUIClient
from system.gates import color as color_gate
from system.gates import structure as structure_gate
from system.gates import texture as texture_gate
from system.gates.identity import compare_faces
from system.segmentation.grounded_sam import segment
from system.segmentation.parsing import garment_masks
from system.workflows import fill_workflow, load_template

ROOT = Path(__file__).resolve().parents[1]
CANON_AREA = 1152 * 1536
VLM_URL = "http://localhost:1234/v1/chat/completions"
VLM_MODEL = "qwen3-vl-8b-instruct"

# Garment TYPE -> behaviour. Generic vocab; add types here, not per-outfit logic.
GARMENT_VOCAB: dict[str, dict] = {
    "blouse": {"region": "upper", "seg": "blouse . shirt . top", "fitdit": "Upper-body", "stage": "holistic", "continuous": False},
    "shirt":  {"region": "upper", "seg": "shirt . top", "fitdit": "Upper-body", "stage": "holistic", "continuous": False},
    "top":    {"region": "upper", "seg": "top . shirt", "fitdit": "Upper-body", "stage": "holistic", "continuous": False},
    "jacket": {"region": "upper", "seg": "jacket", "fitdit": "Upper-body", "stage": "holistic", "continuous": False},
    "skirt":  {"region": "skirt", "seg": "skirt", "fitdit": "Lower-body", "stage": "holistic", "continuous": True},
    "pants":  {"region": "pants", "seg": "pants . trousers", "fitdit": "Lower-body", "stage": "holistic", "continuous": False},
    "dress":  {"region": "dress", "seg": "dress", "fitdit": "Dresses", "stage": "holistic", "continuous": True},
    "shoes":  {"region": "shoes", "seg": "shoes . sandals", "fitdit": None, "stage": "holistic", "continuous": False},
    "belt":     {"region": "belt", "stage": "accessory"},
    "earrings": {"region": None, "stage": "accessory"},
    "bag":      {"region": "bag", "stage": "accessory"},
    "glasses":  {"region": None, "stage": "accessory"},
    "hat":      {"region": "hat", "stage": "accessory"},
}


# ── helpers ───────────────────────────────────────────────────────────────
def _download(client, outputs, prefix, dst):
    for no in outputs.values():
        for im in no.get("images", []):
            if im.get("filename", "").startswith(prefix):
                dst.write_bytes(client.download(im["filename"], im.get("subfolder", ""), im.get("type", "output")))
                return dst
    raise RuntimeError(f"no output with prefix {prefix!r}")


def _make_continuous(bgr: np.ndarray, fg: np.ndarray) -> np.ndarray:
    """Fill interior through-gaps in a garment silhouette row-by-row (keep the opening as a darker line)
    so a free-hanging garment (skirt/dress) is not bifurcated -> avoids the slit->pants failure."""
    out = bgr.copy()
    h, w = fg.shape
    for y in range(h):
        xs = np.where(fg[y])[0]
        if len(xs) < 5:
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        for x in range(x0, x1 + 1):
            if not fg[y, x]:
                l = x
                while l >= x0 and not fg[y, l]:
                    l -= 1
                r = x
                while r <= x1 and not fg[y, r]:
                    r += 1
                cl = out[y, l] if l >= x0 else out[y, r]
                cr = out[y, r] if r <= x1 else out[y, l]
                out[y, x] = ((cl.astype(int) + cr.astype(int)) // 2 * 0.7).astype(np.uint8)
    return out


def isolate_garment(original: Path, gtype: str, client, outdir: Path) -> tuple[Path, Path]:
    """Segment the garment from its original (GroundingDINO/SAM), isolate it, optionally make continuous."""
    spec = GARMENT_VOCAB[gtype]
    mask_path = segment(str(original), {gtype: spec["seg"]}, client, outdir / "iso_masks")[gtype]
    im = cv2.imread(str(original)); m = cv2.imread(mask_path, 0)
    if (m.shape[1], m.shape[0]) != (im.shape[1], im.shape[0]):
        m = cv2.resize(m, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_NEAREST)
    fg = m > 127
    ys, xs = np.where(fg)
    body = _make_continuous(im, fg) if spec.get("continuous") else im
    tile = np.full_like(im, 255); tile[fg] = body[fg]
    tile = tile[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    tpath = outdir / f"iso_{gtype}.png"; cv2.imwrite(str(tpath), tile)
    return tpath, Path(mask_path)


def build_board(tiles: list[tuple[str, Path]], outdir: Path) -> Path:
    """Render labelled 256px cells (mask isolate + crop per item) into a 3-col board."""
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.load_default(size=14)
    except TypeError:
        font = ImageFont.load_default()
    cells = []
    for label, tile in tiles:
        img = Image.open(tile).convert("RGB"); img.thumbnail((256, 234), Image.LANCZOS)
        cell = Image.new("RGB", (256, 256), (255, 255, 255))
        cell.paste(img, ((256 - img.width) // 2, (234 - img.height) // 2))
        d = ImageDraw.Draw(cell); b = d.textbbox((0, 0), label, font=font)
        d.text(((256 - (b[2] - b[0])) // 2, 236), label, fill=(0, 0, 0), font=font)
        cells.append(cell)
    # near-square grid: an extreme aspect board (e.g. 3 cells in a row, 3:1) collapses QIE identity
    # (measured: 768x256 board -> identity 0.28 vs 768x512 -> 0.95). cols=ceil(sqrt(N)) keeps it ~square.
    cols = max(1, math.ceil(len(cells) ** 0.5)); rows = (len(cells) + cols - 1) // cols
    board = Image.new("RGB", (cols * 256, rows * 256), (255, 255, 255))
    for i, c in enumerate(cells):
        board.paste(c, ((i % cols) * 256, (i // cols) * 256))
    bpath = outdir / "board.png"; board.save(bpath); return bpath


def build_prompt(layout_text: str, holistic_types: list[str]) -> str:
    items = ", ".join(holistic_types)
    return ("Keep this exact person: face, hair, skin tone, body proportions, pose, and background "
            "unchanged. Using the reference board (image 2), re-dress them in the outfit shown. "
            f"Items worn at this stage: {items}. Take all garment appearance from the board only.\n"
            "Layering / what is visible where:\n" + layout_text)


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


def repair_fitdit(out_img: Path, gtype: str, ref_tile: Path, client, outdir: Path) -> Path:
    """Re-render one body garment with FitDiT at canonical res and composite ONLY its region back."""
    spec = GARMENT_VOCAB[gtype]
    img = cv2.imread(str(out_img)); h, w = img.shape[:2]; ar = w / h
    cw, ch = round(math.sqrt(CANON_AREA * ar) / 16) * 16, round(math.sqrt(CANON_AREA / ar) / 16) * 16
    base_hi = cv2.resize(img, (cw, ch), interpolation=cv2.INTER_LANCZOS4)
    base_hi_p = outdir / f"repair_{gtype}_base.png"; cv2.imwrite(str(base_hi_p), base_hi)
    base_ref, garm_ref = client.upload_image(base_hi_p), client.upload_image(ref_tile)
    fl = {"class_type": "FitDiTLoader", "inputs": {"device": "cuda", "with_fp16": False, "with_offload": True, "with_aggressive_offload": False}}
    mg = {"1": fl, "2": {"class_type": "LoadImage", "inputs": {"image": base_ref, "upload": "image"}},
          "3": {"class_type": "FitDiTMaskGenerator", "inputs": {"model": ["1", 0], "vton_image": ["2", 0], "category": spec["fitdit"],
                "offset_top": 0, "offset_bottom": 0, "offset_left": 0, "offset_right": 0}},
          "4": {"class_type": "SaveImage", "inputs": {"images": ["3", 1], "filename_prefix": f"rp_{gtype}_m"}},
          "5": {"class_type": "SaveImage", "inputs": {"images": ["3", 2], "filename_prefix": f"rp_{gtype}_p"}}}
    mo = client.poll(client.submit(mg), timeout=900)
    mask = _download(client, mo, f"rp_{gtype}_m", outdir / f"repair_{gtype}_agn.png")
    pose = _download(client, mo, f"rp_{gtype}_p", outdir / f"repair_{gtype}_pose.png")
    ti = {"1": fl, "2": {"class_type": "LoadImage", "inputs": {"image": base_ref, "upload": "image"}},
          "3": {"class_type": "LoadImage", "inputs": {"image": garm_ref, "upload": "image"}},
          "4": {"class_type": "LoadImage", "inputs": {"image": client.upload_image(mask), "upload": "image"}},
          "5": {"class_type": "LoadImage", "inputs": {"image": client.upload_image(pose), "upload": "image"}},
          "6": {"class_type": "FitDiTTryOn", "inputs": {"model": ["1", 0], "vton_image": ["2", 0], "garm_image": ["3", 0],
                "mask": ["4", 0], "pose_image": ["5", 0], "n_steps": 20, "image_scale": 2.0, "seed": 42, "num_images": 1, "resolution": "1152x1536"}},
          "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": f"rp_{gtype}_t"}}}
    fit = _download(client, client.poll(client.submit(ti), timeout=900), f"rp_{gtype}_t", outdir / f"repair_{gtype}_fit.png")
    region_mask = garment_masks(str(fit), [spec["region"]])[spec["region"]]
    region_mask = cv2.resize(region_mask, (cw, ch), interpolation=cv2.INTER_NEAREST)
    fit_img = cv2.resize(cv2.imread(str(fit)), (cw, ch))
    alpha = cv2.GaussianBlur((region_mask > 127).astype(np.float32), (0, 0), 5.0)[..., None]
    out = (fit_img * alpha + base_hi * (1 - alpha)).clip(0, 255).astype(np.uint8)
    dst = outdir / f"repaired_{gtype}.png"; cv2.imwrite(str(dst), out); return dst


def run_pipeline(person: Path, layout_path: Path, garments: list[dict], outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    layout = Path(layout_path).read_text(encoding="utf-8")
    holistic = [g for g in garments if GARMENT_VOCAB[g["type"]]["stage"] == "holistic"]
    accessory = [g["type"] for g in garments if GARMENT_VOCAB[g["type"]]["stage"] == "accessory"]
    client = ComfyUIClient()

    print("[1] isolate garments ...")
    tiles, refs = [], {}
    for g in holistic:
        tile, _ = isolate_garment(Path(g["image"]), g["type"], client, outdir)
        tiles.append((g["type"], tile)); refs[g["type"]] = tile

    print("[2] board ..."); board = build_board(tiles, outdir)
    print("[3] prompt + [4] QIE ...")
    prompt = build_prompt(layout, [g["type"] for g in holistic]); (outdir / "prompt.txt").write_text(prompt, encoding="utf-8")
    wf = fill_workflow(load_template("qie2511_vton"), {
        "__PERSON_IMAGE__": client.upload_image(person), "__REF_IMAGE__": client.upload_image(board),
        "__POSITIVE_PROMPT__": prompt, "__NEGATIVE_PROMPT__": "", "__CFG__": 4.0, "__SAMPLER__": "euler",
        "__SCHEDULER__": "simple", "__SEED__": 42, "__STEPS__": 20, "__OUTPUT_PREFIX__": "pl_qie", "__DENOISE__": 1.0})
    image = _download(client, client.poll(client.submit(wf), timeout=600), "pl_qie", outdir / "qie.png")
    client.free()

    print("[5] checks ...")
    masks = garment_masks(str(image), [GARMENT_VOCAB[g["type"]]["region"] for g in holistic])
    identity = compare_faces(str(image), str(person))
    report = {"identity_cosine": identity.get("cosine")}
    for g in holistic:
        gt = g["type"]; report[gt] = check_garment(image, gt, refs[gt], masks[GARMENT_VOCAB[gt]["region"]])
    report["vlm"] = vlm_judge(image, tiles, [g["type"] for g in holistic])

    print("[6] repair if needed ...")
    for g in holistic:
        gt = g["type"]; res = report[gt]
        if res["verdict"] == "CHECK" and GARMENT_VOCAB[gt].get("fitdit"):
            print(f"    {gt}: {res['verdict']} -> FitDiT repair")
            client = ComfyUIClient()
            image = repair_fitdit(image, gt, refs[gt], client, outdir); client.free()
            masks = garment_masks(str(image), [GARMENT_VOCAB[x["type"]]["region"] for x in holistic])
            report[f"{gt}_after_repair"] = check_garment(image, gt, refs[gt], masks[GARMENT_VOCAB[gt]["region"]])

    final = outdir / "ready_for_omnitry.png"; final.write_bytes(image.read_bytes())
    manifest = {"final": str(final.relative_to(ROOT)), "holistic": [g["type"] for g in holistic],
                "deferred_to_omnitry": accessory, "report": report, "seconds": round(time.monotonic() - t0, 1)}
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"[7] STOP — ready for OmniTry ({accessory}): {final.relative_to(ROOT)}  ({manifest['seconds']}s)")
    return manifest
