"""Drape synthesis — geometric level (see experiments/010.../DRAPE_SYNTHESIS.md).

Reusable foundation:
  - body_model(person)        : pose landmarks → anchor lines + body scale
  - garment_descriptor(crop)  : continuous silhouette (interior gap filled, slit kept as a
                                line) + proportions (length ratio, top/waist width)
  - skirt_agnostic_mask(...)   : place the garment on the body → agnostic mask whose HEM comes
                                from the garment's length ratio × body width (not the leg length),
                                continuous (no leg split), covering the lower body.

Geometric level fixes placement / length / shape; pixel fidelity stays the engine's job.
Deps: mediapipe==0.10.35 (+ system/gates/models/pose_landmarker_full.task), opencv, numpy.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
POSE_MODEL = ROOT / "system/gates/models/pose_landmarker_full.task"

# MediaPipe Pose landmark indices
_L_SH, _R_SH = 11, 12
_L_HIP, _R_HIP = 23, 24
_L_ANK, _R_ANK = 27, 28


def _foreground(garment_path: Path):
    """Return (BGR-on-white image, boolean foreground mask) for a garment crop."""
    raw = cv2.imread(str(garment_path), cv2.IMREAD_UNCHANGED)
    if raw is None:
        raise FileNotFoundError(garment_path)
    if raw.ndim == 3 and raw.shape[2] == 4:
        fg = raw[:, :, 3] > 10
        bgr = raw[:, :, :3]
        img = np.full_like(bgr, 255)
        img[fg] = bgr[fg]
    else:
        img = raw if raw.ndim == 3 else cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR)
        fg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) < 245
    return img, fg


def _fill_silhouette(img: np.ndarray, fg: np.ndarray) -> np.ndarray:
    """Close interior through-gaps with cloned fabric; keep a darkened slit line."""
    out = img.copy()
    h, w = fg.shape
    for y in range(h):
        xs = np.where(fg[y])[0]
        if len(xs) < 5:
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        gap = [x for x in range(x0, x1 + 1) if not fg[y, x]]
        if not gap:
            continue
        for x in gap:
            l = x
            while l >= x0 and not fg[y, l]:
                l -= 1
            r = x
            while r <= x1 and not fg[y, r]:
                r += 1
            cl = img[y, l] if l >= x0 else img[y, r]
            cr = img[y, r] if r <= x1 else img[y, l]
            out[y, x] = ((cl.astype(int) + cr.astype(int)) // 2).astype(np.uint8)
        xc = int(np.mean(gap))
        out[y, max(0, xc - 1):min(w, xc + 2)] = (out[y, xc].astype(int) * 0.55).astype(np.uint8)
    return out


def body_model(person_path) -> dict:
    """Pose-derived anchor lines + body scale (pixel coordinates of the person image)."""
    import mediapipe as mp
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision

    img = cv2.imread(str(person_path))
    if img is None:
        raise FileNotFoundError(person_path)
    h, w = img.shape[:2]
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    landmarker = vision.PoseLandmarker.create_from_options(
        vision.PoseLandmarkerOptions(
            base_options=mp_tasks.BaseOptions(model_asset_path=str(POSE_MODEL)),
            running_mode=vision.RunningMode.IMAGE, num_poses=1))
    lm = landmarker.detect(
        mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))).pose_landmarks[0]

    def px(i):
        return (lm[i].x * w, lm[i].y * h)

    lhip, rhip = px(_L_HIP), px(_R_HIP)
    lank, rank = px(_L_ANK), px(_R_ANK)
    lsh, rsh = px(_L_SH), px(_R_SH)
    return {
        "image_size": (w, h),
        "hip_y": (lhip[1] + rhip[1]) / 2.0,
        "hip_cx": (lhip[0] + rhip[0]) / 2.0,
        "hip_width": abs(lhip[0] - rhip[0]),
        "ankle_y": (lank[1] + rank[1]) / 2.0,
        "shoulder_y": (lsh[1] + rsh[1]) / 2.0,
        "shoulder_width": abs(lsh[0] - rsh[0]),
    }


def garment_descriptor(garment_path, continuous_out: Path | None = None) -> dict:
    """Continuous silhouette + proportions for a garment crop."""
    img, fg = _foreground(Path(garment_path))
    ys = np.where(fg.any(axis=1))[0]
    top, bottom = int(ys.min()), int(ys.max())
    height = bottom - top + 1
    band = fg[top:top + max(1, height // 10)]              # top 10% ~ waistband
    top_width = int(band.sum(axis=1).max()) if band.any() else int(fg.sum(axis=1).max())
    continuous = _fill_silhouette(img, fg)
    if continuous_out is not None:
        cv2.imwrite(str(continuous_out), continuous)
    return {
        "length_ratio": height / max(1, top_width),
        "top_width": top_width,
        "garment_height": height,
        "continuous_path": str(continuous_out) if continuous_out else None,
    }


def measure_on_model(model_photo, segment_prompt: str, client, out_dir=None,
                     anchor: str = "hip", end: str = "ankle") -> dict:
    """Measure an element's BODY-RELATIVE placement from its on-model photo.

    Pose (MediaPipe) + segmentation (GroundingDINO/SAM via ComfyUI) → scale-invariant fractions
    transferable to any target body. The universal placement primitive (DRAPE_SYNTHESIS.md);
    works for any element by choosing anchor/end (skirt: hip→ankle; top: shoulder→hip; …).

    Returns: length_fraction (hem along anchor→end span), top_offset_frac (where the element
    starts vs anchor), width_ratio (element width / body width at anchor).
    """
    import tempfile

    from .segmentation.grounded_sam import segment      # lazy: needs a live ComfyUI

    body = body_model(model_photo)
    out_dir = Path(out_dir) if out_dir else Path(tempfile.mkdtemp())
    mask_path = segment(model_photo, {"element": segment_prompt}, client, out_dir)["element"]
    m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    fg = m > 127
    ys = np.where(fg.any(axis=1))[0]
    if len(ys) == 0:
        raise RuntimeError(f"on-model segmentation found nothing for prompt {segment_prompt!r}")
    top_y, hem_y = int(ys.min()), int(ys.max())
    width = int(fg.sum(axis=1).max())
    a_y, e_y = body[f"{anchor}_y"], body[f"{end}_y"]
    span = max(1.0, e_y - a_y)
    return {
        "anchor": anchor, "end": end,
        "length_fraction": (hem_y - a_y) / span,
        "top_offset_frac": (top_y - a_y) / span,
        "width_ratio": width / max(1.0, body[f"{anchor}_width"]),
        "model_mask": str(mask_path),
    }


def agnostic_mask(auto_mask_path, body: dict, length_fraction: float, out_path: Path,
                  anchor: str = "hip", end: str = "ankle"):
    """Truncate the auto region at the HEM (from a body-relative fraction) + row-fill continuous.

    hem_y = anchor_y + length_fraction * (end_y - anchor_y)  — length transferred from the
    on-model measurement, scale-invariant. Returns (out_path, hem_y).
    """
    w, h = body["image_size"]
    m = cv2.imread(str(auto_mask_path), cv2.IMREAD_GRAYSCALE)
    if m is None:
        raise FileNotFoundError(auto_mask_path)
    if (m.shape[1], m.shape[0]) != (w, h):
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
    fg = m > 127

    a_y, e_y = body[f"{anchor}_y"], body[f"{end}_y"]
    hem_y = int(min(h - 1, a_y + length_fraction * (e_y - a_y)))
    fg[hem_y:] = False                                     # truncate below the measured hem

    out = np.zeros((h, w), np.uint8)
    for y in range(h):
        xs = np.where(fg[y])[0]
        if len(xs):
            out[y, int(xs.min()):int(xs.max()) + 1] = 255  # row-fill → continuous column
    cv2.imwrite(str(out_path), out)
    return out_path, hem_y
