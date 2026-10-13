"""E-010 — first OBJECTIVE garment-fidelity numbers on the chain result (axis #1).

Reuses the per-pass region masks already produced by proto_chain.py (skirt drape mask,
blouse native FitDiT mask) to crop each garment region from the chain final, then runs
the garment-fidelity instrument (FashionSigLIP retrieval-rank against the other outfit
items as decoys + DISTS vs the target reference). Uncalibrated / advisory until a
labelled calibration set exists — but it turns axis #1 from owner-eye-only into a
measured signal and confirms the instrument runs end-to-end on real generated output.

    python experiments/010_protect_by_construction/proto_fidelity.py
No ComfyUI needed (reuses existing masks); system Python (FashionSigLIP + DISTS).
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from system.gates.garment_fidelity import measure_garment_fidelity

CROPS = ROOT / "assets/outfits/outfit_001/crops"
FINAL = ROOT / "experiments/010_protect_by_construction/results/proto_chain/blouse_result.png"
OUT = ROOT / "experiments/010_protect_by_construction/results/proto_chain"

# Region masks from the latest (fixed) chain run: skirt = drape mask, blouse = native FitDiT mask.
REGION_MASKS = {
    "skirt":  OUT / "skirt_ourmask.png",
    "blouse": OUT / "blouse_automask.png",
}

# Natural reference crops (not the FitDiT through-slit crops) + the full outfit as a decoy gallery.
ALL_ITEMS = {
    "skirt":    CROPS / "skirt_front crop.png",
    "blouse":   CROPS / "blouse front crop.png",
    "belt":     CROPS / "belt crop.png",
    "shoes":    CROPS / "shoes crop.png",
    "earrings": CROPS / "earings crop.png",
}


def _crop_region(image_path: Path, mask_path: Path, out_path: Path) -> Path:
    """Cut the masked region to its bbox on a white background."""
    img = cv2.imread(str(image_path))
    m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if (m.shape[1], m.shape[0]) != (img.shape[1], img.shape[0]):
        m = cv2.resize(m, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
    fg = m > 127
    ys, xs = np.where(fg)
    if len(ys) == 0:
        raise RuntimeError(f"empty mask: {mask_path}")
    out = np.full_like(img, 255)
    out[fg] = img[fg]
    crop = out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    cv2.imwrite(str(out_path), crop)
    return out_path


def main() -> None:
    for item in ("skirt", "blouse"):
        gen_crop = _crop_region(FINAL, REGION_MASKS[item], OUT / f"fid_{item}_gencrop.png")
        ref = ALL_ITEMS[item]
        decoys = [p for k, p in ALL_ITEMS.items() if k != item]
        res = measure_garment_fidelity(gen_crop, ref, decoys)
        rr, dd = res["retrieval_rank"], res["dists"]
        print(f"\n{item.upper()}  (rendered crop vs reference {ref.name})")
        print(f"  DISTS = {dd.get('score')}  ({dd.get('verdict')})   [lower = closer]")
        print(f"  retrieval rank = {rr.get('rank')}/{1 + rr.get('n_decoys', 0)}  "
              f"verdict={rr.get('verdict')}  sim_target={rr.get('sim_target')}")
        print(f"    sim_decoys ({[k for k in ALL_ITEMS if k != item]}) = {rr.get('sim_decoys')}")

    print("\nNOTE: ADVISORY — instrument uncalibrated (no labelled set yet). First objective axis-#1 signal:")
    print("  rank=1 means the rendered garment is nearest its own reference among the outfit decoys.")


if __name__ == "__main__":
    main()
