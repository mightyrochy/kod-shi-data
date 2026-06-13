"""Color gate -- per-region CIEDE2000 with lightness normalization.

Compares the average color of a masked region in two images.

Metric: CIEDE2000 (skimage.color.deltaE_ciede2000) -- perceptually uniform,
handles dark/desaturated colors correctly where CIE76 compressed differences.

Lightness normalization: before comparison, the mean L* of region A is shifted
to match region B. This removes lighting/shade/drape offset (photo-pair noise)
while preserving hue and chroma differences. Can be disabled via normalize_l=False.

SCOPE (what this gate does and does not judge): with normalize_l=True (the E-005
default), a *uniform* lightness offset is removed by construction — so a garment
rendered too dark or too washed-out but with the correct hue/chroma will still
PASS. The gate measures HUE and CHROMA fidelity, not absolute lightness. This is
deliberate (lighting/drape vary between a flat product photo and a worn garment),
but it means "color correct per this gate" ≠ "looks identical". Perceived
flatness/washed-out texture (owner's dominant complaint at ΔE 3–5, V-COLOR-002)
lives partly in lightness and texture, which this gate does not cover — that is
the advisory texture indicator's job in the bench-off (design §8).

Dependencies: opencv-python, numpy, scikit-image.
"""

from pathlib import Path

import cv2
import numpy as np
from skimage.color import deltaE_ciede2000


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
    """Load mask (path or array) as boolean H x W."""
    if isinstance(mask, (str, Path)):
        m = cv2.imread(str(mask), cv2.IMREAD_GRAYSCALE)
        if m is None:
            raise FileNotFoundError(f"Cannot read mask: {mask}")
    else:
        m = np.asarray(mask)
    if m.ndim == 3:
        m = m[:, :, 0]
    if m.dtype == bool:
        return m
    return m > 127


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compare_regions(image_a, mask_a, image_b, mask_b=None, normalize_l=True) -> dict:
    """Compute CIEDE2000 between two masked image regions.

    image_a / mask_a -- generated output image + garment region mask
    image_b / mask_b -- reference image + its mask (None = whole image)
    normalize_l      -- shift mean L* of region A to match region B before
                        computing distance (removes lighting/drape offset)

    Returns:
        delta_e_mean     CIEDE2000 between the two region mean LAB colors
        delta_e_p90      90th-percentile of per-pixel CIEDE2000(pixel_a, mean_b)
        n_pixels_a       masked pixel count in region A
        n_pixels_b       masked pixel count in region B
        l_shift          L* shift applied to region A (0 if normalize_l=False)
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
            "l_shift": 0.0,
        }

    mean_b = pixels_b.mean(axis=0)

    l_shift = 0.0
    if normalize_l:
        l_shift = float(mean_b[0] - pixels_a[:, 0].mean())
        pixels_a = pixels_a.copy()
        pixels_a[:, 0] = np.clip(pixels_a[:, 0] + l_shift, 0.0, 100.0)

    mean_a = pixels_a.mean(axis=0)

    # Mean-vs-mean CIEDE2000
    delta_e_mean = float(
        deltaE_ciede2000(
            mean_a.reshape(1, 1, 3),
            mean_b.reshape(1, 1, 3),
        )[0, 0]
    )

    # Per-pixel: each pixel in A vs mean of B
    n = len(pixels_a)
    per_pixel = deltaE_ciede2000(
        pixels_a.reshape(n, 1, 3),
        np.tile(mean_b, (n, 1)).reshape(n, 1, 3),
    )[:, 0]
    delta_e_p90 = float(np.percentile(per_pixel, 90))

    return {
        "delta_e_mean": round(delta_e_mean, 2),
        "delta_e_p90": round(delta_e_p90, 2),
        "n_pixels_a": int(len(pixels_a)),
        "n_pixels_b": int(len(pixels_b)),
        "l_shift": round(l_shift, 2),
    }
