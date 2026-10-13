"""E-009 runner — QIE config comparison (body / face / item colour).

Reuses the audited vertical slice (system/run_slice.py) so every generation parameter
provably reaches the engine. For each (arm, seed) it generates + runs the full gate
suite, copies the run's manifest / generated.png / report.md into results/, and builds a
per-axis comparison table (results/comparison.md).

Run as a script (the package dir name starts with a digit, so not importable via -m):

    python experiments/009_body_preservation/run_e009.py --phase 1
    python experiments/009_body_preservation/run_e009.py --table   # rebuild table only
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

try:  # the table contains Δ/° — don't let a cp1251 console crash the run after results are written
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from system import run_slice  # noqa: E402

RESULTS = Path(__file__).parent / "results"

OUTFIT = "assets/outfits/outfit_001/outfit_package.json"
PERSON = "assets/person/person_front.png"
PERSON_MASK = "experiments/001_segmentation_masks/results/person_front/person.png"
REFERENCES = "assets/outfits/outfit_001/eval_references.json"
BOARD = "hybrid_mask_crop"
SEEDS = (42, 123)
ITEMS = ("top", "bottom", "belt", "earrings", "shoes")

# Two regimes, negative held empty (per protocol §3.1).
ARMS = {
    "R1_lightning": dict(engine="qie-2511-lightning", steps=4, cfg=1.0),
    "R2_full_cfg5": dict(engine="qie-2511", steps=20, cfg=5.0),
}


def _args(arm_cfg: dict, seed: int) -> Namespace:
    return Namespace(
        outfit=OUTFIT, person=PERSON, board=BOARD, seed=seed,
        width=720, height=1024, person_mask=PERSON_MASK, references=REFERENCES,
        generate=True, timeout=600.0, **arm_cfg,
    )


def run_phase1() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    for arm, cfg in ARMS.items():
        for seed in SEEDS:
            dst = RESULTS / arm / f"seed_{seed}"
            if (dst / "manifest.json").is_file():
                print(f"=== {arm} seed={seed}: already complete, skipping ===")
                continue
            print(f"\n=== {arm} seed={seed} ({cfg}) ===")
            run_dir = run_slice.run_slice(_args(cfg, seed))
            dst.mkdir(parents=True, exist_ok=True)
            for name in ("manifest.json", "generated.png", "report.md"):
                src = run_dir / name
                if src.is_file():
                    shutil.copy2(src, dst / name)
            print(f"collected -> {dst.relative_to(ROOT)}")
    build_table()


def _measurement(arm: str, seed: int) -> dict | None:
    path = RESULTS / arm / f"seed_{seed}" / "manifest.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("measurement", {})


def build_table() -> None:
    lines = [
        "# E-009 — per-axis comparison (R1 Lightning vs R2 fair no-Lightning)",
        "",
        "Advisory gates; owner verdict is the acceptance. No aggregate score.",
        "",
        "## Body (pose joints) + Face (ArcFace)",
        "| arm | seed | hipΔ% | shoulderΔ% | ratioΔ% | pose_mism° | face cosine |",
        "|---|---|---|---|---|---|---|",
    ]
    for arm in ARMS:
        for seed in SEEDS:
            m = _measurement(arm, seed)
            if not m:
                lines.append(f"| {arm} | {seed} | — | — | — | — | — |")
                continue
            b = m.get("body", {})
            ch = b.get("change_pct", {}) if b.get("verdict") == "MEASURED" else {}
            lines.append(
                f"| {arm} | {seed} | {ch.get('hip_width_norm')} | "
                f"{ch.get('shoulder_width_norm')} | {ch.get('shoulder_hip_ratio')} | "
                f"{b.get('pose_mismatch_deg')} | {m.get('identity', {}).get('cosine')} |"
            )

    lines += [
        "",
        "## Item colour — ΔE / verdict / hueΔ° / reliable",
        "| arm | seed | " + " | ".join(ITEMS) + " |",
        "|---|---|" + "|".join(["---"] * len(ITEMS)) + "|",
    ]
    for arm in ARMS:
        for seed in SEEDS:
            m = _measurement(arm, seed) or {}
            cells = []
            for item in ITEMS:
                c = m.get("color", {}).get(item, {})
                if "delta_e_mean" in c:
                    rel = "Y" if c.get("hue_reliable") else "n"
                    cells.append(f"{c['delta_e_mean']}/{c['verdict']}/{c.get('hue_delta_deg')}/{rel}")
                else:
                    cells.append(c.get("verdict", "—"))
            lines.append(f"| {arm} | {seed} | " + " | ".join(cells) + " |")

    out = RESULTS / "comparison.md"
    RESULTS.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwritten: {out.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="E-009 QIE config comparison runner")
    parser.add_argument("--phase", type=int, choices=(1,))
    parser.add_argument("--table", action="store_true")
    args = parser.parse_args()
    if args.table:
        build_table()
    elif args.phase == 1:
        run_phase1()
    else:
        parser.error("choose --phase 1 or --table")


if __name__ == "__main__":
    main()
