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


def skirt_agnostic_mask(auto_mask_path, body: dict, descriptor: dict, out_path: Path):
    """Truncate the auto lower-body mask at the garment-derived HEM, then row-fill continuous.

    hem_y = hip_y + length_ratio * hip_width  (skirt length from the garment's own proportions,
    scaled by the body's hip width — NOT the leg length). Returns (out_path, hem_y).
    """
    w, h = body["image_size"]
    m = cv2.imread(str(auto_mask_path), cv2.IMREAD_GRAYSCALE)
    if m is None:
        raise FileNotFoundError(auto_mask_path)
    if (m.shape[1], m.shape[0]) != (w, h):
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
    fg = m > 127

    hem_y = int(min(h - 1, body["hip_y"] + descriptor["length_ratio"] * body["hip_width"]))
    fg[hem_y:] = False                                     # truncate below the garment hem

    out = np.zeros((h, w), np.uint8)
    for y in range(h):
        xs = np.where(fg[y])[0]
        if len(xs):
            out[y, int(xs.min()):int(xs.max()) + 1] = 255  # row-fill → continuous skirt column
    cv2.imwrite(str(out_path), out)
    return out_path, hem_y
