"""Diagnostic: compare 3 workflow configs, seed=42.

Config A: 40 steps, no Lightning, layers=2  (current E-005 plan)
Config B:  4 steps, Lightning LoRA, layers=2 (archived approach)
Config C: 40 steps, no Lightning, layers=3  (node default)

All frames from each run are saved so we can identify which frame
is the actual generated output vs conditioning frames.
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

OUT = Path(__file__).parent / "results" / "config_test"
OUT.mkdir(parents=True, exist_ok=True)

CLIENT = ComfyUIClient()


def base_workflow(person_fn, ref_fn, prompt, seed, steps, layers, prefix):
    return {
        "1": {"class_type": "UNETLoader",
              "inputs": {"unet_name": "qwen_image_edit_2511_fp8mixed.safetensors",
                         "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
                         "type": "qwen_image"}},
        "3": {"class_type": "VAELoader",
              "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "4": {"class_type": "LoadImage", "inputs": {"image": person_fn}},
        "5": {"class_type": "LoadImage", "inputs": {"image": ref_fn}},
        "6": {"class_type": "TextEncodeQwenImageEditPlus",
              "inputs": {"clip": ["2", 0], "vae": ["3", 0], "prompt": prompt,
                         "image1": ["4", 0], "image2": ["5", 0]}},
        "7": {"class_type": "TextEncodeQwenImageEditPlus",
              "inputs": {"clip": ["2", 0], "prompt": ""}},
        "8": {"class_type": "EmptyQwenImageLayeredLatentImage",
              "inputs": {"width": W, "height": H, "layers": layers, "batch_size": 1}},
        "9": {"class_type": "KSampler",
              "inputs": {"model": ["1", 0], "seed": seed, "steps": steps,
                         "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
                         "positive": ["6", 0], "negative": ["7", 0],
                         "latent_image": ["8", 0], "denoise": 1.0}},
        "10": {"class_type": "VAEDecode",
               "inputs": {"samples": ["9", 0], "vae": ["3", 0]}},
        "11": {"class_type": "SaveImage",
               "inputs": {"images": ["10", 0], "filename_prefix": prefix}},
    }


def lightning_workflow(person_fn, ref_fn, prompt, seed, steps, layers, prefix):
    return {
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
        "6": {"class_type": "LoadImage", "inputs": {"image": ref_fn}},
        "7": {"class_type": "TextEncodeQwenImageEditPlus",
              "inputs": {"clip": ["3", 1], "vae": ["4", 0], "prompt": prompt,
                         "image1": ["5", 0], "image2": ["6", 0]}},
        "8": {"class_type": "TextEncodeQwenImageEditPlus",
              "inputs": {"clip": ["3", 1], "prompt": ""}},
        "9": {"class_type": "EmptyQwenImageLayeredLatentImage",
              "inputs": {"width": W, "height": H, "layers": layers, "batch_size": 1}},
        "10": {"class_type": "KSampler",
               "inputs": {"model": ["3", 0], "seed": seed, "steps": steps,
                          "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
                          "positive": ["7", 0], "negative": ["8", 0],
                          "latent_image": ["9", 0], "denoise": 1.0}},
        "11": {"class_type": "VAEDecode",
               "inputs": {"samples": ["10", 0], "vae": ["4", 0]}},
        "12": {"class_type": "SaveImage",
               "inputs": {"images": ["11", 0], "filename_prefix": prefix}},
    }


def run_config(label, wf, prefix):
    print(f"\n--- {label} ---")
    pid = CLIENT.submit(wf)
    print(f"  submitted {pid[:8]}...", end=" ", flush=True)
    t0 = time.monotonic()
    outputs = CLIENT.poll(pid, timeout=600.0)
    elapsed = time.monotonic() - t0
    print(f"done in {elapsed:.0f}s")

    frames = []
    for node_out in outputs.values():
        for img_info in node_out.get("images", []):
            if img_info.get("filename", "").startswith(prefix):
                data = CLIENT.download(img_info["filename"],
                                       img_info.get("subfolder", ""),
                                       img_info.get("type", "output"))
                idx = len(frames) + 1
                path = OUT / f"{label}_frame{idx:02d}.png"
                path.write_bytes(data)
                frames.append(path)
    print(f"  {len(frames)} frames -> {[p.name for p in frames]}")
    return frames


if __name__ == "__main__":
    pkg    = json.loads(OUTFIT.read_text(encoding="utf-8"))
    prompt = build_prompt(pkg)
    W, H   = _auto_resolution(PERSON)
    print(f"Resolution: {W}x{H},  seed={SEED}")
    print(f"Prompt: {prompt[:80]}...")

    person_fn = CLIENT.upload_image(PERSON)
    panel_fn  = CLIENT.upload_image(PANEL)
    print(f"Uploaded: person={person_fn}  panel={panel_fn}")

    # Config A: 40 steps, no LoRA, layers=2
    wf_a = base_workflow(person_fn, panel_fn, prompt, SEED, 40, 2, "cfg_A")
    frames_a = run_config("A_40step_layers2", wf_a, "cfg_A")
    CLIENT.free()
    print("  /free")

    # Config B: 4 steps, Lightning, layers=2
    wf_b = lightning_workflow(person_fn, panel_fn, prompt, SEED, 4, 2, "cfg_B")
    frames_b = run_config("B_lightning_layers2", wf_b, "cfg_B")
    CLIENT.free()
    print("  /free")

    # Config C: 40 steps, no LoRA, layers=3
    wf_c = base_workflow(person_fn, panel_fn, prompt, SEED, 40, 3, "cfg_C")
    frames_c = run_config("C_40step_layers3", wf_c, "cfg_C")
    CLIENT.free()
    print("  /free")

    print(f"\nAll done. Results in {OUT.relative_to(ROOT)}")
    print(f"  A ({len(frames_a)} frames): {[p.name for p in frames_a]}")
    print(f"  B ({len(frames_b)} frames): {[p.name for p in frames_b]}")
    print(f"  C ({len(frames_c)} frames): {[p.name for p in frames_c]}")
