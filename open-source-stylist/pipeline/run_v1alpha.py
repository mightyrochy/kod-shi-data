"""V1-alpha: thin closed loop.

Each invocation creates a NEW numbered folder under runs/experiments/v1alpha/.
Inputs are read from a source run (default: reads from runs/000001 assets,
or from a previous v1alpha run). Outputs go to the new run folder.

Run folder structure (runs/experiments/v1alpha/NNNNNN/):
  input/        person image, outfit_package.json, prompt.txt, reference board
  output/       generated output.png
  experiment/   config.json — model settings, source, timestamp, hypothesis
  conclusion/   evaluation.json (VLM) + notes.md (blank template for human)
  run.log       timestamped execution log

Usage:
    python -m pipeline.run_v1alpha [source_run_id] [--hypothesis "..."]

    source_run_id: run ID to pull inputs from.
      - "000001" (default) reads from runs/000001 (original manual assets)
      - any v1alpha run id reads from runs/experiments/v1alpha/NNNNNN

VRAM sequencing:
    ComfyUI /free → generation (QIE-2511 fp8mixed, 4-step Lightning LoRA)
    → /free → VLM eval (Qwen3-VL-8B) → unload VLM
"""

import datetime
import json
import shutil
import sys
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.comfyui_client import ComfyUIClient
from pipeline.evaluator import Evaluator
from pipeline.lmstudio_client import LMStudioClient
from pipeline.outfit_adapter import OutfitAdapter
from pipeline import run_io

RUNS_DIR       = ROOT / "runs" / "experiments" / "v1alpha"
LEGACY_RUNS    = ROOT / "runs"   # for reading source run 000001
VLM_MODEL      = "qwen3-vl-8b-instruct"

EXPERIMENT_MODEL   = "qwen_image_edit_2511_fp8mixed.safetensors"
EXPERIMENT_LORA    = "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"
EXPERIMENT_STEPS   = 4
EXPERIMENT_CFG     = 1.0
EXPERIMENT_SAMPLER = "euler"


def _find_source(source_id: str) -> Path:
    """Return the path to the source run folder."""
    candidate_v1alpha = RUNS_DIR / source_id
    candidate_legacy  = LEGACY_RUNS / source_id
    if candidate_v1alpha.is_dir():
        return candidate_v1alpha
    if candidate_legacy.is_dir():
        return candidate_legacy
    raise FileNotFoundError(
        f"Source run {source_id} not found in {RUNS_DIR} or {LEGACY_RUNS}"
    )


def main(source_run_id: str = "000001", hypothesis: str = "") -> int:
    source_path = _find_source(source_run_id)

    # -- locate inputs ---------------------------------------------------------
    person_image       = source_path / "input" / "person_front.png"
    outfit_package_src = source_path / "outfit" / "outfit_package.json"
    prompt_src         = source_path / "qwen"  / "prompt.txt"
    ref_board_src      = source_path / "qwen"  / "reference_board_clean.png"

    for p in (person_image, outfit_package_src):
        if not p.exists():
            print(f"ERROR: required input not found: {p}")
            return 1

    with open(outfit_package_src, encoding="utf-8") as f:
        outfit_package = json.load(f)

    # -- create new run --------------------------------------------------------
    run = run_io.create_run(RUNS_DIR)
    run.log(f"source={source_run_id}")
    print(f"Source: {source_run_id}  →  New run: {run.run_id}")

    # -- copy inputs -----------------------------------------------------------
    for sub, src, dst_name in [
        ("input",  person_image,       "person_front.png"),
        ("outfit", outfit_package_src, "outfit_package.json"),
    ]:
        d = run.path / sub
        d.mkdir(exist_ok=True)
        shutil.copy2(src, d / dst_name)

    if prompt_src.exists():
        (run.path / "qwen").mkdir(exist_ok=True)
        shutil.copy2(prompt_src, run.path / "qwen" / "prompt.txt")
    if ref_board_src.exists():
        (run.path / "qwen").mkdir(exist_ok=True)
        shutil.copy2(ref_board_src, run.path / "qwen" / "reference_board_clean.png")

    # local copies
    person_image_local  = run.path / "input"  / "person_front.png"
    outfit_pkg_local    = run.path / "outfit" / "outfit_package.json"
    prompt_local        = run.path / "qwen"   / "prompt.txt"
    ref_board_local     = run.path / "qwen"   / "reference_board_clean.png"

    # -- write experiment config -----------------------------------------------
    run.save_json("experiment/config.json", {
        "timestamp":    datetime.datetime.now().isoformat(timespec="seconds"),
        "source_run":   source_run_id,
        "model":        EXPERIMENT_MODEL,
        "lora":         EXPERIMENT_LORA,
        "steps":        EXPERIMENT_STEPS,
        "cfg":          EXPERIMENT_CFG,
        "sampler":      EXPERIMENT_SAMPLER,
        "scheduler":    "simple",
        "vlm_eval":     VLM_MODEL,
        "hypothesis":   hypothesis,
    })

    # blank conclusion notes for human
    (run.path / "conclusion").mkdir(exist_ok=True)
    (run.path / "conclusion" / "notes.md").write_text(
        f"# Run {run.run_id} — conclusion notes\n\n", encoding="utf-8"
    )

    # -- clients ---------------------------------------------------------------
    comfy = ComfyUIClient()
    lms   = LMStudioClient()

    # -- free VRAM -------------------------------------------------------------
    print("Freeing VRAM...")
    comfy.free()
    run.log(f"vram_free={comfy.vram_free_gb():.1f}GB after /free")

    # -- build workflow --------------------------------------------------------
    print("Building workflow...")
    adapter  = OutfitAdapter(comfy)
    workflow = adapter.prepare_from_package(
        outfit_package_path = outfit_pkg_local,
        person_image        = person_image_local,
        reference_board     = ref_board_local if ref_board_local.exists() else None,
        prompt_path         = prompt_local     if prompt_local.exists()     else None,
        output_prefix       = f"run{run.run_id}",
    )
    run.save_json("experiment/workflow_submitted.json", workflow)
    run.log("workflow built")

    # -- generate --------------------------------------------------------------
    print("Submitting to ComfyUI (4-step Lightning LoRA)...")
    t_gen = time.monotonic()
    try:
        history = comfy.run(workflow, timeout=600)
    except Exception as e:
        run.log(f"generation FAILED: {e}")
        print(f"Generation failed: {e}")
        return 1

    gen_time = time.monotonic() - t_gen
    run.log(f"generation done in {gen_time:.1f}s")
    print(f"Generation done in {gen_time:.1f}s")

    # -- download output -------------------------------------------------------
    output_refs = comfy.output_images(history)
    if not output_refs:
        run.log("ERROR: no output images")
        print("ERROR: no output images in history")
        return 1

    (run.path / "output").mkdir(exist_ok=True)
    output_path = run.path / "output" / "output.png"
    comfy.download_image(output_refs[0], output_path)
    run.log(f"output saved → output/output.png  ({gen_time:.1f}s)")
    print(f"Output: {output_path}")

    # -- free VRAM before VLM --------------------------------------------------
    print("Freeing VRAM for evaluation...")
    comfy.free()

    # -- evaluate --------------------------------------------------------------
    print(f"Evaluating with {VLM_MODEL}...")
    t_eval = time.monotonic()
    evaluator = Evaluator(lms, VLM_MODEL)
    try:
        result = evaluator.evaluate(
            person_before    = person_image_local,
            generated_output = output_path,
            outfit_package   = outfit_package,
        )
    except Exception as e:
        run.log(f"evaluation FAILED: {e}")
        print(f"Evaluation failed: {e}")
        return 1

    eval_time = time.monotonic() - t_eval
    run.log(f"eval done in {eval_time:.1f}s  pass={result.get('overall_pass')}")

    run.save_json("conclusion/evaluation.json", result)

    try:
        lms.unload(VLM_MODEL)
    except Exception:
        pass

    # -- summary ---------------------------------------------------------------
    run.log("done")
    print()
    print("=" * 60)
    print(f"EVALUATION — run {run.run_id}  (source: {source_run_id})")
    print("=" * 60)
    for verdict_key, notes_key in [
        ("identity_preserved",  "identity_notes"),
        ("outfit_items_present","items_notes"),
        ("outfit_logic_followed","logic_notes"),
        ("colors_textures_match","color_notes"),
    ]:
        v = result.get(verdict_key)
        n = result.get(notes_key, "")
        print(f"  [{'PASS' if v else 'FAIL'}] {verdict_key.replace('_',' ').upper()}")
        if n:
            print(f"         {n}")
    print()
    overall = result.get("overall_pass", False)
    print(f"  OVERALL: {'PASS' if overall else 'FAIL'}")
    print(f"  {result.get('summary', '')}")
    print("=" * 60)
    print(f"\nRun folder: runs/experiments/v1alpha/{run.run_id}/")

    return 0 if overall else 1


if __name__ == "__main__":
    args = sys.argv[1:]
    src  = args[0] if args else "000001"
    hyp  = ""
    if "--hypothesis" in args:
        i   = args.index("--hypothesis")
        hyp = args[i + 1] if i + 1 < len(args) else ""
    sys.exit(main(src, hyp))
