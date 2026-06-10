"""V1-alpha: thin closed loop.

Each invocation creates a NEW run folder (next available NNNNNN id).
Inputs are read from a source run; outputs go to the new run.

Stages:
  1. Create new run folder; read inputs from source run
  2. Build QIE-2511 workflow via OutfitAdapter
  3. Run generation on ComfyUI (4 steps, Lightning LoRA)
  4. Download output image
  5. Evaluate with Qwen3-VL-8B (4 criteria)
  6. Save all artifacts to the new run folder
  7. Print summary

Usage:
    python -m pipeline.run_v1alpha [source_run_id]

    source_run_id defaults to 000001 — the run that holds the input assets
    (person_front.png, outfit_package.json, qwen/prompt.txt,
    qwen/reference_board_clean.png).

VRAM sequencing:
    ComfyUI /free → generation (QIE-2511) → /free → VLM evaluation → unload VLM
"""

import json
import shutil
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


def main(source_run_id: str = "000001") -> int:
    source = run_io.open_run(RUNS_DIR, source_run_id)

    # -- locate inputs from source run -----------------------------------------
    person_image = source.path / "input" / "person_front.png"
    outfit_package_path = source.path / "outfit" / "outfit_package.json"
    prompt_path = source.path / "qwen" / "prompt.txt"
    reference_board = source.path / "qwen" / "reference_board_clean.png"

    for p in (person_image, outfit_package_path):
        if not p.exists():
            print(f"ERROR: required input not found: {p}")
            return 1

    with open(outfit_package_path, encoding="utf-8") as f:
        outfit_package = json.load(f)

    # -- create a fresh run for this attempt -----------------------------------
    run = run_io.create_run(RUNS_DIR)
    run.log(f"[v1alpha] source={source_run_id}")
    print(f"Source run: {source_run_id}  →  New run: {run.run_id}")

    # copy key inputs into the new run so it is self-contained
    (run.path / "input").mkdir(exist_ok=True)
    shutil.copy2(person_image, run.path / "input" / "person_front.png")
    (run.path / "outfit").mkdir(exist_ok=True)
    shutil.copy2(outfit_package_path, run.path / "outfit" / "outfit_package.json")
    if prompt_path.exists():
        (run.path / "qwen").mkdir(exist_ok=True)
        shutil.copy2(prompt_path, run.path / "qwen" / "prompt.txt")
    if reference_board.exists():
        run.path.joinpath("qwen").mkdir(exist_ok=True)
        shutil.copy2(reference_board, run.path / "qwen" / "reference_board_clean.png")

    # from here on, reference the copies inside the new run
    person_image = run.path / "input" / "person_front.png"
    outfit_package_path = run.path / "outfit" / "outfit_package.json"
    prompt_path_local = run.path / "qwen" / "prompt.txt"
    reference_board_local = run.path / "qwen" / "reference_board_clean.png"

    # -- clients ---------------------------------------------------------------
    comfy = ComfyUIClient()
    lms = LMStudioClient()

    # -- step 1: free VRAM before generation -----------------------------------
    print("Freeing VRAM...")
    comfy.free()
    run.log(f"[v1alpha] vram_free={comfy.vram_free_gb():.1f}GB after /free")

    # -- step 2: build workflow ------------------------------------------------
    print("Building workflow...")
    adapter = OutfitAdapter(comfy)
    workflow = adapter.prepare_from_package(
        outfit_package_path=outfit_package_path,
        person_image=person_image,
        reference_board=reference_board_local if reference_board_local.exists() else None,
        prompt_path=prompt_path_local if prompt_path_local.exists() else None,
        output_prefix=f"run{run.run_id}",
    )
    run.save_json("generation/workflow_submitted.json", workflow)
    run.log("[v1alpha] workflow built")

    # -- step 3: generate ------------------------------------------------------
    print("Submitting to ComfyUI (4-step Lightning LoRA)...")
    t_gen = time.monotonic()
    try:
        history = comfy.run(workflow, timeout=600)
    except Exception as e:
        run.log(f"[v1alpha] generation FAILED: {e}")
        print(f"Generation failed: {e}")
        return 1

    gen_time = time.monotonic() - t_gen
    run.log(f"[v1alpha] generation done in {gen_time:.1f}s")
    print(f"Generation done in {gen_time:.1f}s")

    # -- step 4: download output -----------------------------------------------
    output_refs = comfy.output_images(history)
    if not output_refs:
        run.log("[v1alpha] ERROR: no output images")
        print("ERROR: no output images in history")
        return 1

    output_path = run.stage_dir("generation") / "output.png"
    comfy.download_image(output_refs[0], output_path)
    run.log(f"[v1alpha] output saved → {output_path.relative_to(run.path)}")
    run.save_json("generation/meta.json", {
        "source_run": source_run_id,
        "output_image": "generation/output.png",
        "generation_time_s": round(gen_time, 2),
    })
    print(f"Output: {output_path}")

    # -- step 5: free VRAM before VLM ------------------------------------------
    print("Freeing VRAM for evaluation...")
    comfy.free()

    # -- step 6: evaluate ------------------------------------------------------
    print(f"Evaluating with {VLM_MODEL}...")
    t_eval = time.monotonic()
    evaluator = Evaluator(lms, VLM_MODEL)
    try:
        result = evaluator.evaluate(
            person_before=person_image,
            generated_output=output_path,
            outfit_package=outfit_package,
        )
    except Exception as e:
        run.log(f"[v1alpha] evaluation FAILED: {e}")
        print(f"Evaluation failed: {e}")
        return 1

    eval_time = time.monotonic() - t_eval
    run.log(f"[v1alpha] eval done in {eval_time:.1f}s pass={result.get('overall_pass')}")
    run.save_json("evaluation/result.json", result)

    try:
        lms.unload(VLM_MODEL)
    except Exception:
        pass

    # -- summary ---------------------------------------------------------------
    run.log("[v1alpha] done")
    print()
    print("=" * 60)
    print(f"EVALUATION — New run {run.run_id}  (source: {source_run_id})")
    print("=" * 60)
    for verdict_key, notes_key in [
        ("identity_preserved", "identity_notes"),
        ("outfit_items_present", "items_notes"),
        ("outfit_logic_followed", "logic_notes"),
        ("colors_textures_match", "color_notes"),
    ]:
        v = result.get(verdict_key)
        n = result.get(notes_key, "")
        print(f"  [{'PASS' if v else 'FAIL'}] {verdict_key.replace('_', ' ').upper()}")
        if n:
            print(f"         {n}")
    print()
    overall = result.get("overall_pass", False)
    print(f"  OVERALL: {'PASS' if overall else 'FAIL'}")
    print(f"  {result.get('summary', '')}")
    print("=" * 60)
    print(f"\nRun folder:   runs/{run.run_id}/")
    print(f"Output image: runs/{run.run_id}/generation/output.png")
    print(f"Evaluation:   runs/{run.run_id}/evaluation/result.json")

    return 0 if overall else 1


if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else "000001"
    sys.exit(main(source))
