"""E-014 — full-pipeline run, stage 1: scoped QIE holistic (blouse + skirt + wedge sandals only).

Belt + earrings are excluded here (added later by OmniTry). Uses the reduced 3-item board and a
logical, visibility-explicit prompt (blouse UNTUCKED — the fix for the E-012 tuck defect; no colours).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from system.clients.comfyui import ComfyUIClient
from system.workflows import fill_workflow, load_template

PERSON = ROOT / "assets/person/person_front.png"
BOARD = ROOT / "assets/outfits/outfit_001/reference_boards/garments3_hybrid.png"
OUT = Path(__file__).parent / "results"
PROMPT = (
    "Keep this exact person: face, hair, skin tone, body proportions, pose, and background unchanged. "
    "Using the reference board (image 2), re-dress them in the outfit shown. The board shows labeled "
    "garments: blouse, skirt, and wedge sandals. Dress the person in a blouse, a maxi skirt, and wedge "
    "sandals. The blouse is worn UNTUCKED — its hem hangs loose over the skirt waistband, not tucked "
    "in. The skirt is high-waisted and falls to the ankles. The wedge sandals are on the feet, visible "
    "below the skirt hem. Take all garment appearance from the board only."
)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c = ComfyUIClient()
    person = c.upload_image(PERSON)
    board = c.upload_image(BOARD)
    wf = fill_workflow(load_template("qie2511_vton"), {
        "__PERSON_IMAGE__": person, "__REF_IMAGE__": board,
        "__POSITIVE_PROMPT__": PROMPT, "__NEGATIVE_PROMPT__": "",
        "__CFG__": 4.0, "__SAMPLER__": "euler", "__SCHEDULER__": "simple",
        "__SEED__": 42, "__STEPS__": 20, "__OUTPUT_PREFIX__": "e014_qie", "__DENOISE__": 1.0,
    })
    t0 = time.monotonic()
    outs = c.poll(c.submit(wf), timeout=600)
    dst = OUT / "e014_qie.png"
    for no in outs.values():
        for im in no.get("images", []):
            if im.get("filename", "").startswith("e014_qie"):
                dst.write_bytes(c.download(im["filename"], im.get("subfolder", ""), im.get("type", "output")))
    c.free()
    print(f"done {round(time.monotonic()-t0,1)}s -> {dst.relative_to(ROOT)}")
    print("OWNER CHECKPOINT pending after checks: blouse untucked? skirt? shoes visible? identity?")


if __name__ == "__main__":
    main()
