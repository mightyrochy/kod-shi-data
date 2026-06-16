"""E-010 runner — garment-faithful try-on with FitDiT.

Engine: FitDiT (DiT-based, high-res garment feature injection).
FLUX Fill arm from the previous build is disqualified (text-only conditioning,
no garment image — see STARTER.md 2026-06-16).

Phase 0 (engine selection checkpoint):
    python experiments/010_protect_by_construction/run_e010.py --phase 0
    Generates blouse try-on seed=42 only. Owner reviews before Phase 1.

Phase 1 (full arm B generation):
    python experiments/010_protect_by_construction/run_e010.py --phase 1
    Runs FitDiT on blouse + skirt for seeds [42, 123].
    Arm A data is read from E-009 R1_lightning results (not regenerated).

Table rebuild:
    python experiments/010_protect_by_construction/run_e010.py --table

Resumable: any seed/item already in results/ (manifest.json present) is skipped.
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RESULTS = Path(__file__).parent / "results"
E009_RESULTS = ROOT / "experiments/009_body_preservation/results"

PERSON = ROOT / "assets/person/person_front.png"
CROPS  = ROOT / "assets/outfits/outfit_001/crops"
OUTFIT = ROOT / "assets/outfits/outfit_001/outfit_package.json"

# Garment items: (crop filename, FitDiT category, label)
GARMENTS = [
    ("blouse front crop.png", "Upper-body", "blouse"),
    ("skirt_front crop.png",  "Lower-body", "skirt"),
]

# Arm A: QIE Lightning results already in E-009 — do not regenerate
ARM_A_LABEL    = "A_qie_lightning"
ARM_A_E009_KEY = "R1_lightning"

# Arm B: FitDiT garment-faithful try-on
ARM_B_LABEL = "B_fitdit"
SEEDS       = (42, 123)

# FitDiT generation parameters
FITDIT_CFG = dict(
    n_steps=20,
    guidance_scale=2.0,
    resolution="768x1024",
)

TIMEOUT = 900.0   # 15 min; 20-step FitDiT on 16 GB VRAM


# ── ComfyUI prompt builder ────────────────────────────────────────────────

def _fitdit_prompt(
    person_ref: str,
    garm_ref: str,
    category: str,
    seed: int,
    n_steps: int = 20,
    guidance_scale: float = 2.0,
    resolution: str = "768x1024",
    output_prefix: str = "fitdit_out",
    with_offload: bool = False,
) -> dict:
    return {
        "1": {
            "class_type": "FitDiTLoader",
            "inputs": {
                "device": "cuda",
                "with_fp16": False,
                "with_offload": with_offload,
                "with_aggressive_offload": False,
            },
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": person_ref, "upload": "image"},
        },
        "3": {
            "class_type": "LoadImage",
            "inputs": {"image": garm_ref, "upload": "image"},
        },
        "4": {
            "class_type": "FitDiTMaskGenerator",
            "inputs": {
                "model":         ["1", 0],
                "vton_image":    ["2", 0],
                "category":      category,
                "offset_top":    0,
                "offset_bottom": 0,
                "offset_left":   0,
                "offset_right":  0,
            },
        },
        "5": {
            "class_type": "FitDiTTryOn",
            "inputs": {
                "model":       ["1", 0],
                "vton_image":  ["2", 0],
                "garm_image":  ["3", 0],
                "mask":        ["4", 1],
                "pose_image":  ["4", 2],
                "n_steps":     n_steps,
                "image_scale": guidance_scale,
                "seed":        seed,
                "num_images":  1,
                "resolution":  resolution,
            },
        },
        "6": {
            "class_type": "SaveImage",
            "inputs": {
                "images":          ["5", 0],
                "filename_prefix": output_prefix,
            },
        },
    }


# ── Helpers ───────────────────────────────────────────────────────────────

def _sha256(path: Path, length: int = 12) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:length]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Single-run generator ──────────────────────────────────────────────────

def run_fitdit(
    crop_file: str,
    category: str,
    seed: int,
    dst: Path,
    with_offload: bool = False,
) -> None:
    """Run FitDiT for one garment/seed; save generated.png + manifest.json to dst/.

    Resumable: if dst/manifest.json already exists, returns immediately.
    """
    if (dst / "manifest.json").is_file():
        print(f"  already done: {dst.relative_to(ROOT)}")
        return

    dst.mkdir(parents=True, exist_ok=True)
    crop_path = CROPS / crop_file
    if not crop_path.is_file():
        raise FileNotFoundError(f"Garment crop not found: {crop_path}")

    from system.clients.comfyui import ComfyUIClient

    client = ComfyUIClient()
    person_ref = client.upload_image(PERSON)
    garm_ref   = client.upload_image(crop_path)

    outfit_id = json.loads(OUTFIT.read_text(encoding="utf-8"))["outfit_id"]
    prefix    = f"e010_{outfit_id}_fitdit_{category.lower().replace('-', '_')}_s{seed}"

    prompt = _fitdit_prompt(
        person_ref=person_ref,
        garm_ref=garm_ref,
        category=category,
        seed=seed,
        output_prefix=prefix,
        with_offload=with_offload,
        **FITDIT_CFG,
    )

    print(f"  submitting FitDiT: {category}, seed={seed}, {FITDIT_CFG['resolution']}")
    t0        = time.monotonic()
    prompt_id = client.submit(prompt)
    outputs   = client.poll(prompt_id, timeout=TIMEOUT)
    elapsed   = round(time.monotonic() - t0, 2)
    client.free()

    output_path = dst / "generated.png"
    for node_out in outputs.values():
        for img in node_out.get("images", []):
            if img.get("filename", "").startswith(prefix):
                output_path.write_bytes(
                    client.download(img["filename"],
                                    img.get("subfolder", ""),
                                    img.get("type", "output"))
                )
                break

    if not output_path.is_file():
        raise RuntimeError(f"No output image with prefix {prefix!r} in ComfyUI outputs")

    measurement = _measure(output_path, dst)

    manifest = {
        "run_id":      prefix,
        "created_utc": _now(),
        "engine":      "fitdit",
        "inputs": {
            "person":  {"path": str(PERSON),    "sha256": _sha256(PERSON)},
            "garment": {"path": str(crop_path), "sha256": _sha256(crop_path),
                        "category": category},
        },
        "params": {**FITDIT_CFG, "seed": seed, "with_offload": with_offload},
        "generation": {
            "comfyui_prompt_id": prompt_id,
            "seconds": elapsed,
            "output": {"path": str(output_path), "sha256": _sha256(output_path)},
        },
        "measurement": measurement,
    }
    (dst / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"  done in {elapsed}s -> {output_path.relative_to(ROOT)}")


def _measure(generated: Path, run_dir: Path) -> dict:
    """Identity gate (ArcFace). Color/FashionSigLIP/DISTS require calibration set."""
    try:
        from system.gates.identity import compare_faces
        ident = compare_faces(generated, PERSON)
        cosine = ident.get("cosine")
        identity = {
            **ident,
            "verdict": ("SKIP_DETECTION" if cosine is None
                        else "PASS" if cosine >= 0.57 else "FAIL"),
        }
    except Exception as e:
        identity = {"verdict": "ERROR", "error": str(e)}

    return {
        "identity": identity,
        "garment_fidelity": {
            "verdict": "PENDING_CALIBRATION",
            "note": ("FashionSigLIP retrieval-rank and DISTS require calibration set "
                     "(EVAL_INSTRUMENTS.md Layer 1-2). Owner visual verdict is primary for Phase 0."),
        },
    }


# ── Arm A copy from E-009 ─────────────────────────────────────────────────

def _ensure_arm_a() -> None:
    for seed in SEEDS:
        src = E009_RESULTS / ARM_A_E009_KEY / f"seed_{seed}"
        dst = RESULTS / ARM_A_LABEL / f"seed_{seed}"
        if (dst / "manifest.json").is_file():
            continue
        if not (src / "manifest.json").is_file():
            print(f"WARNING: E-009 arm A seed={seed} not at {src}")
            continue
        dst.mkdir(parents=True, exist_ok=True)
        for name in ("manifest.json", "generated.png", "report.md"):
            if (src / name).is_file():
                shutil.copy2(src / name, dst / name)
        print(f"  arm A seed={seed}: copied from E-009")


# ── Phase 0 ───────────────────────────────────────────────────────────────

def run_phase0(with_offload: bool = False) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    crop_file, category, label = GARMENTS[0]  # blouse: primary garment, hardest fidelity test
    seed = 42
    dst  = RESULTS / ARM_B_LABEL / f"{label}_seed{seed}"

    print(f"\n=== Phase 0 -- FitDiT {label} seed={seed} ===")
    run_fitdit(crop_file, category, seed, dst, with_offload=with_offload)

    print()
    print("OWNER CHECKPOINT -- Phase 0")
    print(f"  Generated: {(dst / 'generated.png').relative_to(ROOT)}")
    print(f"  Manifest:  {(dst / 'manifest.json').relative_to(ROOT)}")
    print()
    print("Review generated.png (STARTER.md garment-first acceptance):")
    print("  AXIS 1 (HARD GATE): lime blouse with buttons -- same item?")
    print("  AXIS 2: face/identity preserved?")
    print("  AXIS 3: body morphology acceptable?")
    print()
    print("Pass -> run --phase 1 (blouse+skirt, seeds 42+123).")
    print("Fail -> engine decision needed (see ENGINE_LANDSCAPE.md).")


# ── Phase 1 ───────────────────────────────────────────────────────────────

def run_phase1(with_offload: bool = False) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    _ensure_arm_a()
    for crop_file, category, label in GARMENTS:
        for seed in SEEDS:
            dst = RESULTS / ARM_B_LABEL / f"{label}_seed{seed}"
            print(f"\n=== arm B: {label} seed={seed} ===")
            run_fitdit(crop_file, category, seed, dst, with_offload=with_offload)
    build_table()


# ── Comparison table ──────────────────────────────────────────────────────

def _load_measurement(arm: str, key: str) -> dict:
    path = RESULTS / arm / key / "manifest.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("measurement", {})


def build_table() -> None:
    lines = [
        "# E-010 comparison: A (QIE Lightning) vs B (FitDiT garment-faithful try-on)",
        "",
        "Garment fidelity is the HARD gate. Body is secondary. Owner verdict per axis.",
        "",
        "## Identity (ArcFace cosine)",
        "| arm | item | seed | face cosine | verdict |",
        "|---|---|---|---|---|",
    ]
    for seed in SEEDS:
        m = _load_measurement(ARM_A_LABEL, f"seed_{seed}")
        ident = m.get("identity", {})
        lines.append(
            f"| {ARM_A_LABEL} | all | {seed} | {ident.get('cosine', '--')} | {ident.get('verdict', '--')} |"
        )
    for _, _, label in GARMENTS:
        for seed in SEEDS:
            m = _load_measurement(ARM_B_LABEL, f"{label}_seed{seed}")
            ident = m.get("identity", {})
            lines.append(
                f"| {ARM_B_LABEL} | {label} | {seed} | {ident.get('cosine', '--')} | {ident.get('verdict', '--')} |"
            )
    lines += [
        "",
        "## Garment fidelity",
        "FashionSigLIP retrieval-rank and DISTS: PENDING_CALIBRATION",
        "Build calibration set before these numbers are decision-grade.",
        "",
        "## Acceptance (STARTER.md)",
        "- Axis 1 HARD GATE: garment same item (owner per-item verdict)",
        "- Axis 2: identity cosine >= 0.57 and not below arm A",
        "- Axis 3: body reported, blocks only if grossly wrong",
    ]
    out = RESULTS / "comparison.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwritten: {out.relative_to(ROOT)}")


# ── CLI ───────────────────────────────────────────────────────────────────

def main() -> None:
    parser = ArgumentParser(description="E-010 FitDiT garment-faithful try-on runner")
    parser.add_argument("--phase", type=int, choices=(0, 1))
    parser.add_argument("--table", action="store_true")
    parser.add_argument("--offload", action="store_true",
                        help="enable FitDiT model CPU offload (use if VRAM OOM)")
    args = parser.parse_args()

    if args.table:
        build_table()
    elif args.phase == 0:
        run_phase0(with_offload=args.offload)
    elif args.phase == 1:
        run_phase1(with_offload=args.offload)
    else:
        parser.error("choose --phase 0, --phase 1, or --table")


if __name__ == "__main__":
    main()
