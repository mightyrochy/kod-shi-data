"""One-shot test: layers=1, Lightning, seed=42.
Hypothesis: output_frames = 4 * layers + 1 = 5.
Frame01 = generated output; frames 02-05 = conditioning slots.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from system.clients.comfyui import ComfyUIClient
from system.adapter.adapter import _auto_resolution
from system.adapter.prompt import build_prompt

SEED   = 42
OUTFIT = ROOT / "assets/outfits/outfit_001/outfit_package.json"
PERSON = ROOT / "assets/person/person_front.png"
PANEL  = ROOT / "experiments/005_variance_baseline/results/panels/reference_panel.png"
OUT    = Path(__file__).parent / "results" / "layers_test"
OUT.mkdir(parents=True, exist_ok=True)

CLIENT = ComfyUIClient()
pkg    = json.loads(OUTFIT.read_text(encoding="utf-8"))
prompt = build_prompt(pkg)
W, H   = _auto_resolution(PERSON)
print(f"Resolution: {W}x{H}")

person_fn = CLIENT.upload_image(PERSON)
panel_fn  = CLIENT.upload_image(PANEL)
print(f"Uploaded: person={person_fn}  panel={panel_fn}")

wf = {
    "1": {"class_type": "UNETLoader",
          "inputs": {"unet_name": "qwen_image_edit_2511_fp8mixed.safetensors",
                     "weight_dtype": "default"}},
    "2": {"class_type": "CLIPLoader",
          "inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
                     "type": "qwen_image"}},
    "3": {"class_type": "LoraLoader",
          "inputs": {"model": ["1", 0], "clip": ["2", 0],
                     "lora_name": "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors",
                     "strength_model": 1.0, "strength_clip": 1.0}},
    "4": {"class_type": "VAELoader",
          "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
    "5": {"class_type": "LoadImage", "inputs": {"image": person_fn}},
    "6": {"class_type": "LoadImage", "inputs": {"image": panel_fn}},
    "7": {"class_type": "TextEncodeQwenImageEditPlus",
          "inputs": {"clip": ["3", 1], "vae": ["4", 0], "prompt": prompt,
                     "image1": ["5", 0], "image2": ["6", 0]}},
    "8": {"class_type": "TextEncodeQwenImageEditPlus",
          "inputs": {"clip": ["3", 1], "prompt": ""}},
    "9": {"class_type": "EmptyQwenImageLayeredLatentImage",
          "inputs": {"width": W, "height": H, "layers": 1, "batch_size": 1}},
    "10": {"class_type": "KSampler",
           "inputs": {"model": ["3", 0], "seed": SEED, "steps": 4,
                      "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
                      "positive": ["7", 0], "negative": ["8", 0],
                      "latent_image": ["9", 0], "denoise": 1.0}},
    "11": {"class_type": "VAEDecode",
           "inputs": {"samples": ["10", 0], "vae": ["4", 0]}},
    "12": {"class_type": "SaveImage",
           "inputs": {"images": ["11", 0], "filename_prefix": "layers1_test"}},
}

print("Submitting layers=1 job...")
t0 = time.monotonic()
pid = CLIENT.submit(wf)
outputs = CLIENT.poll(pid, timeout=300.0)
elapsed = time.monotonic() - t0
print(f"Done in {elapsed:.0f}s")

frames = []
for node_out in outputs.values():
    for img_info in node_out.get("images", []):
        if img_info.get("filename", "").startswith("layers1_test"):
            data = CLIENT.download(img_info["filename"],
                                   img_info.get("subfolder", ""),
                                   img_info.get("type", "output"))
            idx = len(frames) + 1
            path = OUT / f"layers1_frame{idx:02d}.png"
            path.write_bytes(data)
            frames.append(path)

CLIENT.free()
print(f"\nResult: {len(frames)} frames (hypothesis predicted 5)")
print(f"Formula check: 4*layers+1 = 4*1+1 = 5")
print(f"Files: {[p.name for p in frames]}")
