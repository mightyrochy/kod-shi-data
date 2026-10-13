"""Composite the original background back outside the person silhouette.

Prevention by construction: pixels the request does not change (background) are
taken from the original photo, not trusted to the generator.

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


def restore_background(generated, original, person_mask) -> np.ndarray:
    """Return ``generated`` inside the person mask, ``original`` outside it."""
    gen = _load_bgr(generated)
    orig = _load_bgr(original)
    m = _load_mask(person_mask)
    if gen.shape != orig.shape:
        raise ValueError(f"Shape mismatch: generated {gen.shape} != original {orig.shape}")
    if m.shape != gen.shape[:2]:
        raise ValueError(f"Mask shape {m.shape} != image shape {gen.shape[:2]}")
    out = gen.copy()
    out[~m] = orig[~m]
    return out
