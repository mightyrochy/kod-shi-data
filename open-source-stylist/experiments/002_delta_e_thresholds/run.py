"""E-002 -- delta-E threshold separability.

Run from project root:
    python experiments/002_delta_e_thresholds/run.py

No external servers required (opencv + numpy only).
"""

import csv
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from system.gates.color import compare_regions

RESULTS = Path(__file__).parent / "results"
SHIFTS_DIR = RESULTS / "synthetic_shifts"
RESULTS.mkdir(exist_ok=True)
SHIFTS_DIR.mkdir(exist_ok=True)

E001 = ROOT / "experiments" / "001_segmentation_masks" / "results"
ASSETS = ROOT / "assets" / "outfits" / "outfit_001"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_bgr(path: Path) -> np.ndarray:
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(path)
    return img


def load_mask_bool(path: Path) -> np.ndarray:
    m = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if m is None:
        raise FileNotFoundError(path)
    return m > 127


def apply_hue_shift(bgr: np.ndarray, mask: np.ndarray, shift_deg: int) -> np.ndarray:
    """Rotate hue of masked pixels by shift_deg degrees (HSV hue is 0-179 in OpenCV)."""
    out = bgr.copy()
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.int32)
    hsv[:, :, 0][mask] = (hsv[:, :, 0][mask] + shift_deg // 2) % 180
    hsv_u8 = hsv.clip(0, 255).astype(np.uint8)
    shifted = cv2.cvtColor(hsv_u8, cv2.COLOR_HSV2BGR)
    out[mask] = shifted[mask]
    return out


def save_overlay(bgr: np.ndarray, mask: np.ndarray, name: str) -> None:
    """Save image with mask region outlined for visual inspection."""
    vis = bgr.copy()
    contours, _ = cv2.findContours(
        mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    cv2.drawContours(vis, contours, -1, (0, 255, 0), 2)
    cv2.imwrite(str(SHIFTS_DIR / f"{name}.png"), vis)


# ---------------------------------------------------------------------------
# Series A — synthetic hue shifts
# ---------------------------------------------------------------------------

def series_a(rows: list) -> None:
    print("\n=== Series A: synthetic hue shifts ===")
    skirt_img_path = ASSETS / "skirt_front.webp"
    skirt_mask_path = E001 / "outfit_001_skirt_front" / "skirt.png"

    base = load_bgr(skirt_img_path)
    mask = load_mask_bool(skirt_mask_path)

    shifts = [0, 5, 10, 15, 20, 30, 45, 60, 90, 120, 150, 180]
    save_preview_at = {0, 30, 90, 180}

    for shift in shifts:
        shifted = apply_hue_shift(base, mask, shift)
        result = compare_regions(shifted, mask, base, mask)

        if shift in save_preview_at:
            save_overlay(shifted, mask, f"skirt_hue_{shift:03d}deg")

        row = {
            "series": "A",
            "pair_name": f"skirt_hue_shift_{shift:03d}deg",
            "shift_deg": shift,
            "delta_e_mean": result["delta_e_mean"],
            "delta_e_p90": result["delta_e_p90"],
            "n_pixels_a": result["n_pixels_a"],
            "n_pixels_b": result["n_pixels_b"],
        }
        rows.append(row)
        print(f"  shift={shift:3d}deg  dE_mean={result['delta_e_mean']:6.2f}  dE_p90={result['delta_e_p90']:6.2f}")


# ---------------------------------------------------------------------------
# Series B — same-garment front/back (natural variation)
# ---------------------------------------------------------------------------

def series_b(rows: list) -> None:
    print("\n=== Series B: same-garment front/back ===")

    pairs = [
        (
            "skirt_front_vs_back",
            ASSETS / "skirt_front.webp",
            E001 / "outfit_001_skirt_front" / "skirt.png",
            ASSETS / "skirt_back.webp",
            E001 / "outfit_001_skirt_back" / "skirt.png",
        ),
        (
            "blouse_front_vs_back",
            ASSETS / "blouse_front.webp",
            E001 / "outfit_001_blouse_front" / "blouse.png",
            ASSETS / "blouse_back.webp",
            E001 / "outfit_001_blouse_back" / "blouse.png",
        ),
    ]

    for name, img_a, mask_a, img_b, mask_b in pairs:
        result = compare_regions(img_a, mask_a, img_b, mask_b)
        row = {
            "series": "B",
            "pair_name": name,
            "shift_deg": "",
            "delta_e_mean": result["delta_e_mean"],
            "delta_e_p90": result["delta_e_p90"],
            "n_pixels_a": result["n_pixels_a"],
            "n_pixels_b": result["n_pixels_b"],
        }
        rows.append(row)
        print(f"  {name}  dE_mean={result['delta_e_mean']:6.2f}  dE_p90={result['delta_e_p90']:6.2f}")


# ---------------------------------------------------------------------------
# Series C — different garments (upper bound)
# ---------------------------------------------------------------------------

def series_c(rows: list) -> None:
    print("\n=== Series C: different garments ===")

    skirt_img  = ASSETS / "skirt_front.webp"
    skirt_mask = E001 / "outfit_001_skirt_front" / "skirt.png"

    others = [
        ("skirt_vs_belt",   ASSETS / "belt.jpg",         E001 / "outfit_001_belt" / "belt.png"),
        ("skirt_vs_shoes",  ASSETS / "shoes_wedge.webp",  E001 / "outfit_001_shoes_wedge" / "shoes.png"),
        ("skirt_vs_blouse", ASSETS / "blouse_front.webp", E001 / "outfit_001_blouse_front" / "blouse.png"),
    ]

    for name, img_b, mask_b in others:
        result = compare_regions(skirt_img, skirt_mask, img_b, mask_b)
        row = {
            "series": "C",
            "pair_name": name,
            "shift_deg": "",
            "delta_e_mean": result["delta_e_mean"],
            "delta_e_p90": result["delta_e_p90"],
            "n_pixels_a": result["n_pixels_a"],
            "n_pixels_b": result["n_pixels_b"],
        }
        rows.append(row)
        print(f"  {name}  dE_mean={result['delta_e_mean']:6.2f}  dE_p90={result['delta_e_p90']:6.2f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    rows = []
    series_a(rows)
    series_b(rows)
    series_c(rows)

    csv_path = RESULTS / "scores.csv"
    fieldnames = ["series", "pair_name", "shift_deg", "delta_e_mean", "delta_e_p90",
                  "n_pixels_a", "n_pixels_b"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved: {csv_path}")

    # Monotonicity check for Series A
    a_means = [r["delta_e_mean"] for r in rows if r["series"] == "A"]
    violations = sum(
        1 for i in range(1, len(a_means)) if a_means[i] < a_means[i - 1] - 0.5
    )
    print(f"\nMonotonicity check (Series A): {violations} violation(s) "
          f"({'PASS' if violations == 0 else 'FAIL — check results'})")

    b_max = max((r["delta_e_mean"] for r in rows if r["series"] == "B"), default=0)
    c_min = min((r["delta_e_mean"] for r in rows if r["series"] == "C"), default=0)
    print(f"Separation check: Series B max={b_max:.2f}, Series C min={c_min:.2f}  "
          f"({'gap exists' if c_min > b_max else 'NO GAP — investigate'})")


if __name__ == "__main__":
    main()
