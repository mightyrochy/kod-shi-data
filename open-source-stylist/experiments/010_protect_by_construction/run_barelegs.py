"""Standard preprocessing step (candidate): expose the legs.

For a leg-revealing garment (skirt/dress) the target person must HAVE visible legs.
Our person wears full-length jeans -> the legs are hidden -> Leffa renders trousers /
invents bad legs. Fix: inpaint the jeans region into bare legs (FLUX Fill), THEN try-on.

    python experiments/010_protect_by_construction/run_barelegs.py
Needs ComfyUI live (:8000) with flux1-fill-dev.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from system.clients.comfyui import ComfyUIClient

PROJ = ROOT / "experiments/010_protect_by_construction/results/proto_chain"
TEMPLATE = ROOT / "system/workflows/flux_fill_inpaint.json"
PERSON = PROJ / "person_dcstyle.png"
MASK = PROJ / "jeans_mask.png"
OUT = PROJ / "person_barelegs.png"

POS = "bare legs, smooth bare skin, photorealistic, natural lighting, standing"
NEG = "pants, trousers, jeans, leggings, shorts, skirt, clothing, fabric, text"


def main():
    client = ComfyUIClient()
    person_ref = client.upload_image(PERSON)
    mask_ref = client.upload_image(MASK)

    wf = TEMPLATE.read_text(encoding="utf-8")
    repl = {
        '"__WIDTH__"': "768", '"__HEIGHT__"': "1024",
        '"__CFG__"': "30", '"__SEED__"': "42", '"__STEPS__"': "30", '"__DENOISE__"': "1.0",
        "__PERSON_IMAGE__": person_ref, "__MASK_IMAGE__": mask_ref,
        "__POSITIVE_PROMPT__": POS, "__NEGATIVE_PROMPT__": NEG,
        "__SAMPLER__": "euler", "__SCHEDULER__": "normal", "__OUTPUT_PREFIX__": "barelegs",
    }
    for k, v in repl.items():
        wf = wf.replace(k, v)
    workflow = json.loads(wf)  # validates + correct types

    print("  FLUX Fill: jeans -> bare legs ...")
    t0 = time.monotonic()
    outputs = client.poll(client.submit(workflow), timeout=900.0)
    for node_out in outputs.values():
        for img in node_out.get("images", []):
            if img.get("filename", "").startswith("barelegs"):
                OUT.write_bytes(client.download(img["filename"], img.get("subfolder", ""),
                                                img.get("type", "output")))
                client.free()
                print(f"  done {round(time.monotonic()-t0,1)}s -> {OUT.relative_to(ROOT)}")
                return
    raise RuntimeError("no barelegs output")


if __name__ == "__main__":
    main()
