"""E-016 step 3 — QIE holistic pass WITH pose-control (union control-LoRA + DWPose of the source person),
same board + seed as run_qie.py, so the only changed variable is pose-control on/off. Tests whether pinning
the skeleton fixes the measured body-proportion drift (hips -10.9%, shoulder/hip +9%)."""
from pathlib import Path

from system.clients.comfyui import ComfyUIClient
from system.pipeline import build_prompt
from system.workflows import fill_workflow, load_template

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "assets/outfits/outfit_001"
OUT = Path(__file__).resolve().parent / "results"
PERSON = ROOT / "assets/person/person_front.png"
BOARD = OUT / "board.png"
LABELS = ["blouse front", "skirt front", "shoes"]
DEFERRED = ("belt", "earrings")
LORA_STRENGTH = 1.0


def _download(client, outputs, prefix, dst):
    for node in outputs.values():
        for im in node.get("images", []):
            if im.get("filename", "").startswith(prefix):
                dst.write_bytes(client.download(im["filename"], im.get("subfolder", ""), im.get("type", "output")))
                return dst
    raise RuntimeError(f"no output with prefix {prefix!r}")


if __name__ == "__main__":
    prompt = build_prompt((A / "outfit layout.txt").read_text(encoding="utf-8"), LABELS, DEFERRED)
    client = ComfyUIClient()
    wf = fill_workflow(load_template("qie2511_vton_pose"), {
        "__PERSON_IMAGE__": client.upload_image(PERSON), "__REF_IMAGE__": client.upload_image(BOARD),
        "__POSITIVE_PROMPT__": prompt, "__NEGATIVE_PROMPT__": "", "__CFG__": 4.0, "__SAMPLER__": "euler",
        "__SCHEDULER__": "simple", "__SEED__": 42, "__STEPS__": 20, "__OUTPUT_PREFIX__": "e016poseqie",
        "__DENOISE__": 1.0, "__LORA_STRENGTH__": LORA_STRENGTH})
    out = client.poll(client.submit(wf), timeout=600)
    img = _download(client, out, "e016poseqie", OUT / "qie_pose.png")
    try:
        skel = _download(client, out, "e016poseskel", OUT / "pose_skeleton.png")
        print("pose skeleton:", skel)
    except RuntimeError as e:
        print("skeleton not saved:", e)
    client.free()
    print("saved", img)
