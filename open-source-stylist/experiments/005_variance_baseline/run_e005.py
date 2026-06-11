"""E-005 runner — generation variance baseline.

Usage (from project root):
    python -m experiments.005_variance_baseline.run_e005

Two-phase execution:
  Phase 1: build reference panel + generate K=5 images
  Phase 2: (after owner review pause) segment generated images + compute gates

Configuration is frozen per protocol — do not modify between runs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np

from system.clients.comfyui import ComfyUIClient
from system.adapter.adapter import build_generation_request, _auto_resolution
from system.adapter.panel import build_panel
from system.segmentation.grounded_sam import segment
from system.workflows import load_template, fill_workflow
from system.gates.color import compare_regions
from system.gates.identity import compare_faces
from system.gates.proportions import compare as compare_proportions

# ---------------------------------------------------------------------------
# Frozen configuration (per protocol — do not change after first run)
# ---------------------------------------------------------------------------

SEEDS = [42, 123, 456, 789, 1337]
STEPS = 40
ENGINE = "qie-2511"

PERSON_IMAGE = ROOT / "assets" / "person" / "person_front.png"
OUTFIT_PACKAGE = ROOT / "assets" / "outfits" / "outfit_001" / "outfit_package.json"
WORKFLOW_NAME = "qie2511_vton"

RESULTS_DIR = Path(__file__).parent / "results"
PANELS_DIR = RESULTS_DIR / "panels"

# Segmentation prompts for the generated image
GENERATED_PROMPTS = {
    "person":   "person",
    "face":     "face",
    "top":      "blouse . shirt . top",
    "bottom":   "skirt",
    "shoes":    "shoes . sandals . wedge",
    "belt":     "belt",
    "earrings": "earrings",
}

# E-001 reference masks reused for color comparison (garment images → masks)
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

# Person mask from E-001 for proportions baseline
E001_PERSON_MASK = E001 / "person_front" / "person.png"

# Color gate thresholds (provisional — this experiment finalises them)
COLOR_PASS = 3.0
COLOR_FAIL = 5.0

# Overlay colours per region (BGR)
OVERLAY_COLORS = [
    (80,  80,  255),   # top — blue
    (80,  200, 80),    # bottom — green
    (60,  220, 220),   # shoes — cyan
    (40,  140, 255),   # belt — orange
    (200, 80,  200),   # earrings — purple
    (80,  80,  255),   # person — (fallback)
    (255, 200, 60),    # face — yellow
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
            print(f"  [overlay] {label}: empty or missing mask, skipping")
            continue
        m_r = cv2.resize(m, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
        fg = m_r > 127
        color = OVERLAY_COLORS[i % len(OVERLAY_COLORS)]
        for c in range(3):
            overlay[:, :, c][fg] = overlay[:, :, c][fg] * 0.5 + color[2 - c] * 0.5
    cv2.imwrite(str(out_path), overlay.astype(np.uint8))
    print(f"  overlay saved → {out_path.relative_to(ROOT)}")


def color_verdict(delta_e: float | None) -> str:
    if delta_e is None:
        return "MASK_EMPTY"
    if delta_e <= COLOR_PASS:
        return "PASS"
    if delta_e <= COLOR_FAIL:
        return "WARN"
    return "FAIL"


# ---------------------------------------------------------------------------
# Phase 1: build panel + generate all K images
# ---------------------------------------------------------------------------

def phase1_generate(outfit_package: dict) -> dict[int, Path]:
    """Generate K images.  Returns {seed: path_to_generated_png}."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # --- 1a. build reference panel (SAM active) ---
    print("\n=== Phase 1a: building reference panel ===")
    panel_path = build_panel(outfit_package, PANELS_DIR, CLIENT)
    print(f"  panel saved → {panel_path.relative_to(ROOT)}")

    print("  POST /free (unload SAM/GDINO)")
    CLIENT.free()

    # --- 1b. determine resolution from person image ---
    width, height = _auto_resolution(PERSON_IMAGE)
    print(f"  resolution: {width}×{height}")

    # --- 1c. upload static inputs once ---
    print("\n=== Phase 1b: uploading inputs to ComfyUI ===")
    person_fn = CLIENT.upload_image(PERSON_IMAGE)
    panel_fn  = CLIENT.upload_image(panel_path)
    print(f"  person: {person_fn}, panel: {panel_fn}")

    # --- 1d. generate all K seeds ---
    template = load_template(WORKFLOW_NAME)
    generated: dict[int, Path] = {}

    print("\n=== Phase 1c: generating (QIE-2511 full, 40 steps) ===")
    for seed in SEEDS:
        seed_dir = RESULTS_DIR / f"seed_{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        prefix = f"e005_s{seed}"

        wf = fill_workflow(template, {
            "__PERSON_IMAGE__":   person_fn,
            "__REF_IMAGE__":      panel_fn,
            "__POSITIVE_PROMPT__": build_prompt(outfit_package),
            "__SEED__":            seed,
            "__STEPS__":           STEPS,
            "__WIDTH__":           width,
            "__HEIGHT__":          height,
            "__OUTPUT_PREFIX__":   prefix,
        })

        print(f"  seed={seed} ...", end=" ", flush=True)
        prompt_id = CLIENT.submit(wf)
        outputs = CLIENT.poll(prompt_id, timeout=600.0)

        # find output image
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
            raise RuntimeError(f"No output image for seed={seed}. Check ComfyUI logs.")
        print(f"saved → {gen_path.relative_to(ROOT)}")
        generated[seed] = gen_path

    print("\n  POST /free (unload QIE-2511)")
    CLIENT.free()
    return generated


def build_prompt(outfit_package: dict) -> str:
    from system.adapter.prompt import build_prompt as _bp
    return _bp(outfit_package)


# ---------------------------------------------------------------------------
# Phase 2: segment + overlay (first image) + owner review pause
# ---------------------------------------------------------------------------

def phase2_review(generated: dict[int, Path]) -> dict[int, dict[str, str]]:
    """Segment all generated images.  Pauses after first for owner review."""
    all_masks: dict[int, dict[str, str]] = {}

    print("\n=== Phase 2a: segmenting generated outputs (SAM active) ===")
    for i, seed in enumerate(SEEDS):
        gen_path = generated[seed]
        masks_dir = gen_path.parent / "masks"
        print(f"  seed={seed} segmenting ...", end=" ", flush=True)
        masks = segment(gen_path, GENERATED_PROMPTS, CLIENT, masks_dir)
        all_masks[seed] = masks
        print(f"{list(masks.keys())}")

        # produce individual overlays
        make_overlay(gen_path, masks, gen_path.parent / "_overlay_all.png")
        for label, mpath in masks.items():
            make_overlay(gen_path, {label: mpath}, gen_path.parent / f"_overlay_{label}.png")

        if i == 0:
            print(f"\n{'='*60}")
            print("OWNER REVIEW REQUIRED (E-005 protocol carry-over from E-001)")
            print("E-001 validated segmentation on real photos only.")
            print("Review the generated image and its mask overlays:")
            print(f"  Image:    {gen_path.relative_to(ROOT)}")
            print(f"  Overlays: {gen_path.parent.relative_to(ROOT)}/")
            print()
            print("Core regions to check: person, face, background, top, bottom, shoes")
            print("If any core region mask looks wrong, Ctrl+C to stop and investigate.")
            print()
            resp = input("Type OK to continue with remaining generations and gate computation: ").strip().upper()
            if resp != "OK":
                print("Aborted by user.")
                sys.exit(0)
            print(f"{'='*60}\n")

    print("\n  POST /free (unload SAM/GDINO)")
    CLIENT.free()
    return all_masks


# ---------------------------------------------------------------------------
# Phase 3: compute gates
# ---------------------------------------------------------------------------

def compute_all_gates(generated: dict[int, Path], all_masks: dict[int, dict[str, str]]) -> dict:
    print("\n=== Phase 3: computing gates (CPU) ===")
    measurements: dict[str, dict] = {}

    for seed in SEEDS:
        gen_path = generated[seed]
        masks = all_masks[seed]
        print(f"\n  seed={seed}")
        run_result: dict = {"seed": seed, "color": {}, "identity": {}, "proportions": {}}

        # -- color gate per region --
        for region, (ref_img, ref_mask) in REGION_TO_REF.items():
            gen_mask_path = masks.get(region)
            if gen_mask_path is None:
                print(f"    [color] {region}: no mask produced")
                run_result["color"][region] = {"verdict": "MASK_MISSING"}
                continue

            result = compare_regions(gen_path, gen_mask_path, ref_img, ref_mask)
            verdict = color_verdict(result["delta_e_mean"])
            run_result["color"][region] = {**result, "verdict": verdict}
            marker = "*** WARN ***" if verdict == "WARN" else verdict
            print(f"    [color] {region}: dE={result['delta_e_mean']} → {marker}")

        # -- identity gate --
        id_result = compare_faces(gen_path, PERSON_IMAGE)
        cosine = id_result.get("cosine")
        id_verdict = "PASS" if (cosine is not None and cosine >= 0.57) else "FAIL"
        run_result["identity"] = {**id_result, "verdict": id_verdict}
        print(f"    [identity] cosine={cosine} → {id_verdict}")

        # -- proportions gate --
        gen_person_mask = masks.get("person")
        if gen_person_mask and E001_PERSON_MASK.exists():
            prop_result = compare_proportions(E001_PERSON_MASK, gen_person_mask)
            score = prop_result.get("max_abs_change_pct", 0)
            prop_verdict = "PASS" if score <= 5.3 else "FAIL"
            run_result["proportions"] = {**prop_result, "verdict": prop_verdict}
            print(f"    [proportions] max_abs={score:.2f}% → {prop_verdict}")
        else:
            run_result["proportions"] = {"verdict": "MASK_MISSING"}
            print(f"    [proportions] person mask missing")

        measurements[str(seed)] = run_result

    return measurements


# ---------------------------------------------------------------------------
# Phase 4: summarise + save
# ---------------------------------------------------------------------------

def save_and_report(measurements: dict) -> None:
    out_path = RESULTS_DIR / "measurements.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(measurements, fh, indent=2)
    print(f"\n  measurements saved → {out_path.relative_to(ROOT)}")

    print("\n=== E-005 Summary ===\n")

    # Color: per-region variance across seeds
    print("Color (dE mean ± std per region, provisional thresholds PASS≤3 WARN3-5 FAIL>5):")
    color_regions = list(REGION_TO_REF.keys())
    for region in color_regions:
        vals = [measurements[str(s)]["color"].get(region, {}).get("delta_e_mean")
                for s in SEEDS]
        valid = [v for v in vals if v is not None]
        if valid:
            mu = np.mean(valid)
            sigma = np.std(valid)
            verdicts = [color_verdict(v) for v in vals]
            warns = [str(SEEDS[i]) for i, v in enumerate(verdicts) if v == "WARN"]
            fails = [str(SEEDS[i]) for i, v in enumerate(verdicts) if v == "FAIL"]
            warn_note = f"  *** WARN seeds: {warns}" if warns else ""
            fail_note = f"  *** FAIL seeds: {fails}" if fails else ""
            print(f"  {region:<12} dE={mu:.2f}±{sigma:.2f} {warn_note}{fail_note}")
        else:
            print(f"  {region:<12} no data")

    # Identity
    cosines = [measurements[str(s)]["identity"].get("cosine") for s in SEEDS]
    valid_c = [c for c in cosines if c is not None]
    if valid_c:
        print(f"\nIdentity (ArcFace cosine, provisional threshold 0.57):")
        print(f"  cosine = {[round(c,4) for c in valid_c]}")
        print(f"  mean={np.mean(valid_c):.4f}  min={min(valid_c):.4f}  max={max(valid_c):.4f}")

    # Proportions
    scores = [measurements[str(s)]["proportions"].get("max_abs_change_pct")
              for s in SEEDS]
    valid_p = [p for p in scores if p is not None]
    if valid_p:
        print(f"\nProportions (max_abs_change_pct, provisional threshold 5.3%):")
        print(f"  scores = {[round(p,2) for p in valid_p]}")
        print(f"  mean={np.mean(valid_p):.2f}%  max={max(valid_p):.2f}%")

    print("\n(WARN and FAIL values require owner review before threshold revision.)")
    print("Write results to experiments/005_variance_baseline/results/segmentation_review.md")
    print("then document threshold decisions in knowledge/verified.md.\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not PERSON_IMAGE.exists():
        sys.exit(f"Person image not found: {PERSON_IMAGE}")
    if not OUTFIT_PACKAGE.exists():
        sys.exit(f"Outfit package not found: {OUTFIT_PACKAGE}")

    # Guard: warn if results already exist
    existing = list(RESULTS_DIR.glob("seed_*/generated.png"))
    if existing:
        print(f"WARNING: {len(existing)} generated images already in {RESULTS_DIR}")
        resp = input("Results exist. Overwrite? (yes/no): ").strip().lower()
        if resp != "yes":
            print("Aborted."); sys.exit(0)

    outfit_package = json.loads(OUTFIT_PACKAGE.read_text(encoding="utf-8"))

    generated   = phase1_generate(outfit_package)
    all_masks   = phase2_review(generated)
    measurements = compute_all_gates(generated, all_masks)
    save_and_report(measurements)
