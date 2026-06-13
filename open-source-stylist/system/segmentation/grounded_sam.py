"""Segmentation via GroundingDINO + SAM (comfyui_segment_anything pack).

ComfyUI workflow per label:
  LoadImage → SAMModelLoader → GroundingDinoModelLoader
  → GroundingDinoSAMSegment → ImpactFlattenMask → MaskToImage → SaveImage

Returns a dict {label: mask_png_path} compatible with RegionMap schema.

Model files required (already present in models/):
  models/sams/sam_vit_h_4b8939.pth
  models/grounding-dino/groundingdino_swint_ogc.pth
"""

from __future__ import annotations

import uuid
from pathlib import Path

import cv2
import numpy as np

from ..clients.comfyui import ComfyUIClient

# Model names as ComfyUI node dropdowns expect them
_SAM_MODEL = "sam_vit_h (2.56GB)"
_GDINO_MODEL = "GroundingDINO_SwinT_OGC (694MB)"


def segment(
    image_path: str | Path,
    prompts: dict[str, str],
    client: ComfyUIClient,
    output_dir: str | Path,
    threshold: float = 0.3,
) -> dict[str, str]:
    """Segment regions from image_path using text prompts.

    Args:
        image_path: source image (any format ComfyUI LoadImage accepts).
        prompts: {label: text_prompt}, e.g. {"person": "person", "top": "shirt . top"}.
                 GroundingDINO uses period-separated phrases as multi-label queries.
        client: ComfyUIClient pointing at the running ComfyUI instance.
        output_dir: directory where mask PNGs will be saved as {label}.png.
        threshold: GroundingDINO confidence threshold (0.3 is a reasonable default;
                   raise if too many false positives, lower if missing detections).

    Returns:
        {label: absolute_path_to_mask_png}
        Mask PNG: grayscale, 255 = foreground, 0 = background.
        If GroundingDINO finds nothing, mask is all zeros (caller should check).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    upload_name = client.upload_image(image_path)

    results: dict[str, str] = {}
    for label, prompt in prompts.items():
        mask_path = _run_label(client, upload_name, prompt, label, output_dir, threshold)
        results[label] = str(mask_path)

    return results


def _run_label(
    client: ComfyUIClient,
    upload_name: str,
    prompt: str,
    label: str,
    output_dir: Path,
    threshold: float,
) -> Path:
    prefix = f"seg_{label}_{uuid.uuid4().hex[:8]}"
    workflow = _build_workflow(upload_name, prompt, threshold, prefix)

    prompt_id = client.submit(workflow)
    outputs = client.poll(prompt_id, timeout=120.0)

    for node_out in outputs.values():
        for img_info in node_out.get("images", []):
            if img_info.get("filename", "").startswith(prefix):
                data = client.download(
                    img_info["filename"],
                    img_info.get("subfolder", ""),
                    img_info.get("type", "output"),
                )
                out_path = output_dir / f"{label}.png"
                out_path.write_bytes(data)
                return out_path

    raise RuntimeError(
        f"No output image produced for label '{label}' (prompt='{prompt}'). "
        "Check ComfyUI logs for segmentation errors."
    )


def _largest_area_mask(mask_data: bytes) -> bytes:
    """From a union mask PNG, return only its largest connected component.

    ImpactFlattenMask unions ALL GroundingDINO detections, which can absorb
    adjacent garments or background model bodies into a single merged mask.
    Keeping only the largest connected component selects the primary detected
    instance and discards spurious secondary detections.

    If the mask has zero or one component (empty or already single), the input
    bytes are returned unchanged.
    """
    arr = np.frombuffer(mask_data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise RuntimeError("_largest_area_mask: cv2.imdecode returned None")

    binary = (img > 128).astype(np.uint8)
    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)

    # n_labels includes background (label 0); skip it.
    if n_labels <= 2:
        # 1 = only background (empty mask), 2 = one foreground component.
        return mask_data

    # stats rows: [left, top, width, height, area]; row 0 = background.
    areas = stats[1:, cv2.CC_STAT_AREA]
    best_label = int(areas.argmax()) + 1  # +1 to account for skipped background row

    selected = np.where(labels == best_label, np.uint8(255), np.uint8(0))
    ok, encoded = cv2.imencode(".png", selected)
    if not ok:
        raise RuntimeError("_largest_area_mask: cv2.imencode failed")
    return encoded.tobytes()


def _build_workflow(
    image_name: str,
    prompt: str,
    threshold: float,
    filename_prefix: str,
) -> dict:
    """Build ComfyUI workflow JSON for one label."""
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": image_name},
        },
        "2": {
            "class_type": "SAMModelLoader (segment anything)",
            "inputs": {"model_name": _SAM_MODEL},
        },
        "3": {
            "class_type": "GroundingDinoModelLoader (segment anything)",
            "inputs": {"model_name": _GDINO_MODEL},
        },
        "4": {
            "class_type": "GroundingDinoSAMSegment (segment anything)",
            "inputs": {
                "sam_model": ["2", 0],
                "grounding_dino_model": ["3", 0],
                "image": ["1", 0],
                "prompt": prompt,
                "threshold": threshold,
            },
        },
        # ImpactFlattenMask collapses (N, H, W) batch → single (H, W) mask
        # by taking the union of all detected-object masks.
        "5": {
            "class_type": "ImpactFlattenMask",
            "inputs": {"masks": ["4", 1]},
        },
        "6": {
            "class_type": "MaskToImage",
            "inputs": {"mask": ["5", 0]},
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["6", 0],
                "filename_prefix": filename_prefix,
            },
        },
    }
