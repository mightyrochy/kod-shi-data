"""V1-alpha: thin closed loop.

Stages:
  1. Read run folder (outfit_package.json, person_front.png, qwen/prompt.txt,
     qwen/reference_board_clean.png)
  2. Build QIE-2511 workflow via OutfitAdapter
  3. Run generation on ComfyUI (4 steps, Lightning LoRA)
  4. Download output image
  5. Evaluate with Qwen3-VL-8B (4 criteria)
  6. Save evaluation + generation metadata to run folder
  7. Print summary

Usage:
    python -m pipeline.run_v1alpha [run_id]

    run_id defaults to 000001 for the initial test.

VRAM sequencing:
    ComfyUI /free → generation (QIE-2511, ~12GB) → /free → VLM evaluation → unload VLM
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.comfyui_client import ComfyUIClient
from pipeline.evaluator import Evaluator
from pipeline.lmstudio_client import LMStudioClient
from pipeline.outfit_adapter import OutfitAdapter
from pipeline import run_io

RUNS_DIR = ROOT / "runs"
VLM_MODEL = "qwen3-vl-8b-instruct"
STAGE = "v1alpha"


def main(run_id: str = "000001") -> int:
    run = run_io.open_run(RUNS_DIR, run_id)
    stage_dir = run.stage_dir(STAGE)

    run.log(f"[{STAGE}] start")
    print(f"Run {run_id} — V1-alpha closed loop")

    # -- locate inputs ---------------------------------------------------------
    person_image = run.path / "input" / "person_front.png"
    outfit_package_path = run.path / "outfit" / "outfit_package.json"
    prompt_path = run.path / "qwen" / "prompt.txt"
    reference_board = run.path / "qwen" / "reference_board_clean.png"

    for p in (person_image, outfit_package_path):
        if not p.exists():
            print(f"ERROR: required file not found: {p}")
            return 1

    with open(outfit_package_path, encoding="utf-8") as f:
        outfit_package = json.load(f)

    # -- clients ---------------------------------------------------------------
    comfy = ComfyUIClient()
    lms = LMStudioClient()

    # -- step 1: free VRAM before generation -----------------------------------
    print("Freeing VRAM...")
    comfy.free()
    run.log(f"[{STAGE}] vram_free={comfy.vram_free_gb():.1f}GB after /free")

    # -- step 2: build workflow ------------------------------------------------
    print("Building workflow...")
    adapter = OutfitAdapter(comfy)
    workflow = adapter.prepare_from_package(
        outfit_package_path=outfit_package_path,
        person_image=person_image,
        reference_board=reference_board if reference_board.exists() else None,
        prompt_path=prompt_path if prompt_path.exists() else None,
        output_prefix=f"run{run_id}_{STAGE}",
    )
    run.save_json(f"{STAGE}/workflow_submitted.json", workflow)
    run.log(f"[{STAGE}] workflow built and saved")

    # -- step 3: generate ------------------------------------------------------
    print("Submitting to ComfyUI (4-step Lightning LoRA)...")
    t_gen_start = time.monotonic()
    try:
        history = comfy.run(workflow, timeout=600)
    except Exception as e:
        run.log(f"[{STAGE}] generation FAILED: {e}")
        print(f"Generation failed: {e}")
        return 1

    gen_time = time.monotonic() - t_gen_start
    run.log(f"[{STAGE}] generation done in {gen_time:.1f}s")
    print(f"Generation done in {gen_time:.1f}s")

    # -- step 4: download output -----------------------------------------------
    output_refs = comfy.output_images(history)
    if not output_refs:
        msg = "no output images in history entry"
        run.log(f"[{STAGE}] ERROR: {msg}")
        print(f"ERROR: {msg}")
        return 1

    output_path = stage_dir / "output.png"
    comfy.download_image(output_refs[0], output_path)
    run.log(f"[{STAGE}] output saved to {output_path.relative_to(run.path)}")
    print(f"Output: {output_path}")

    # save generation metadata
    run.save_json(
        f"{STAGE}/generation_meta.json",
        {
            "output_image": str(output_path.relative_to(run.path)),
            "generation_time_s": round(gen_time, 2),
            "output_refs": output_refs,
        },
    )

    # -- step 5: free VRAM before VLM ------------------------------------------
    print("Freeing VRAM for evaluation...")
    comfy.free()
    run.log(f"[{STAGE}] vram_free={comfy.vram_free_gb():.1f}GB before VLM eval")

    # -- step 6: evaluate ------------------------------------------------------
    print(f"Evaluating with {VLM_MODEL}...")
    t_eval_start = time.monotonic()
    evaluator = Evaluator(lms, VLM_MODEL)
    try:
        result = evaluator.evaluate(
            person_before=person_image,
            generated_output=output_path,
            outfit_package=outfit_package,
        )
    except Exception as e:
        run.log(f"[{STAGE}] evaluation FAILED: {e}")
        print(f"Evaluation failed: {e}")
        return 1

    eval_time = time.monotonic() - t_eval_start
    run.log(f"[{STAGE}] evaluation done in {eval_time:.1f}s, pass={result.get('overall_pass')}")

    # -- step 7: save results --------------------------------------------------
    run.save_json(f"{STAGE}/evaluation.json", result)

    # -- step 8: unload VLM ----------------------------------------------------
    try:
        lms.unload(VLM_MODEL)
    except Exception:
        pass

    # -- summary ---------------------------------------------------------------
    run.log(f"[{STAGE}] done")
    print()
    print("=" * 60)
    print(f"EVALUATION — Run {run_id}")
    print("=" * 60)
    fields = [
        ("identity_preserved", "identity_notes"),
        ("outfit_items_present", "items_notes"),
        ("outfit_logic_followed", "logic_notes"),
        ("colors_textures_match", "color_notes"),
    ]
    for verdict_key, notes_key in fields:
        v = result.get(verdict_key)
        n = result.get(notes_key, "")
        icon = "PASS" if v else "FAIL"
        label = verdict_key.replace("_", " ").upper()
        print(f"  [{icon}] {label}")
        if n:
            print(f"         {n}")
    print()
    overall = result.get("overall_pass", False)
    print(f"  OVERALL: {'PASS' if overall else 'FAIL'}")
    print(f"  {result.get('summary', '')}")
    print("=" * 60)
    print(f"\nEvaluation saved to: {run.path / STAGE / 'evaluation.json'}")
    print(f"Output image:        {output_path}")

    return 0 if overall else 1


if __name__ == "__main__":
    run_id = sys.argv[1] if len(sys.argv) > 1 else "000001"
    sys.exit(main(run_id))
