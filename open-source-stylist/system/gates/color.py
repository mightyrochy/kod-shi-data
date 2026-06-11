"""Color gate — per-region ΔE CIE76 (CIELAB).

Compares the average color of a masked region in two images.
CIE76 = Euclidean distance in LAB. Fast, sufficient for separability;
upgrade to CIEDE2000 via scikit-image if E-002 shows CIE76 is not
monotonically separable on our image pairs.

Dependencies: opencv-python, numpy (both already installed).
"""

from pathlib import Path

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_lab(image) -> np.ndarray:
    """Load image (path or BGR ndarray) and return float32 LAB in standard ranges.

    OpenCV LAB encoding: L in [0,255], a/b in [0,255] centred at 128.
    We remap to: L in [0,100], a/b in [-128, 127].
    """
    if isinstance(image, (str, Path)):
        img = cv2.imread(str(image))
        if img is None:
            raise FileNotFoundError(f"Cannot read image: {image}")
    else:
        img = np.asarray(image)
    if img.dtype != np.uint8:
        img = img.clip(0, 255).astype(np.uint8)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[:, :, 0] *= 100.0 / 255.0
    lab[:, :, 1] -= 128.0
    lab[:, :, 2] -= 128.0
    return lab


def _load_mask(mask) -> np.ndarray:
    """Load mask (path or array) as boolean H×W."""
    if isinstance(mask, (str, Path)):
        m = cv2.imread(str(mask), cv2.IMREAD_GRAYSCALE)
        if m is None:
            raise FileNotFoundError(f"Cannot read mask: {mask}")
    else:
        m = np.asarray(mask)
    if m.ndim == 3:
        m = m[:, :, 0]
    return m > 127


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compare_regions(image_a, mask_a, image_b, mask_b=None) -> dict:
    """Compute CIE76 ΔE between two masked image regions.

    image_a / mask_a — generated output image + garment region mask
    image_b / mask_b — reference image + its mask (None = whole image)

    Returns:
        delta_e_mean   ΔE between the two region mean LAB colors
        delta_e_p90    90th-percentile of per-pixel ΔE(pixel_a, mean_b)
        n_pixels_a     masked pixel count in region A
        n_pixels_b     masked pixel count in region B
    """
    lab_a = _load_lab(image_a)
    lab_b = _load_lab(image_b)
    ma = _load_mask(mask_a)
    mb = _load_mask(mask_b) if mask_b is not None else np.ones(lab_b.shape[:2], dtype=bool)

    pixels_a = lab_a[ma]   # (N, 3)
    pixels_b = lab_b[mb]   # (M, 3)

    if len(pixels_a) == 0 or len(pixels_b) == 0:
        return {
            "delta_e_mean": None,
            "delta_e_p90": None,
            "n_pixels_a": int(len(pixels_a)),
            "n_pixels_b": int(len(pixels_b)),
        }

    mean_a = pixels_a.mean(axis=0)
    mean_b = pixels_b.mean(axis=0)

    delta_e_mean = float(np.sqrt(np.sum((mean_a - mean_b) ** 2)))

    # distribution: per-pixel distance from each pixel in A to mean_B
    per_pixel = np.sqrt(((pixels_a - mean_b) ** 2).sum(axis=1))
    delta_e_p90 = float(np.percentile(per_pixel, 90))

    return {
        "delta_e_mean": round(delta_e_mean, 2),
        "delta_e_p90": round(delta_e_p90, 2),
        "n_pixels_a": int(len(pixels_a)),
        "n_pixels_b": int(len(pixels_b)),
    }
