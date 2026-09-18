"""E-010 — warping head-to-head, arm B: geometric warp of the REAL skirt pixels.

Thesis: FitDiT re-synthesises the skirt → colour drifts (brown → olive). A geometric warp
pastes the REAL reference pixels into the body silhouette → colour is exact BY CONSTRUCTION.
This is the cheapest arm of the warping head-to-head (pure CPU, no model, no ComfyUI): it
isolates the single variable "does keeping real pixels fix the colour?".

Method (non-parametric silhouette warp):
  - region   = the drape skirt mask (hip→measured hem, continuous) — where the skirt goes,
  - garment  = the continuous brown skirt crop (real reference pixels),
  - per mask row, scale the garment's row to the mask's width at that row (follows the body
    silhouette), composite onto the person, feather the seam.

Judged by: the garment-fidelity instrument vs the reference (note: near-circular for this arm —
same pixels) AND the owner's eye for REALISM (shading/fit/seam), which is the real question for
a warp. Arm A (FitDiT) already measured: skirt DISTS 0.319 / sim 0.823.

    python experiments/010_protect_by_construction/proto_warp.py
No ComfyUI needed; system Python (cv2, numpy, + FashionSigLIP/DISTS for the score).
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

PERSON = ROOT / "assets/person/person_front.png"
OUT = ROOT / "experiments/010_protect_by_construction/results/proto_chain"
SKIRT_MASK = OUT / "skirt_ourmask.png"          # drape mask: hip→measured hem, continuous
SKIRT_GARM = OUT / "skirt_continuous.png"        # real brown skirt pixels (slit as a line)
CROPS = ROOT / "assets/outfits/outfit_001/crops"
ALL_ITEMS = {
    "skirt":    CROPS / "skirt_front crop.png",
    "blouse":   CROPS / "blouse front crop.png",
    "belt":     CROPS / "belt crop.png",
    "shoes":    CROPS / "shoes crop.png",
    "earrings": CROPS / "earings crop.png",
}


def _row_span(fg_row: np.ndarray):
    xs = np.where(fg_row)[0]
    return (int(xs.min()), int(xs.max())) if len(xs) else None


def main() -> None:
    person = cv2.imread(str(PERSON))
    h, w = person.shape[:2]

    mask = cv2.imread(str(SKIRT_MASK), cv2.IMREAD_GRAYSCALE)
    if (mask.shape[1], mask.shape[0]) != (w, h):
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
    mfg = mask > 127

    garm = cv2.imread(str(SKIRT_GARM))
    gfg = cv2.cvtColor(garm, cv2.COLOR_BGR2GRAY) < 245

    mrows = np.where(mfg.any(axis=1))[0]
    grows = np.where(gfg.any(axis=1))[0]
    mtop, mbot = int(mrows.min()), int(mrows.max())
    gtop, gbot = int(grows.min()), int(grows.max())

    warped = person.copy()
    for y in range(mtop, mbot + 1):
        span = _row_span(mfg[y])
        if span is None:
            continue
        x0, x1 = span
        gy = int(round(gtop + (y - mtop) / max(1, mbot - mtop) * (gbot - gtop)))
        gspan = _row_span(gfg[gy])
        if gspan is None:
            continue
        gx0, gx1 = gspan
        seg = garm[gy, gx0:gx1 + 1].reshape(1, -1, 3)
        seg = cv2.resize(seg, (x1 - x0 + 1, 1), interpolation=cv2.INTER_LINEAR)[0]
        warped[y, x0:x1 + 1] = seg

    # Feather the seam: soft alpha from the mask, composite warped over the person.
    alpha = cv2.GaussianBlur(mfg.astype(np.float32), (0, 0), 3.0)[..., None]
    result = (warped.astype(np.float32) * alpha + person.astype(np.float32) * (1 - alpha))
    out_path = OUT / "warp_skirt_result.png"
    cv2.imwrite(str(out_path), result.astype(np.uint8))

    # Crop the warped skirt region for the fidelity instrument.
    ys, xs = np.where(mfg)
    crop = result[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.uint8)
    crop_path = OUT / "fid_warp_skirt_gencrop.png"
    cv2.imwrite(str(crop_path), crop)

    decoys = [p for k, p in ALL_ITEMS.items() if k != "skirt"]
    res = measure_garment_fidelity(crop_path, ALL_ITEMS["skirt"], decoys)
    rr, dd = res["retrieval_rank"], res["dists"]
    print(f"WARPED SKIRT -> {out_path.relative_to(ROOT)}")
    print(f"  DISTS = {dd.get('score')} ({dd.get('verdict')})   [FitDiT arm A was 0.319]")
    print(f"  retrieval rank = {rr.get('rank')}/{1 + rr.get('n_decoys', 0)}  "
          f"verdict={rr.get('verdict')}  sim_target={rr.get('sim_target')}  [FitDiT sim 0.823]")
    print("\nNOTE: the instrument is near-CIRCULAR for the warp (same pixels) — expect a near-perfect")
    print("  colour/DISTS score. The REAL question is owner-eye REALISM: does the pasted skirt look")
    print("  natural on the body (shading/fit/seam) vs FitDiT's integrated-but-olive skirt?")
    print("  OWNER CHECKPOINT: warp_skirt_result.png vs chain skirt_result.png.")


if __name__ == "__main__":
    main()
