"""Deterministic per-region color correction toward a reference garment.

Prevention by construction (METHODOLOGY §3.7): garment color is corrected toward the
reference instead of being trusted to the generator. Only the region's MEAN LAB is
shifted, bounded per channel; per-pixel deviation from the mean (shading/texture) is
left untouched, so the correction cannot flatten texture.

LAB here is real-range (L 0..100, a/b ~ -127..127) via OpenCV float conversion.

Dependencies: opencv-python, numpy.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def _load_bgr(image) -> np.ndarray:
    if isinstance(image, (str, Path)):
        img = cv2.imread(str(image), cv2.IMREAD_COLOR)
        if img is None:
            raise FileNotFoundError(f"Cannot read image: {image}")
        return img
    return np.asarray(image)


def _load_mask(mask) -> np.ndarray:
    if isinstance(mask, (str, Path)):
        m = cv2.imread(str(mask), cv2.IMREAD_GRAYSCALE)
        if m is None:
            raise FileNotFoundError(f"Cannot read mask: {mask}")
    else:
        m = np.asarray(mask)
    if m.ndim == 3:
        m = m[:, :, 0]
    return m > 127


def _to_lab(bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(bgr.astype(np.float32) / 255.0, cv2.COLOR_BGR2LAB)


def _to_bgr(lab: np.ndarray) -> np.ndarray:
    bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    return np.clip(bgr * 255.0, 0, 255).astype(np.uint8)


def correct_region(
    image,
    mask,
    ref_image,
    ref_mask,
    max_shift=(6.0, 6.0, 6.0),
) -> np.ndarray:
    """Shift the masked region's mean LAB toward the reference region's mean.

    The shift is one per-channel constant (clamped to ``max_shift``) added only
    inside the mask. Variance within the region is untouched → texture preserved.
    Returns a BGR uint8 image.
    """
    bgr = _load_bgr(image)
    lab = _to_lab(bgr)
    m = _load_mask(mask)
    ref_lab = _to_lab(_load_bgr(ref_image))
    rm = _load_mask(ref_mask)

    if not m.any():
        raise ValueError("Output region mask is empty; cannot correct.")
    if not rm.any():
        raise ValueError("Reference region mask is empty; cannot correct.")
    if m.shape != lab.shape[:2]:
        raise ValueError(f"Mask shape {m.shape} != image shape {lab.shape[:2]}")

    out_mean = lab[m].mean(axis=0)
    ref_mean = ref_lab[rm].mean(axis=0)
    cap = np.asarray(max_shift, dtype=np.float32)
    shift = np.clip(ref_mean - out_mean, -cap, cap).astype(np.float32)

    lab[m] += shift
    return _to_bgr(lab)


def correct(
    image,
    regions: dict,
    references: dict,
    max_shift=(6.0, 6.0, 6.0),
) -> np.ndarray:
    """Apply ``correct_region`` for every label present in both dicts.

    regions:    {label: output_mask}
    references: {label: (ref_image, ref_mask)}
    Regions are corrected in turn; disjoint masks make order irrelevant.
    """
    result = _load_bgr(image)
    for label, mask in regions.items():
        if label not in references:
            continue
        ref_image, ref_mask = references[label]
        result = correct_region(result, mask, ref_image, ref_mask, max_shift=max_shift)
    return result
