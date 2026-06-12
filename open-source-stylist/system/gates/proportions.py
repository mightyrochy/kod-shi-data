"""Body proportions gate — shoulder/waist/hip widths from person silhouette mask.

Algorithm: scan each horizontal row of the binary mask and count mask pixels
(= silhouette width). Measure at three anatomical zones, normalise by body
height so the metric is resolution-independent.

Zones (fraction of body bounding-box height, measured from the top):
    shoulders  max width in [0.20, 0.35]
    waist      min width in [0.40, 0.60]
    hips       max width in [0.55, 0.75]

These zones avoid the head (top ~18%) and feet/legs divergence (bottom ~25%).
Thresholds are chosen conservatively and validated by E-004.

Dependencies: opencv-python, numpy (both installed).
"""

from pathlib import Path

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_mask(mask) -> np.ndarray:
    if isinstance(mask, (str, Path)):
        m = cv2.imread(str(mask), cv2.IMREAD_GRAYSCALE)
        if m is None:
            raise FileNotFoundError(f"Cannot read mask: {mask}")
    else:
        m = np.asarray(mask)
    if m.ndim == 3:
        m = m[:, :, 0]
    return (m > 127).astype(np.uint8)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def measure(mask) -> dict:
    """Measure normalised shoulder/waist/hip widths from a person silhouette mask.

    All width values are normalised by body height (pixels), so they are
    independent of image resolution and person scale.

    Returns:
        shoulder_width_norm   float or None
        waist_width_norm      float or None
        hip_width_norm        float or None
        height_px             int — pixel height of the person bounding box
    """
    m = _load_mask(mask)
    row_widths = m.sum(axis=1).astype(np.float32)  # shape (H,)

    body_rows = np.where(row_widths > 0)[0]
    if len(body_rows) < 20:
        return {
            "shoulder_width_norm": None,
            "waist_width_norm": None,
            "hip_width_norm": None,
            "height_px": 0,
        }

    top = int(body_rows[0])
    bottom = int(body_rows[-1])
    height_px = bottom - top + 1
    h = float(height_px)

    def zone_slice(frac_start, frac_end):
        r0 = top + int(frac_start * h)
        r1 = top + int(frac_end * h)
        r1 = max(r1, r0 + 1)
        return row_widths[r0:r1]

    shoulder_zone = zone_slice(0.20, 0.35)
    waist_zone    = zone_slice(0.40, 0.60)
    hip_zone      = zone_slice(0.55, 0.75)

    def safe_norm(arr, fn):
        if len(arr) == 0 or arr.max() == 0:
            return None
        return round(float(fn(arr)) / h, 4)

    return {
        "shoulder_width_norm": safe_norm(shoulder_zone, np.max),
        "waist_width_norm":    safe_norm(waist_zone,    np.min),
        "hip_width_norm":      safe_norm(hip_zone,      np.max),
        "height_px":           height_px,
    }


def compare(mask_a, mask_b) -> dict:
    """Compare body proportions between two person masks.

    Returns the relative change (%) for each measurement.
    Positive = wider in image_b; negative = narrower.

    Returns:
        shoulder_change_pct   float or None
        waist_change_pct      float or None
        hip_change_pct        float or None
        profile_a             measure() result for mask_a
        profile_b             measure() result for mask_b

    Verdict threshold is NOT applied here — it is calibrated by E-004.
    """
    pa = measure(mask_a)
    pb = measure(mask_b)

    def pct_change(a_val, b_val):
        if a_val is None or b_val is None or a_val == 0:
            return None
        return round((b_val - a_val) / a_val * 100.0, 2)

    shoulder_pct = pct_change(pa["shoulder_width_norm"], pb["shoulder_width_norm"])
    waist_pct    = pct_change(pa["waist_width_norm"],    pb["waist_width_norm"])
    hip_pct      = pct_change(pa["hip_width_norm"],      pb["hip_width_norm"])

    individual = [abs(v) for v in [shoulder_pct, waist_pct, hip_pct] if v is not None]
    max_abs = round(max(individual), 2) if individual else None

    return {
        "shoulder_change_pct": shoulder_pct,
        "waist_change_pct":    waist_pct,
        "hip_change_pct":      hip_pct,
        "max_abs_change_pct":  max_abs,
        "profile_a": pa,
        "profile_b": pb,
    }
