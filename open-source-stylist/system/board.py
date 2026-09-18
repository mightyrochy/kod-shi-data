"""The reference-board builder — turns input garments into the combined (mask + crop) board QIE reads.

Quality lives HERE, in the builder; the check at the end is only a thin guard against gross failures
leaking downstream. General by construction — no garment is special-cased. For each garment it:

  1. ISOLATES it, choosing the method from the image itself (not from the garment type):
     try human-parsing (ATR) first — on an on-model photo it excludes the person and keeps fine detail
     (buttons, slit); if that region comes back empty or shattered (a product / close-up shot, or a label
     outside the parser's ontology), fall back to open-vocabulary GroundingDINO + SAM.
  2. CLEANS the mask — drops speckle, keeps the significant part(s).
  3. Makes a single-piece garment CONTINUOUS — fills interior through-gaps so a slit/opening stays a line
     rather than splitting the silhouette into two shapes a try-on model would render as legs. Inherently
     multi-part items (a pair of shoes) are left alone — decided from the mask's geometry, not the type.
  4. Emits TWO cells: the garment isolated on white (identity) and a padded crop of the original
     (context / layering logic). The combined board reads better than either half alone.
  5. GUARDS each isolate cell: non-empty and not shattered. A garment that fails stops the build for owner
     review instead of leaking a broken tile into generation.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from system.garment import GarmentSpec
from system.segmentation.grounded_sam import segment
from system.segmentation.parsing import garment_mask

# gross-error thresholds — coarse bounds, not tuning knobs: an isolate this far gone is plainly broken.
_MIN_AREA_FRAC = 0.004   # < 0.4% of the image -> empty / failed isolation
_KEEP_FRAC = 0.06        # drop components smaller than 6% of the largest (speckle / confetti)
_MIN_PX = 300            # ...but always keep components of at least this many pixels
_DOMINANT_FRAC = 0.55    # a single-piece garment's main blob must hold most of the foreground
_MAX_PARTS = 4           # a clean isolate is one blob or a few (a pair); dozens of parts = shattered
_ATR_DOMINANCE = 0.18    # accept human-parsing only if the garment dominates the parse; below this the
                         # parser mis-read a close-up (target is a sliver of a garbage body parse) -> SAM
_CROP_PAD = 0.12         # context padding around the garment for the crop cell
_CELL = 256              # board cell size (px)


# ── mask analysis ─────────────────────────────────────────────────────────
def _analyze(mask: np.ndarray) -> tuple[np.ndarray, list, dict]:
    """Clean speckle and judge a mask. Returns (clean_mask, parts, quality).

    `parts` are the kept components' stats rows (x, y, w, h, area), largest first.
    `quality.ok` = the single source of truth used both to choose ATR-vs-SAM and as the final guard.
    """
    fg = (mask > 127).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
    comps = [(i, int(stats[i, cv2.CC_STAT_AREA])) for i in range(1, n)]
    if not comps:
        return np.zeros_like(mask), [], {"ok": False, "reason": "empty", "area_frac": 0.0,
                                         "parts": 0, "largest_frac": 0.0, "single_piece": False}
    largest = max(a for _, a in comps)
    keep = [i for i, a in comps if a >= max(_MIN_PX, _KEEP_FRAC * largest)]
    if not keep:  # only speckle survived -> a failed / empty isolation (e.g. ATR fragmenting a close-up)
        return np.zeros_like(mask), [], {"ok": False, "reason": "too small / empty", "area_frac": 0.0,
                                         "parts": 0, "largest_frac": 0.0, "single_piece": False}
    clean = np.where(np.isin(labels, keep), 255, 0).astype(np.uint8)
    parts = sorted((stats[i] for i in keep), key=lambda s: -int(s[cv2.CC_STAT_AREA]))
    total = sum(int(s[cv2.CC_STAT_AREA]) for s in parts)
    area_frac = total / mask.size
    largest_frac = int(parts[0][cv2.CC_STAT_AREA]) / total
    single = len(parts) == 1
    ok = area_frac >= _MIN_AREA_FRAC and (
        (single and largest_frac >= _DOMINANT_FRAC) or (not single and len(parts) <= _MAX_PARTS))
    if area_frac < _MIN_AREA_FRAC:
        reason = "too small / empty"
    elif not ok:
        reason = "shattered (no dominant part)"
    else:
        reason = "ok"
    return clean, parts, {"ok": ok, "reason": reason, "area_frac": round(area_frac, 4),
                          "parts": len(parts), "largest_frac": round(largest_frac, 3),
                          "single_piece": single}


def _make_continuous(bgr: np.ndarray, fg: np.ndarray) -> np.ndarray:
    """Fill interior through-gaps of a silhouette row-by-row, keeping the opening as a darker line, so a
    free-hanging single-piece garment (skirt/dress) is not bifurcated -> avoids the slit->legs failure."""
    out = bgr.copy()
    h, w = fg.shape
    for y in range(h):
        xs = np.where(fg[y])[0]
        if len(xs) < 5:
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        for x in range(x0, x1 + 1):
            if not fg[y, x]:
                left = x
                while left >= x0 and not fg[y, left]:
                    left -= 1
                right = x
                while right <= x1 and not fg[y, right]:
                    right += 1
                cl = out[y, left] if left >= x0 else out[y, right]
                cr = out[y, right] if right <= x1 else out[y, left]
                out[y, x] = ((cl.astype(int) + cr.astype(int)) // 2 * 0.7).astype(np.uint8)
    return out


def _bbox_union(parts: list) -> tuple[int, int, int, int]:
    x0 = min(int(s[cv2.CC_STAT_LEFT]) for s in parts)
    y0 = min(int(s[cv2.CC_STAT_TOP]) for s in parts)
    x1 = max(int(s[cv2.CC_STAT_LEFT] + s[cv2.CC_STAT_WIDTH]) for s in parts)
    y1 = max(int(s[cv2.CC_STAT_TOP] + s[cv2.CC_STAT_HEIGHT]) for s in parts)
    return x0, y0, x1, y1


def _pad_crop(im: np.ndarray, box: tuple[int, int, int, int], pad: float) -> np.ndarray:
    x0, y0, x1, y1 = box
    h, w = im.shape[:2]
    px, py = int((x1 - x0) * pad), int((y1 - y0) * pad)
    return im[max(0, y0 - py):min(h, y1 + py), max(0, x0 - px):min(w, x1 + px)]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "garment"


def _read_mask(path, ref_shape) -> np.ndarray | None:
    m = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if m is None:
        return None
    if (m.shape[1], m.shape[0]) != (ref_shape[1], ref_shape[0]):
        m = cv2.resize(m, (ref_shape[1], ref_shape[0]), interpolation=cv2.INTER_NEAREST)
    return m


# ── isolation ──────────────────────────────────────────────────────────────
def isolate(spec: GarmentSpec, original: Path, client, outdir: Path) -> dict:
    """Isolate one garment from its original image, returning the mask cell, crop cell, and a guard verdict."""
    outdir.mkdir(parents=True, exist_ok=True)
    im = cv2.imread(str(original))
    if im is None:
        raise FileNotFoundError(original)
    slug = _slug(spec.label)

    # 1. try human-parsing first; accept it only if the garment DOMINATES the parse (a real on-model /
    #    product shot) and the region is clean. A low-dominance parse = ATR mis-read a close-up -> SAM.
    method, raw = None, None
    if spec.atr_region:
        try:
            atr, dom = garment_mask(str(original), spec.atr_region, out_size=(im.shape[1], im.shape[0]))
            if dom >= _ATR_DOMINANCE and _analyze(atr)[2]["ok"]:
                raw, method = atr, "atr"
            else:
                print(f"    [{spec.label}] ATR weak (dominance {dom}) -> GroundingDINO+SAM")
        except Exception as exc:  # parser unavailable / off-photo -> just fall through to open-vocabulary
            print(f"    [{spec.label}] ATR unavailable ({exc}); using GroundingDINO+SAM")
    # 2. open-vocabulary fallback (product / close-up shots, or labels ATR does not model)
    if raw is None:
        seg_path = segment(str(original), {slug: spec.seg_term}, client, outdir / "seg")[slug]
        raw, method = _read_mask(seg_path, im.shape), "grounded_sam"

    mask, parts, quality = _analyze(raw) if raw is not None else (None, [], {"ok": False, "reason": "no mask"})
    result = {"label": spec.label, "method": method, "quality": quality}
    if not parts:
        result["ok"] = False
        return result

    fg = mask > 127
    body = _make_continuous(im, fg) if quality["single_piece"] else im

    # 3a. mask cell — garment isolated on white, tight to its bounding box
    box = _bbox_union(parts)
    iso = np.full_like(im, 255)
    iso[fg] = body[fg]
    mask_cell = iso[box[1]:box[3], box[0]:box[2]]
    mask_cell_p = outdir / f"{slug}_mask.png"
    cv2.imwrite(str(mask_cell_p), mask_cell)

    # 3b. crop cell — the garment in context, a padded crop of the original
    crop_cell_p = outdir / f"{slug}_crop.png"
    cv2.imwrite(str(crop_cell_p), _pad_crop(im, box, _CROP_PAD))

    cv2.imwrite(str(outdir / f"{slug}_mask_raw.png"), mask)  # kept for owner review when guard trips
    result.update({"ok": quality["ok"], "mask_cell": mask_cell_p, "crop_cell": crop_cell_p, "mask": mask})
    return result


# ── board assembly ───────────────────────────────────────────────────────
def _render(cells: list[tuple[str, Path]], dst: Path) -> Path:
    try:
        font = ImageFont.load_default(size=14)
    except TypeError:
        font = ImageFont.load_default()
    imgs = []
    for label, path in cells:
        img = Image.open(path).convert("RGB")
        img.thumbnail((_CELL, _CELL - 22), Image.LANCZOS)
        cell = Image.new("RGB", (_CELL, _CELL), (255, 255, 255))
        cell.paste(img, ((_CELL - img.width) // 2, (_CELL - 22 - img.height) // 2))
        d = ImageDraw.Draw(cell)
        b = d.textbbox((0, 0), label, font=font)
        d.text(((_CELL - (b[2] - b[0])) // 2, _CELL - 20), label, fill=(0, 0, 0), font=font)
        imgs.append(cell)
    # near-square grid: an extreme aspect ratio collapses QIE identity (measured: 3:1 board -> 0.40 vs
    # ~square -> 0.95), so keep cols = ceil(sqrt(N)).
    cols = max(1, math.ceil(len(imgs) ** 0.5))
    rows = math.ceil(len(imgs) / cols)
    board = Image.new("RGB", (cols * _CELL, rows * _CELL), (255, 255, 255))
    for i, cell in enumerate(imgs):
        board.paste(cell, ((i % cols) * _CELL, (i // cols) * _CELL))
    board.save(dst)
    return dst


def build(garments: list[tuple[GarmentSpec, Path]], client, outdir: Path) -> dict:
    """Isolate every garment and assemble the combined board.

    Returns {board, cells, masks, flags, report}. `flags` lists garments whose isolate failed the guard —
    a non-empty `flags` means the caller should STOP and show those tiles to the owner, not proceed.
    """
    iso_dir = outdir / "isolate"
    cells: list[tuple[str, Path]] = []
    masks: dict[str, np.ndarray] = {}        # label -> output-space mask of the isolated garment
    mask_cells: dict[str, Path] = {}         # label -> isolated-garment tile (FitDiT garment ref)
    report, flags = {}, []
    for spec, original in garments:
        r = isolate(spec, Path(original), client, iso_dir)
        report[spec.label] = {"method": r["method"], **r["quality"]}
        if not r.get("ok"):
            flags.append(spec.label)
            # still surface whatever was produced so the owner can see the failure
            if r.get("mask_cell"):
                cells += [(f"{spec.label} mask (FLAGGED)", r["mask_cell"]), (f"{spec.label} crop", r["crop_cell"])]
            continue
        cells += [(f"{spec.label} mask", r["mask_cell"]), (f"{spec.label} crop", r["crop_cell"])]
        masks[spec.label] = r["mask"]
        mask_cells[spec.label] = r["mask_cell"]

    board = _render(cells, outdir / "board.png") if cells else None
    return {"board": board, "cells": cells, "masks": masks, "mask_cells": mask_cells,
            "flags": flags, "report": report}
