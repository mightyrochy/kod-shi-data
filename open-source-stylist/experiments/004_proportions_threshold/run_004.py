"""E-004 — Proportions gate threshold calibration.

Run from the project root:
    python experiments/004_proportions_threshold/run_004.py

Outputs:
    experiments/004_proportions_threshold/results/scores.csv
    experiments/004_proportions_threshold/results/mask_twoview.png
    experiments/004_proportions_threshold/results/log.txt
"""

import csv
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT))
from system.gates.proportions import compare, measure
from system.segmentation.grounded_sam import segment
from system.clients.comfyui import ComfyUIClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def max_abs_change(cmp: dict) -> float | None:
    """Single scalar: max of absolute zone changes."""
    vals = [
        cmp.get("shoulder_change_pct"),
        cmp.get("waist_change_pct"),
        cmp.get("hip_change_pct"),
    ]
    vals = [v for v in vals if v is not None]
    return round(max(abs(v) for v in vals), 2) if vals else None


def scale_mask_width(mask_path: Path, fx: float) -> np.ndarray:
    """Return a horizontally scaled copy of the mask (fy=1.0, width changes only)."""
    m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    h, w = m.shape
    new_w = int(round(w * fx))
    scaled = cv2.resize(m, (new_w, h), interpolation=cv2.INTER_NEAREST)
    return scaled


# ---------------------------------------------------------------------------
# Step 1 — segment person_two_view left crop
# ---------------------------------------------------------------------------

def get_twoview_mask(log) -> Path:
    """Crop left half of person_two_view.png, segment, return mask path."""
    src = ROOT / "assets/person/person_two_view.png"
    img = cv2.imread(str(src))
    if img is None:
        raise FileNotFoundError(f"Cannot read {src}")

    h, w = img.shape[:2]
    crop = img[:, : w // 2]

    crop_path = RESULTS_DIR / "person_twoview_front_crop.png"
    cv2.imwrite(str(crop_path), crop)
    log(f"  Saved two-view front crop: {crop_path} ({crop.shape[1]}x{crop.shape[0]})")

    client = ComfyUIClient("localhost", 8000)
    masks = segment(
        image_path=crop_path,
        prompts={"person": "person"},
        client=client,
        output_dir=RESULTS_DIR,
    )
    mask_path = Path(masks["person"])
    log(f"  Segmentation done -> {mask_path}")
    return mask_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log_lines = []

    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=== E-004: Proportions gate threshold calibration ===")
    log()

    # --- Step 1: get mask_twoview ---
    log("--- Step 1: segment person_two_view front crop ---")
    mask_twoview_path = get_twoview_mask(log)
    log()

    # --- Step 2: load / synthesise masks ---
    mask_front_path = (
        ROOT / "experiments/001_segmentation_masks/results/person_front/person.png"
    )
    log(f"--- Step 2: masks ---")
    log(f"  mask_front   : {mask_front_path}")
    log(f"  mask_twoview : {mask_twoview_path}")

    mask_scaled_10 = scale_mask_width(mask_front_path, 1.10)
    mask_scaled_20 = scale_mask_width(mask_front_path, 1.20)
    mask_scaled_30 = scale_mask_width(mask_front_path, 1.30)
    log("  Synthetic masks (fx=1.10 / 1.20 / 1.30) created in memory.")
    log()

    # --- Step 3: measure profiles ---
    log("--- Step 3: profiles ---")
    for label, src in [
        ("mask_front",   mask_front_path),
        ("mask_twoview", mask_twoview_path),
    ]:
        p = measure(src)
        log(f"  {label:<14}  shoulder={p['shoulder_width_norm']}  "
            f"waist={p['waist_width_norm']}  hip={p['hip_width_norm']}  "
            f"height={p['height_px']}px")
    log()

    # --- Step 4: pair comparisons ---
    log("--- Step 4: pair scores ---")
    PAIRS = [
        ("SAN-00", mask_front_path,  mask_front_path,  "sanity"),
        ("NAT-01", mask_front_path,  mask_twoview_path, "natural"),
        ("SYN-10", mask_front_path,  mask_scaled_10,   "synthetic+10%"),
        ("SYN-20", mask_front_path,  mask_scaled_20,   "synthetic+20%"),
        ("SYN-30", mask_front_path,  mask_scaled_30,   "synthetic+30%"),
    ]

    rows = []
    for pair_id, a, b, pair_type in PAIRS:
        cmp = compare(a, b)
        score = max_abs_change(cmp)
        score_str = f"{score:.2f}%" if score is not None else "N/A"
        log(f"  {pair_id:<8}  type={pair_type:<16}  "
            f"shoulder={cmp['shoulder_change_pct']}%  "
            f"waist={cmp['waist_change_pct']}%  "
            f"hip={cmp['hip_change_pct']}%  "
            f"max_abs={score_str}")
        rows.append({
            "pair_id": pair_id,
            "type": pair_type,
            "shoulder_pct": cmp["shoulder_change_pct"],
            "waist_pct": cmp["waist_change_pct"],
            "hip_pct": cmp["hip_change_pct"],
            "max_abs_pct": score,
        })

    log()

    # --- Step 5: threshold analysis ---
    log("--- Step 5: threshold analysis ---")
    nat_score  = next(r["max_abs_pct"] for r in rows if r["pair_id"] == "NAT-01")
    syn10_score = next(r["max_abs_pct"] for r in rows if r["pair_id"] == "SYN-10")
    san_score  = next(r["max_abs_pct"] for r in rows if r["pair_id"] == "SAN-00")

    log(f"  SAN-00 (sanity)      : {san_score}%  (expected <1)")
    log(f"  NAT-01 (natural var) : {nat_score}%")
    log(f"  SYN-10 (+10% synth)  : {syn10_score}%")

    verdict = "UNKNOWN"
    threshold = None

    if san_score is not None and san_score >= 1.0:
        verdict = "FAIL — sanity check failed (bug in measure())"
    elif nat_score is None or syn10_score is None:
        verdict = "FAIL — missing scores"
    elif nat_score >= syn10_score:
        gap = syn10_score - nat_score
        log(f"  gap = {gap:.2f}%  (negative — natural >= synthetic)")
        verdict = "FAIL — no separation; zones need adjustment"
    else:
        gap = syn10_score - nat_score
        threshold = round(nat_score + gap / 2, 1)
        log(f"  gap = {gap:.2f}%")
        log(f"  proposed threshold = {threshold}%")
        if gap >= 5.0:
            verdict = f"PASS — clear separation (gap={gap:.2f}% >= 5%)"
        else:
            verdict = f"FAIL — gap too narrow ({gap:.2f}% < 5%)"

    log(f"  VERDICT: {verdict}")
    log()

    # --- write outputs ---
    csv_path = RESULTS_DIR / "scores.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["pair_id", "type", "shoulder_pct", "waist_pct",
                           "hip_pct", "max_abs_pct"]
        )
        writer.writeheader()
        writer.writerows(rows)
    log(f"Results written: {csv_path}")

    log_path = RESULTS_DIR / "log.txt"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    log(f"Log written:     {log_path}")

    return threshold


if __name__ == "__main__":
    main()
