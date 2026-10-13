"""E-007 v2: frozen masked-crop board vs frozen rectangular-crop board.

Phase 1 generates paired outputs. Phase 2 segments and measures them. Board
files are never rebuilt here; their SHA-256 values are checked by the adapter.

The hybrid supplement is stored separately because both its board and layout
text differ from the original A/B. It can be compared as a complete input
candidate, but it does not isolate which of those two changes caused a result.

    python -m experiments.007_task_correct_adapter.run_e007 --phase 1
    python -m experiments.007_task_correct_adapter.run_e007 --phase 2
    python -m experiments.007_task_correct_adapter.run_e007 --summary
    python -m experiments.007_task_correct_adapter.run_e007 --hybrid-phase 1
    python -m experiments.007_task_correct_adapter.run_e007 --hybrid-phase 2
    python -m experiments.007_task_correct_adapter.run_e007 --hybrid-summary
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from system.adapter.adapter import build_generation_request
from system.adapter.panel import file_sha256
from system.adapter.prompt import build_prompt
from system.clients.comfyui import ComfyUIClient
from system.gates.color import compare_regions
from system.gates.identity import compare_faces
from system.gates.proportions import compare as compare_proportions
from system.segmentation.grounded_sam import segment
from system.segmentation.prompts import generated_prompts
from system.segmentation.sanity import check_all
from system.workflows import fill_workflow, load_template


ARMS = ("masked_crops", "rectangular_crops")
HYBRID_ARM = "hybrid_mask_crop"
COMPARISON_ARMS = (*ARMS, HYBRID_ARM)
SEEDS = (42, 123, 456, 789, 1337)
STEPS = 4
WIDTH = 720
HEIGHT = 1024
WORKFLOW_NAME = "qie2511_vton_lightning"

PERSON_IMAGE = ROOT / "assets/person/person_front.png"
OUTFIT_PACKAGE = ROOT / "assets/outfits/outfit_001/outfit_package.json"
E001 = ROOT / "experiments/001_segmentation_masks/results"
SOURCE_PERSON_MASK = E001 / "person_front/person.png"
RESULTS_DIR = Path(__file__).parent / "results"
STATE_FILE = RESULTS_DIR / "phase1_state.json"
MEASUREMENTS_FILE = RESULTS_DIR / "measurements.json"
HYBRID_STATE_FILE = RESULTS_DIR / "hybrid_phase1_state.json"
HYBRID_MEASUREMENTS_FILE = RESULTS_DIR / "hybrid_measurements.json"
THREE_WAY_SHEET = RESULTS_DIR / "three_way_contact_sheet.png"
THREE_WAY_OVERLAYS = RESULTS_DIR / "three_way_mask_overlays.png"

REGION_TO_REFERENCE = {
    "top": (ROOT / "assets/outfits/outfit_001/blouse_front.webp", E001 / "outfit_001_blouse_front/blouse.png"),
    "bottom": (ROOT / "assets/outfits/outfit_001/skirt_front.webp", E001 / "outfit_001_skirt_front/skirt.png"),
    "shoes": (ROOT / "assets/outfits/outfit_001/shoes_wedge.webp", E001 / "outfit_001_shoes_wedge/shoes.png"),
    "belt": (ROOT / "assets/outfits/outfit_001/belt.jpg", E001 / "outfit_001_belt/belt.png"),
    "earrings": (ROOT / "assets/outfits/outfit_001/earrings_disc.webp", E001 / "outfit_001_earrings_disc/earrings.png"),
}
GENERATED_PROMPTS = generated_prompts("person", "face", "top", "bottom", "shoes", "belt", "earrings")

COLOR_PASS = 3.0
COLOR_FAIL = 5.0
IDENTITY_THRESHOLD = 0.57
PROPORTIONS_THRESHOLD = 5.3

CLIENT = ComfyUIClient("localhost", 8000)


def _load_package() -> dict:
    return json.loads(OUTFIT_PACKAGE.read_text(encoding="utf-8"))


def _download_output(outputs: dict, prefix: str, destination: Path) -> None:
    for node_output in outputs.values():
        for image_info in node_output.get("images", []):
            if image_info.get("filename", "").startswith(prefix):
                data = CLIENT.download(
                    image_info["filename"],
                    image_info.get("subfolder", ""),
                    image_info.get("type", "output"),
                )
                destination.write_bytes(data)
                return
    raise RuntimeError(f"ComfyUI produced no image with prefix {prefix!r}")


def _fixed_record() -> dict:
    return {
        "seeds": list(SEEDS),
        "steps": STEPS,
        "width": WIDTH,
        "height": HEIGHT,
        "workflow": WORKFLOW_NAME,
        "workflow_sha256": file_sha256(ROOT / "system/workflows" / f"{WORKFLOW_NAME}.json"),
        "person_sha256": file_sha256(PERSON_IMAGE),
    }


def _measurement_input_record() -> dict:
    return {
        "source_person_mask": file_sha256(SOURCE_PERSON_MASK),
        "regions": {
            region: {
                "image_sha256": file_sha256(image_path),
                "mask_sha256": file_sha256(mask_path),
            }
            for region, (image_path, mask_path) in REGION_TO_REFERENCE.items()
        },
    }


def run_phase1() -> None:
    if STATE_FILE.exists():
        raise FileExistsError(
            f"E-007 phase 1 state already exists: {STATE_FILE}. "
            "Refusing to overwrite an experimental record."
        )

    package = _load_package()
    prompt = build_prompt(package)
    template = load_template(WORKFLOW_NAME)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    state = {
        "protocol": "protocol.md",
        "prompt": prompt,
        "layout_path": package["layout_path"],
        "layout_sha256": file_sha256(ROOT / package["layout_path"]),
        "fixed": _fixed_record(),
        "measurement_inputs": _measurement_input_record(),
        "arms": {},
    }

    person_name = CLIENT.upload_image(PERSON_IMAGE)
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    for arm in ARMS:
        first_request = build_generation_request(
            package,
            PERSON_IMAGE,
            reference_board_variant=arm,
            seed=SEEDS[0],
            steps=STEPS,
            resolution=(WIDTH, HEIGHT),
        )
        board_path = Path(first_request["reference_panel_path"])
        board_name = CLIENT.upload_image(board_path)
        arm_state = {
            "board_path": str(board_path),
            "board_sha256": file_sha256(board_path),
            "outputs": {},
        }
        state["arms"][arm] = arm_state
        STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

        for seed in SEEDS:
            output_dir = RESULTS_DIR / arm / f"seed_{seed}"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "generated.png"
            if output_path.exists():
                raise FileExistsError(f"Refusing to overwrite experimental output: {output_path}")
            prefix = f"e007_{arm}_s{seed}"

            request = build_generation_request(
                package,
                PERSON_IMAGE,
                reference_board_variant=arm,
                seed=seed,
                steps=STEPS,
                resolution=(WIDTH, HEIGHT),
            )
            params = request["params"]

            workflow = fill_workflow(template, {
                "__PERSON_IMAGE__": person_name,
                "__REF_IMAGE__": board_name,
                "__POSITIVE_PROMPT__": request["prompt"],
                "__NEGATIVE_PROMPT__": request["negative_prompt"],
                "__CFG__": params["cfg"],
                "__SAMPLER__": params["sampler"],
                "__SCHEDULER__": params["scheduler"],
                "__SEED__": params["seed"],
                "__STEPS__": params["steps"],
                "__WIDTH__": params["width"],
                "__HEIGHT__": params["height"],
                "__OUTPUT_PREFIX__": prefix,
            })

            started = time.monotonic()
            prompt_id = CLIENT.submit(workflow)
            outputs = CLIENT.poll(prompt_id, timeout=600)
            _download_output(outputs, prefix, output_path)
            arm_state["outputs"][str(seed)] = {
                "path": str(output_path),
                "seconds": round(time.monotonic() - started, 2),
                "comfyui_prompt_id": prompt_id,
                "generation_request_id": request["request_id"],
            }
            STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            print(f"{arm} seed={seed}: {output_path.relative_to(ROOT)}")

        CLIENT.free()

    print(f"state: {STATE_FILE.relative_to(ROOT)}")
    print("Phase 1 complete. Review all paired outputs before phase 2.")


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _validate_hybrid_state(state: dict, require_outputs: bool) -> None:
    package = _load_package()
    expected_prompt = build_prompt(package, reference_board_variant=HYBRID_ARM)
    if state.get("prompt") != expected_prompt:
        raise RuntimeError("The hybrid prompt changed after its run started")
    if state.get("layout_sha256") != file_sha256(ROOT / package["layout_path"]):
        raise RuntimeError("outfit layout.txt changed after the hybrid run started")
    if state.get("fixed") != _fixed_record():
        raise RuntimeError("A fixed hybrid generation input changed")
    if state.get("measurement_inputs") != _measurement_input_record():
        raise RuntimeError("A hybrid measurement input changed")

    request = build_generation_request(
        package,
        PERSON_IMAGE,
        reference_board_variant=HYBRID_ARM,
        seed=SEEDS[0],
        steps=STEPS,
        resolution=(WIDTH, HEIGHT),
    )
    board_path = Path(request["reference_panel_path"])
    arm_state = state.get("arm", {})
    if arm_state.get("board_sha256") != file_sha256(board_path):
        raise RuntimeError("The frozen hybrid board changed")
    if require_outputs:
        for seed in SEEDS:
            output = arm_state.get("outputs", {}).get(str(seed), {}).get("path")
            if not output or not Path(output).is_file():
                raise RuntimeError(f"Hybrid generation is incomplete: seed {seed}")


def run_hybrid_phase1() -> None:
    package = _load_package()
    prompt = build_prompt(package, reference_board_variant=HYBRID_ARM)
    template = load_template(WORKFLOW_NAME)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    request = build_generation_request(
        package,
        PERSON_IMAGE,
        reference_board_variant=HYBRID_ARM,
        seed=SEEDS[0],
        steps=STEPS,
        resolution=(WIDTH, HEIGHT),
    )
    board_path = Path(request["reference_panel_path"])

    if HYBRID_STATE_FILE.exists():
        state = json.loads(HYBRID_STATE_FILE.read_text(encoding="utf-8"))
        _validate_hybrid_state(state, require_outputs=False)
    else:
        original_state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        state = {
            "protocol": "protocol.md#hybrid-supplement",
            "supplement_to": str(STATE_FILE),
            "comparison_limitations": {
                "board_changed": True,
                "layout_changed": True,
                "original_layout_sha256": original_state["layout_sha256"],
                "interpretation": (
                    "Compare the complete hybrid input candidate; do not attribute "
                    "differences to the board alone."
                ),
            },
            "prompt": prompt,
            "layout_path": package["layout_path"],
            "layout_sha256": file_sha256(ROOT / package["layout_path"]),
            "fixed": _fixed_record(),
            "measurement_inputs": _measurement_input_record(),
            "arm": {
                "name": HYBRID_ARM,
                "board_path": str(board_path),
                "board_sha256": file_sha256(board_path),
                "outputs": {},
            },
        }
        _write_json(HYBRID_STATE_FILE, state)

    person_name = CLIENT.upload_image(PERSON_IMAGE)
    board_name = CLIENT.upload_image(board_path)
    outputs_record = state["arm"]["outputs"]
    for seed in SEEDS:
        recorded = outputs_record.get(str(seed), {})
        if recorded.get("path") and Path(recorded["path"]).is_file():
            print(f"{HYBRID_ARM} seed={seed}: already complete")
            continue

        output_dir = RESULTS_DIR / HYBRID_ARM / f"seed_{seed}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "generated.png"
        if output_path.exists():
            raise FileExistsError(f"Unrecorded hybrid output exists: {output_path}")
        prefix = f"e007_{HYBRID_ARM}_s{seed}"

        request = build_generation_request(
            package,
            PERSON_IMAGE,
            reference_board_variant=HYBRID_ARM,
            seed=seed,
            steps=STEPS,
            resolution=(WIDTH, HEIGHT),
        )
        params = request["params"]
        workflow = fill_workflow(template, {
            "__PERSON_IMAGE__": person_name,
            "__REF_IMAGE__": board_name,
            "__POSITIVE_PROMPT__": request["prompt"],
            "__NEGATIVE_PROMPT__": request["negative_prompt"],
            "__CFG__": params["cfg"],
            "__SAMPLER__": params["sampler"],
            "__SCHEDULER__": params["scheduler"],
            "__SEED__": params["seed"],
            "__STEPS__": params["steps"],
            "__WIDTH__": params["width"],
            "__HEIGHT__": params["height"],
            "__OUTPUT_PREFIX__": prefix,
        })

        started = time.monotonic()
        prompt_id = CLIENT.submit(workflow)
        outputs = CLIENT.poll(prompt_id, timeout=600)
        _download_output(outputs, prefix, output_path)
        outputs_record[str(seed)] = {
            "path": str(output_path),
            "sha256": file_sha256(output_path),
            "seconds": round(time.monotonic() - started, 2),
            "comfyui_prompt_id": prompt_id,
            "generation_request_id": request["request_id"],
        }
        _write_json(HYBRID_STATE_FILE, state)
        print(f"{HYBRID_ARM} seed={seed}: {output_path.relative_to(ROOT)}")

    CLIENT.free()
    _validate_hybrid_state(state, require_outputs=True)
    make_three_way_sheet("generated.png", THREE_WAY_SHEET)
    print(f"hybrid state: {HYBRID_STATE_FILE.relative_to(ROOT)}")
    print(f"comparison: {THREE_WAY_SHEET.relative_to(ROOT)}")


def _make_overlay(source: Path, masks: dict[str, str], output: Path) -> None:
    image = cv2.imread(str(source))
    if image is None:
        raise FileNotFoundError(source)
    overlay = image.astype(np.float32)
    colors = [(80, 80, 255), (80, 200, 80), (60, 220, 220), (40, 140, 255), (200, 80, 200)]
    for index, (label, mask_path) in enumerate(masks.items()):
        if label in ("person", "face"):
            continue
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if mask is None:
            continue
        foreground = mask > 127
        color = colors[index % len(colors)]
        for channel in range(3):
            overlay[:, :, channel][foreground] = overlay[:, :, channel][foreground] * 0.5 + color[channel] * 0.5
    cv2.imwrite(str(output), overlay.astype(np.uint8))


def make_three_way_sheet(filename: str, destination: Path) -> None:
    cell_width = 360
    cell_height = 512
    label_height = 34
    header_height = 44
    sheet = np.full(
        (header_height + len(SEEDS) * (cell_height + label_height), cell_width * 3, 3),
        245,
        dtype=np.uint8,
    )
    for column, arm in enumerate(COMPARISON_ARMS):
        cv2.putText(
            sheet,
            arm,
            (column * cell_width + 12, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (20, 20, 20),
            2,
            cv2.LINE_AA,
        )
        for row, seed in enumerate(SEEDS):
            source = RESULTS_DIR / arm / f"seed_{seed}" / filename
            image = cv2.imread(str(source))
            if image is None:
                raise FileNotFoundError(source)
            resized = cv2.resize(image, (cell_width, cell_height), interpolation=cv2.INTER_AREA)
            y = header_height + row * (cell_height + label_height)
            x = column * cell_width
            sheet[y:y + cell_height, x:x + cell_width] = resized
            cv2.putText(
                sheet,
                f"seed {seed}",
                (x + 12, y + cell_height + 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (20, 20, 20),
                2,
                cv2.LINE_AA,
            )
    if not cv2.imwrite(str(destination), sheet):
        raise RuntimeError(f"Failed to write comparison sheet: {destination}")


def _flags_to_json(sanity: dict) -> dict:
    return {
        region: [{"check": flag.check, "detail": flag.detail} for flag in result.flags]
        for region, result in sanity.items()
        if not result.clean
    }


def _color_verdict(value: float | None) -> str:
    if value is None:
        return "INVALID"
    if value <= COLOR_PASS:
        return "PASS"
    if value <= COLOR_FAIL:
        return "WARN"
    return "FAIL"


def _measure_output(generated: Path, output_dir: Path) -> dict:
    masks_dir = output_dir / "masks"
    masks = segment(generated, GENERATED_PROMPTS, CLIENT, masks_dir)
    sanity = check_all(masks)
    flags = _flags_to_json(sanity)
    _make_overlay(generated, masks, output_dir / "_overlay_all.png")

    result = {"sanity_flags": flags, "color": {}}
    for region, (reference_image, reference_mask) in REGION_TO_REFERENCE.items():
        if region in flags:
            result["color"][region] = {"verdict": "SKIP_SANITY", "flags": flags[region]}
            continue
        measurement = compare_regions(generated, masks[region], reference_image, reference_mask)
        result["color"][region] = {**measurement, "verdict": _color_verdict(measurement["delta_e_mean"])}

    identity = compare_faces(generated, PERSON_IMAGE)
    cosine = identity["cosine"]
    result["identity"] = {
        **identity,
        "verdict": (
            "SKIP_DETECTION" if cosine is None
            else "PASS" if cosine >= IDENTITY_THRESHOLD
            else "FAIL"
        ),
    }

    if "person" in flags:
        result["proportions"] = {"verdict": "SKIP_SANITY", "flags": flags["person"]}
    else:
        proportions = compare_proportions(SOURCE_PERSON_MASK, masks["person"])
        score = proportions["max_abs_change_pct"]
        result["proportions"] = {
            **proportions,
            "verdict": (
                "SKIP_MEASUREMENT" if score is None
                else "PASS" if score <= PROPORTIONS_THRESHOLD
                else "FAIL"
            ),
            "interpretation": "diagnostic; silhouette includes clothing and depends on framing",
        }
    return result


def run_phase2() -> None:
    if not STATE_FILE.is_file():
        raise FileNotFoundError(f"Run phase 1 first: {STATE_FILE}")
    if MEASUREMENTS_FILE.exists():
        raise FileExistsError(
            f"E-007 measurements already exist: {MEASUREMENTS_FILE}. "
            "Refusing to overwrite an experimental record."
        )
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    _validate_phase2_state(state)
    measurements = {"arms": {}}

    for arm in ARMS:
        arm_results = {}
        measurements["arms"][arm] = arm_results
        for seed in SEEDS:
            output = Path(state["arms"][arm]["outputs"][str(seed)]["path"])
            print(f"measure {arm} seed={seed}")
            arm_results[str(seed)] = _measure_output(output, output.parent)
            MEASUREMENTS_FILE.write_text(
                json.dumps(measurements, indent=2) + "\n", encoding="utf-8"
            )
        CLIENT.free()

    print(f"measurements: {MEASUREMENTS_FILE.relative_to(ROOT)}")
    print_summary(measurements)


def run_hybrid_phase2() -> None:
    if not HYBRID_STATE_FILE.is_file():
        raise FileNotFoundError(f"Run hybrid phase 1 first: {HYBRID_STATE_FILE}")
    if HYBRID_MEASUREMENTS_FILE.exists():
        raise FileExistsError(
            f"Hybrid measurements already exist: {HYBRID_MEASUREMENTS_FILE}. "
            "Refusing to overwrite an experimental record."
        )
    state = json.loads(HYBRID_STATE_FILE.read_text(encoding="utf-8"))
    _validate_hybrid_state(state, require_outputs=True)
    measurements = {"arm": HYBRID_ARM, "results": {}}

    for seed in SEEDS:
        output = Path(state["arm"]["outputs"][str(seed)]["path"])
        print(f"measure {HYBRID_ARM} seed={seed}")
        measurements["results"][str(seed)] = _measure_output(output, output.parent)
        _write_json(HYBRID_MEASUREMENTS_FILE, measurements)
    CLIENT.free()

    make_three_way_sheet("_overlay_all.png", THREE_WAY_OVERLAYS)
    print(f"hybrid measurements: {HYBRID_MEASUREMENTS_FILE.relative_to(ROOT)}")
    print(f"overlay comparison: {THREE_WAY_OVERLAYS.relative_to(ROOT)}")
    print_hybrid_summary(measurements)


def _validate_phase2_state(state: dict) -> None:
    package = _load_package()
    if state.get("prompt") != build_prompt(package):
        raise RuntimeError("The active prompt changed after phase 1; phase 2 is not comparable")
    if state.get("layout_sha256") != file_sha256(ROOT / package["layout_path"]):
        raise RuntimeError("outfit layout.txt changed after phase 1")

    fixed = state.get("fixed", {})
    expected_fixed_hashes = {
        "workflow_sha256": file_sha256(ROOT / "system/workflows" / f"{WORKFLOW_NAME}.json"),
        "person_sha256": file_sha256(PERSON_IMAGE),
    }
    for key, expected in expected_fixed_hashes.items():
        if fixed.get(key) != expected:
            raise RuntimeError(f"E-007 fixed input changed after phase 1: {key}")

    measurement_inputs = state.get("measurement_inputs", {})
    if measurement_inputs.get("source_person_mask") != file_sha256(SOURCE_PERSON_MASK):
        raise RuntimeError("E-007 source person mask changed after phase 1")
    recorded_regions = measurement_inputs.get("regions", {})
    for region, (image_path, mask_path) in REGION_TO_REFERENCE.items():
        recorded = recorded_regions.get(region, {})
        if recorded.get("image_sha256") != file_sha256(image_path):
            raise RuntimeError(f"E-007 reference image changed after phase 1: {region}")
        if recorded.get("mask_sha256") != file_sha256(mask_path):
            raise RuntimeError(f"E-007 reference mask changed after phase 1: {region}")

    for arm in ARMS:
        request = build_generation_request(
            package,
            PERSON_IMAGE,
            reference_board_variant=arm,
            seed=SEEDS[0],
            steps=STEPS,
            resolution=(WIDTH, HEIGHT),
        )
        arm_state = state.get("arms", {}).get(arm)
        if not arm_state:
            raise RuntimeError(f"E-007 phase 1 is incomplete: missing arm {arm}")
        board_path = Path(request["reference_panel_path"])
        if arm_state.get("board_sha256") != file_sha256(board_path):
            raise RuntimeError(f"E-007 board changed after phase 1: {arm}")
        for seed in SEEDS:
            output = arm_state.get("outputs", {}).get(str(seed), {}).get("path")
            if not output or not Path(output).is_file():
                raise RuntimeError(f"E-007 phase 1 is incomplete: {arm} seed {seed}")


def _mean(values: list[float | None]) -> float | None:
    valid = [value for value in values if value is not None]
    return round(float(np.mean(valid)), 4) if valid else None


def print_summary(measurements: dict) -> None:
    print("\nE-007 v2 paired summary")
    for arm in ARMS:
        rows = measurements["arms"][arm].values()
        identity = _mean([row.get("identity", {}).get("cosine") for row in rows])
        proportions = _mean([row.get("proportions", {}).get("max_abs_change_pct") for row in rows])
        print(f"\n{arm}: identity_mean={identity} proportions_mean={proportions}")
        for region in REGION_TO_REFERENCE:
            values = [row.get("color", {}).get(region, {}).get("delta_e_mean") for row in rows]
            print(f"  {region}: dE_mean={_mean(values)}")
    print("\nNo automatic winner. Owner review of each same-seed pair is required.")


def print_hybrid_summary(measurements: dict) -> None:
    rows = measurements["results"].values()
    identity = _mean([row.get("identity", {}).get("cosine") for row in rows])
    proportions = _mean([row.get("proportions", {}).get("max_abs_change_pct") for row in rows])
    print(f"\n{HYBRID_ARM}: identity_mean={identity} proportions_mean={proportions}")
    for region in REGION_TO_REFERENCE:
        values = [row.get("color", {}).get(region, {}).get("delta_e_mean") for row in rows]
        print(f"  {region}: dE_mean={_mean(values)}")
    print("\nCompare as a complete input candidate; board and layout both changed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="E-007 v2 frozen-board A/B")
    parser.add_argument("--phase", type=int, choices=(1, 2))
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--hybrid-phase", type=int, choices=(1, 2))
    parser.add_argument("--hybrid-summary", action="store_true")
    args = parser.parse_args()

    selected = sum(bool(value) for value in (
        args.phase,
        args.summary,
        args.hybrid_phase,
        args.hybrid_summary,
    ))
    if selected != 1:
        parser.error("choose exactly one phase or summary action")

    if args.summary:
        if not MEASUREMENTS_FILE.is_file():
            raise FileNotFoundError(MEASUREMENTS_FILE)
        print_summary(json.loads(MEASUREMENTS_FILE.read_text(encoding="utf-8")))
    elif args.hybrid_summary:
        if not HYBRID_MEASUREMENTS_FILE.is_file():
            raise FileNotFoundError(HYBRID_MEASUREMENTS_FILE)
        print_hybrid_summary(json.loads(HYBRID_MEASUREMENTS_FILE.read_text(encoding="utf-8")))
    elif args.phase == 1:
        run_phase1()
    elif args.phase == 2:
        run_phase2()
    elif args.hybrid_phase == 1:
        run_hybrid_phase1()
    elif args.hybrid_phase == 2:
        run_hybrid_phase2()
    else:
        parser.error("choose a phase or summary action")


if __name__ == "__main__":
    main()
