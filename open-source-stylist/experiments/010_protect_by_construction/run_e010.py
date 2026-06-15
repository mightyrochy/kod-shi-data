"""E-010 runner — protect-by-construction (inpaint) try-on.

Compares:
  Arm A — full re-generation, QIE Lightning (data from E-009 R1_lightning; NOT regenerated)
  Arm B — FLUX Fill inpaint, clothing mask only

Phase 0 (build + owner checkpoint):
    python experiments/010_protect_by_construction/run_e010.py --phase 0
    Generates seed=42 arm B only. Owner reviews before Phase 1.

Phase 1 (full gate run):
    python experiments/010_protect_by_construction/run_e010.py --phase 1
    Generates arm B for seeds [42, 123] with full gate suite.
    Arm A data is read from E-009 results (no regeneration).

Table rebuild only:
    python experiments/010_protect_by_construction/run_e010.py --table

Resumable: any seed/arm already in results/ (manifest.json present) is skipped.
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

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from system import run_slice  # noqa: E402

RESULTS = Path(__file__).parent / "results"
E009_RESULTS = ROOT / "experiments/009_body_preservation/results"

OUTFIT = "assets/outfits/outfit_001/outfit_package.json"
PERSON = "assets/person/person_front.png"
PERSON_MASK = "experiments/001_segmentation_masks/results/person_front/person.png"
CLOTHING_MASK = "experiments/010_protect_by_construction/masks/clothing_region.png"
REFERENCES = "assets/outfits/outfit_001/eval_references.json"
BOARD = "hybrid_mask_crop"
SEEDS = (42, 123)
ITEMS = ("top", "bottom", "belt", "earrings", "shoes")

# Arm A: QIE Lightning (E-009 R1_lightning). NOT regenerated — results read from E-009.
ARM_A_LABEL = "A_qie_lightning"
ARM_A_E009_KEY = "R1_lightning"

# Arm B: FLUX Fill inpaint.
ARM_B_LABEL = "B_flux_fill"
ARM_B_CFG = dict(
    engine="flux-fill",
    steps=20,
    cfg=3.5,
    mask=CLOTHING_MASK,
    denoise=1.0,
)


def _args_b(seed: int) -> Namespace:
    return Namespace(
        outfit=OUTFIT, person=PERSON, board=BOARD, seed=seed,
        width=720, height=1024,
        person_mask=PERSON_MASK, references=REFERENCES,
        generate=True, timeout=900.0,
        **ARM_B_CFG,
    )


def _collect(run_dir: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for name in ("manifest.json", "generated.png", "report.md"):
        src = run_dir / name
        if src.is_file():
            shutil.copy2(src, dst / name)


# ---------------------------------------------------------------------------
# Arm A symlink — copy E-009 R1_lightning results into E-010 results tree
# ---------------------------------------------------------------------------

def _ensure_arm_a() -> None:
    """Copy (not symlink) arm A results from E-009 into E-010 results/."""
    for seed in SEEDS:
        src_dir = E009_RESULTS / ARM_A_E009_KEY / f"seed_{seed}"
        dst_dir = RESULTS / ARM_A_LABEL / f"seed_{seed}"
        if (dst_dir / "manifest.json").is_file():
            print(f"=== arm A seed={seed}: already present ===")
            continue
        if not (src_dir / "manifest.json").is_file():
            print(f"WARNING: E-009 arm A seed={seed} not found at {src_dir}")
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)
        for name in ("manifest.json", "generated.png", "report.md"):
            src = src_dir / name
            if src.is_file():
                shutil.copy2(src, dst_dir / name)
        print(f"=== arm A seed={seed}: copied from E-009 ===")


# ---------------------------------------------------------------------------
# Phase 0 — one test image, owner checkpoint
# ---------------------------------------------------------------------------

def run_phase0() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    seed = 42
    dst = RESULTS / ARM_B_LABEL / f"seed_{seed}"
    if (dst / "manifest.json").is_file():
        print(f"Phase 0 seed={seed} already complete at {dst.relative_to(ROOT)}")
        print("Owner checkpoint: review generated.png before running --phase 1")
        return
    print(f"\n=== Phase 0 — arm B seed={seed} (FLUX Fill inpaint) ===")
    run_dir = run_slice.run_slice(_args_b(seed))
    _collect(run_dir, dst)
    print(f"\n--- Phase 0 complete ---")
    print(f"Generated: {(dst / 'generated.png').relative_to(ROOT)}")
    print(f"Manifest:  {(dst / 'manifest.json').relative_to(ROOT)}")
    print(f"Report:    {(dst / 'report.md').relative_to(ROOT)}")
    print()
    print("OWNER CHECKPOINT: Review generated.png against the four criteria:")
    print("  1. Identity preserved (face, hair, skin tone, body proportions)")
    print("  2. All outfit items present (blouse, skirt, belt, earrings, shoes)")
    print("  3. Outfit logic correct (layering, visibility)")
    print("  4. Seam/halo at the mask boundary acceptable")
    print()
    print("If OK: run --phase 1 to generate seed=123 and build comparison table.")
    print("If not OK: adjust mask / workflow / denoise before proceeding.")


# ---------------------------------------------------------------------------
# Phase 1 — full generation + table
# ---------------------------------------------------------------------------

def run_phase1() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    _ensure_arm_a()
    for seed in SEEDS:
        dst = RESULTS / ARM_B_LABEL / f"seed_{seed}"
        if (dst / "manifest.json").is_file():
            print(f"=== arm B seed={seed}: already complete, skipping ===")
            continue
        print(f"\n=== arm B seed={seed} (FLUX Fill inpaint) ===")
        run_dir = run_slice.run_slice(_args_b(seed))
        _collect(run_dir, dst)
        print(f"collected -> {dst.relative_to(ROOT)}")
    build_table()


# ---------------------------------------------------------------------------
# Comparison table
# ---------------------------------------------------------------------------

def _measurement(arm_label: str, seed: int) -> dict | None:
    path = RESULTS / arm_label / f"seed_{seed}" / "manifest.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("measurement", {})


def build_table() -> None:
    arms = [ARM_A_LABEL, ARM_B_LABEL]
    arm_display = {
        ARM_A_LABEL: "A — QIE Lightning (E-009 R1)",
        ARM_B_LABEL: "B — FLUX Fill inpaint",
    }

    lines = [
        "# E-010 — protect-by-construction comparison (A: QIE Lightning vs B: FLUX Fill inpaint)",
        "",
        "Advisory gates; owner verdict per axis is the acceptance. No aggregate score.",
        "Garment fidelity is a HARD GATE — body win traded for garment regression does NOT pass.",
        "",
        "## Body (pose joints, clothing-robust) + Face (ArcFace)",
        "| arm | seed | hipΔ% | shoulderΔ% | ratioΔ% | pose_mism° | face cosine |",
        "|---|---|---|---|---|---|---|",
    ]
    for arm in arms:
        for seed in SEEDS:
            m = _measurement(arm, seed)
            if not m:
                lines.append(f"| {arm_display[arm]} | {seed} | — | — | — | — | — |")
                continue
            b = m.get("body", {})
            ch = b.get("change_pct", {}) if b.get("verdict") == "MEASURED" else {}
            lines.append(
                f"| {arm_display[arm]} | {seed} | {ch.get('hip_width_norm')} | "
                f"{ch.get('shoulder_width_norm')} | {ch.get('shoulder_hip_ratio')} | "
                f"{b.get('pose_mismatch_deg')} | {m.get('identity', {}).get('cosine')} |"
            )

    lines += [
        "",
        "## Item colour — ΔE / verdict / hueΔ° / reliable",
        "| arm | seed | " + " | ".join(ITEMS) + " |",
        "|---|---|" + "|".join(["---"] * len(ITEMS)) + "|",
    ]
    for arm in arms:
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
            lines.append(f"| {arm_display[arm]} | {seed} | " + " | ".join(cells) + " |")

    lines += [
        "",
        "## Acceptance (from protocol §5)",
        "- Body better: mean |hipΔ%| materially below arm A ~8.85% (target ≤ ~4.5%)",
        "- Face not worse: cosine ≥ 0.57 and not below arm A",
        "- Garment not worse (hard gate): every item ΔE not worse, all items present, layering correct",
        "- No seam/halo the owner rejects",
        "- **Owner verdict per item is final; gates are advisory.**",
    ]

    out = RESULTS / "comparison.md"
    RESULTS.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwritten: {out.relative_to(ROOT)}")


# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="E-010 protect-by-construction runner")
    parser.add_argument("--phase", type=int, choices=(0, 1),
                        help="0=Phase 0 test output (owner checkpoint); 1=full A/B run")
    parser.add_argument("--table", action="store_true", help="rebuild comparison table only")
    args = parser.parse_args()

    if args.table:
        build_table()
    elif args.phase == 0:
        run_phase0()
    elif args.phase == 1:
        run_phase1()
    else:
        parser.error("choose --phase 0, --phase 1, or --table")


if __name__ == "__main__":
    main()
