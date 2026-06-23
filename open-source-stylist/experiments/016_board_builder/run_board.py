"""E-016 — build ONLY the combined board on outfit_001 with the general builder (no QIE). Owner reviews."""
import json
from pathlib import Path

from system.board import build
from system.clients.comfyui import ComfyUIClient
from system.garment import classify

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "assets/outfits/outfit_001"
OUT = Path(__file__).resolve().parent / "results"

GARMENTS = [
    (classify("blouse front"), A / "blouse_front.webp"),
    (classify("skirt front"), A / "skirt_front.webp"),
    (classify("shoes"), A / "shoes_wedge.webp"),
]

if __name__ == "__main__":
    for spec, img in GARMENTS:
        print(f"{spec.label:14s} -> {spec.category:9s} atr={spec.atr_region} seg={spec.seg_term!r}  ({img.name})")
    client = ComfyUIClient()
    bd = build(GARMENTS, client, OUT)
    client.free()
    print("\n=== board_report ===")
    print(json.dumps(bd["report"], indent=2))
    print("flags:", bd["flags"])
    print("board:", bd["board"])
