"""E-001 runner — segmentation mask quality check.

Usage: python -m experiments.001_segmentation_masks.run
       (from project root)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np
from system.clients.comfyui import ComfyUIClient
from system.segmentation.grounded_sam import segment

RESULTS = Path(__file__).parent / "results"
ASSETS  = ROOT / "assets"

CLIENT = ComfyUIClient(host="localhost", port=8000)

# ---------------------------------------------------------------------------
# Image configs
# ---------------------------------------------------------------------------

PERSON_PROMPTS = {
    "person":     "person",
    "face":       "face",
    "hair":       "hair",
    "background": "background",
    "top":        "sweater . shirt . top",
    "bottom":     "pants . jeans . trousers",
    "shoes":      "shoes . slippers",
    "glasses":    "glasses . eyeglasses",
}

OUTFIT_001 = {
    "belt.jpg":           {"belt":  "belt"},
    "blouse_front.webp":  {"blouse": "blouse . shirt . top"},
    "blouse_back.webp":   {"blouse": "blouse . shirt . top"},
    "earrings_disc.webp": {"earrings": "earrings"},
    "shoes_wedge.webp":   {"shoes": "shoes . heels . wedge"},
    "skirt_front.webp":   {"skirt": "skirt"},
    "skirt_back.webp":    {"skirt": "skirt"},
}

# ---------------------------------------------------------------------------
# Overlay helper
# ---------------------------------------------------------------------------

OVERLAY_COLORS = [
    (255,  80,  80),   # red
    ( 80, 200,  80),   # green
    ( 80, 120, 255),   # blue
    (255, 200,  60),   # yellow
    (200,  80, 200),   # purple
    ( 60, 220, 220),   # cyan
    (255, 140,  40),   # orange
    (160, 255, 100),   # lime
    (255, 100, 160),   # pink
]

def make_overlay(source_path: Path, masks: dict[str, str], out_path: Path) -> None:
    img = cv2.imread(str(source_path))
    if img is None:
        print(f"  [overlay] cannot read {source_path}")
        return
    overlay = img.copy().astype(np.float32)

    for i, (label, mask_path) in enumerate(masks.items()):
        m = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if m is None or m.max() == 0:
            print(f"  [overlay] {label}: empty or missing mask")
            continue
        m_resized = cv2.resize(m, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
        fg = m_resized > 127
        color = OVERLAY_COLORS[i % len(OVERLAY_COLORS)]
        for c in range(3):
            overlay[:, :, c][fg] = overlay[:, :, c][fg] * 0.5 + color[2 - c] * 0.5

    cv2.imwrite(str(out_path), overlay.astype(np.uint8))
    print(f"  overlay -> {out_path.name}")

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_person():
    src = ASSETS / "person" / "person_front.png"
    out_dir = RESULTS / "person_front"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n=== person_front.png ({len(PERSON_PROMPTS)} labels) ===")
    masks = segment(src, PERSON_PROMPTS, CLIENT, out_dir)
    print(f"  masks: {list(masks.keys())}")
    make_overlay(src, masks, out_dir / "_overlay_all.png")
    # individual overlays per label
    for label, mpath in masks.items():
        make_overlay(src, {label: mpath}, out_dir / f"_overlay_{label}.png")


def run_outfit_001():
    outfit_dir = ASSETS / "outfits" / "outfit_001"
    for filename, prompts in OUTFIT_001.items():
        src = outfit_dir / filename
        stem = Path(filename).stem
        out_dir = RESULTS / f"outfit_001_{stem}"
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n=== outfit_001/{filename} ({list(prompts.keys())}) ===")
        try:
            masks = segment(src, prompts, CLIENT, out_dir)
            print(f"  masks: {list(masks.keys())}")
            make_overlay(src, masks, out_dir / "_overlay.png")
        except Exception as e:
            print(f"  ERROR: {e}")


if __name__ == "__main__":
    run_person()
    run_outfit_001()
    print("\nDone. Review overlays in experiments/001_segmentation_masks/results/")
