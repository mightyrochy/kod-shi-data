"""E-003 — ArcFace identity gate threshold calibration.

Run from the project root:
    python experiments/003_arcface_threshold/run_003.py

Outputs:
    experiments/003_arcface_threshold/results/scores.csv
    experiments/003_arcface_threshold/results/log.txt  (printed + written)
"""

import csv
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT))
from system.gates.identity import get_embedding, cosine


# ---------------------------------------------------------------------------
# Image sources
# ---------------------------------------------------------------------------

def load_p1_frontal() -> np.ndarray:
    """Crop the left half of the two-view composite (frontal panel)."""
    path = ROOT / "assets/person/person_two_view.png"
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Cannot read {path}")
    h, w = img.shape[:2]
    return img[:, : w // 2]


SOURCES = {
    "P0": ROOT / "assets/person/person_front.png",
    "D1": ROOT / "assets/outfits/outfit_001/blouse_front.webp",
    "D2": ROOT / "assets/outfits/outfit_001/skirt_front.webp",
}

PAIRS = [
    ("SP-01", "P0", "P1", "same"),
    ("DP-01", "P0", "D1", "different"),
    ("DP-02", "P0", "D2", "different"),
    ("DP-03", "D1", "D2", "different"),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log_lines = []

    def log(msg=""):
        print(msg)
        log_lines.append(msg)

    log("=== E-003: ArcFace threshold calibration ===")
    log()

    # --- extract embeddings ---
    embeddings = {}

    log("--- Extracting embeddings ---")
    for key, path in SOURCES.items():
        emb = get_embedding(path)
        embeddings[key] = emb
        status = f"ok (norm={np.linalg.norm(emb):.4f})" if emb is not None else "FACE NOT DETECTED"
        log(f"  {key}  {Path(path).name:<30}  {status}")

    # P1: crop left half of two-view composite
    p1_crop = load_p1_frontal()
    emb_p1 = get_embedding(p1_crop)
    embeddings["P1"] = emb_p1
    status = f"ok (norm={np.linalg.norm(emb_p1):.4f})" if emb_p1 is not None else "FACE NOT DETECTED"
    log(f"  P1  person_two_view.png (left crop)     {status}")

    log()

    # --- compute pairs ---
    log("--- Pair scores ---")
    rows = []
    same_scores = []
    diff_scores = []

    for pair_id, key_a, key_b, pair_type in PAIRS:
        emb_a = embeddings.get(key_a)
        emb_b = embeddings.get(key_b)

        if emb_a is None or emb_b is None:
            score = None
            note = "SKIPPED (no embedding)"
        else:
            score = round(cosine(emb_a, emb_b), 4)
            note = ""
            if pair_type == "same":
                same_scores.append(score)
            else:
                diff_scores.append(score)

        score_str = f"{score:.4f}" if score is not None else "N/A"
        log(f"  {pair_id:<8}  {key_a} vs {key_b}  type={pair_type:<10}  cosine={score_str}  {note}")
        rows.append({"pair_id": pair_id, "img_a": key_a, "img_b": key_b,
                     "type": pair_type, "cosine": score_str, "note": note})

    log()

    # --- threshold analysis ---
    log("--- Threshold analysis ---")
    if same_scores and diff_scores:
        same_min = min(same_scores)
        diff_max = max(diff_scores)
        gap = same_min - diff_max
        threshold = round(diff_max + gap / 2, 3)

        log(f"  Same-person scores : {same_scores}")
        log(f"  Diff-person scores : {diff_scores}")
        log(f"  same_min           : {same_min:.4f}")
        log(f"  diff_max           : {diff_max:.4f}")
        log(f"  gap                : {gap:.4f}")
        log(f"  proposed threshold : {threshold}")

        if gap >= 0.15:
            log(f"  VERDICT: PASS — clear separation (gap={gap:.4f} >= 0.15)")
        else:
            log(f"  VERDICT: FAIL — gap too narrow (gap={gap:.4f} < 0.15), threshold NOT promoted")
    else:
        threshold = None
        log("  Cannot derive threshold: missing same or different scores.")

    log()

    # --- write CSV ---
    csv_path = RESULTS_DIR / "scores.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["pair_id", "img_a", "img_b", "type", "cosine", "note"])
        writer.writeheader()
        writer.writerows(rows)
    log(f"Results written: {csv_path}")

    # --- write log ---
    log_path = RESULTS_DIR / "log.txt"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    log(f"Log written:     {log_path}")

    return threshold


if __name__ == "__main__":
    main()
