"""E-006 runner — resolution sensitivity.

Usage (from project root):
    python -m experiments.006_resolution.run_e006 --phase 1
    python -m experiments.006_resolution.run_e006 --phase 2

Phase 1: generate Low / High / High+ tiers (15 new images) + segment first seed
         of each tier + overlays. Saves state to results/phase1_state.json.
         High+ may OOM — recorded as a legitimate outcome, not retried.
Phase 2: segment remaining seeds + compute all gates + compare against E-005 baseline.

Between phases: review overlays for each tier's first seed.
Configuration is frozen per protocol — do not modify between runs.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np

from system.adapter.prompt import build_prompt
from system.clients.comfyui import ComfyUIClient
from system.gates.color import compare_regions
from system.gates.identity import compare_faces
from system.gates.proportions import compare as compare_proportions
from system.segmentation.grounded_sam import segment
from system.segmentation.sanity import check_all, format_report
from system.workflows import fill_workflow, load_template

# ---------------------------------------------------------------------------
# Frozen configuration (per protocol — do not change after first run)
# ---------------------------------------------------------------------------

SEEDS = [42, 123, 456, 789, 1337]
STEPS = 4  # Lightning 4-step

PERSON_IMAGE   = ROOT / "assets/person/person_front.png"
OUTFIT_PACKAGE = ROOT / "assets/outfits/outfit_001/outfit_package.json"
WORKFLOW_NAME  = "qie2511_vton_lightning"

# Reuse E-005 panel — reference panel is resolution-independent
E005_PANEL        = ROOT / "experiments/005_variance_baseline/results/panels/reference_panel.png"
E005_MEASUREMENTS = ROOT / "experiments/005_variance_baseline/results/measurements.json"

RESULTS_DIR = Path(__file__).parent / "results"
STATE_FILE  = RESULTS_DIR / "phase1_state.json"

# (name, width, height) — ordered Low → High → High+
TIERS = [
    ("low",       576,   816),
    ("high",      896,  1280),
    ("high_plus", 1120, 1600),
]

# E-001 reference images + masks for color gate
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

GENERATED_PROMPTS = {
    "person":   "person",
    "face":     "face",
    "top":      "shirt",
    "bottom":   "skirt",
    "shoes":    "footwear",
    "belt":     "belt",
    "earrings": "earrings",
}

COLOR_PASS      = 3.0
COLOR_FAIL      = 5.0
PROP_THRESHOLD  = 5.3
ID_THRESHOLD    = 0.57

OVERLAY_COLORS = [
    (80,  80,  255),   # top — blue
    (80,  200, 80),    # bottom — green
    (60,  220, 220),   # shoes — cyan
    (40,  140, 255),   # belt — orange
    (200, 80,  200),   # earrings — purple
    (255, 80,  80),    # person — red
    (255, 200, 60),    # face — yellow
]

CLIENT = ComfyUIClient(host="localhost", port=8000)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def vram_used_mb() -> int | None:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True, timeout=5,
        ).strip()
        return int(out.split("\n")[0].strip())
    except Exception:
        return None


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


def color_verdict(de: float | None) -> str:
    if de is None:
        return "MASK_EMPTY"
    return "PASS" if de <= COLOR_PASS else ("WARN" if de <= COLOR_FAIL else "FAIL")


def segment_and_guard(gen_path: Path, label_prefix: str) -> dict[str, str]:
    """Segment gen_path, run sanity guard, print any flags. Returns masks dict."""
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


# ---------------------------------------------------------------------------
# Phase 1: generate all tiers + first-seed overlays
# ---------------------------------------------------------------------------

def run_phase1(prompt: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not E005_PANEL.exists():
        sys.exit(f"E-005 panel missing: {E005_PANEL}\nRun E-005 phase 1 first.")

    template = load_template(WORKFLOW_NAME)

    print("\n=== Upload inputs (shared across tiers) ===")
    person_fn = CLIENT.upload_image(PERSON_IMAGE)
    panel_fn  = CLIENT.upload_image(E005_PANEL)
    print(f"  person={person_fn}  panel={panel_fn}")

    state: dict = {"tiers": {}}

    for tier_name, width, height in TIERS:
        print(f"\n{'='*60}")
        print(f"Tier: {tier_name}  {width}x{height}  ({width*height/1e6:.2f}MP)")
        print(f"{'='*60}")
        tier_dir = RESULTS_DIR / tier_name
        tier_dir.mkdir(parents=True, exist_ok=True)

        ts: dict = {
            "width": width, "height": height,
            "seeds": {},
            "oom": False,
            "vram_before_mb": [],
            "vram_after_mb": [],
            "times_s": [],
        }

        for seed in SEEDS:
            seed_dir = tier_dir / f"seed_{seed}"
            seed_dir.mkdir(parents=True, exist_ok=True)
            prefix = f"e006_{tier_name}_s{seed}"

            vram_before = vram_used_mb()
            ts["vram_before_mb"].append(vram_before)

            wf = fill_workflow(template, {
                "__PERSON_IMAGE__":    person_fn,
                "__REF_IMAGE__":       panel_fn,
                "__POSITIVE_PROMPT__": prompt,
                "__SEED__":            seed,
                "__STEPS__":           STEPS,
                "__WIDTH__":           width,
                "__HEIGHT__":          height,
                "__OUTPUT_PREFIX__":   prefix,
            })

            print(f"  seed={seed}  VRAM_before={vram_before}MB ...", end=" ", flush=True)
            t0 = time.time()

            try:
                pid = CLIENT.submit(wf)
                outputs = CLIENT.poll(pid, timeout=600.0)
            except Exception as exc:
                elapsed = time.time() - t0
                print(f"FAILED ({elapsed:.1f}s): {exc}")
                ts["oom"] = True
                ts["oom_error"] = str(exc)
                print(f"  OOM/error on {tier_name} — stopping this tier.")
                break

            elapsed = time.time() - t0
            vram_after = vram_used_mb()
            ts["vram_after_mb"].append(vram_after)
            ts["times_s"].append(round(elapsed, 1))

            gen_path = None
            for node_out in outputs.values():
                for img_info in node_out.get("images", []):
                    if img_info.get("filename", "").startswith(prefix):
                        data = CLIENT.download(
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
                print(f"  No output image for seed={seed}. Check ComfyUI logs.")
                ts["oom"] = True
                break

            ts["seeds"][str(seed)] = str(gen_path)
            print(f"done  {elapsed:.1f}s  VRAM_after={vram_after}MB")

        CLIENT.free()
        print(f"  /free")

        if not ts["seeds"]:
            state["tiers"][tier_name] = ts
            continue

        # Segment first successful seed for overlay review
        first_seed_str = next(iter(ts["seeds"]))
        first_path = Path(ts["seeds"][first_seed_str])
        print(f"\n  Segment seed={first_seed_str} for review ...")
        masks = segment_and_guard(first_path, f"{tier_name}/seed_{first_seed_str}")
        save_overlays(first_path, masks)
        CLIENT.free()

        sanity = check_all(masks)
        flagged = {k: v for k, v in sanity.items() if not v.clean}
        ts["first_seed"] = first_seed_str
        ts["first_seed_masks"] = {k: str(v) for k, v in masks.items()}
        ts["first_seed_sanity_flags"] = {
            k: [{"check": f.check, "detail": f.detail} for f in r.flags]
            for k, r in flagged.items()
        }
        state["tiers"][tier_name] = ts

    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"\n  state -> {STATE_FILE.relative_to(ROOT)}")

    print("\n" + "="*60)
    print("Phase 1 complete. Review overlays before phase 2.")
    for tier_name, width, height in TIERS:
        ts = state["tiers"].get(tier_name, {})
        if ts.get("oom"):
            print(f"  {tier_name}: OOM — {ts.get('oom_error', '')[:80]}")
        elif ts.get("first_seed"):
            fs = ts["first_seed"]
            fp = Path(ts["seeds"][fs]).relative_to(ROOT)
            flags = ts.get("first_seed_sanity_flags", {})
            flag_str = f"  *** {len(flags)} SANITY FLAG(S) ***" if flags else "  sanity clean"
            print(f"  {tier_name}/seed_{fs}: {fp}{flag_str}")
        else:
            print(f"  {tier_name}: no seeds generated")
    print("\nIf any sanity flags — review overlays and confirm before phase 2.")
    print("If overlays look correct — run phase 2.")
    print("="*60)


# ---------------------------------------------------------------------------
# Phase 2: segment remaining seeds + compute all gates
# ---------------------------------------------------------------------------

def run_phase2() -> None:
    if not STATE_FILE.exists():
        sys.exit(f"State not found: {STATE_FILE}\nRun phase 1 first.")

    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    # Load E-005 baseline
    baseline_raw: dict = {}
    if E005_MEASUREMENTS.exists():
        baseline_raw = json.loads(E005_MEASUREMENTS.read_text(encoding="utf-8"))
        print(f"E-005 baseline loaded ({len(baseline_raw)} seeds)")
    else:
        print(f"WARNING: E-005 measurements missing at {E005_MEASUREMENTS}")

    all_results: dict = {
        "baseline_720x1024": _load_baseline(baseline_raw),
        "tiers": {},
    }

    for tier_name, width, height in TIERS:
        ts = state["tiers"].get(tier_name, {})
        if not ts.get("seeds"):
            print(f"\n{tier_name}: no seeds (OOM or not generated), skipping.")
            all_results["tiers"][tier_name] = {
                "width": width, "height": height,
                "oom": ts.get("oom", False),
                "seeds": {},
            }
            continue

        print(f"\n{'='*60}")
        print(f"Gates: {tier_name}  {width}x{height}")
        print(f"{'='*60}")

        # Build masks dict — first seed from state, rest from fresh segmentation
        all_masks: dict[str, dict[str, str]] = {}
        first_seed_str = ts.get("first_seed")
        if first_seed_str:
            all_masks[first_seed_str] = ts["first_seed_masks"]

        remaining = [s for s in ts["seeds"] if s != first_seed_str]
        if remaining:
            print(f"  Segment {len(remaining)} remaining seeds ...")

        for seed_str in remaining:
            gen_path = Path(ts["seeds"][seed_str])
            print(f"  seed={seed_str} ...", end=" ", flush=True)
            masks = segment_and_guard(gen_path, f"{tier_name}/seed_{seed_str}")
            save_overlays(gen_path, masks)
            all_masks[seed_str] = masks

        CLIENT.free()
        print(f"  /free")

        # Compute gates for all seeds
        tier_results: dict = {
            "width": width, "height": height,
            "times_s": ts.get("times_s", []),
            "vram_after_mb": ts.get("vram_after_mb", []),
            "seeds": {},
        }

        for seed_str, masks in all_masks.items():
            gen_path = Path(ts["seeds"][seed_str])
            seed_result: dict = {"color": {}, "identity": {}, "proportions": {}}
            print(f"\n  seed={seed_str}")

            for region, (ref_img, ref_mask) in REGION_TO_REF.items():
                gen_mask = masks.get(region)
                if gen_mask is None:
                    seed_result["color"][region] = {"delta_e_mean": None, "verdict": "MASK_MISSING"}
                    print(f"    [color] {region}: MASK_MISSING")
                    continue
                result = compare_regions(gen_path, gen_mask, ref_img, ref_mask)
                verdict = color_verdict(result["delta_e_mean"])
                seed_result["color"][region] = {**result, "verdict": verdict}
                warn_tag = "  *** WARN ***" if verdict == "WARN" else ""
                print(f"    [color] {region}: dE={result['delta_e_mean']} -> {verdict}{warn_tag}")

            id_result = compare_faces(gen_path, PERSON_IMAGE)
            cosine = id_result.get("cosine")
            id_verdict = "PASS" if (cosine is not None and cosine >= ID_THRESHOLD) else "FAIL"
            seed_result["identity"] = {**id_result, "verdict": id_verdict}
            print(f"    [identity] cosine={cosine} -> {id_verdict}")

            person_mask = masks.get("person")
            if person_mask and E001_PERSON_MASK.exists():
                prop = compare_proportions(E001_PERSON_MASK, person_mask)
                score = prop["max_abs_change_pct"]
                if score is None:
                    raise RuntimeError(
                        f"Proportions gate returned max_abs_change_pct=None for "
                        f"{tier_name}/seed={seed_str} — person mask may be empty."
                    )
                prop_verdict = "PASS" if score <= PROP_THRESHOLD else "FAIL"
                seed_result["proportions"] = {**prop, "verdict": prop_verdict}
                print(f"    [proportions] max_abs={score:.2f}% -> {prop_verdict}")
            else:
                seed_result["proportions"] = {"verdict": "MASK_MISSING"}
                print(f"    [proportions]: MASK_MISSING")

            tier_results["seeds"][seed_str] = seed_result

        all_results["tiers"][tier_name] = tier_results

    out_path = RESULTS_DIR / "measurements.json"
    out_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"\n  measurements -> {out_path.relative_to(ROOT)}")

    _print_summary(all_results)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def _load_baseline(raw: dict) -> dict:
    result = {}
    for seed_str, meas in raw.items():
        result[seed_str] = {
            "identity_cosine": meas.get("identity", {}).get("cosine"),
            "proportions_max_abs": meas.get("proportions", {}).get("max_abs_change_pct"),
            "color": {
                r: meas.get("color", {}).get(r, {}).get("delta_e_mean")
                for r in REGION_TO_REF
            },
        }
    return result


def _identity_values(results: dict, tier_key: str) -> list[float]:
    if tier_key == "baseline":
        return [v["identity_cosine"] for v in results["baseline_720x1024"].values()
                if v.get("identity_cosine") is not None]
    tr = results["tiers"].get(tier_key, {})
    return [s["identity"].get("cosine") for s in tr.get("seeds", {}).values()
            if s.get("identity", {}).get("cosine") is not None]


def _color_values(results: dict, tier_key: str, region: str) -> list[float]:
    if tier_key == "baseline":
        return [v["color"].get(region) for v in results["baseline_720x1024"].values()
                if v.get("color", {}).get(region) is not None]
    tr = results["tiers"].get(tier_key, {})
    return [s["color"].get(region, {}).get("delta_e_mean")
            for s in tr.get("seeds", {}).values()
            if s.get("color", {}).get(region, {}).get("delta_e_mean") is not None]


def _prop_values(results: dict, tier_key: str) -> list[float]:
    if tier_key == "baseline":
        return [v["proportions_max_abs"] for v in results["baseline_720x1024"].values()
                if v.get("proportions_max_abs") is not None]
    tr = results["tiers"].get(tier_key, {})
    return [s["proportions"].get("max_abs_change_pct")
            for s in tr.get("seeds", {}).values()
            if s.get("proportions", {}).get("max_abs_change_pct") is not None]


def _print_summary(results: dict) -> None:
    print("\n" + "="*70)
    print("E-006 -- Resolution sensitivity summary")
    print("="*70)

    # Row definitions: (display_name, tier_key, width, height)
    rows = [("baseline_720x1024", "baseline", 720, 1024)]
    for tier_name, w, h in TIERS:
        rows.append((f"{tier_name}_{w}x{h}", tier_name, w, h))

    def _oom(tier_key: str) -> bool:
        if tier_key == "baseline":
            return False
        return results["tiers"].get(tier_key, {}).get("oom", False)

    # Identity
    print(f"\nIdentity (ArcFace cosine, >=0.57 PASS):")
    print(f"  {'Tier':<26} {'mean':>8} {'std':>8} {'min':>8} {'max':>8}")
    for label, tier_key, w, h in rows:
        if _oom(tier_key):
            print(f"  {label:<26} OOM")
            continue
        vals = _identity_values(results, tier_key)
        if not vals:
            continue
        print(f"  {label:<26} {np.mean(vals):>8.4f} {np.std(vals):>8.4f}"
              f" {min(vals):>8.4f} {max(vals):>8.4f}")

    # Color per region
    for region in REGION_TO_REF:
        print(f"\nColor dE -- {region} (PASS<=3  WARN 3-5  FAIL>5):")
        print(f"  {'Tier':<26} {'mean':>8} {'std':>8} {'P/W/F':>10}")
        for label, tier_key, w, h in rows:
            if _oom(tier_key):
                print(f"  {label:<26} OOM")
                continue
            vals = _color_values(results, tier_key, region)
            if not vals:
                continue
            verdicts = [color_verdict(v) for v in vals]
            pvwf = (f"P:{verdicts.count('PASS')}"
                    f" W:{verdicts.count('WARN')}"
                    f" F:{verdicts.count('FAIL')}")
            print(f"  {label:<26} {np.mean(vals):>8.2f} {np.std(vals):>8.2f} {pvwf:>10}")

    # Proportions
    print(f"\nProportions max_abs_change_pct (<=5.3% PASS):")
    print(f"  {'Tier':<26} {'mean':>8} {'std':>8} {'max':>8}")
    for label, tier_key, w, h in rows:
        if _oom(tier_key):
            print(f"  {label:<26} OOM")
            continue
        vals = _prop_values(results, tier_key)
        if not vals:
            continue
        print(f"  {label:<26} {np.mean(vals):>8.2f} {np.std(vals):>8.2f} {max(vals):>8.2f}")

    # Timing
    print(f"\nGeneration time per image (seconds):")
    print(f"  {'Tier':<26} {'mean':>8} {'min':>8} {'max':>8}")
    for label, tier_key, w, h in rows:
        if tier_key == "baseline":
            print(f"  {label:<26} (E-005 — not re-timed)")
            continue
        if _oom(tier_key):
            print(f"  {label:<26} OOM")
            continue
        tr = results["tiers"].get(tier_key, {})
        times = tr.get("times_s", [])
        if not times:
            continue
        print(f"  {label:<26} {np.mean(times):>8.1f} {min(times):>8.1f} {max(times):>8.1f}")

    # VRAM
    print(f"\nPeak VRAM after generation (MB):")
    print(f"  {'Tier':<26} {'peak':>8} {'all readings':}")
    for label, tier_key, w, h in rows:
        if tier_key == "baseline":
            print(f"  {label:<26} (not recorded in E-005)")
            continue
        if _oom(tier_key):
            print(f"  {label:<26} OOM")
            continue
        tr = results["tiers"].get(tier_key, {})
        vrams = [v for v in tr.get("vram_after_mb", []) if v is not None]
        if not vrams:
            continue
        print(f"  {label:<26} {max(vrams):>8}   {vrams}")

    print("\nAll WARNs/FAILs require owner review.")
    print("Resolution choice rule: protocol §4.2.")
    print("="*70)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E-006 resolution sensitivity runner")
    parser.add_argument("--phase", type=int, choices=[1, 2],
                        help="1 = generate + first-seed overlays; 2 = gates (after review)")
    parser.add_argument("--summary", action="store_true",
                        help="Print summary table from saved measurements.json (no GPU)")
    args = parser.parse_args()

    if args.summary:
        meas_path = RESULTS_DIR / "measurements.json"
        if not meas_path.exists():
            sys.exit(f"measurements.json not found: {meas_path}\nRun phase 2 first.")
        _print_summary(json.loads(meas_path.read_text(encoding="utf-8")))
        sys.exit(0)

    if args.phase is None:
        parser.error("--phase or --summary required")

    if not PERSON_IMAGE.exists():
        sys.exit(f"Missing: {PERSON_IMAGE}")
    if not OUTFIT_PACKAGE.exists():
        sys.exit(f"Missing: {OUTFIT_PACKAGE}")

    outfit_package = json.loads(OUTFIT_PACKAGE.read_text(encoding="utf-8"))
    prompt = build_prompt(outfit_package)

    if args.phase == 1:
        run_phase1(prompt)
    else:
        run_phase2()
