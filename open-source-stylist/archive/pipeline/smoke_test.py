"""Plumbing smoke test.

Verifies against the live local environment:
1. ComfyUI: system_stats, /free, image upload
2. LM Studio: model listing, vision call with schema-enforced JSON (timed:
   first call includes JIT model load), explicit unload
3. run_io: round-trip in a temp directory

Read-only with respect to project data; writes only to temp dirs and
ComfyUI's input folder. Exit code 0 = all checks passed.
"""

import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.comfyui_client import ComfyUIClient
from pipeline.lmstudio_client import LMStudioClient
from pipeline import run_io

VLM_MODEL = "qwen3-vl-8b-instruct"
TEST_IMAGE = Path(__file__).resolve().parent.parent / "runs/000001/input/person_front.png"

results: list[tuple[str, str]] = []


def check(name: str, fn):
    try:
        detail = fn()
        results.append((name, f"OK {detail or ''}".strip()))
    except Exception as e:
        results.append((name, f"FAIL {type(e).__name__}: {e}"))


def main() -> int:
    comfy = ComfyUIClient()
    lms = LMStudioClient()

    # --- ComfyUI ---
    def comfy_stats():
        s = comfy.system_stats()
        dev = s["devices"][0]
        return (f"v{s['system']['comfyui_version']}, "
                f"vram_free={dev['vram_free'] / 1024**3:.1f}GB")
    check("comfyui.system_stats", comfy_stats)
    check("comfyui.free", lambda: comfy.free())
    check("comfyui.upload_image", lambda: f"name={comfy.upload_image(TEST_IMAGE)}")

    # --- LM Studio ---
    def lms_models():
        models = lms.list_models()
        keys = [m.get("key") for m in models]
        if VLM_MODEL not in keys:
            raise RuntimeError(f"{VLM_MODEL} not in {keys}")
        return f"{len(models)} models, VLM present"
    check("lmstudio.list_models", lms_models)

    schema = {
        "type": "object",
        "properties": {
            "person_present": {"type": "boolean"},
            "description": {"type": "string"},
        },
        "required": ["person_present", "description"],
    }
    timings = {}

    def vlm_call(label):
        t0 = time.monotonic()
        out = lms.vision_chat(
            "Is there a person in this image? Describe them in one sentence.",
            [TEST_IMAGE], model=VLM_MODEL, json_schema=schema, schema_name="person_check",
        )
        timings[label] = time.monotonic() - t0
        if not isinstance(out, dict) or "person_present" not in out:
            raise RuntimeError(f"unexpected output: {out}")
        return f"{timings[label]:.1f}s, person_present={out['person_present']}"

    check("lmstudio.vision_cold (incl. JIT load)", lambda: vlm_call("cold"))
    check("lmstudio.vision_warm", lambda: vlm_call("warm"))

    def lms_unload():
        loaded = lms.loaded_models()
        if not loaded:
            return "nothing loaded (TTL already evicted?)"
        key = loaded[0]["key"]
        t0 = time.monotonic()
        lms.unload(key)
        still = [m["key"] for m in lms.loaded_models()]
        if key in still:
            raise RuntimeError(f"{key} still loaded after unload")
        return f"unloaded {key} in {time.monotonic() - t0:.1f}s"
    check("lmstudio.unload", lms_unload)

    # --- run_io ---
    def runio_roundtrip():
        with tempfile.TemporaryDirectory() as tmp:
            run = run_io.create_run(Path(tmp))
            run.save_json("evaluation/test.json", {"x": 1})
            assert run.load_json("evaluation/test.json") == {"x": 1}
            run.log("smoke test entry")
            run2 = run_io.create_run(Path(tmp))
            assert run.run_id == "000001" and run2.run_id == "000002"
        return "create/save/load/log/sequence OK"
    check("run_io.roundtrip", runio_roundtrip)

    width = max(len(n) for n, _ in results)
    failed = 0
    for name, status in results:
        print(f"{name:<{width}}  {status}")
        if status.startswith("FAIL"):
            failed += 1
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
