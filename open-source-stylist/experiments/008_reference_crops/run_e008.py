"""E-008 runner — reference panel: cropped vs raw product photos.

Usage (from project root):
    python -m experiments.008_reference_crops.run_e008 --phase 1
    python -m experiments.008_reference_crops.run_e008 --phase 2

Phase 1: build raw panel → generate 5 seeds → segment seed_42 + overlays.
         Saves state to results/phase1_state.json.
         Checkpoint: review seed_42 overlays before phase 2.
Phase 2: segment remaining seeds → compute all gates → print comparison table
         (raw condition B vs E-005 cropped baseline condition A).

Configuration is frozen per protocol — do not modify between phases.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np
from PIL import Image

from system.adapter.prompt import build_prompt
from system.clients.comfyui import ComfyUIClient
from system.gates.color import compare_regions
from system.gates.identity import compare_faces
from system.gates.proportions import compare as compare_proportions
from system.segmentation.grounded_sam import segment
from system.segmentation.prompts import generated_prompts
from system.segmentation.sanity import check_all, format_report
from system.workflows import fill_workflow, load_template

# ---------------------------------------------------------------------------
# Frozen configuration (per protocol — do not change after first run)
# ---------------------------------------------------------------------------

SEEDS  = [42, 123, 456, 789, 1337]
STEPS  = 4          # Lightning 4-step
WIDTH  = 720
HEIGHT = 1024

PERSON_IMAGE   = ROOT / "assets/person/person_front.png"
OUTFIT_PACKAGE = ROOT / "assets/outfits/outfit_001/outfit_package.json"
WORKFLOW_NAME  = "qie2511_vton_lightning"

E005_MEASUREMENTS = ROOT / "experiments/005_variance_baseline/results/measurements.json"

RESULTS_DIR = Path(__file__).parent / "results"
STATE_FILE  = RESULTS_DIR / "phase1_state.json"
RAW_PANEL   = RESULTS_DIR / "raw_panel.png"

# E-001 reference images + masks for color gate (same as E-005/E-006)
E001 = ROOT / "experiments/001_segmentation_masks/results"
REGION_TO_REF: dict[str, tuple[Path, Path]] = {
    "top":      (ROOT / "assets/outfits/outfit_001/blouse_front.webp",
                 E001 / "outfit_001_blouse_front/blouse.png"),
    "bottom":   (ROOT / "assets/outfits/outfit_001/skirt_front.webp",
                 E001 / "outfit_001_skirt_front/skirt.png"),
    "shoes":    (ROOT / "assets/outfits/outfit_001/shoes_wedge.webp",
                 E001 / "outfit_001_shoes_wedge/shoes.png"),
    "belt":     (ROOT / "assets/outfits/outfit_001/belt.jpg",
                 E001 / "outfit_001_belt/belt.png"),
    "earrings": (ROOT / "assets/outfits/outfit_001/earrings_disc.webp",
                 E001 / "outfit_001_earrings_disc/earrings.png"),
}

E001_PERSON_MASK = E001 / "person_front/person.png"

# Segmentation prompts from canonical source (system/segmentation/prompts.py)
GENERATED_PROMPTS = generated_prompts(
    "person", "face", "top", "bottom", "shoes", "belt", "earrings"
)

COLOR_PASS     = 3.0
COLOR_FAIL     = 5.0
PROP_THRESHOLD = 5.3
ID_THRESHOLD   = 0.57

OVERLAY_COLORS = [
    (80,  80,  255),   # top
    (80,  200, 80),    # bottom
    (60,  220, 220),   # shoes
    (40,  140, 255),   # belt
    (200, 80,  200),   # earrings
    (255, 80,  80),    # person
    (255, 200, 60),    # face
]

CELL_SIZE = 256
MAX_COLS  = 3

CLIENT = ComfyUIClient(host="localhost", port=8000)


# ---------------------------------------------------------------------------
# Raw panel builder (no SAM — full product photos tiled)
# ---------------------------------------------------------------------------

def build_raw_panel(outfit_package: dict, out_path: Path) -> Path:
    """Tile full product photos into a grid (no garment-only cropping).

    Each reference image is resized to fit a CELL_SIZE×CELL_SIZE cell with
    white padding and no masking.  This is condition B — the uncropped baseline.
    """
    crops: list[Image.Image] = []
    for item in outfit_package["items"]:
        for ref_path_str in item["reference_image_paths"]:
            img = Image.open(ROOT / ref_path_str).convert("RGB")
            img.thumbnail((CELL_SIZE, CELL_SIZE), Image.LANCZOS)
            cell = Image.new("RGB", (CELL_SIZE, CELL_SIZE), (255, 255, 255))
            x = (CELL_SIZE - img.width) // 2
            y = (CELL_SIZE - img.height) // 2
            cell.paste(img, (x, y))
            crops.append(cell)

    n = len(crops)
    cols = min(n, MAX_COLS)
    rows = math.ceil(n / cols)
    panel = Image.new("RGB", (cols * CELL_SIZE, rows * CELL_SIZE), (255, 255, 255))
    for i, crop in enumerate(crops):
        row, col = divmod(i, cols)
        panel.paste(crop, (col * CELL_SIZE, row * CELL_SIZE))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    panel.save(out_path)
    print(f"  raw panel -> {out_path.relative_to(ROOT)}  ({n} cells, {cols}x{rows})")
    return out_path


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def make_overlay(source: Path, masks: dict[str, str], out: Path) -> None:
    img = cv2.imread(str(source))
    if img is None:
        return
    overlay = img.copy().astype(np.float32)
    for i, (label, mask_path) in enumerate(masks.items()):
        m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if m is None or m.max() == 0:
            continue
        m_r = cv2.resize(m, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
        fg = m_r > 127
        color = OVERLAY_COLORS[i % len(OVERLAY_COLORS)]
        for c in range(3):
            overlay[:, :, c][fg] = overlay[:, :, c][fg] * 0.5 + color[2 - c] * 0.5
    cv2.imwrite(str(out), overlay.astype(np.uint8))
    print(f"  overlay -> {out.relative_to(ROOT)}")


def save_overlays(gen_path: Path, masks: dict[str, str]) -> None:
    make_overlay(gen_path, masks, gen_path.parent / "_overlay_all.png")
    for label, mpath in masks.items():
        make_overlay(gen_path, {label: mpath}, gen_path.parent / f"_overlay_{label}.png")


def segment_and_guard(gen_path: Path, label_prefix: str) -> dict[str, str]:
    masks_dir = gen_path.parent / "masks"
    masks = segment(gen_path, GENERATED_PROMPTS, CLIENT, masks_dir)
    sanity = check_all(masks)
    flagged = {k: v for k, v in sanity.items() if not v.clean}
    if flagged:
        print(f"\n  *** SANITY FLAGS on {label_prefix} ***")
        print(f"  {format_report(sanity)}")
    else:
        print(f"  sanity guard: all clean")
    return masks


def color_verdict(de: float | None) -> str:
    if de is None:
        return "MASK_EMPTY"
    return "PASS" if de <= COLOR_PASS else ("WARN" if de <= COLOR_FAIL else "FAIL")


# ---------------------------------------------------------------------------
# Phase 1: build raw panel, generate, segment first seed
# ---------------------------------------------------------------------------

def run_phase1(outfit_package: dict, prompt: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("\n=== Build raw panel (condition B — no garment cropping) ===")
    build_raw_panel(outfit_package, RAW_PANEL)

    template = load_template(WORKFLOW_NAME)

    print("\n=== Upload inputs ===")
    person_fn = CLIENT.upload_image(PERSON_IMAGE)
    panel_fn  = CLIENT.upload_image(RAW_PANEL)
    print(f"  person={person_fn}  panel={panel_fn}")

    state: dict = {"seeds": {}}

    for seed in SEEDS:
        seed_dir = RESULTS_DIR / f"seed_{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        prefix = f"e008_s{seed}"

        wf = fill_workflow(template, {
            "__PERSON_IMAGE__":    person_fn,
            "__REF_IMAGE__":       panel_fn,
            "__POSITIVE_PROMPT__": prompt,
            "__SEED__":            seed,
            "__STEPS__":           STEPS,
            "__WIDTH__":           WIDTH,
            "__HEIGHT__":          HEIGHT,
            "__OUTPUT_PREFIX__":   prefix,
        })

        print(f"  seed={seed} ...", end=" ", flush=True)
        t0 = time.time()

        try:
            pid     = CLIENT.submit(wf)
            outputs = CLIENT.poll(pid, timeout=600.0)
        except Exception as exc:
            print(f"FAILED: {exc}")
            continue

        elapsed   = time.time() - t0
        gen_path  = None
        for node_out in outputs.values():
            for img_info in node_out.get("images", []):
                if img_info.get("filename", "").startswith(prefix):
                    data     = CLIENT.download(
                        img_info["filename"],
                        img_info.get("subfolder", ""),
                        img_info.get("type", "output"),
                    )
                    gen_path = seed_dir / "generated.png"
                    gen_path.write_bytes(data)
                    break
            if gen_path:
                break

        if gen_path is None:
            print(f"  no output image for seed={seed}")
            continue

        state["seeds"][str(seed)] = str(gen_path)
        print(f"done  {elapsed:.1f}s")

    CLIENT.free()
    print("  /free")

    if not state["seeds"]:
        sys.exit("Phase 1 produced no outputs — check ComfyUI.")

    # Segment first seed (seed_42) for checkpoint review
    first_seed = str(SEEDS[0])
    if first_seed in state["seeds"]:
        first_path = Path(state["seeds"][first_seed])
        print(f"\n  Segment seed={first_seed} for checkpoint review ...")
        masks = segment_and_guard(first_path, f"seed_{first_seed}")
        save_overlays(first_path, masks)
        CLIENT.free()
        print("  /free")

        sanity = check_all(masks)
        flagged = {k: v for k, v in sanity.items() if not v.clean}
        state["first_seed"] = first_seed
        state["first_seed_masks"] = masks
        state["first_seed_sanity_flags"] = {
            k: [{"check": f.check, "detail": f.detail} for f in r.flags]
            for k, r in flagged.items()
        }

    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"\n  state -> {STATE_FILE.relative_to(ROOT)}")

    print("\n" + "="*60)
    print("Phase 1 complete.")
    print(f"  Generated: {len(state['seeds'])}/5 seeds")
    print(f"  Review overlays at: experiments/008_reference_crops/results/seed_42/")
    flags = state.get("first_seed_sanity_flags", {})
    if flags:
        print(f"  *** {len(flags)} SANITY FLAG(S) on seed_42 — review before phase 2 ***")
        for region, fs in flags.items():
            for f in fs:
                print(f"    [{region}] {f['check']}: {f['detail']}")
    else:
        print("  sanity guard seed_42: all clean")
    print("\nReview seed_42 overlays. If clean — run phase 2.")
    print("="*60)


# ---------------------------------------------------------------------------
# Phase 2: segment remaining seeds, compute gates, compare vs E-005 baseline
# ---------------------------------------------------------------------------

def run_phase2() -> None:
    if not STATE_FILE.exists():
        sys.exit(f"State not found: {STATE_FILE}\nRun phase 1 first.")

    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    # Load E-005 baseline (condition A — cropped panel)
    if not E005_MEASUREMENTS.exists():
        sys.exit(f"E-005 measurements not found: {E005_MEASUREMENTS}")
    baseline_raw = json.loads(E005_MEASUREMENTS.read_text(encoding="utf-8"))
    print(f"E-005 baseline loaded ({len(baseline_raw)} seeds)")

    # Build masks dict — first seed from phase 1 state, rest fresh
    all_masks: dict[str, dict[str, str]] = {}
    first_seed = state.get("first_seed")
    if first_seed and "first_seed_masks" in state:
        all_masks[first_seed] = state["first_seed_masks"]

    remaining = [str(s) for s in SEEDS if str(s) != first_seed]
    print(f"  Segment {len(remaining)} remaining seeds ...")
    for seed_str in remaining:
        if seed_str not in state["seeds"]:
            print(f"  seed={seed_str}: no output (skipping)")
            continue
        gen_path = Path(state["seeds"][seed_str])
        print(f"  seed={seed_str} ...", end=" ", flush=True)
        masks = segment_and_guard(gen_path, f"seed_{seed_str}")
        save_overlays(gen_path, masks)
        all_masks[seed_str] = masks

    CLIENT.free()
    print("  /free")

    # Compute gates for condition B (raw)
    results_raw: dict[str, dict] = {}

    for seed_str, masks in all_masks.items():
        gen_path = Path(state["seeds"][seed_str])
        sr: dict = {"color": {}, "identity": {}, "proportions": {}}
        print(f"\n  seed={seed_str}")

        for region, (ref_img, ref_mask) in REGION_TO_REF.items():
            gen_mask = masks.get(region)
            if gen_mask is None:
                sr["color"][region] = {"delta_e_mean": None, "verdict": "MASK_MISSING"}
                print(f"    [color] {region}: MASK_MISSING")
                continue
            result  = compare_regions(gen_path, gen_mask, ref_img, ref_mask)
            verdict = color_verdict(result["delta_e_mean"])
            sr["color"][region] = {**result, "verdict": verdict}
            warn_tag = "  *** WARN ***" if verdict == "WARN" else ""
            print(f"    [color] {region}: dE={result['delta_e_mean']} -> {verdict}{warn_tag}")

        id_result  = compare_faces(gen_path, PERSON_IMAGE)
        cosine     = id_result.get("cosine")
        id_verdict = "PASS" if (cosine is not None and cosine >= ID_THRESHOLD) else "FAIL"
        sr["identity"] = {**id_result, "verdict": id_verdict}
        print(f"    [identity] cosine={cosine} -> {id_verdict}")

        person_mask = masks.get("person")
        if person_mask and E001_PERSON_MASK.exists():
            prop  = compare_proportions(E001_PERSON_MASK, person_mask)
            score = prop["max_abs_change_pct"]
            if score is None:
                raise RuntimeError(
                    f"Proportions gate returned max_abs_change_pct=None for "
                    f"seed={seed_str} — person mask may be empty."
                )
            prop_verdict = "PASS" if score <= PROP_THRESHOLD else "FAIL"
            sr["proportions"] = {**prop, "verdict": prop_verdict}
            print(f"    [proportions] max_abs={score:.2f}% -> {prop_verdict}")
        else:
            sr["proportions"] = {"verdict": "MASK_MISSING"}
            print("    [proportions]: MASK_MISSING")

        results_raw[seed_str] = sr

    out_path = RESULTS_DIR / "measurements.json"
    out_path.write_text(json.dumps(results_raw, indent=2), encoding="utf-8")
    print(f"\n  measurements -> {out_path.relative_to(ROOT)}")

    _print_comparison(results_raw, baseline_raw)


# ---------------------------------------------------------------------------
# Comparison table
# ---------------------------------------------------------------------------

def _extract_baseline(raw: dict) -> dict[str, dict]:
    """Return {seed_str: {identity_cosine, proportions_max_abs, color: {region: dE}}}."""
    result = {}
    for seed_str, meas in raw.items():
        result[seed_str] = {
            "identity_cosine":    meas.get("identity", {}).get("cosine"),
            "proportions_max_abs": meas.get("proportions", {}).get("max_abs_change_pct"),
            "color": {
                r: meas.get("color", {}).get(r, {}).get("delta_e_mean")
                for r in REGION_TO_REF
            },
        }
    return result


def _stats(vals: list[float | None]) -> tuple[float, float]:
    v = [x for x in vals if x is not None]
    if not v:
        return float("nan"), float("nan")
    return float(np.mean(v)), float(np.std(v))


def _print_comparison(raw_results: dict, baseline_raw: dict) -> None:
    baseline = _extract_baseline(baseline_raw)

    print("\n" + "="*72)
    print("E-008 — Comparison: Condition B (raw) vs Condition A (cropped, E-005)")
    print("="*72)

    # --- Identity ---
    b_cos = [v["identity_cosine"] for v in baseline.values()]
    r_cos = [v.get("identity", {}).get("cosine") for v in raw_results.values()]
    bm, bs = _stats(b_cos)
    rm, rs = _stats(r_cos)
    b_pass = sum(1 for x in b_cos if x is not None and x >= ID_THRESHOLD)
    r_pass = sum(1 for x in r_cos if x is not None and x >= ID_THRESHOLD)
    print(f"\nIdentity (ArcFace cosine, >=0.57 PASS):")
    print(f"  {'Condition':<32} {'mean':>8} {'std':>8} {'PASS/5':>8}")
    print(f"  {'A cropped (E-005 baseline)':<32} {bm:>8.4f} {bs:>8.4f} {b_pass:>8}")
    print(f"  {'B raw':<32} {rm:>8.4f} {rs:>8.4f} {r_pass:>8}")

    # --- Proportions ---
    b_prop = [v["proportions_max_abs"] for v in baseline.values()]
    r_prop = [v.get("proportions", {}).get("max_abs_change_pct") for v in raw_results.values()]
    bm, bs = _stats(b_prop)
    rm, rs = _stats(r_prop)
    b_fail = sum(1 for x in b_prop if x is not None and x > PROP_THRESHOLD)
    r_fail = sum(1 for x in r_prop if x is not None and x > PROP_THRESHOLD)
    threshold_line = 11.16 + 2 * 3.07  # baseline mean + 2*baseline_std (from protocol §4.2)
    print(f"\nProportions max_abs_change_pct (<=5.3% PASS; contamination threshold: {threshold_line:.1f}%):")
    print(f"  {'Condition':<32} {'mean':>8} {'std':>8} {'FAIL/5':>8}")
    print(f"  {'A cropped (E-005 baseline)':<32} {bm:>8.2f} {bs:>8.2f} {b_fail:>8}")
    print(f"  {'B raw':<32} {rm:>8.2f} {rs:>8.2f} {r_fail:>8}")
    if not np.isnan(rm):
        if rm > threshold_line:
            print(f"  -> raw > {threshold_line:.1f}% threshold: proportions CONTAMINATION CONFIRMED")
        elif rm > bm + 2 * bs:
            print(f"  -> raw within noise ({rm:.2f}% vs {bm:.2f}±{bs:.2f}%): proportions ambiguous")
        else:
            print(f"  -> raw within noise: H-REF-CONTAMINATION REFUTED for proportions")

    # --- Color per region ---
    print(f"\nColor dE (CIEDE2000, PASS<=3  WARN 3-5  FAIL>5):")
    print(f"  {'Region':<12} {'A mean':>8} {'A std':>8} {'B mean':>8} {'B std':>8}  verdict")
    for region in REGION_TO_REF:
        b_vals = [v["color"].get(region) for v in baseline.values()]
        r_vals = [v.get("color", {}).get(region, {}).get("delta_e_mean")
                  if isinstance(v.get("color", {}).get(region), dict)
                  else v.get("color", {}).get(region)
                  for v in raw_results.values()]
        bm, bs = _stats(b_vals)
        rm, rs = _stats(r_vals)
        if region == "shoes":
            # Protocol §4.2: contamination check for shoes
            if not np.isnan(rm):
                if rm > 18.0:
                    verdict = "raw WORSE (contamination plausible)"
                elif rm <= bm:
                    verdict = "raw NOT worse (contamination REFUTED)"
                else:
                    verdict = "inconclusive"
            else:
                verdict = "no data"
        else:
            verdict = ""
            if not np.isnan(rm) and not np.isnan(bm) and not np.isnan(bs):
                if rm > bm + bs:
                    verdict = "raw worse (flag)"
                elif rm < bm - bs:
                    verdict = "raw better"
        print(f"  {region:<12} {bm:>8.2f} {bs:>8.2f} {rm:>8.2f} {rs:>8.2f}  {verdict}")

    print("\nAll WARNs/FAILs require owner review.")
    print("Decision rule: protocol §4.2.")
    print("="*72)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E-008 reference-crops runner")
    parser.add_argument("--phase", type=int, choices=[1, 2],
                        help="1 = generate + first-seed overlays; 2 = gates + comparison")
    parser.add_argument("--summary", action="store_true",
                        help="Print comparison table from saved measurements.json (no GPU)")
    args = parser.parse_args()

    if args.summary:
        meas_path = RESULTS_DIR / "measurements.json"
        if not meas_path.exists():
            sys.exit(f"measurements.json not found: {meas_path}\nRun phase 2 first.")
        raw_results = json.loads(meas_path.read_text(encoding="utf-8"))
        baseline_raw = json.loads(E005_MEASUREMENTS.read_text(encoding="utf-8"))
        _print_comparison(raw_results, baseline_raw)
        sys.exit(0)

    if args.phase is None:
        parser.error("--phase or --summary required")

    for p in (PERSON_IMAGE, OUTFIT_PACKAGE, E001_PERSON_MASK):
        if not p.exists():
            sys.exit(f"Missing required file: {p}")

    outfit_package = json.loads(OUTFIT_PACKAGE.read_text(encoding="utf-8"))
    prompt         = build_prompt(outfit_package)

    if args.phase == 1:
        run_phase1(outfit_package, prompt)
    else:
        run_phase2()
