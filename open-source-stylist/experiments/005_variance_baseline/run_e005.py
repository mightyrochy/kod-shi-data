"""E-005 runner -- generation variance baseline.

Usage (from project root):
    python -m experiments.005_variance_baseline.run_e005 --phase 1
    python -m experiments.005_variance_baseline.run_e005 --phase 2

Phase 1: build reference panel + generate K=5 images + segment first output + overlays.
         Saves state to results/phase1_state.json; no interactive pauses.
Phase 2: segment remaining 4 outputs + compute all gates + save measurements.json.
         Reads state from results/phase1_state.json.

Between phases: review overlays in results/seed_42/ before running phase 2.

Configuration is frozen per protocol -- do not modify between runs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np

from system.clients.comfyui import ComfyUIClient
from system.adapter.adapter import _auto_resolution
from system.adapter.panel import build_panel
from system.adapter.prompt import build_prompt
from system.segmentation.grounded_sam import segment
from system.workflows import load_template, fill_workflow
from system.gates.color import compare_regions
from system.gates.identity import compare_faces
from system.gates.proportions import compare as compare_proportions

# ---------------------------------------------------------------------------
# Frozen configuration (per protocol -- do not change after first run)
# ---------------------------------------------------------------------------

SEEDS = [42, 123, 456, 789, 1337]
STEPS = 40

PERSON_IMAGE   = ROOT / "assets" / "person" / "person_front.png"
OUTFIT_PACKAGE = ROOT / "assets" / "outfits" / "outfit_001" / "outfit_package.json"
WORKFLOW_NAME  = "qie2511_vton"

RESULTS_DIR = Path(__file__).parent / "results"
PANELS_DIR  = RESULTS_DIR / "panels"
STATE_FILE  = RESULTS_DIR / "phase1_state.json"

# Segmentation prompts for generated images
GENERATED_PROMPTS = {
    "person":   "person",
    "face":     "face",
    "top":      "blouse . shirt . top",
    "bottom":   "skirt",
    "shoes":    "shoes . sandals . wedge",
    "belt":     "belt",
    "earrings": "earrings",
}

# E-001 reference masks reused for color comparison
E001 = ROOT / "experiments" / "001_segmentation_masks" / "results"
REGION_TO_REF = {
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

E001_PERSON_MASK = E001 / "person_front" / "person.png"

COLOR_PASS = 3.0
COLOR_FAIL = 5.0

OVERLAY_COLORS = [
    (80,  80,  255),  # top -- blue
    (80,  200, 80),   # bottom -- green
    (60,  220, 220),  # shoes -- cyan
    (40,  140, 255),  # belt -- orange
    (200, 80,  200),  # earrings -- purple
    (255, 80,  80),   # person -- red
    (255, 200, 60),   # face -- yellow
]

CLIENT = ComfyUIClient(host="localhost", port=8000)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_overlay(source_path: Path, masks: dict[str, str], out_path: Path) -> None:
    img = cv2.imread(str(source_path))
    if img is None:
        print(f"  [overlay] cannot read {source_path}")
        return
    overlay = img.copy().astype(np.float32)
    for i, (label, mask_path) in enumerate(masks.items()):
        m = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if m is None or m.max() == 0:
            print(f"  [overlay] {label}: empty/missing mask, skipping")
            continue
        m_r = cv2.resize(m, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
        fg = m_r > 127
        color = OVERLAY_COLORS[i % len(OVERLAY_COLORS)]
        for c in range(3):
            overlay[:, :, c][fg] = overlay[:, :, c][fg] * 0.5 + color[2 - c] * 0.5
    cv2.imwrite(str(out_path), overlay.astype(np.uint8))
    print(f"  overlay -> {out_path.relative_to(ROOT)}")


def color_verdict(delta_e: float | None) -> str:
    if delta_e is None:
        return "MASK_EMPTY"
    if delta_e <= COLOR_PASS:
        return "PASS"
    if delta_e <= COLOR_FAIL:
        return "WARN"
    return "FAIL"


# ---------------------------------------------------------------------------
# Phase 1: panel + generate + segment seed_42 + overlays
# ---------------------------------------------------------------------------

def run_phase1(outfit_package: dict) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1a. build reference panel (skip if already exists -- deterministic output)
    print("\n=== Phase 1a: reference panel (SAM) ===")
    panel_path = PANELS_DIR / "reference_panel.png"
    if panel_path.exists():
        print(f"  panel exists, reusing -> {panel_path.relative_to(ROOT)}")
    else:
        panel_path = build_panel(outfit_package, PANELS_DIR, CLIENT)
        print(f"  panel -> {panel_path.relative_to(ROOT)}")
        CLIENT.free()
        print("  /free done")

    # 1b. resolution
    width, height = _auto_resolution(PERSON_IMAGE)
    print(f"  resolution: {width}x{height}")

    # 1c. upload inputs
    print("\n=== Phase 1b: upload inputs ===")
    person_fn = CLIENT.upload_image(PERSON_IMAGE)
    panel_fn  = CLIENT.upload_image(panel_path)
    print(f"  person={person_fn}  panel={panel_fn}")

    # 1d. generate all K seeds
    prompt = build_prompt(outfit_package)
    template = load_template(WORKFLOW_NAME)
    generated: dict[str, str] = {}

    print("\n=== Phase 1c: generate (QIE-2511 40-step) ===")
    for seed in SEEDS:
        seed_dir = RESULTS_DIR / f"seed_{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        prefix = f"e005_s{seed}"
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
        print(f"  seed={seed} ...", end=" ", flush=True)
        pid = CLIENT.submit(wf)
        outputs = CLIENT.poll(pid, timeout=600.0)

        gen_path = None
        for node_out in outputs.values():
            for img_info in node_out.get("images", []):
                if img_info.get("filename", "").startswith(prefix):
                    data = CLIENT.download(img_info["filename"],
                                           img_info.get("subfolder", ""),
                                           img_info.get("type", "output"))
                    gen_path = seed_dir / "generated.png"
                    gen_path.write_bytes(data)
                    break
            if gen_path:
                break
        if gen_path is None:
            raise RuntimeError(f"No output for seed={seed}. Check ComfyUI logs.")
        generated[str(seed)] = str(gen_path)
        print(f"-> {gen_path.relative_to(ROOT)}")

    CLIENT.free()
    print("  /free done")

    # 1e. segment seed_42 + produce overlays for review
    first_seed = SEEDS[0]
    first_path = Path(generated[str(first_seed)])
    print(f"\n=== Phase 1d: segment seed={first_seed} for review ===")
    masks_dir = first_path.parent / "masks"
    masks = segment(first_path, GENERATED_PROMPTS, CLIENT, masks_dir)
    print(f"  masks: {list(masks.keys())}")

    make_overlay(first_path, masks, first_path.parent / "_overlay_all.png")
    for label, mpath in masks.items():
        make_overlay(first_path, {label: mpath}, first_path.parent / f"_overlay_{label}.png")

    CLIENT.free()
    print("  /free done")

    # save state for phase 2
    state = {
        "generated": generated,
        "seed_42_masks": {k: str(v) for k, v in masks.items()},
        "panel_path": str(panel_path),
        "width": width,
        "height": height,
    }
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"\n  state saved -> {STATE_FILE.relative_to(ROOT)}")

    print("\n" + "="*60)
    print("Phase 1 complete. Review overlays before running phase 2:")
    print(f"  Generated:  {first_path.relative_to(ROOT)}")
    print(f"  Overlay:    {(first_path.parent / '_overlay_all.png').relative_to(ROOT)}")
    print(f"  Per-region: {first_path.parent.relative_to(ROOT)}/_overlay_<label>.png")
    print()
    print("Core regions: person, face, background, top, bottom, shoes")
    print("If masks look correct -> run phase 2.")
    print("If a core region is broken -> investigate before phase 2.")
    print("="*60)


# ---------------------------------------------------------------------------
# Phase 2: segment remaining + compute all gates
# ---------------------------------------------------------------------------

def run_phase2() -> None:
    if not STATE_FILE.exists():
        sys.exit(f"State file not found: {STATE_FILE}\nRun phase 1 first.")

    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    generated = {int(k): Path(v) for k, v in state["generated"].items()}

    print("\n=== Phase 2a: segment remaining generated images (SAM) ===")
    all_masks: dict[int, dict[str, str]] = {}

    # restore seed_42 masks from state
    all_masks[SEEDS[0]] = state["seed_42_masks"]
    print(f"  seed={SEEDS[0]}: masks loaded from phase 1 state")

    for seed in SEEDS[1:]:
        gen_path = generated[seed]
        masks_dir = gen_path.parent / "masks"
        print(f"  seed={seed} ...", end=" ", flush=True)
        masks = segment(gen_path, GENERATED_PROMPTS, CLIENT, masks_dir)
        all_masks[seed] = masks
        print(f"{list(masks.keys())}")
        make_overlay(gen_path, masks, gen_path.parent / "_overlay_all.png")
        for label, mpath in masks.items():
            make_overlay(gen_path, {label: mpath}, gen_path.parent / f"_overlay_{label}.png")

    CLIENT.free()
    print("  /free done")

    # gates (CPU)
    print("\n=== Phase 2b: compute gates ===")
    measurements: dict[str, dict] = {}

    for seed in SEEDS:
        gen_path = generated[seed]
        masks = all_masks[seed]
        print(f"\n  seed={seed}")
        run_result: dict = {"seed": seed, "color": {}, "identity": {}, "proportions": {}}

        for region, (ref_img, ref_mask) in REGION_TO_REF.items():
            gen_mask_path = masks.get(region)
            if gen_mask_path is None:
                print(f"    [color] {region}: no mask")
                run_result["color"][region] = {"verdict": "MASK_MISSING"}
                continue
            result = compare_regions(gen_path, gen_mask_path, ref_img, ref_mask)
            verdict = color_verdict(result["delta_e_mean"])
            run_result["color"][region] = {**result, "verdict": verdict}
            warn_flag = " *** WARN ***" if verdict == "WARN" else ""
            print(f"    [color] {region}: dE={result['delta_e_mean']} -> {verdict}{warn_flag}")

        id_result = compare_faces(gen_path, PERSON_IMAGE)
        cosine = id_result.get("cosine")
        id_verdict = "PASS" if (cosine is not None and cosine >= 0.57) else "FAIL"
        run_result["identity"] = {**id_result, "verdict": id_verdict}
        print(f"    [identity] cosine={cosine} -> {id_verdict}")

        gen_person_mask = masks.get("person")
        if gen_person_mask and E001_PERSON_MASK.exists():
            prop_result = compare_proportions(E001_PERSON_MASK, gen_person_mask)
            score = prop_result.get("max_abs_change_pct", 0)
            prop_verdict = "PASS" if score <= 5.3 else "FAIL"
            run_result["proportions"] = {**prop_result, "verdict": prop_verdict}
            print(f"    [proportions] max_abs={score:.2f}% -> {prop_verdict}")
        else:
            run_result["proportions"] = {"verdict": "MASK_MISSING"}
            print(f"    [proportions] person mask missing")

        measurements[str(seed)] = run_result

    # save + report
    out_path = RESULTS_DIR / "measurements.json"
    out_path.write_text(json.dumps(measurements, indent=2), encoding="utf-8")
    print(f"\n  measurements -> {out_path.relative_to(ROOT)}")

    print("\n=== E-005 Summary ===\n")
    print("Color (CIEDE2000, provisional PASS<=3 WARN3-5 FAIL>5):")
    for region in REGION_TO_REF:
        vals = [measurements[str(s)]["color"].get(region, {}).get("delta_e_mean") for s in SEEDS]
        valid = [v for v in vals if v is not None]
        if valid:
            mu, sigma = np.mean(valid), np.std(valid)
            verdicts = [color_verdict(v) for v in vals]
            warns = [str(SEEDS[i]) for i, v in enumerate(verdicts) if v == "WARN"]
            fails = [str(SEEDS[i]) for i, v in enumerate(verdicts) if v == "FAIL"]
            extras = ("  *** WARN seeds " + str(warns) if warns else "") + \
                     ("  *** FAIL seeds " + str(fails) if fails else "")
            print(f"  {region:<12} dE={mu:.2f}+-{sigma:.2f}{extras}")
        else:
            print(f"  {region:<12} no data")

    cosines = [measurements[str(s)]["identity"].get("cosine") for s in SEEDS]
    valid_c = [c for c in cosines if c is not None]
    if valid_c:
        print(f"\nIdentity (provisional >=0.57):")
        print(f"  {[round(c,4) for c in valid_c]}")
        print(f"  mean={np.mean(valid_c):.4f}  min={min(valid_c):.4f}  max={max(valid_c):.4f}")

    scores = [measurements[str(s)]["proportions"].get("max_abs_change_pct") for s in SEEDS]
    valid_p = [p for p in scores if p is not None]
    if valid_p:
        print(f"\nProportions (provisional <=5.3%):")
        print(f"  {[round(p,2) for p in valid_p]}")
        print(f"  mean={np.mean(valid_p):.2f}%  max={max(valid_p):.2f}%")

    print("\nAll WARNs/FAILs require owner review before updating knowledge/verified.md.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E-005 variance baseline runner")
    parser.add_argument("--phase", type=int, choices=[1, 2], required=True,
                        help="1 = generate + first-image overlays; 2 = gates (after review)")
    args = parser.parse_args()

    if not PERSON_IMAGE.exists():
        sys.exit(f"Missing: {PERSON_IMAGE}")
    if not OUTFIT_PACKAGE.exists():
        sys.exit(f"Missing: {OUTFIT_PACKAGE}")

    outfit_package = json.loads(OUTFIT_PACKAGE.read_text(encoding="utf-8"))

    if args.phase == 1:
        run_phase1(outfit_package)
    else:
        run_phase2()
