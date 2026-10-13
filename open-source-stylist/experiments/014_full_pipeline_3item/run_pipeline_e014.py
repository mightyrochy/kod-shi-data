"""Drive the universal pipeline on outfit_001 (originals + types only — no pre-made crops/masks)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from system.pipeline import run_pipeline

A = ROOT / "assets/outfits/outfit_001"
GARMENTS = [
    {"type": "blouse", "image": A / "blouse_front.webp"},
    {"type": "skirt",  "image": A / "skirt_front.webp"},
    {"type": "shoes",  "image": A / "shoes_wedge.webp"},
    {"type": "belt",     "image": A / "belt.jpg"},            # accessory -> OmniTry (deferred)
    {"type": "earrings", "image": A / "earrings_disc.webp"},  # accessory -> OmniTry (deferred)
]

if __name__ == "__main__":
    run_pipeline(ROOT / "assets/person/person_front.png", A / "outfit layout.txt",
                 GARMENTS, Path(__file__).parent / "pipeline_run")
