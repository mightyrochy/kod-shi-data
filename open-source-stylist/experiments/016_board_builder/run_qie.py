"""E-016 step 2 — run the QIE holistic pass on the board built by run_board.py (no checks, no repair).
Shows the raw generation so the owner can judge identity + outfit before any repair step."""
from pathlib import Path

from system.clients.comfyui import ComfyUIClient
from system.workflows import fill_workflow, load_template

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "assets/outfits/outfit_001"
OUT = Path(__file__).resolve().parent / "results"
PERSON = ROOT / "assets/person/person_front.png"
BOARD = OUT / "board.png"
LABELS = ["blouse front", "skirt front", "shoes"]


def build_prompt(layout_text: str, items: list[str]) -> str:
    return ("Keep this exact person: face, hair, skin tone, body proportions, pose, and background "
            "unchanged. Using the reference board (image 2), re-dress them in the outfit shown. "
            f"Items worn at this stage: {', '.join(items)}. Take all garment appearance from the board only.\n"
            "Layering / what is visible where:\n" + layout_text)


def _download(client, outputs, prefix, dst):
    for node in outputs.values():
        for im in node.get("images", []):
            if im.get("filename", "").startswith(prefix):
                dst.write_bytes(client.download(im["filename"], im.get("subfolder", ""), im.get("type", "output")))
                return dst
    raise RuntimeError(f"no output with prefix {prefix!r}")


if __name__ == "__main__":
    prompt = build_prompt((A / "outfit layout.txt").read_text(encoding="utf-8"), LABELS)
    (OUT / "prompt.txt").write_text(prompt, encoding="utf-8")
    client = ComfyUIClient()
    wf = fill_workflow(load_template("qie2511_vton"), {
        "__PERSON_IMAGE__": client.upload_image(PERSON), "__REF_IMAGE__": client.upload_image(BOARD),
        "__POSITIVE_PROMPT__": prompt, "__NEGATIVE_PROMPT__": "", "__CFG__": 4.0, "__SAMPLER__": "euler",
        "__SCHEDULER__": "simple", "__SEED__": 42, "__STEPS__": 20, "__OUTPUT_PREFIX__": "e016_qie", "__DENOISE__": 1.0})
    img = _download(client, client.poll(client.submit(wf), timeout=600), "e016_qie", OUT / "qie.png")
    client.free()
    print("saved", img)
