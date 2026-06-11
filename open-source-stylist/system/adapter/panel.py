"""Reference panel builder.

Crops each garment reference image to the garment region (via segmentation),
then composites the crops into a single tiled panel image for use as the
reference conditioning input to QIE-2511.

Segmentation requires a live ComfyUI instance.  VRAM note: call this before
loading QIE-2511 — SAM/GroundingDINO and QIE-2511 fp8 together exceed 16GB.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image

from ..clients.comfyui import ComfyUIClient
from ..segmentation.grounded_sam import segment
from .prompt import item_sam_prompt


def build_panel(
    outfit_package: dict,
    output_dir: str | Path,
    client: ComfyUIClient,
    cell_size: int = 256,
    max_cols: int = 3,
) -> Path:
    """Build a tiled reference panel from all garment reference images.

    For each item in the outfit, each reference image is segmented to isolate
    the garment region.  The resulting crops are tiled into a grid and saved
    as ``reference_panel.png`` in output_dir.

    Returns the path to the saved panel PNG.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    masks_dir = output_dir / "seg_masks"
    masks_dir.mkdir(parents=True, exist_ok=True)

    crops: list[Image.Image] = []
    for item in outfit_package["items"]:
        sam_prompt = item_sam_prompt(item)
        for ref_path in item["reference_image_paths"]:
            crop = _crop_garment(ref_path, sam_prompt, item["item_id"], masks_dir, client, cell_size)
            crops.append(crop)

    panel_path = output_dir / "reference_panel.png"
    _tile_panel(crops, panel_path, cell_size, max_cols)
    return panel_path


def _crop_garment(
    ref_path: str,
    sam_prompt: str,
    label: str,
    masks_dir: Path,
    client: ComfyUIClient,
    cell_size: int,
) -> Image.Image:
    """Segment one reference image and return a cell_size×cell_size crop."""
    ref_path = Path(ref_path)
    label_safe = f"{label}_{ref_path.stem}"

    mask_results = segment(
        image_path=ref_path,
        prompts={label_safe: sam_prompt},
        client=client,
        output_dir=masks_dir,
    )
    mask_path = Path(mask_results[label_safe])

    img = Image.open(ref_path).convert("RGBA")
    mask = Image.open(mask_path).convert("L")

    mask_arr = np.array(mask)
    img_arr = np.array(img)
    img_arr[:, :, 3] = mask_arr
    masked = Image.fromarray(img_arr)

    bbox = mask.getbbox()
    if bbox is not None:
        masked = masked.crop(bbox)
    # else: segmentation produced no foreground — use the full image as fallback

    return _fit_to_cell(masked, cell_size)


def _fit_to_cell(img: Image.Image, cell_size: int) -> Image.Image:
    """Resize img (keeping aspect ratio) into a cell_size×cell_size square with white padding."""
    img.thumbnail((cell_size, cell_size), Image.LANCZOS)
    cell = Image.new("RGBA", (cell_size, cell_size), (255, 255, 255, 255))
    x = (cell_size - img.width) // 2
    y = (cell_size - img.height) // 2
    cell.paste(img, (x, y), mask=img.split()[3] if img.mode == "RGBA" else None)
    return cell


def _tile_panel(crops: list[Image.Image], out_path: Path, cell_size: int, max_cols: int):
    n = len(crops)
    if n == 0:
        raise ValueError("No crops to tile — outfit_package has no reference images.")
    cols = min(n, max_cols)
    rows = math.ceil(n / cols)
    panel = Image.new("RGB", (cols * cell_size, rows * cell_size), (255, 255, 255))
    for i, crop in enumerate(crops):
        row, col = divmod(i, cols)
        # Flatten RGBA → RGB over white background
        bg = Image.new("RGB", (cell_size, cell_size), (255, 255, 255))
        if crop.mode == "RGBA":
            bg.paste(crop, mask=crop.split()[3])
        else:
            bg.paste(crop)
        panel.paste(bg, (col * cell_size, row * cell_size))
    panel.save(out_path)
